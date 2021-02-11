class FileMockFactory(object):

    def __init__(self, filename="filename.xml", stream=None):
        self.filename = filename
        self.stream = stream

    def save(self, path):
        with open(path, "wb") as f:
            try:
                f.write(self.stream.read())
            except Exception as e:
                print(str(e))
