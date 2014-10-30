from unittest import TestCase
from portality import core, dao
from doajtest.bootstrap import prepare_for_test
import time
import dictdiffer

prepare_for_test()

class DoajTestCase(TestCase):
    def setUp(self):
        core.initialise_index(core.app)
        time.sleep(1)

    def tearDown(self):
        dao.DomainObject.destroy_index()
        time.sleep(1)

def diff_dicts(d1, d2, d1_label='d1', d2_label='d2', print_unchanged=False):
    """
    Diff two dictionaries - prints changed, added and removed keys and the changed values. DOES NOT DO NESTED DICTS!

    :param d1: First dict - we compare this with d2
    :param d2: Second dict - we compare against this one
    :param d1_label: Will be used instead of "d1" in debugging output to make it more helpful.
    :param d2_label: Will be used instead of "d2" in debugging output to make it more helpful.
    :param print_unchanged: - should we print set of unchanged keys (can be long and useless). Default: False.
    :return: nothing, prints results to STDOUT
    """
    differ = dictdiffer.DictDiffer(d1, d2)
    print 'Added :: keys present in {d1} which are not in {d2}'.format(d1=d1_label, d2=d2_label)
    print differ.added()
    print
    print 'Removed :: keys present in {d2} which are not in {d1}'.format(d1=d1_label, d2=d2_label)
    print differ.removed()
    print
    print 'Changed :: keys which are the same in {d1} and {d2} but whose values are different'.format(d1=d1_label, d2=d2_label)
    print differ.changed()
    print

    if differ.changed():
        print 'Changed values :: the values of keys which have changed. Format is as follows:'
        print '  Key name:'
        print '    value in {d1}'.format(d1=d1_label)
        print '    value in {d2}'.format(d2=d2_label)
        print
        for key in differ.changed():
            print ' ', key + ':'
            print '   ', d1[key]
            print '   ', d2[key]
            print
        print

    if print_unchanged:
        print 'Unchanged :: keys which are the same in {d1} and {d2} and whose values are also the same'.format(d1=d1_label, d2=d2_label)
        print differ.unchanged()
