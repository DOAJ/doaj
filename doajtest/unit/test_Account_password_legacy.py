import hashlib
from doajtest.helpers import DoajTestCase
from portality import models


class TestAccountPasswordLegacy(DoajTestCase):
    def test_legacy_password_upgrade_plain_sha1(self):
        """ Test that a plain SHA1 hash (legacy) is verified and upgraded. """
        password = "password123"
        # Create legacy SHA1 hex digest
        legacy_hash = hashlib.sha1(password.encode('utf-8')).hexdigest()

        acc = models.Account()
        acc.set_id("test_legacy_user")
        # Manually inject the legacy hash into the data
        acc.data['password'] = legacy_hash
        acc.save(blocking=True)

        # Pull fresh copy
        acc = models.Account.pull("test_legacy_user")

        # Check password - should return True and trigger upgrade
        self.assertTrue(acc.check_password(password))

        # Reload to verify persistence of the upgrade
        acc = models.Account.pull("test_legacy_user")
        current_hash = acc.data['password']

        self.assertNotEqual(current_hash, legacy_hash)
        self.assertFalse(models.Account._is_legacy_sha1_hash(current_hash))
        # Verify the new hash still works (via standard Werkzeug check inside check_password)
        self.assertTrue(acc.check_password(password))

    def test_legacy_password_upgrade_salted_sha1(self):
        """ Test that a salted SHA1 hash (sha1$salt$hash) is verified and upgraded. """
        password = "password456"
        salt = "somesalt"
        # Create legacy salted hash: sha1(salt + password)
        h = hashlib.sha1((salt + password).encode('utf-8')).hexdigest()
        legacy_salted = f"sha1${salt}${h}"

        acc = models.Account()
        acc.set_id("test_legacy_salted_user")
        acc.data['password'] = legacy_salted
        acc.save(blocking=True)

        # Pull fresh copy
        acc = models.Account.pull("test_legacy_salted_user")

        # Check password
        self.assertTrue(acc.check_password(password))

        # Reload to verify persistence
        acc = models.Account.pull("test_legacy_salted_user")
        current_hash = acc.data['password']

        self.assertNotEqual(current_hash, legacy_salted)
        self.assertFalse(current_hash.startswith('sha1$'))
        # Verify new hash works
        self.assertTrue(acc.check_password(password))