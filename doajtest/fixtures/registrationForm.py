from werkzeug.datastructures import ImmutableMultiDict, CombinedMultiDict
from portality.core import app

def get_longer_time_than_hp_threshold():
    return app.config.get("HONEYPOT_TIMER_THRESHOLD", 5000) + 100

def get_shorter_time_than_hp_threshold():
    return app.config.get("HONEYPOT_TIMER_THRESHOLD", 5000) - 100

COMMON = ImmutableMultiDict([
    ('next', '/register'),
])

VALID_FORM = ImmutableMultiDict([
    ('name', 'Aga'),
    ('sender_email', 'aga@example.com'),
])

INVALID_FORM = ImmutableMultiDict([
    ('name', 'Aga'),
    ('sender_email', ''),
])

VALID_HONEYPOT = ImmutableMultiDict([
    ('email', ''),
    ('hptimer', get_longer_time_than_hp_threshold())
])

INVALID_HONEYPOT_TIMER_BELOW_THRESHOLD = ImmutableMultiDict([
    ('email', ''),
    ('hptimer', get_shorter_time_than_hp_threshold())
])

INVALID_HONEYPOT_EMAIL_NOT_EMPTY = ImmutableMultiDict([
    ('email', 'this_field@should_be.empty'),
    ('hptimer', get_shorter_time_than_hp_threshold())
])

INVALID_HONEYPOT_BOTH_FIELDS = ImmutableMultiDict([
    ('email', 'this_field@should_be.empty'),
    ('hptimer', get_longer_time_than_hp_threshold())
])

# Method 1: Valid form with valid honeypot
def create_valid_form_with_valid_honeypot():
    return CombinedMultiDict([COMMON, VALID_FORM, VALID_HONEYPOT])

# Method 2: Valid form with invalid honeypot (timer exceeds threshold)
def create_valid_form_with_invalid_honeypot_timer_exceeds():
    return CombinedMultiDict([COMMON, VALID_FORM, INVALID_HONEYPOT_TIMER_BELOW_THRESHOLD])

# Method 3: Valid form with invalid honeypot (email not empty)
def create_valid_form_with_invalid_honeypot_email_not_empty():
    return CombinedMultiDict([COMMON, VALID_FORM, INVALID_HONEYPOT_EMAIL_NOT_EMPTY])

# Method 4: Invalid form with valid honeypot
def create_invalid_form_with_valid_honeypot():
    return CombinedMultiDict([COMMON, INVALID_FORM, VALID_HONEYPOT])

# Method 5: Invalid form with invalid honeypot (timer exceeds threshold)
def create_invalid_form_with_invalid_honeypot_timer_exceeds():
    return CombinedMultiDict([COMMON, INVALID_FORM, INVALID_HONEYPOT_TIMER_BELOW_THRESHOLD])

# Method 6: Invalid form with invalid honeypot (email not empty)
def create_invalid_form_with_invalid_honeypot_email_not_empty():
    return CombinedMultiDict([COMMON, INVALID_FORM, INVALID_HONEYPOT_EMAIL_NOT_EMPTY])

# Method 7: Valid form with invalid honeypot (both fields)
def create_valid_form_with_invalid_honeypot_both_fields():
    return CombinedMultiDict([COMMON, VALID_FORM, INVALID_HONEYPOT_BOTH_FIELDS])

# Method 8: Invalid form with invalid honeypot (both fields)
def create_invalid_form_with_invalid_honeypot_both_fields():
    return CombinedMultiDict([COMMON, INVALID_FORM, INVALID_HONEYPOT_BOTH_FIELDS])
