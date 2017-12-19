from doajtest.helpers import DoajTestCase
from parameterized import parameterized, param

from doajtest.fixtures import ApplicationFixtureFactory

from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions

from werkzeug.datastructures import MultiDict
from portality.formcontext import formcontext


def load_formcontext_cases():
    application_source = ApplicationFixtureFactory.make_application_source()
    application = models.Suggestion(**application_source)

    application_form = ApplicationFixtureFactory.make_application_form_info()
    form_data = MultiDict(application_form)

    # generate the comparison functions
    application_publisher_source = comparator_closure(formcontext.PublisherUpdateRequest, True, True, False)
    application_publisher_form_data = comparator_closure(formcontext.PublisherUpdateRequest, True, True, True)

    return [
        param("unnown_type", "unknown", "publisher", raises=exceptions.NoSuchFormContext),
        param("application_unknown_role", "application", "unknown", none_result=True),
        param("application_publisher_source", "application", "publisher", source=application, comparator=application_publisher_source),
        param("application_publisher_form_data", "application", "publisher", form_data=form_data, source=application, comparator=application_publisher_form_data)
    ]


def comparator_closure(instance, form, source, form_data):
    def comparator(fc):
        assert isinstance(fc, instance)

        if form:
            assert fc.form is not None
        else:
            assert fc.form is None

        if source:
            assert fc.source is not None
        else:
            assert fc.source is None

        if form_data:
            assert fc.form_data is not None
        else:
            assert fc.form_data is None

    return comparator


class TestBLLFormContext(DoajTestCase):

    @parameterized.expand(load_formcontext_cases)
    def test_01_formcontext_factory(self, name, type, role, source=None, form_data=None, none_result=False, raises=None, comparator=None):
        doaj = DOAJ()

        if raises is not None:
            with self.assertRaises(raises):
                fc = doaj.formcontext(type, role, source=source, form_data=form_data)
        else:
            fc = doaj.formcontext(type, role, source=source, form_data=form_data)
            if none_result is True:
                assert fc is None
            else:
                if comparator is not None:
                    comparator(fc)
                else:
                    assert fc is not None