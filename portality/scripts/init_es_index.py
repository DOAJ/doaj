def main():
    from portality import core
    from portality.core import app, initialise_index
    initialise_index(app, core.es_connection)


if __name__ == '__main__':
    main()
