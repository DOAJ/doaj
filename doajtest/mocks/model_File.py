class ModelFileMockFactory(object):

    def __init__(self, filename="filename.xml", stream=None):
        self.filename = filename
        self.stream = stream

    def save(self, path):
        with open(path, "w") as f:
            f.write(self.stream.read())
