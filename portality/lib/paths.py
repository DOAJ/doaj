import os
import tempfile
from pathlib import Path


def rel2abs(file, *args):
    file = os.path.realpath(file)
    if os.path.isfile(file):
        file = os.path.dirname(file)
    return os.path.abspath(os.path.join(file, *args))


def list_subdirs(path):
    return [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]


def get_project_root():
    """ Should return folder path of `doaj` """
    return Path(os.path.dirname(os.path.dirname(__file__))).parent


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
