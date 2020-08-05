import types

from doajtest.helpers import DoajTestCase
from portality import util


class TestUtil(DoajTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_batch_up(self):
        """ Test and document how the batching up function works """
        long_list = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]  # len(long_list) is 22

        lazy_batches = util.batch_up(long_list, batch_size=5)
        assert isinstance(lazy_batches, types.GeneratorType), type(lazy_batches)

        batches = []
        for batch in lazy_batches:
            batches.append(batch)
        assert isinstance(batches, list), type(batches)
        assert len(batches) == 5, len(batches)

        assert isinstance(batches[0], list), "wrong type {} for batch {} of {}".format(type(batches[0]), 0, len(batches))
        assert batches[0] == [10, 11, 12, 13, 14], batches[0]
        assert isinstance(batches[1], list), "wrong type {} for batch {} of {}".format(type(batches[1]), 1, len(batches))
        assert batches[1] == [15, 16, 17, 18, 19], batches[1]
        assert isinstance(batches[2], list), "wrong type {} for batch {} of {}".format(type(batches[2]), 2, len(batches))
        assert batches[2] == [20, 21, 22, 23, 24], batches[2]
        assert isinstance(batches[3], list), "wrong type {} for batch {} of {}".format(type(batches[3]), 3, len(batches))
        assert batches[3] == [25, 26, 27, 28, 29], batches[3]
        assert isinstance(batches[4], list), "wrong type {} for batch {} of {}".format(type(batches[4]), 4, len(batches))
        assert batches[4] == [30, 31], batches[4]
