__author__ = 'steve'

from unittest import TestCase
from portality.clcsv import ClCsv
import csv
import os

class TestCsvWrapper(TestCase):

    PRFX = 'doajtest/unit/resources/'

    def setUp(self):
        # Create a CSV file to read, and objects to write
        self.gold_csv = open(self.PRFX + 'rescsv_gold_standard', 'wb')

        writer = csv.writer(self.gold_csv)
        writer.writerow(['', 'issn1', 'issn2', 'issn3', 'issn4'])
        writer.writerow(['q1', 'i1a1', 'i2a1', 'i3a1', 'i4a1'])
        writer.writerow(['q2', 'i1a2', 'i2a2', 'i3a2', 'i4a2'])
        writer.writerow(['q3', 'i1a3', 'i2a3', 'i3a3', 'i4a3'])
        writer.writerow(['q4', 'i1a4', 'i2a4', 'i3a4', 'i4a4'])
        self.gold_csv.close()

    def tearDown(self):
        # Remove aforementioned gubbins
        os.remove(self.gold_csv.name)

        # attempt to remove items created in tests
        try:
            os.remove(self.PRFX + 'test_write_csv')
        except OSError:
            pass

        try:
            os.remove(self.PRFX + 'test_overwrite_csv')
        except OSError:
            pass

    def a_test_read_01(self):
        # Check that reading the gold standard file gives the right object
        clcsv = ClCsv(self.gold_csv.name)
        assert clcsv.get_column(1) == ('issn1', ['i1a1', 'i1a2', 'i1a3', 'i1a4'])
        assert clcsv.get_column('issn1') == ('issn1', ['i1a1', 'i1a2', 'i1a3', 'i1a4'])
        assert clcsv.get_column(0) == ('', ['q1', 'q2', 'q3', 'q4'])
        assert clcsv.get_column('issn4') == ('issn4', ['i4a1', 'i4a2', 'i4a3', 'i4a4'])

    def a_test_read_02(self):
        # Create an open file object first and pass it in (a different form of CSV creation)
        f = open(self.gold_csv.name, 'rb')
        clcsv = ClCsv(f)
        assert clcsv.get_column(3) == ('issn3', ['i3a1', 'i3a2', 'i3a3', 'i3a4'])

    def a_test_read_03(self):
        # When the file object is closed
        assert self.gold_csv.closed
        clcsv = ClCsv(self.gold_csv)
        assert clcsv.get_column(3) == ('issn3', ['i3a1', 'i3a2', 'i3a3', 'i3a4'])

    def b_test_write_01(self):
        # write an object to a file, and check against pre-bult one
        wr_csv = ClCsv(self.PRFX + 'test_write_csv', 'wb')
        wr_csv.set_column('', ['q1', 'q2', 'q3', 'q4'])
        wr_csv.set_column('issn1', ['i1a1', 'i1a2', 'i1a3', 'i1a4'])
        wr_csv.set_column('issn2', ['i2a1', 'i2a2', 'i2a3', 'i2a4'])
        wr_csv.set_column('issn3', ['i3a1', 'i3a2', 'i3a3', 'i3a4'])
        wr_csv.set_column('issn4', ['i4a1', 'i4a2', 'i4a3', 'i4a4'])
        wr_csv.save()

        wr_lines = open(wr_csv.file_object.name, 'rb').readlines()
        gold_lines = open(self.gold_csv.name, 'rb').readlines()
        assert gold_lines == wr_lines

    def b_test_write_02(self):
        # Check we can overwrite an existing column.
        ow_csv = ClCsv(self.PRFX + 'test_overwrite_csv', 'wb')
        ow_csv.set_column('', ['q1', 'q2', 'q3', 'q4'])
        ow_csv.set_column('issn1', ['i1a1', 'i1a2', 'i1a3', 'i1a4'])
        ow_csv.set_column('issn2', ['i2a1', 'i2a2', 'i2a3', 'WRONG'])
        ow_csv.set_column('issn3', ['i3a1', 'i3a2', 'i3a3', 'i3a4'])
        ow_csv.set_column('issnX', ['iXa1', 'iXa2', 'iXa3', 'iXa4'])
        ow_csv.save()

        ow_csv = ClCsv(ow_csv.file_object.name, 'r+b')
        ow_csv.set_column('issn2', ['i2a1', 'i2a2', 'i2a3', 'i2a4'])
        ow_csv.set_column(4, ('issn4', ['i4a1', 'i4a2', 'i4a3', 'i4a4']))
        ow_csv.save()

        # The changes above should make the file the same as our gold standard
        ow_lines = open(ow_csv.file_object.name, 'rb').readlines()
        gold_lines = open(self.gold_csv.name, 'rb').readlines()
        assert gold_lines == ow_lines

    def c_test_gets(self):
        # test the functions which get
        rd_csv = ClCsv(self.gold_csv.name, 'rb')

        assert rd_csv.get_colnumber('issn3') == 3
        assert rd_csv.get_colnumber('pineapple') == None

        assert rd_csv.get_rownumber('q4') == 4
        assert rd_csv.get_rownumber('nothing') == None
