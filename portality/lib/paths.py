import os

def rel2abs(file, *args):
    file = os.path.realpath(file)
    if os.path.isfile(file):
        file = os.path.dirname(file)
    return os.path.abspath(os.path.join(file, *args))

def list_subdirs(path):
    return [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]