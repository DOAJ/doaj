# import os
# import pandas as pd
# from doajtest.helpers import DoajTestCase
# from portality.scripts import journal_urls, link_checker_report as report
#
#
# class TestCSVtoHTML(DoajTestCase):
#     def setUp(self):
#         self.df = pd.DataFrame({
#             'Journal ID': [1, 2, 3],
#             'Journal URL': ['http://example1.com', 'http://example2.com', None],
#             'URL in DOAJ': ['http://example1.com', 'http://example2.com', None]
#         })
#         self.df.to_csv('test_data.csv', index=False)
#         self.file_name_base = 'test_file'
#         self.rows_count = 2
#
#     def test_get_csv_file_name(self):
#         csv_file_name = journal_urls.get_csv_file_name()
#         self.assertEqual(csv_file_name, 'doaj_journals_links.csv')
#
#     def test_add_link(self):
#         df_test = journal_urls.add_link(self.df.copy(), 'Journal URL')
#         df_expected = self.df.copy()
#         df_expected['Journal URL'] = ['<a href="http://example1.com">http://example1.com</a>', '<a href="http://example2.com">http://example2.com</a>', ""]
#         pd.testing.assert_frame_equal(df_test, df_expected)
#
#     def test_select_columns(self):
#         columns = ['Journal ID', 'Journal URL']
#         df_test = journal_urls.select_columns(self.df, columns)
#         df_expected = self.df.loc[:, columns]
#         pd.testing.assert_frame_equal(df_test, df_expected)
#
#     def test_read_csv(self):
#         self.df.to_csv('test_data.csv', index=False)
#         df_test = journal_urls.read_csv('test_data.csv')
#         pd.testing.assert_frame_equal(df_test, self.df)
#
#     def test_generate_html_files(self):
#         journal_urls.generate_html_files(self.df, self.file_name_base, self.rows_count)
#         for i in range(len(self.df) // self.rows_count):
#             file_name = self.file_name_base + f'{i + 1}.html'
#             self.assertTrue(os.path.exists(file_name))
#
#     def tearDown(self):
#         if os.path.exists('test_data.csv'):
#             os.remove('test_data.csv')
#         for i in range(len(self.df) // self.rows_count):
#             file_name = self.file_name_base + f'{i + 1}.html'
#             if os.path.exists(file_name):
#                 os.remove(file_name)
#
#
# class TestLinkCheck(DoajTestCase):
#     def setUp(self):
#         self.journal_df = pd.DataFrame({
#             'Journal title': ['Journal1', 'Journal2', 'Journal3'],
#             'Added on Date': ['01-01-2021', '02-02-2021', '03-03-2021'],
#             'Last updated Date': ['01-02-2021', '02-03-2021', '03-04-2021'],
#             'Url': ['http://example1.com', 'http://example2.com', 'http://example3.com']
#         })
#         self.report_df = pd.DataFrame({
#             'url': ['http://example1.com', 'http://example2.com'],
#             'broken_check': ['OK', 'Broken'],
#             'redirect_url': ['http://example1.com', 'http://example2.com'],
#             'redirect_type': ['301', '302']
#         })
#         self.report_values = pd.DataFrame({
#             'Url': ['http://example1.com', 'http://example2.com'],
#             'BrokenCheck': ['OK', 'Broken'],
#             'RedirectUrl': ['http://example1.com', 'http://example2.com'],
#             'RedirectType': ['301', '302']
#         })
#
#     def test_fetch_matching_rows(self):
#         result = report.fetch_matching_rows(self.journal_df, self.report_df.loc[0].to_dict())
#         expected_result = pd.DataFrame({
#             'Journal title': ['Journal1'],
#             'Added on Date': ['01-01-2021'],
#             'Last updated Date': ['01-02-2021'],
#             'Url': ['http://example1.com'],
#             'BrokenCheck': ['OK'],
#             'RedirectUrl': ['http://example1.com'],
#             'RedirectType': ['301']
#         })
#         pd.testing.assert_frame_equal(result, expected_result)
#
#     def test_check_links(self):
#         result = report.check_links(self.report_values, self.journal_df)
#         expected_result = pd.concat([
#             report.fetch_matching_rows(self.journal_df, self.report_df.loc[0].to_dict()),
#             report.fetch_matching_rows(self.journal_df, self.report_df.loc[1].to_dict())
#         ])
#         pd.testing.assert_frame_equal(result, expected_result)
