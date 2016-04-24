# -*- coding: utf-8 -*-
import os
import json as pyjson

import marshmallow as ma

__version__ = '0.1.0.dev0'

class EnvError(Exception):
    pass

def method_for_field(field_or_factory, name, preprocess=None):
    def method(self, name, subcast=None, **kwargs):
        if isinstance(field_or_factory, type) and issubclass(field_or_factory, ma.fields.Field):
            field = field_or_factory(**kwargs)
        else:
            field = field_or_factory(subcast=subcast, **kwargs)
        raw_value = os.environ.get(name, ma.missing)
        if raw_value is ma.missing and field.missing is ma.missing:
            raise EnvError('Environment variable "{}" not set'.format(name))
        value = raw_value or field.missing
        if preprocess:
            value = preprocess(value, subcast=subcast, **kwargs)
        try:
            return field.deserialize(value)
        except ma.ValidationError as err:
            raise EnvError('Environment variable "{}" invalid: {}'.format(name, err.args[0]))
    method.__name__ = name
    return method

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
    get = method_for_field(ma.fields.Field, 'get')
    str = method_for_field(ma.fields.Str, 'str')
    int = method_for_field(ma.fields.Int, 'int')
    float = method_for_field(ma.fields.Float, 'float')
    bool = method_for_field(ma.fields.Bool, 'bool')
    decimal = method_for_field(ma.fields.Decimal, 'decimal')
    list = method_for_field(_make_list_field, 'list', preprocess=_preprocess_list)
    dict = method_for_field(ma.fields.Dict, 'dict', preprocess=_preprocess_dict)
    json = method_for_field(ma.fields.Field, 'json', preprocess=_preprocess_json)
    datetime = method_for_field(ma.fields.DateTime, 'datetime')
