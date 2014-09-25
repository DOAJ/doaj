# Class to wrap the Python CSV library

class ClCsv():

    def __init__(self, file_path, mode):
        self.file_object = open(file_path, mode)
        pass

    def get_column(self, col_identifier):
        """
        Get a column from the CSV file.
        :param col_identifier: An int column index or a str column heading.
        :return: The column, as a { heading : [contents] } dict.
        """
        if type(col_identifier) == int:
            # get column by index
            pass
        elif type(col_identifier) == str:
            # get column by title


    def set_column(self, col_identifier, col_contents):
        """
        Set a column in the CSV file.
        :param col_identifier: An int column index or a str column heading.
        :param col_contents: The contents for the column
        """
        if type(col_identifier) == int:
            # set column by index
            pass
        elif type(col_identifier) == str:
            # set column by title


    def get_colnumber(self, header):
        """
        Return the column number of a given header
        :param header:
        :return: The column number
        """
        pass


    def get_rownumber(self, first_col_val):
        """
        Get the row number of a given first column value
        :param first_col_val:
        :return: The row number
        """
        pass
