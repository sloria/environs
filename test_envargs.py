from __future__ import unicode_literals

from decimal import Decimal
import datetime as dt

import pytest
from marshmallow import fields

import envargs

@pytest.fixture
def set_env(monkeypatch):
    def _set_env(envvars):
        for key, val in envvars.items():
            monkeypatch.setenv(key, val)
    return _set_env


@pytest.fixture
def env():
    return envargs.Env()


class TestCasting:

    def test_get(self, set_env, env):
        set_env({'STR': 'foo', 'INT': '42'})
        assert env.get('STR') == 'foo'
        assert env.get('INT') == '42'

    def test_get_with_default(self, env):
        assert env.get('NOT_SET', default='mydefault') == 'mydefault'
        assert env.get('NOT_SET', 'mydefault') == 'mydefault'

    def test_call_is_same_as_get(self, set_env, env):
        set_env({'STR': 'foo', 'INT': '42'})
        assert env('STR') == 'foo'
        assert env('NOT_SET', 'mydefault') == 'mydefault'

    def test_basic(self, set_env, env):
        set_env({'STR': 'foo'})
        assert env.str('STR') == 'foo'

    def test_int_cast(self, set_env, env):
        set_env({'INT': '42'})
        assert env.int('INT') == 42

    def test_invalid_int(self, set_env, env):
        set_env({'INT': 'invalid'})
        with pytest.raises(envargs.EnvError) as excinfo:
            env.int('INT') == 42
        assert 'Environment variable "INT" invalid' in excinfo.value.args[0]

    def test_float_cast(self, set_env, env):
        set_env({'FLOAT': '33.3'})
        assert env.float('FLOAT') == 33.3

    def test_list_cast(self, set_env, env):
        set_env({'LIST': '1,2,3'})
        assert env.list('LIST') == ['1', '2', '3']

    def test_list_with_subcast(self, set_env, env):
        set_env({'LIST': '1,2,3'})
        assert env.list('LIST', subcast=int) == [1, 2, 3]
        assert env.list('LIST', subcast=float) == [1.0, 2.0, 3.0]

    def test_bool(self, set_env, env):
        set_env({'TRUTHY': '1', 'FALSY': '0'})
        assert env.bool('TRUTHY') is True
        assert env.bool('FALSY') is False

        set_env({'TRUTHY2': 'True', 'FALSY2': 'False'})
        assert env.bool('TRUTHY2') is True
        assert env.bool('FALSY2') is False

    def test_list_with_spaces(self, set_env, env):
        set_env({'LIST': ' 1,  2,3'})
        assert env.list('LIST', subcast=int) == [1, 2, 3]

    def test_dict(self, set_env, env):
        set_env({'DICT': 'key1=1,key2=2'})
        assert env.dict('DICT') == {'key1': '1', 'key2': '2'}

    def test_dict_with_subcast(self, set_env, env):
        set_env({'DICT': 'key1=1,key2=2'})
        assert env.dict('DICT', subcast=int) == {'key1': 1, 'key2': 2}

    def test_decimat_cast(self, set_env, env):
        set_env({'DECIMAL': '12.34'})
        assert env.decimal('DECIMAL') == Decimal('12.34')

    def test_missing_raises_error(self, env):
        with pytest.raises(envargs.EnvError) as exc:
            env.str('FOO')
        assert exc.value.args[0] == 'Environment variable "FOO" not set'

    def test_default_set(self, env):
        assert env.str('FOO', missing='foo') == 'foo'
        # Passed positionally
        assert env.str('FOO', 'foo') == 'foo'

    def test_json_cast(self, set_env, env):
        set_env({'JSON': '{"foo": "bar", "baz": [1, 2, 3]}'})
        assert env.json('JSON') == {'foo': 'bar', 'baz': [1, 2, 3]}

    def test_datetime_cast(self, set_env, env):
        dtime = dt.datetime.utcnow()
        set_env({'DTIME': dtime.isoformat()})
        result = env.datetime('DTIME')
        assert type(result) is dt.datetime
        assert result.year == dtime.year
        assert result.month == dtime.month
        assert result.day == dtime.day

    def test_date_cast(self, set_env, env):
        date = dt.date.today()
        set_env({'DATE': date.isoformat()})
        assert env.date('DATE') == date

class TestCustomTypes:

    def test_add_parser(self, set_env, env):
        set_env({'URL': 'test.test/'})

        def url(value):
            return 'https://' + value

        env.add_parser('url', url)
        assert env.url('URL') == 'https://test.test/'
        with pytest.raises(envargs.EnvError) as excinfo:
            env.url('NOT_SET')
        assert excinfo.value.args[0] == 'Environment variable "NOT_SET" not set'

        assert env.url('NOT_SET', 'default.test/') == 'https://default.test/'

    def test_parser_for(self, set_env, env):
        set_env({'URL': 'test.test/'})

        @env.parser_for('url')
        def url(value):
            return 'https://' + value
        assert env.url('URL') == 'https://test.test/'

        with pytest.raises(envargs.EnvError) as excinfo:
            env.url('NOT_SET')
        assert excinfo.value.args[0] == 'Environment variable "NOT_SET" not set'

        assert env.url('NOT_SET', 'default.test/') == 'https://default.test/'

    def test_parser_for_field(self, set_env, env):
        class MyURL(fields.Field):
            def _deserialize(self, value, *args, **kwargs):
                return 'https://' + value

        env.parser_from_field('url', MyURL)

        set_env({'URL': 'test.test/'})
        assert env.url('URL') == 'https://test.test/'

        with pytest.raises(envargs.EnvError) as excinfo:
            env.url('NOT_SET')
        assert excinfo.value.args[0] == 'Environment variable "NOT_SET" not set'

class TestDumping:
    def test_dump(self, set_env, env):
        dtime = dt.datetime.utcnow()
        set_env({'STR': 'foo', 'INT': '42', 'DTIME': dtime.isoformat()})

        env.str('STR')
        env.int('INT')
        env.datetime('DTIME')

        result = env.dump()
        assert result['STR'] == 'foo'
        assert result['INT'] == 42
        assert 'DTIME' in result
        assert type(result['DTIME']) is str

    def test_env_with_custom_parser(self, set_env, env):
        @env.parser_for('url')
        def url(value):
            return 'https://' + value

        set_env({'URL': 'test.test'})

        env.url('URL')

        assert env.dump() == {'URL': 'https://test.test'}

def test_repr(set_env, env):
    set_env({'FOO': 'foo', 'BAR': 42})
    env.str('FOO')
    assert repr(env) == '<Env {}>'.format({'FOO': 'foo'})

def test_str(set_env, env):
    set_env({'FOO': 'foo', 'BAR': 42})
    env.str('FOO')
    assert repr(env) == '<Env {}>'.format({'FOO': 'foo'})

class TestPrefix:

    @pytest.fixture(autouse=True)
    def default_environ(self, set_env):
        set_env({'APP_STR': 'foo', 'APP_INT': '42'})

    def test_prefixed(self, env):
        with env.prefixed('APP_'):
            assert env.str('STR') == 'foo'
            assert env.int('INT') == 42
            assert env('NOT_FOUND', 'mydefault') == 'mydefault'

    def test_dump_with_prefixed(self, env):
        with env.prefixed('APP_'):
            env.str('STR') == 'foo'
            env.int('INT') == 42
            env('NOT_FOUND', 'mydefault') == 'mydefault'
        assert env.dump() == {'APP_STR': 'foo', 'APP_INT': 42, 'APP_NOT_FOUND': 'mydefault'}
