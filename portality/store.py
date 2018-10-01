from portality.core import app
from portality.lib import plugin

import os, shutil, codecs, boto3

class StoreException(Exception):
    pass

class StoreFactory(object):

    @classmethod
    def get(cls, scope):
        """
        Returns an implementation of the base Store class
        """
        si = app.config.get("STORE_IMPL")
        sm = plugin.load_class(si)
        return sm(scope)

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

    def __init__(self, scope):
        pass

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

class StoreS3(Store):
    """
    Primitive local storage system.  Use this for testing in place of remote store
    """
    def __init__(self, scope):
        cfg = app.config.get("STORE_S3_SCOPES", {}).get(scope)
        access_key = cfg.get("aws_access_key_id")
        secret = cfg.get("aws_secret_access_key")
        if access_key is None or secret is None:
            raise StoreException("'aws_access_key_id' and 'aws_secret_access_key' must be set in STORE_S3_SCOPE for scope '{x}'".format(x=scope))

        self.client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret
        )

    def store(self, container_id, target_name, source_path=None, source_stream=None):
        # Note that this assumes the container (bucket) exists
        if source_path is not None:
            with codecs.open(source_path, "rb", "utf-8") as f:
                self.client.put_object(Bucket=container_id, Body=f, Key=target_name)
        elif source_stream is not None:
            self.client.put_object(Bucket=container_id, Body=source_stream, Key=target_name)

    def exists(self, container_id):
        pass

    def list(self, container_id):
        pass

    def get(self, container_id, target_name):
        obj = self.client.get_object(Bucket=container_id, Key=target_name)
        body = obj["Body"]
        return body

    def delete(self, container_id, target_name=None):
        pass


class StoreLocal(Store):
    def __init__(self, scope):
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
