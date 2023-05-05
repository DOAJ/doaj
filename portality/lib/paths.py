import os
import tempfile
from pathlib import Path
from typing import Union, TypeVar

PathStr = TypeVar("PathStr", str, Path)  # type of str or Path


def rel2abs(src, *paths):
    """  Output is absolute path of paths joined with src's dir

    Example:
    >>> rel2abs('/opt/doaj/abc.xml', 'corrections.csv')
    '/opt/doaj/corrections.csv'
    >>> rel2abs('/opt/doaj/', 'corrections.csv')
    '/opt/doaj/corrections.csv'
    >>> rel2abs('/opt/doaj/abc.xml', '..', 'corrections.csv')
    '/opt/corrections.csv'

    :param src:
    :param paths:
    :return:
    """
    src = os.path.realpath(src)
    if os.path.isfile(src):
        src = os.path.dirname(src)
    return os.path.abspath(os.path.join(src, *paths))


def list_subdirs(path):
    return [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]


def get_project_root() -> Path:
    """ Should return folder path of `doaj` """
    return Path(__file__).parent.parent.parent.absolute()


def create_tmp_dir(is_auto_mkdir=False) -> Path:
    num_retry = 20
    for _ in range(num_retry):
        path = Path(tempfile.NamedTemporaryFile().name)
        if not path.exists():
            break
    else:
        raise EnvironmentError(f'create tmp dir retry [{num_retry}] failed')

    if is_auto_mkdir:
        path.mkdir(parents=True, exist_ok=True)
    return path


def abs_dir_path(src) -> str:
    return os.path.dirname(os.path.realpath(src))
