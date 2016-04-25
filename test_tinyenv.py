from decimal import Decimal
import datetime as dt

import pytest
from marshmallow import fields

import tinyenv

@pytest.fixture
def set_env(monkeypatch):
    def _set_env(envvars):
        for key, val in envvars.items():
            monkeypatch.setenv(key, val)
    return _set_env


@pytest.fixture
def env():
    return tinyenv.Env()


class TestCasting:

    def test_get(self, set_env, env):
        set_env({'STR': 'foo', 'INT': '42'})
        assert env.get('STR') == 'foo'
        assert env.get('INT') == '42'

    def test_basic(self, set_env, env):
        set_env({'STR': 'foo'})
        assert env.str('STR') == 'foo'

    def test_int_cast(self, set_env, env):
        set_env({'INT': '42'})
        assert env.int('INT') == 42

    def test_invalid_int(self, set_env, env):
        set_env({'INT': 'invalid'})
        with pytest.raises(tinyenv.EnvError) as excinfo:
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
        assert env.list('LIST', int) == [1, 2, 3]
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
        assert env.list('LIST', int) == [1, 2, 3]

    def test_dict(self, set_env, env):
        set_env({'DICT': 'key1=1,key2=2'})
        assert env.dict('DICT') == {'key1': '1', 'key2': '2'}

    def test_dict_with_subcast(self, set_env, env):
        set_env({'DICT': 'key1=1,key2=2'})
        assert env.dict('DICT', int) == {'key1': 1, 'key2': 2}

    def test_decimat_cast(self, set_env, env):
        set_env({'DECIMAL': '12.34'})
        assert env.decimal('DECIMAL') == Decimal('12.34')

    def test_missing_raises_error(self, env):
        with pytest.raises(tinyenv.EnvError) as exc:
            env.str('FOO')
        assert exc.value.args[0] == 'Environment variable "FOO" not set'

    def test_default_set(self, env):
        assert env.str('FOO', missing='foo') == 'foo'

    def test_json_cast(self, set_env, env):
        set_env({'JSON': '{"foo": "bar", "baz": [1, 2, 3]}'})
        assert env.json('JSON') == {'foo': 'bar', 'baz': [1, 2, 3]}

    def test_datetime_cast(self, set_env, env):
        dtime = dt.datetime.utcnow()
        set_env({'DTIME': dtime.isoformat()})
        assert env.datetime('DTIME') == dtime

    def test_date_cast(self, set_env, env):
        date = dt.datetime.today()
        set_env({'DATE': date.isoformat()})
        assert env.datetime('DATE') == date

class TestCustomTypes:

    def test_parser_for(self, set_env, env):
        @env.parser_for('url')
        def url(value):
            return 'https://' + value
        set_env({'URL': 'test.test/'})
        assert env.url('URL') == 'https://test.test/'

        with pytest.raises(tinyenv.EnvError) as excinfo:
            env.url('NOT_SET')
        assert excinfo.value.args[0] == 'Environment variable "NOT_SET" not set'

    def test_parser_for_field(self, set_env, env):
        class MyURL(fields.Field):
            def _deserialize(self, value, *args, **kwargs):
                return 'https://' + value

        env.parser_from_field('url', MyURL)

        set_env({'URL': 'test.test/'})
        assert env.url('URL') == 'https://test.test/'

        with pytest.raises(tinyenv.EnvError) as excinfo:
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
