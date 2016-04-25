# -*- coding: utf-8 -*-
import contextlib
import functools
import json as pyjson
import os

import marshmallow as ma

__version__ = '0.1.0.dev0'
__all__ = ['EnvError', 'Env']

class EnvError(Exception):
    pass

def _field2method(field_or_factory, method_name, preprocess=None):
    def method(self, name, default=ma.missing, subcast=None, **kwargs):
        name = self._prefix + name if self._prefix else name
        missing = kwargs.pop('missing', None) or default
        if isinstance(field_or_factory, type) and issubclass(field_or_factory, ma.fields.Field):
            field = field_or_factory(missing=missing, **kwargs)
        else:
            field = field_or_factory(subcast=subcast, missing=missing, **kwargs)
        self._fields[name] = field
        raw_value = os.environ.get(name, ma.missing)
        if raw_value is ma.missing and field.missing is ma.missing:
            raise EnvError('Environment variable "{}" not set'.format(name))
        value = raw_value or field.missing
        if preprocess:
            value = preprocess(value, subcast=subcast, **kwargs)
        try:
            value = field.deserialize(value)
        except ma.ValidationError as err:
            raise EnvError('Environment variable "{}" invalid: {}'.format(name, err.args[0]))
        else:
            self._values[name] = value
            return value
    method.__name__ = method_name
    return method

def _func2method(func, method_name):
    def method(self, name, default=ma.missing, subcast=None, **kwargs):
        name = self._prefix + name if self._prefix else name
        raw_value = os.environ.get(name, default)
        if raw_value is ma.missing:
            raise EnvError('Environment variable "{}" not set'.format(name))
        value = func(raw_value)
        self._fields[name] = ma.fields.Field(**kwargs)
        self._values[name] = value
        return value
    method.__name__ = method_name
    return method

def _dict2schema(argmap, instance=False, **kwargs):
    """Generate a `marshmallow.Schema` class given a dictionary of fields.
    """
    class Meta(object):
        strict = True
    attrs = dict(argmap, Meta=Meta)
    cls = type(str(''), (ma.Schema,), attrs)
    return cls if not instance else cls(**kwargs)

def _make_list_field(**kwargs):
    subcast = kwargs.pop('subcast', None)
    inner_field = ma.Schema.TYPE_MAPPING[subcast] if subcast else ma.fields.Field
    return ma.fields.List(inner_field, **kwargs)

def _preprocess_list(value, **kwargs):
    return value if ma.utils.is_iterable_but_not_string(value) else value.split(',')

def _preprocess_dict(value, **kwargs):
    subcast = kwargs.get('subcast')
    return {key.strip(): subcast(val.strip()) if subcast else val.strip()
            for key, val in (item.split('=')
            for item in value.split(',') if value)}

def _preprocess_json(value, **kwargs):
    return pyjson.loads(value)

class Env(object):
    """An environment variable reader."""
    __parser_map__ = dict(
        get=_field2method(ma.fields.Field, 'get'),
        str=_field2method(ma.fields.Str, 'str'),
        int=_field2method(ma.fields.Int, 'int'),
        float=_field2method(ma.fields.Float, 'float'),
        bool=_field2method(ma.fields.Bool, 'bool'),
        decimal=_field2method(ma.fields.Decimal, 'decimal'),
        list=_field2method(_make_list_field, 'list', preprocess=_preprocess_list),
        dict=_field2method(ma.fields.Dict, 'dict', preprocess=_preprocess_dict),
        json=_field2method(ma.fields.Field, 'json', preprocess=_preprocess_json),
        datetime=_field2method(ma.fields.DateTime, 'datetime'),
        date=_field2method(ma.fields.Date, 'date'),
    )
    __call__ = __parser_map__['get']

    def __init__(self):
        self._fields = {}
        self._values = {}
        self._prefix = None

    def __str__(self):
        return str(self._values)

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self._values)

    @contextlib.contextmanager
    def prefixed(self, prefix):
        """Context manager for parsing envvars with a common prefix."""
        self._prefix = prefix
        yield
        self._prefix = None

    def __getattr__(self, name, **kwargs):
        try:
            partial = functools.partial(self.__parser_map__[name], self)
            return partial
        except KeyError:
            raise AttributeError('{} has not attribute {}'.format(self, name))

    def add_parser(self, name, func):
        """Register a new parser method with the name ``name``. ``func`` must
        receive the input value for an environment variable.
        """
        self.__parser_map__[name] = _func2method(func, method_name=name)
        return None

    def parser_for(self, name):
        """Decorator that registers a new parser method with the name ``name``.
        The decorated function must receive the input value for an environment variable.
        """
        def decorator(func):
            self.add_parser(name, func)
            return func
        return decorator

    def parser_from_field(self, name, field_cls):
        """Decorator that registers a new parser function given a marshmallow ``Field``."""
        self.__parser_map__[name] = _field2method(field_cls, method_name=name)

    def dump(self):
        """Dump parsed environment variables to a dictionary of simple data types (numbers
        and strings).
        """
        schema = _dict2schema(self._fields, instance=True)
        return schema.dump(self._values).data
