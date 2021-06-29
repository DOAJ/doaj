from portality import datasets
from doajtest.helpers import DoajTestCase


class TestDatasets(DoajTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_countries(self):
        """ Use country information from our datasets """
        assert datasets.get_country_code('united kingdom') == 'GB', 'expected GB, received: {}'.format(datasets.get_country_name('GB'))
        assert datasets.get_country_name('GB') == 'United Kingdom', 'expected United Kingdom, received: {}'.format(datasets.get_country_name('GB'))

        # If the country is unrecognised, we send it back unchanged.
        assert datasets.get_country_code('mordor') == 'mordor'
        assert datasets.get_country_name('mordor') == 'mordor'

        # Unless fail_if_not_found is set in get_country_code()
        assert datasets.get_country_code('united states') == 'US'
        assert datasets.get_country_code('the shire', fail_if_not_found=True) is None
        assert datasets.get_country_code('the shire', fail_if_not_found=False) == 'the shire'

        # When we have more than one option, the first alphabetically is returned
        assert datasets.get_country_name('AE') == 'United Arab Emirates'

    def test_02_currencies(self):
        """ Utilise currency information from the datasets """
        assert datasets.get_currency_code('yen') == 'JPY'
        assert datasets.get_currency_name('JPY') == 'JPY - Yen'

        assert datasets.get_currency_code('pound sterling') == 'GBP'
        assert datasets.get_currency_name('GBP') == 'GBP - Pound Sterling'

        assert datasets.get_currency_code('pound') is None
        assert datasets.get_currency_code('doubloons') is None

    def test_03_languages(self):
        """ Use language information from our datasets """
        assert datasets.name_for_lang('en') == 'English'
        assert datasets.name_for_lang('eng') == 'English'
        assert datasets.language_for('English').name == 'English'

        assert datasets.language_for('german').bibliographic == 'ger'
