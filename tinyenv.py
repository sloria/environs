# -*- coding: utf-8 -*-
import os
import functools
import json as pyjson

import marshmallow as ma

__version__ = '0.1.0.dev0'
__all__ = ['EnvError', 'Env']

class EnvError(Exception):
    pass

def field2parser(field_or_factory, name, preprocess=None):
    def method(self, name, default=ma.missing, subcast=None, **kwargs):
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
    method.__name__ = name
    return method

def func2parser(func, name):
    def method(self, name, default=ma.missing, subcast=None, **kwargs):
        raw_value = os.environ.get(name, default)
        if raw_value is ma.missing:
            raise EnvError('Environment variable "{}" not set'.format(name))
        value = func(raw_value)
        self._fields[name] = ma.fields.Field(**kwargs)
        self._values[name] = value
        return value
    method.__name__ = name
    return method

def dict2schema(argmap, instance=False, **kwargs):
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
    return {k.strip(): subcast(v.strip()) if subcast else v.strip()
                for k, v in (i.split('=')
                for i in value.split(',') if value)}

def _preprocess_json(value, **kwargs):
    return pyjson.loads(value)

class Env(object):
    __parser_map__ = dict(
        get=field2parser(ma.fields.Field, 'get'),
        str=field2parser(ma.fields.Str, 'str'),
        int=field2parser(ma.fields.Int, 'int'),
        float=field2parser(ma.fields.Float, 'float'),
        bool=field2parser(ma.fields.Bool, 'bool'),
        decimal=field2parser(ma.fields.Decimal, 'decimal'),
        list=field2parser(_make_list_field, 'list', preprocess=_preprocess_list),
        dict=field2parser(ma.fields.Dict, 'dict', preprocess=_preprocess_dict),
        json=field2parser(ma.fields.Field, 'json', preprocess=_preprocess_json),
        datetime=field2parser(ma.fields.DateTime, 'datetime'),
        date=field2parser(ma.fields.DateTime, 'date'),
    )
    __call__ = __parser_map__['get']

    def __init__(self):
        self._fields = {}
        self._values = {}

    def __getattr__(self, name, **kwargs):
        try:
            return functools.partial(self.__parser_map__[name], self)
        except KeyError:
            raise AttributeError('{} has not attribute {}'.format(self, name))

    def parser_for(self, name):
        """Decorator that registers a new parser method with the name ``name``.
        The decorated function must receive the input value for an environment variable.

        Example: ::

            @env.parser_for('url')
            def url(value):
                return urlparse.urlparse(value)

            env.url('MY_URL')
        """
        def decorator(func):
            self.__parser_map__[name] = func2parser(func, name=name)
            return func
        return decorator

    def parser_from_field(self, name, field_cls):
        """Decorator that registers a new parser function given a marshmallow ``Field``."""
        self.__parser_map__[name] = field2parser(field_cls, name)

    def dump(self):
        """Dump parsed environment variables to a dictionary of simple data types (numbers
        and strings).
        """
        schema = dict2schema(self._fields, instance=True)
        return schema.dump(self._values).data
