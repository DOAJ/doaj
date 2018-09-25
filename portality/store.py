from portality.core import app
from portality.lib import plugin

import os, shutil, codecs, requests

class StoreException(Exception):
    pass

class StoreFactory(object):

    @classmethod
    def get(cls):
        """
        Returns an implementation of the base Store class
        """
        si = app.config.get("STORE_IMPL")
        sm = plugin.load_class(si)
        return sm()

    @classmethod
    def tmp(cls):
        """
        Returns an implementation of the base Store class which should be able
        to provide local temp storage to the app.  In addition to the methods supplied
        by Store, it must also provide a "path" function to give the path on-disk to
        the file
        """
        si = app.config.get("STORE_TMP_IMPL")
        sm = plugin.load_class(si)
        return sm()

class Store(object):

    def store(self, container_id, target_name, source_path=None, source_stream=None):
        pass

    def exists(self, container_id):
        return False

    def list(self, container_id):
        pass

    def get(self, container_id, target_name):
        return None

    def delete(self, container_id, target_name=None):
        pass

class StoreLocal(Store):
    """
    Primitive local storage system.  Use this for testing in place of remote store
    """
    def __init__(self):
        self.dir = app.config.get("STORE_LOCAL_DIR")
        if self.dir is None:
            raise StoreException("STORE_LOCAL_DIR is not defined in config")

    def store(self, container_id, target_name, source_path=None, source_stream=None):
        cpath = os.path.join(self.dir, container_id)
        if not os.path.exists(cpath):
            os.makedirs(cpath)
        tpath = os.path.join(cpath, target_name)

        if source_path:
            shutil.copyfile(source_path, tpath)
        elif source_stream:
            with codecs.open(tpath, "wb") as f:
                f.write(source_stream.read())

    def exists(self, container_id):
        cpath = os.path.join(self.dir, container_id)
        return os.path.exists(cpath) and os.path.isdir(cpath)

    def list(self, container_id):
        cpath = os.path.join(self.dir, container_id)
        return os.listdir(cpath)

    def get(self, container_id, target_name):
        cpath = os.path.join(self.dir, container_id, target_name)
        if os.path.exists(cpath) and os.path.isfile(cpath):
            f = codecs.open(cpath, "r")
            return f

    def delete(self, container_id, target_name=None):
        cpath = os.path.join(self.dir, container_id)
        if target_name is not None:
            cpath = os.path.join(cpath, target_name)
        if os.path.exists(cpath):
            if os.path.isfile(cpath):
                os.remove(cpath)
            else:
                shutil.rmtree(cpath)



class TempStore(StoreLocal):
    def __init__(self):
        self.dir = app.config.get("STORE_TMP_DIR")
        if self.dir is None:
            raise StoreException("STORE_TMP_DIR is not defined in config")

    def path(self, container_id, filename, create_container=False, must_exist=True):
        container_path = os.path.join(self.dir, container_id)
        if create_container and not os.path.exists(container_path):
            os.makedirs(container_path)
        fpath = os.path.join(self.dir, container_id, filename)
        if not os.path.exists(fpath) and must_exist:
            raise StoreException("Unable to create path for container {x}, file {y}".format(x=container_id, y=filename))
        return fpath

    def list_container_ids(self):
        return [x for x in os.listdir(self.dir) if os.path.isdir(os.path.join(self.dir, x))]
