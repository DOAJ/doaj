from portality import datasets
from doajtest.helpers import DoajTestCase
from portality.lib.isolang import get_doaj_3char_lang_by_lang


class TestDatasets(DoajTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_countries(self):
        """ Use country information from our datasets """
        assert datasets.get_country_code('united kingdom') == 'GBR'
        assert datasets.get_country_name('GB') == 'United Kingdom'

        # If the country is unrecognised, we send it back unchanged.
        assert datasets.get_country_code('mordor') == 'mordor'
        assert datasets.get_country_name('mordor') == 'mordor'

        # Unless fail_if_not_found is set in get_country_code()
        assert datasets.get_country_code('united states') == 'USA'
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

        # Specific languages we were asked to correct e.g. https://github.com/DOAJ/doajPM/issues/1262
        assert datasets.name_for_lang("ro") == "Romanian"  # alpha_2
        assert datasets.name_for_lang("ron") == "Romanian"  # alpha_3
        assert datasets.name_for_lang("rum") == "Romanian"  # bibliographic
        assert datasets.name_for_lang("hr") == "Croatian"
        assert datasets.name_for_lang("hrv") == "Croatian"
        assert datasets.name_for_lang("ga") == "Irish"
        assert datasets.name_for_lang("gle") == "Irish"
        assert datasets.name_for_lang("gd") == "Scottish Gaelic"
        assert datasets.name_for_lang("gla") == "Scottish Gaelic"

    def test_04_from_options(self):
        """ Verify our lookups will resolve to the same records that the options expect """
        countries_options = datasets.country_options
        currencies_options = datasets.currency_options
        languages_options = datasets.language_options

        # We want an empty record at the start of each options list
        assert countries_options.pop(0) == ('', '')
        assert currencies_options.pop(0) == ('', '')
        assert languages_options.pop(0) == ('', '')

        for (code, name) in countries_options:
            assert datasets.get_country_name(code) == name
            assert datasets.get_country_code(name).upper() == code

        for (code, name) in currencies_options:
            # We retrieve these names as "code - name" as in "GBP - Pound Sterling"
            assert f'{datasets.get_currency_name(code)} ({code})' == f'{code} - {name}'

            # FIXME: skip post-2018 Venezuelan Bolívar Soberano; it appears twice with different codes but will be
            #  retrieved by pycountry via name as VES, the old one. Same with Sierra Leonean leone (old SLL /
            #  new SLE since July 22)
            if code in ["VED", 'SLE']:
                continue

            # Here we need to remove the (code) from the end of e.g. "Pound Sterling (GBP)" to do our lookup.
            assert datasets.get_currency_code(name[:-6]) == code

        for (code, name) in languages_options:
            assert datasets.name_for_lang(code) == name
            assert get_doaj_3char_lang_by_lang(datasets.language_for(code)).upper() == code
