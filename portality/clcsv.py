import csv, codecs
import io


class ClCsv():

    def __init__(self, file_path):
        """
        Class to wrap the Python CSV library. Allows reading and writing by column.
        :param file_path: A file object or path to a file. Will create one at specified path if it does not exist.
        """

        # Store the csv contents in a list of tuples, [ (column_header, [contents]) ]
        self.data = []

        # Get an open file object from the given file_path or file object
        if type(file_path) == file:
            self.file_object = file_path
            if self.file_object.closed:
                self.file_object = codecs.open(self.file_object.name, 'r+b', encoding='utf-8')
            self.read_file()
        else:
            try:
                self.file_object = codecs.open(file_path, 'r+b', encoding='utf-8')
                self.read_file()
            except IOError:
                # If the file doesn't exist, create it.
                self.file_object = codecs.open(file_path, 'w+b', encoding='utf-8')

    def read_file(self):
        """
        Retrieve all of the information from the stored file using standard csv lib
        :return: Entire CSV contents, a list of rows (like the standard csv lib)
        """
        if self.file_object.closed:
            codecs.open(self.file_object.name, 'r+b', encoding='utf-8')

        reader = UnicodeReader(self.file_object)
        rows = []
        for row in reader:
            rows.append(row)

        self._populate_data(rows)
        return rows

    def headers(self):
        """
        Return the headers of all of the columns in the csv in the order that they appear
        :return: just the headers
        """
        return [h for h, _ in self.data]

    def columns(self):
        """
        Iterate over the columns in the csv in the order that they appear
        :return: a generator which yields columns
        """
        headers = self.headers()
        for h in headers:
            col = self.get_column(h)
            yield col

    def get_column(self, col_identifier):
        """
        Get a column from the CSV file.
        :param col_identifier: An int column index or a str column heading.
        :return: The column, as a { heading : [contents] } dict.
        """
        try:
            if type(col_identifier) == int:
                # get column by index
                return self.data[col_identifier]
            elif isinstance(col_identifier, str):
                # get column by title
                for col in self.data:
                    if col[0] == col_identifier:
                        return col
        except IndexError:
            return None

    def set_column(self, col_identifier, col_contents):
        """
        Set a column in the CSV file.
        :param col_identifier: An int column index or a str column heading.
        :param col_contents: The contents for the column
        """
        try:
            if type(col_identifier) == int:
                self.data[col_identifier] = col_contents
            elif isinstance(col_identifier, str):
                # set column by title.
                num = self.get_colnumber(col_identifier)
                if num is not None and type(col_contents) == list:
                    self.set_column(num, (col_identifier, col_contents))
                else:
                    raise IndexError

        except IndexError:
            # The column isn't there already; append a new one
            if type(col_identifier) == int:
                self.data.append(col_contents)
            elif isinstance(col_identifier, str):
                self.data.append((col_identifier, col_contents))

    def get_colnumber(self, header):
        """
        Return the column number of a given header
        :param header:
        :return: The column number
        """
        for i in range(0, len(self.data)):
            if self.data[i][0] == header:
                return i
        return None

    def get_rownumber(self, first_col_val):
        """
        Get the row number of a given first column value, or none if not found
        :param first_col_val:
        :return: The row number
        """

        try:
            (col_name, col_contents) = self.data[0]
            col_data = [col_name] + col_contents
            return col_data.index(first_col_val)
        except ValueError:
            return None

    def save(self):
        """
        Write and close the file.
        """
        rows = []
        # find out how many rows we're going to need to write
        max_rows = 0
        for _, cont in self.data:
            if len(cont) > max_rows:
                max_rows = len(cont)
        max_rows += 1 # add the header row

        for i in range(0, max_rows):
            row = []
            for (col_name, col_contents) in self.data:
                col_data = [col_name] + col_contents
                if len(col_data) > i:
                    row.append(col_data[i])
                else:
                    row.append("")
            rows.insert(i, row)

        # Remove current contents of file
        self.file_object.seek(0)
        self.file_object.truncate()

        # Write new CSV data
        writer = UnicodeWriter(self.file_object)
        writer.writerows(rows)
        self.file_object.close()

    def _populate_data(self, csv_rows):
        # Reset the stored data
        self.data = []
        if len(csv_rows) == 0:
            return

        # Add new data
        for i in range(0, len(csv_rows[0])):
            col_data = []
            for row in csv_rows[1:]:
                col_data.append(row[i])
            self.data.append((csv_rows[0][i], col_data))


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = f

    def __iter__(self):
        return self

    def __next__(self):
        val = next(self.reader)
        raw = val.encode("utf-8")
        if raw.startswith(codecs.BOM_UTF8):
            raw = raw.replace(codecs.BOM_UTF8, '', 1)
        return raw

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def __next__(self):
        row = next(self.reader)
        return [str(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = io.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        encoded_row = []
        for s in row:
            if s is None:
                s = ''
            if not isinstance(s, str):
                s = str(s)
            encoded_row.append(s.encode("utf-8"))
        self.writer.writerow(encoded_row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
