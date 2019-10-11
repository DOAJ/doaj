__author__ = 'steve'

from doajtest.helpers import DoajTestCase
from portality.clcsv import ClCsv
import csv
import os


class TestCsvWrapper(DoajTestCase):

    # Set this file prefix to the resources dir relative to where tests are run from.
    BASE_FILE_PATH = os.path.dirname(os.path.realpath(__file__))
    PRFX = os.path.join(BASE_FILE_PATH, "resources")

    def setUp(self):
        # Create a CSV file to read, and objects to write
        self.gold_csv = open(os.path.join(self.PRFX, 'rescsv_gold_standard'), 'w')

        writer = csv.writer(self.gold_csv)
        writer.writerow(['', 'issn1', 'issn2', 'issn3', 'issn4'])
        writer.writerow(['q1', 'i1a1', 'i2a1', 'i3a1', 19])
        writer.writerow(['q2', 'i1a2', 'i2a2', 'i3a2', None])
        writer.writerow(['q3', 'i1a3', 'i2a3', 'i3a3', 'i4a3'])
        writer.writerow(['q4', 'i1a4', 'i2a4', 'i3a4', 'i4a4'])
        self.gold_csv.close()

        self.gold_csv_unicode = open(os.path.join(self.PRFX, 'rescsv_gold_standard_unicode'), 'w')

        self.gold_csv_unicode.write("\r\n".join([u',иссн1', u'в1,ила1', u'в2,ила2', u'в3,ила3', u'в4,ила4']) + "\r\n")
        self.gold_csv_unicode.close()

    def tearDown(self):
        # Remove aforementioned gubbins
        os.remove(self.gold_csv.name)
        os.remove(self.gold_csv_unicode.name)

        # attempt to remove items created in tests
        try:
            os.remove(self.PRFX + 'test_write_csv')
        except OSError:
            pass

        try:
            os.remove(self.PRFX + 'test_overwrite_csv')
        except OSError:
            pass

    def test_01_read_01(self):
        # Check that reading the gold standard file gives the right object
        clcsv = ClCsv(self.gold_csv.name)
        assert clcsv.get_column(1) == ('issn1', ['i1a1', 'i1a2', 'i1a3', 'i1a4'])
        assert clcsv.get_column('issn1') == ('issn1', ['i1a1', 'i1a2', 'i1a3', 'i1a4'])
        assert clcsv.get_column(0) == ('', ['q1', 'q2', 'q3', 'q4'])
        assert clcsv.get_column('issn4') == ('issn4', ['19', '', 'i4a3', 'i4a4'])

    def test_02_read_02(self):
        # Create an open file object first and pass it in (a different form of CSV creation)
        f = open(self.gold_csv.name, 'r')
        clcsv = ClCsv(f)
        assert clcsv.get_column(3) == ('issn3', ['i3a1', 'i3a2', 'i3a3', 'i3a4'])

    def test_03_read_03(self):
        # When the file object is closed
        assert self.gold_csv.closed
        clcsv = ClCsv(self.gold_csv)
        assert clcsv.get_column(3) == ('issn3', ['i3a1', 'i3a2', 'i3a3', 'i3a4'])
    
    def test_08_read_unicode(self):
        # Check that reading the gold standard file gives the right object
        clcsv = ClCsv(self.gold_csv_unicode.name)
        assert clcsv.get_column(1) == ('иссн1', ['ила1', 'ила2', 'ила3', 'ила4'])
        assert clcsv.get_column('иссн1') == ('иссн1', ['ила1', 'ила2', 'ила3', 'ила4'])
        assert clcsv.get_column(0) == ('', ['в1', 'в2', 'в3', 'в4'])

    def test_04_write_01(self):
        # write an object to a file, and check against pre-bult one
        wr_csv = ClCsv(self.PRFX + 'test_write_csv')
        wr_csv.set_column('', ['q1', 'q2', 'q3', 'q4'])
        wr_csv.set_column('issn1', ['i1a1', 'i1a2', 'i1a3', 'i1a4'])
        wr_csv.set_column('issn2', ['i2a1', 'i2a2', 'i2a3', 'i2a4'])
        wr_csv.set_column('issn3', ['i3a1', 'i3a2', 'i3a3', 'i3a4'])
        wr_csv.set_column('issn4', [19, None, 'i4a3', 'i4a4'])
        wr_csv.save()

        wr_lines = open(wr_csv.file_object.name, 'r').readlines()
        gold_lines = open(self.gold_csv.name, 'r').readlines()
        assert gold_lines == wr_lines

    def test_05_write_02(self):
        # Check we can overwrite an existing column.
        ow_csv = ClCsv(self.PRFX + 'test_overwrite_csv')
        ow_csv.set_column('', ['q1', 'q2', 'q3', 'q4'])
        ow_csv.set_column('issn1', ['i1a1', 'i1a2', 'i1a3', 'i1a4'])
        ow_csv.set_column('issn2', ['i2a1', 'i2a2', 'i2a3', 'WRONG'])
        ow_csv.set_column('issn3', ['i3a1', 'i3a2', 'i3a3', 'i3a4'])
        ow_csv.set_column('issnX', ['iXa1', 'iXa2', 'iXa3', 'iXa4'])
        ow_csv.save()

        ow_csv = ClCsv(ow_csv.file_object.name)
        ow_csv.set_column('issn2', ['i2a1', 'i2a2', 'i2a3', 'i2a4'])
        ow_csv.set_column(4, ('issn4', [19, None, 'i4a3', 'i4a4']))
        ow_csv.save()

        # The changes above should make the file the same as our gold standard
        ow_lines = open(ow_csv.file_object.name, 'r').readlines()
        gold_lines = open(self.gold_csv.name, 'r').readlines()
        assert gold_lines == ow_lines

    def test_06_gets(self):
        # test the functions which get
        rd_csv = ClCsv(self.gold_csv.name)

        assert rd_csv.get_colnumber('issn3') == 3
        assert rd_csv.get_colnumber('pineapple') == None

        assert rd_csv.get_rownumber('q4') == 4
        assert rd_csv.get_rownumber('nothing') == None

    def test_07_write_unicode(self):
        # write an object to a file, and check against pre-bult one

        wr_csv = ClCsv(self.PRFX + 'test_write_csv')
        wr_csv.set_column('', ['в1', 'в2', 'в3', 'в4'])
        wr_csv.set_column('иссн1', ['ила1', 'ила2', 'ила3', 'ила4'])
        wr_csv.save()

        wr_lines = open(wr_csv.file_object.name, 'r').readlines()
        gold_lines_unicode = open(self.gold_csv_unicode.name, 'r').readlines()
        assert gold_lines_unicode == wr_lines
