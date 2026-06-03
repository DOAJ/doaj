from collections.abc import Mapping


def deep_merge(a, b, overlay=False):
    if isinstance(a, list) and isinstance(b, list):
        for item in b:
            if item not in a:
                a.append(item)
    elif isinstance(a, dict) and isinstance(b, dict):
        for key in b:
            if key in a:
                a[key] = deep_merge(a[key], b[key], overlay=overlay)
            else:
                a[key] = b[key]
    else:
        if overlay:
            return b
    return a


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if args:
            if len(args) > 1:
                raise TypeError(f"expected at most 1 positional argument, got {len(args)}")
            source = args[0]
            if isinstance(source, Mapping):
                for key, value in source.items():
                    self[key] = value
            else:
                # Keep parity with dict() support for iterable key/value pairs.
                for key, value in source:
                    self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    @classmethod
    def wrap(cls, value):
        """Recursively convert dict-like values to AttrDict values."""
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls({k: cls.wrap(v) for k, v in value.items()})
        if isinstance(value, list):
            return [cls.wrap(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls.wrap(item) for item in value)
        return value

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'AttrDict' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value

    def __setitem__(self, key, value):
        super().__setitem__(key, self.wrap(value))

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'AttrDict' object has no attribute '{name}'")