from pathlib import Path
from unittest import TestCase

from parameterized import parameterized

from portality.lib import paths


class TestPaths(TestCase):

    @parameterized.expand([
        ('/tmp/aabbcc/abc.xml', ('new.csv',), True,
         '/tmp/aabbcc/new.csv'),
        ('/tmp/aabbcc/', ('new.csv',), False,
         '/tmp/aabbcc/new.csv'),
        ('/tmp/aabbcc/abc.xml', ('..', 'new.csv',), False,
         '/tmp/new.csv'),
        ('/tmp/aabbcc/abc.xml', ('../new.csv',), False,
         '/tmp/new.csv'),
    ])
    def test_rel2abs(self, src, path_args, is_file, expected):
        if is_file:
            Path(src).parent.mkdir(parents=True, exist_ok=True)
            with open(src, 'w') as f:
                f.write('')
        assert paths.rel2abs(src, *path_args) == expected

    @parameterized.expand([
        ('/opt/doaj/abc.xml', '/opt/doaj'),
        ('/opt/doaj/', '/opt'),
        ('/opt/doaj', '/opt'),
    ])
    def test_abs_dir_path(self, input, expected):
        assert paths.abs_dir_path(input) == expected


    def test_get_project_root(self):
        assert paths.get_project_root().name == 'doaj'
        assert paths.get_project_root().joinpath('doajtest').exists()
        assert paths.get_project_root().joinpath('portality').exists()
