from flask import url_for as flask_url_for


def url_for(*args, **kwargs):
    """
    This function is a hack to allow us to use url_for where we may nor may not have the
    right request context.

    HACK: this bit of code is required because notifications called from huey using the shortcircuit event
    dispatcher do not have the correct request context, and I was unable to figure out how to set the correct
    one in the framework above.  So instead this is a dirty workaround which pushes the right test context
    if needed.

    :param args:
    :param kwargs:
    :return:
    """
    try:
        url = flask_url_for(*args, **kwargs)
    except:
        from portality.app import app as doajapp

        with doajapp.test_request_context("/"):
            url = flask_url_for(*args, **kwargs)

    return url