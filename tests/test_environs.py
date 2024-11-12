import datetime as dt
import logging
import os
import pathlib
import urllib.parse
import uuid
from decimal import Decimal
from enum import Enum

import dj_database_url
import dj_email_url
import django_cache_url
import marshmallow as ma
import pytest
from marshmallow import fields, validate

import environs

HERE = pathlib.Path(__file__).parent


@pytest.fixture
def set_env(monkeypatch):
    def _set_env(envvars):
        for key, val in envvars.items():
            monkeypatch.setenv(key, val)

    return _set_env


@pytest.fixture(scope="function")
def env():
    return environs.Env()


class FauxTestException(Exception):
    pass


class DayEnum(Enum):
    SUNDAY = 1
    MONDAY = 2
    TUESDAY = 3


class TestCasting:
    def test_call(self, set_env, env):
        set_env({"STR": "foo", "INT": "42"})
        assert env("STR") == "foo"
        assert env("NOT_SET", "mydefault") == "mydefault"
        with pytest.raises(
            environs.EnvError, match='Environment variable "NOT_SET" not set'
        ):
            assert env("NOT_SET")

    def test_call_with_default(self, env):
        assert env("NOT_SET", default="mydefault") == "mydefault"
        assert env("NOT_SET", "mydefault") == "mydefault"

    def test_basic(self, set_env, env):
        set_env({"STR": "foo"})
        assert env.str("STR") == "foo"

    def test_empty_str(self, set_env, env):
        set_env({"STR": ""})
        assert env.str("STR") == ""

    def test_int_cast(self, set_env, env):
        set_env({"INT": "42"})
        assert env.int("INT") == 42

    def test_invalid_int(self, set_env, env):
        set_env({"INT": "invalid"})
        with pytest.raises(
            environs.EnvError, match='Environment variable "INT" invalid'
        ) as excinfo:
            env.int("INT")
        exc = excinfo.value
        assert "Not a valid integer." in exc.error_messages

    def test_float_cast(self, set_env, env):
        set_env({"FLOAT": "33.3"})
        assert env.float("FLOAT") == 33.3

    def test_list_cast(self, set_env, env):
        set_env({"LIST": "1,2,3"})
        assert env.list("LIST") == ["1", "2", "3"]

    def test_list_with_default_from_string(self, env):
        assert env.list("LIST", "1,2") == ["1", "2"]

    def test_list_with_default_from_list(self, env):
        assert env.list("LIST", ["1"]) == ["1"]

    # https://github.com/sloria/environs/issues/298
    def test_list_with_default_none(self, env):
        assert env.list("LIST", default=None) is None

    def test_list_with_subcast(self, set_env, env):
        set_env({"LIST": "1,2,3"})
        assert env.list("LIST", subcast=int) == [1, 2, 3]
        assert env.list("LIST", subcast=float) == [1.0, 2.0, 3.0]

    def test_list_with_empty_env_and_subcast(self, set_env, env):
        set_env({"LIST": ""})
        assert env.list("LIST", subcast=int) == []
        assert env.list("LIST", subcast=float) == []

    def test_bool(self, set_env, env):
        set_env({"TRUTHY": "1", "FALSY": "0"})
        assert env.bool("TRUTHY") is True
        assert env.bool("FALSY") is False

        set_env({"TRUTHY2": "True", "FALSY2": "False"})
        assert env.bool("TRUTHY2") is True
        assert env.bool("FALSY2") is False

    def test_list_with_spaces(self, set_env, env):
        set_env({"LIST": " 1,  2,3"})
        assert env.list("LIST", subcast=int) == [1, 2, 3]

    def test_list_with_spaces_as_delimiter(self, set_env, env):
        set_env({"LIST": "a b c"})
        assert env.list("LIST", delimiter=" ") == ["a", "b", "c"]

    def test_dict(self, set_env, env):
        set_env({"DICT": "key1=1,key2=2"})
        assert env.dict("DICT") == {"key1": "1", "key2": "2"}

    def test_dict_with_spaces_as_delimiter(self, set_env, env):
        set_env({"DICT": "key1=1 key2=2"})
        assert env.dict("DICT", delimiter=" ") == {"key1": "1", "key2": "2"}

    def test_dict_with_subcast_values(self, set_env, env):
        set_env({"DICT": "key1=1,key2=2"})
        assert env.dict("DICT", subcast_values=int) == {"key1": 1, "key2": 2}

    def test_dict_without_subcast_keys(self, set_env, env):
        set_env({"DICT": "1=value1,2=value2"})
        assert env.dict("DICT") == {"1": "value1", "2": "value2"}

    def test_dict_with_subcast_keys(self, set_env, env):
        set_env({"DICT": "1=value1,2=value2"})
        assert env.dict("DICT", subcast_keys=int) == {1: "value1", 2: "value2"}

    def test_custom_subcast_list(self, set_env, env):
        class CustomTuple(ma.fields.Field):
            def _deserialize(self, value: str, *args, **kwargs):
                return tuple(value[1:-1].split(":"))

        def custom_tuple(value: str):
            return tuple(value[1:-1].split(":"))

        set_env({"LIST": "(127.0.0.1:26380),(127.0.0.1:26379)"})
        assert env.list("LIST", subcast=CustomTuple) == [
            ("127.0.0.1", "26380"),
            ("127.0.0.1", "26379"),
        ]
        assert env.list("LIST", subcast=custom_tuple) == [
            ("127.0.0.1", "26380"),
            ("127.0.0.1", "26379"),
        ]

    def test_custom_subcast_keys_values(self, set_env, env):
        def custom_tuple(value: str):
            return tuple(value.split(":"))

        set_env({"DICT": "1:1=foo:bar"})
        assert env.dict(
            "DICT", subcast_keys=custom_tuple, subcast_values=custom_tuple
        ) == {("1", "1"): ("foo", "bar")}

    def test_dict_with_default_from_string(self, set_env, env):
        assert env.dict("DICT", "key1=1,key2=2") == {"key1": "1", "key2": "2"}

    def test_dict_with_default_from_dict(self, set_env, env):
        assert env.dict("DICT", {"key1": "1"}) == {"key1": "1"}

    def test_dict_with_equal(self, set_env, env):
        set_env({"DICT": "expr1=1 < 2,expr2=(1+1) = 2"})
        assert env.dict("DICT") == {"expr1": "1 < 2", "expr2": "(1+1) = 2"}

    def test_decimal_cast(self, set_env, env):
        set_env({"DECIMAL": "12.34"})
        assert env.decimal("DECIMAL") == Decimal("12.34")

    def test_missing_raises_error(self, env):
        with pytest.raises(environs.EnvError) as exc:
            env.str("FOO")
        assert exc.value.args[0] == 'Environment variable "FOO" not set'

    def test_default_set(self, env):
        if ma.__version_info__ >= (3, 13):
            assert env.str("FOO", load_default="foo") == "foo"
        else:
            assert env.str("FOO", missing="foo") == "foo"
        # Passed positionally
        assert env.str("FOO", "foo") == "foo"

    def test_json_cast(self, set_env, env):
        set_env({"JSON": '{"foo": "bar", "baz": [1, 2, 3]}'})
        assert env.json("JSON") == {"foo": "bar", "baz": [1, 2, 3]}

    def test_invalid_json_raises_error(self, set_env, env):
        set_env({"JSON": "foo"})
        with pytest.raises(environs.EnvError) as exc:
            env.json("JSON")
        assert "Not valid JSON." in exc.value.args[0]

    def test_json_default(self, set_env, env):
        assert env.json("JSON", {"foo": "bar"}) == {"foo": "bar"}
        assert env.json("JSON", ["foo", "bar"]) == ["foo", "bar"]
        with pytest.raises(environs.EnvError) as exc:
            env.json("JSON", int)  # a builtin is not a valid json
        assert "Not valid JSON." in exc.value.args[0]

    def test_datetime_cast(self, set_env, env):
        dtime = dt.datetime.now(dt.timezone.utc)
        set_env({"DTIME": dtime.isoformat()})
        result = env.datetime("DTIME")
        assert type(result) is dt.datetime
        assert result.year == dtime.year
        assert result.month == dtime.month
        assert result.day == dtime.day

    def test_date_cast(self, set_env, env):
        date = dt.date.today()
        set_env({"DATE": date.isoformat()})
        assert env.date("DATE") == date

    def test_timedelta_cast(self, set_env, env):
        set_env({"TIMEDELTA": "42"})
        assert env.timedelta("TIMEDELTA") == dt.timedelta(seconds=42)
        set_env({"TIMEDELTA": "42s"})
        assert env.timedelta("TIMEDELTA") == dt.timedelta(seconds=42)
        # whitespace, case-insensitive, missing units
        set_env({"TIMEDELTA": " 42 D  42s "})
        assert env.timedelta("TIMEDELTA") == dt.timedelta(days=42, seconds=42)
        # unicode µs (in addition to us below)
        set_env({"TIMEDELTA": "42µs"})
        assert env.timedelta("TIMEDELTA") == dt.timedelta(microseconds=42)
        # all supported units
        set_env({"TIMEDELTA": "42w 42d 42h 42m 42s 42ms 42us"})
        assert env.timedelta("TIMEDELTA") == dt.timedelta(
            weeks=42,
            days=42,
            hours=42,
            minutes=42,
            seconds=42,
            milliseconds=42,
            microseconds=42,
        )

    def test_time_cast(self, set_env, env):
        set_env({"TIME": "10:30"})
        assert env.time("TIME") == dt.time(hour=10, minute=30, second=0)

    def test_uuid_cast(self, set_env, env):
        uid = uuid.uuid1()
        set_env({"UUID": str(uid)})
        assert env.uuid("UUID") == uid

    def test_url_cast(self, set_env, env):
        set_env({"URL": "http://stevenloria.com/projects/?foo=42"})
        res = env.url("URL")
        assert isinstance(res, urllib.parse.ParseResult)

    def test_url_db_cast(self, env, set_env):
        mongodb_url = "mongodb://user:pass@mongo.example.local/db?authSource=admin"
        set_env({"MONGODB_URL": mongodb_url})
        res = env.url(
            "MONGODB_URL", schemes={"mongodb", "mongodb+srv"}, require_tld=False
        )
        assert isinstance(res, urllib.parse.ParseResult)

    def test_path_cast(self, set_env, env):
        set_env({"PTH": "/home/sloria"})
        res = env.path("PTH")
        assert isinstance(res, pathlib.Path)

    def test_path_default_value(self, env):
        default_value = pathlib.Path("/home/sloria")
        res = env.path("MISSING_ENV", default_value)
        assert isinstance(res, pathlib.Path)
        assert res == default_value

    def test_log_level_cast(self, set_env, env):
        set_env(
            {
                "LOG_LEVEL": "WARNING",
                "LOG_LEVEL_INT": str(logging.WARNING),
                "LOG_LEVEL_LOWER": "info",
            }
        )
        assert env.log_level("LOG_LEVEL_INT") == logging.WARNING
        assert env.log_level("LOG_LEVEL") == logging.WARNING
        assert env.log_level("LOG_LEVEL_LOWER") == logging.INFO

    def test_invalid_log_level(self, set_env, env):
        set_env({"LOG_LEVEL": "INVALID", "LOG_LEVEL_BAD": "getLogger"})
        with pytest.raises(environs.EnvError) as excinfo:
            env.log_level("LOG_LEVEL")
        assert "Not a valid log level" in excinfo.value.args[0]
        with pytest.raises(environs.EnvError) as excinfo:
            env.log_level("LOG_LEVEL_BAD")
        assert "Not a valid log level" in excinfo.value.args[0]

    @pytest.mark.parametrize("url", ["foo", "42", "foo@bar"])
    def test_invalid_url(self, url, set_env, env):
        set_env({"URL": url})
        with pytest.raises(environs.EnvError) as excinfo:
            env.url("URL")
        assert 'Environment variable "URL" invalid' in excinfo.value.args[0]

    def test_enum_cast(self, set_env, env):
        set_env({"DAY": "SUNDAY"})
        assert env.enum("DAY", type=DayEnum) == DayEnum.SUNDAY

    def test_enum_cast_ignore_case(self, set_env, env):
        set_env({"DAY": "suNDay"})
        assert env.enum("DAY", type=DayEnum, ignore_case=True) == DayEnum.SUNDAY

    def test_invalid_enum(self, set_env, env):
        set_env({"DAY": "suNDay"})
        with pytest.raises(environs.EnvError):
            assert env.enum("DAY", type=DayEnum)

    def test_invalid_enum_ignore_case(self, set_env, env):
        set_env({"DAY": "SonDAY"})
        with pytest.raises(environs.EnvError):
            assert env.enum("DAY", type=DayEnum, ignore_case=True)


class TestEnvFileReading:
    def test_read_env(self, env):
        if "STRING" in os.environ:
            os.environ.pop("STRING")
        assert env("STRING", "default") == "default"  # sanity check
        result = env.read_env()
        assert result is True
        assert env("STRING") == "foo"
        assert env.list("LIST") == ["wat", "wer", "wen"]
        assert env("EXPANDED") == "foo"

    def test_read_env_returns_false_if_file_not_found(self, env):
        result = env.read_env(HERE / ".does_not_exist", verbose=True)
        assert result is False

    # Regression test for https://github.com/sloria/environs/issues/96
    def test_read_env_recurse(self, env):
        if "CUSTOM_STRING" in os.environ:
            os.environ.pop("CUSTOM_STRING")
        assert env("CUSTOM_STRING", "default") == "default"  # sanity check
        env.read_env(HERE / ".custom.env", recurse=True)
        assert env("CUSTOM_STRING") == "foo"

    def test_read_env_non_recurse(self, env):
        if "CUSTOM_STRING" in os.environ:
            os.environ.pop("CUSTOM_STRING")
        assert env("CUSTOM_STRING", "default") == "default"  # sanity check
        env.read_env(HERE / ".custom.env", recurse=False)
        assert env("CUSTOM_STRING") == "foo"

    def test_read_env_recurse_from_subfolder(self, env, monkeypatch):
        if "CUSTOM_STRING" in os.environ:
            os.environ.pop("CUSTOM_STRING")
        env.read_env(HERE / "subfolder" / ".custom.env", recurse=True)
        assert env("CUSTOM_STRING") == "foo"

    @pytest.mark.parametrize(
        "path", [".custom.env", (HERE / "subfolder" / ".custom.env")]
    )
    def test_read_env_recurse_start_from_subfolder(self, env, path, monkeypatch):
        if "CUSTOM_STRING" in os.environ:
            os.environ.pop("CUSTOM_STRING")
        monkeypatch.chdir(HERE / "subfolder")
        env.read_env(path, recurse=True)
        assert env("CUSTOM_STRING") == "foo"

    def test_read_env_directory(self, env):
        with pytest.raises(ValueError, match="path must be a filename"):
            assert env.read_env("tests")

    def test_read_env_return_path(self, env):
        path = env.read_env(return_path=True)
        env_path = str(HERE / ".env")
        assert path == env_path


def always_fail(value):
    raise environs.EnvError("something went wrong")


class TestValidation:
    def test_can_add_validator(self, set_env, env):
        set_env({"NUM": "3"})

        with pytest.raises(environs.EnvError) as excinfo:
            env.int("NUM", validate=lambda n: n > 3)
        assert "Invalid value." in excinfo.value.args[0]

    def test_can_add_marshmallow_validator(self, set_env, env):
        set_env({"NODE_ENV": "invalid"})
        with pytest.raises(environs.EnvError):
            env("NODE_ENV", validate=validate.OneOf(["development", "production"]))

    def test_validator_can_raise_enverror(self, set_env, env):
        with pytest.raises(environs.EnvError) as excinfo:
            env("NODE_ENV", "development", validate=always_fail)
        assert "something went wrong" in excinfo.value.args[0]

    def test_failed_vars_are_not_serialized(self, set_env, env):
        set_env({"FOO": "42"})
        try:
            env("FOO", validate=always_fail)
        except environs.EnvError:
            pass
        assert "FOO" not in env.dump()


class TestCustomTypes:
    def test_add_parser(self, set_env, env):
        set_env({"URL": "test.test/"})

        def https_url(value):
            return "https://" + value

        env.add_parser("https_url", https_url)
        assert env.https_url("URL") == "https://test.test/"
        with pytest.raises(environs.EnvError) as excinfo:
            env.url("NOT_SET")
        assert excinfo.value.args[0] == 'Environment variable "NOT_SET" not set'

        assert env.https_url("NOT_SET", "default.test/") == "https://default.test/"

    def test_cannot_override_built_in_parser(self, set_env, env):
        def https_url(value):
            return "https://" + value

        with pytest.raises(environs.ParserConflictError):
            env.add_parser("url", https_url)

    def test_parser_for(self, set_env, env):
        set_env({"URL": "test.test/"})

        @env.parser_for("https_url")
        def https_url(value):
            return "https://" + value

        assert env.https_url("URL") == "https://test.test/"

        with pytest.raises(environs.EnvError) as excinfo:
            env.https_url("NOT_SET")
        assert excinfo.value.args[0] == 'Environment variable "NOT_SET" not set'

        assert env.https_url("NOT_SET", "default.test/") == "https://default.test/"

    def test_parser_function_can_take_extra_arguments(self, set_env, env):
        set_env({"ENV": "dev"})

        @env.parser_for("choice")
        def choice_parser(value, choices):
            if value not in choices:
                raise environs.EnvError("Invalid!")
            return value

        assert env.choice("ENV", choices=["dev", "prod"]) == "dev"

        set_env({"ENV": "invalid"})
        with pytest.raises(environs.EnvError):
            env.choice("ENV", choices=["dev", "prod"])

    def test_add_parser_from_field(self, set_env, env):
        class HTTPSURL(fields.Field):
            def _deserialize(self, value, *args, **kwargs):
                return "https://" + value

        env.add_parser_from_field("https_url", HTTPSURL)

        set_env({"URL": "test.test/"})
        assert env.https_url("URL") == "https://test.test/"

        with pytest.raises(environs.EnvError) as excinfo:
            env.https_url("NOT_SET")
        assert excinfo.value.args[0] == 'Environment variable "NOT_SET" not set'


class TestDumping:
    def test_dump(self, set_env, env):
        dtime = dt.datetime.now(dt.timezone.utc)
        set_env(
            {
                "STR": "foo",
                "INT": "42",
                "DTIME": dtime.isoformat(),
                "URLPARSE": "http://stevenloria.com/projects/?foo=42",
                "PTH": "/home/sloria",
                "LOG_LEVEL": "WARNING",
            }
        )

        env.str("STR")
        env.int("INT")
        env.datetime("DTIME")
        env.url("URLPARSE")
        env.path("PTH")
        env.log_level("LOG_LEVEL")

        result = env.dump()
        assert result["STR"] == "foo"
        assert result["INT"] == 42
        assert "DTIME" in result
        assert type(result["DTIME"]) is str
        assert isinstance(result["URLPARSE"], str)
        assert result["URLPARSE"] == "http://stevenloria.com/projects/?foo=42"
        assert isinstance(result["PTH"], str)
        assert result["PTH"] == str(pathlib.Path("/home/sloria"))
        assert result["LOG_LEVEL"] == logging.WARNING

    def test_env_with_custom_parser(self, set_env, env):
        @env.parser_for("https_url")
        def https_url(value):
            return "https://" + value

        set_env({"URL": "test.test"})

        env.https_url("URL")

        assert env.dump() == {"URL": "https://test.test"}


def test_repr(set_env, env):
    env = environs.Env(eager=True, expand_vars=True)
    set_env({"FOO": "foo", "BAR": "42"})
    env.str("FOO")
    assert repr(env) == "<Env(eager=True, expand_vars=True)>"


def test_str(set_env, env):
    env = environs.Env(eager=True, expand_vars=True)
    set_env({"FOO": "foo", "BAR": "42"})
    env.str("FOO")
    assert str(env) == "<Env(eager=True, expand_vars=True)>"


def test_env_isolation(set_env):
    set_env({"FOO": "foo"})
    env1 = environs.Env()

    @env1.parser_for("foo")
    def foo(value):
        return value

    env2 = environs.Env()

    # env1 has a parser for foo, but env2 does not
    assert env1.foo("FOO") == "foo"
    with pytest.raises(AttributeError):
        env2.foo("FOO")


class TestPrefix:
    @pytest.fixture(autouse=True)
    def default_environ(self, set_env):
        set_env({"APP_STR": "foo", "APP_INT": "42"})

    def test_prefixed(self, env):
        with env.prefixed("APP_"):
            assert env.str("STR") == "foo"
            assert env.int("INT") == 42
            assert env("NOT_FOUND", "mydefault") == "mydefault"

    def test_dump_with_prefixed(self, env):
        with env.prefixed("APP_"):
            assert env.str("STR") == "foo"
            assert env.int("INT") == 42
            assert env("NOT_FOUND", "mydefault") == "mydefault"
        assert env.dump() == {
            "APP_STR": "foo",
            "APP_INT": 42,
            "APP_NOT_FOUND": "mydefault",
        }

    def test_error_message_for_prefixed_var(self, env):
        with env.prefixed("APP_"):
            with pytest.raises(
                environs.EnvError, match='Environment variable "APP_INT" invalid'
            ):
                env.int("INT", validate=lambda val: val < 42)


class TestNestedPrefix:
    @pytest.fixture(autouse=True)
    def default_environ(self, set_env):
        set_env({"APP_STR": "foo", "APP_NESTED_INT": "42"})

    def test_nested_prefixed(self, env):
        with env.prefixed("APP_"):
            with env.prefixed("NESTED_"):
                assert env.int("INT") == 42
                assert env("NOT_FOUND", "mydefault") == "mydefault"
            assert env.str("STR") == "foo"
            assert env("NOT_FOUND", "mydefault") == "mydefault"

    def test_dump_with_nested_prefixed(self, env):
        with env.prefixed("APP_"):
            with env.prefixed("NESTED_"):
                assert env.int("INT") == 42
                assert env("NOT_FOUND", "mydefault") == "mydefault"
            assert env.str("STR") == "foo"
            assert env("NOT_FOUND", "mydefault") == "mydefault"
        assert env.dump() == {
            "APP_STR": "foo",
            "APP_NOT_FOUND": "mydefault",
            "APP_NESTED_INT": 42,
            "APP_NESTED_NOT_FOUND": "mydefault",
        }


class TestFailedNestedPrefix:
    @pytest.fixture(autouse=True)
    def default_environ(self, set_env):
        set_env({"APP_STR": "foo", "APP_NESTED_INT": "42"})

    def test_failed_nested_prefixed(self, env):
        # define repeated prefixed steps
        def nested_prefixed(env, fail=False):
            with env.prefixed("APP_"):
                with env.prefixed("NESTED_"):
                    assert env.int("INT") == 42
                    assert env("NOT_FOUND", "mydefault") == "mydefault"
                assert env.str("STR") == "foo"
                assert env("NOT_FOUND", "mydefault") == "mydefault"
                if fail:
                    raise FauxTestException

        try:
            nested_prefixed(env, fail=True)
        except FauxTestException:
            nested_prefixed(env, fail=False)

    def test_failed_dump_with_nested_prefixed(self, env):
        # define repeated prefixed steps
        def dump_with_nested_prefixed(env, fail=False):
            with env.prefixed("APP_"):
                with env.prefixed("NESTED_"):
                    assert env.int("INT") == 42
                    assert env("NOT_FOUND", "mydefault") == "mydefault"
                assert env.str("STR") == "foo"
                assert env("NOT_FOUND", "mydefault") == "mydefault"
                if fail:
                    raise FauxTestException
            assert env.dump() == {
                "APP_STR": "foo",
                "APP_NOT_FOUND": "mydefault",
                "APP_NESTED_INT": 42,
                "APP_NESTED_NOT_FOUND": "mydefault",
            }

        try:
            dump_with_nested_prefixed(env, fail=True)
        except FauxTestException:
            dump_with_nested_prefixed(env, fail=False)


class TestDjango:
    def test_dj_db_url(self, env, set_env):
        db_url = "postgresql://localhost:5432/mydb"
        set_env({"DATABASE_URL": db_url})
        res = env.dj_db_url("DATABASE_URL")
        assert res == dj_database_url.parse(db_url)

    def test_dj_db_url_passes_kwargs(self, env, set_env):
        db_url = "postgresql://localhost:5432/mydb"
        set_env({"DATABASE_URL": db_url})
        res = env.dj_db_url("DATABASE_URL", conn_max_age=600)
        assert res == dj_database_url.parse(db_url, conn_max_age=600)

    def test_dj_email_url(self, env, set_env):
        email_url = "smtp://user@domain.com:pass@smtp.example.com:465/?ssl=True"
        set_env({"EMAIL_URL": email_url})
        res = env.dj_email_url("EMAIL_URL")
        assert res == dj_email_url.parse(email_url)

    def test_dj_cache_url(self, env, set_env):
        cache_url = "redis://redis:6379/0"
        set_env({"CACHE_URL": cache_url})
        res = env.dj_cache_url("CACHE_URL")
        assert res == django_cache_url.parse(cache_url)


class TestDeferredValidation:
    @pytest.fixture
    def env(self):
        return environs.Env(eager=False)

    def test_valid(self, env, set_env):
        set_env({"STR": "foo", "INT": "42"})
        str_val = env.str("STR")
        int_val = env.int("INT")
        env.seal()
        assert str_val == "foo"
        assert int_val == 42

    def test_validation(self, env, set_env):
        set_env({"INT": "invalid", "DTIME": "notadatetime"})
        env.int("INT")
        env.datetime("DTIME")
        env.str("REQUIRED")
        with pytest.raises(environs.EnvValidationError) as excinfo:
            env.seal()
        exc = excinfo.value
        msg = exc.args[0]
        assert "REQUIRED" in msg
        assert "INT" in msg
        assert "DTIME" in msg
        assert "REQUIRED" in exc.error_messages
        assert "INT" in exc.error_messages
        assert "DTIME" in exc.error_messages

    def test_deferred_required_validation(self, env):
        env.int("STR")
        env.int("INT")
        env.datetime("DTIME")
        with pytest.raises(environs.EnvValidationError) as excinfo:
            env.seal()
        exc = excinfo.value
        assert exc.error_messages == {
            "STR": ["Environment variable not set."],
            "INT": ["Environment variable not set."],
            "DTIME": ["Environment variable not set."],
        }

    def test_cannot_add_after_seal(self, env, set_env):
        set_env({"STR": "foo", "INT": "42"})
        env.str("STR")
        env.seal()
        with pytest.raises(
            environs.EnvSealedError, match="Env has already been sealed"
        ):
            env.int("INT")

    def test_custom_parser_not_called_after_seal(self, env, set_env):
        set_env({"URL": "test.test/"})

        @env.parser_for("https_url")
        def https_url(value):
            return "https://" + value

        env.seal()
        with pytest.raises(
            environs.EnvSealedError, match="Env has already been sealed"
        ):
            env.https_url("URL")

    # Regression tests for https://github.com/sloria/environs/issues/121
    def test_dj_db_url_with_deferred_validation_missing(self, env):
        env.dj_db_url("DATABASE_URL")
        with pytest.raises(environs.EnvValidationError) as excinfo:
            env.seal()

        exc = excinfo.value
        assert exc.error_messages == {"DATABASE_URL": ["Environment variable not set."]}

    def test_dj_db_url_with_deferred_validation_invalid(self, env, set_env):
        set_env({"DATABASE_URL": "invalid://"})
        env.dj_db_url("DATABASE_URL")
        with pytest.raises(environs.EnvValidationError) as excinfo:
            env.seal()
        exc = excinfo.value
        assert exc.error_messages == {"DATABASE_URL": ["Not a valid database URL."]}

    def test_dj_email_url_with_deferred_validation_missing(self, env):
        env.dj_email_url("EMAIL_URL")
        with pytest.raises(environs.EnvValidationError) as excinfo:
            env.seal()
        exc = excinfo.value
        assert exc.error_messages == {"EMAIL_URL": ["Environment variable not set."]}

    def test_dj_cache_url_with_deferred_validation_missing(self, env):
        env.dj_cache_url("CACHE_URL")
        with pytest.raises(environs.EnvValidationError) as excinfo:
            env.seal()

        exc = excinfo.value
        assert exc.error_messages == {"CACHE_URL": ["Environment variable not set."]}

    def test_dj_cache_url_with_deferred_validation_invalid(self, env, set_env):
        set_env({"CACHE_URL": "invalid://"})
        env.dj_cache_url("CACHE_URL")
        with pytest.raises(environs.EnvValidationError) as excinfo:
            env.seal()
        exc = excinfo.value
        assert exc.error_messages == {"CACHE_URL": ['Unknown backend: "invalid"']}

    def test_custom_parser_with_deferred_validation_missing(self, env):
        @env.parser_for("always_fail")
        def always_fail(value):
            raise environs.EnvError("Invalid!")

        env.always_fail("MY_VAR")

        with pytest.raises(environs.EnvValidationError) as excinfo:
            env.seal()
        exc = excinfo.value
        assert exc.error_messages == {"MY_VAR": ["Environment variable not set."]}

    def test_custom_parser_with_deferred_validation_invalid(self, env, set_env):
        set_env({"MY_VAR": "foo"})

        @env.parser_for("always_fail")
        def always_fail(value):
            raise environs.EnvError("Invalid!")

        env.always_fail("MY_VAR")

        with pytest.raises(environs.EnvValidationError) as excinfo:
            env.seal()
        exc = excinfo.value
        assert exc.error_messages == {"MY_VAR": ["Invalid!"]}


class TestExpandVars:
    @pytest.fixture
    def env(self):
        return environs.Env(expand_vars=True)

    def test_full_expand_vars(self, env, set_env):
        set_env(
            {
                "MAIN": "${SUBSTI}",
                "MAIN_INT": "${SUBS_INT}",
                "MAIN_DEF": "${SUBS_NOT_FOUND:-maindef}",
                "MAIN_INT_DEF": "${SUBS_NOT_FOUND_I:-454}",
                "MAIN_NEG_INT_DEF": "${SUBS_NOT_FOUND_I:--454}",
                "SUBSTI": "substivalue",
                "SUBS_INT": "48",
                "USE_DEFAULT": "${FOOBAR}",
                "UNDEFINED": "${MYVAR}",
            }
        )
        assert env.str("MAIN") == "substivalue"
        assert env.int("MAIN_INT") == 48
        assert env.str("MAIN_DEF") == "maindef"
        assert env.int("MAIN_INT_DEF") == 454
        assert env.int("MAIN_NEG_INT_DEF") == -454
        assert env.str("USE_DEFAULT", "main_default") == "main_default"

        with pytest.raises(
            environs.EnvError, match='Environment variable "MYVAR" not set'
        ):
            env.str("UNDEFINED")

    def test_multiple_expands(self, env, set_env):
        set_env(
            {
                "PGURL": "postgres://${USER:-sloria}:${PASSWORD:-secret}@localhost",
                "USER": "gnarvaja",
                "HELLOCOUNTRY": "Hello ${COUNTRY}",
                "COUNTRY": "Argentina",
                "HELLOWORLD": "Hello ${WORLD}",
            }
        )
        assert env.str("PGURL") == "postgres://gnarvaja:secret@localhost"
        assert env.str("HELLOCOUNTRY") == "Hello Argentina"

        with pytest.raises(
            environs.EnvError, match='Environment variable "WORLD" not set'
        ):
            env.str("HELLOWORLD")

    def test_recursive_expands(self, env, set_env):
        set_env(
            {
                "PGURL": "postgres://${PGUSER:-sloria}:${PGPASS:-secret}@localhost",
                "PGUSER": "${USER}",
                "USER": "gnarvaja",
            }
        )
        assert env.str("PGURL") == "postgres://gnarvaja:secret@localhost"

    def test_default_expands(self, env, set_env):
        set_env(
            {
                "MAIN": "${SUBSTI}",
                "SUBSTI": "substivalue",
            }
        )
        assert env.str("NOT_SET", "${SUBSTI}") == "substivalue"
        assert env.str("NOT_SET", "${MAIN}") == "substivalue"
        assert env.str("NOT_SET", "${NOT_SET2:-set2}") == "set2"
        with pytest.raises(
            environs.EnvError, match='Environment variable "NOT_SET2" not set'
        ):
            assert env.str("NOT_SET", "${NOT_SET2}")

    def test_escaped_expand(self, env, set_env):
        set_env({"ESCAPED_EXPAND": r"\${ESCAPED}", "ESCAPED": "fail"})
        assert env.str("ESCAPED_EXPAND") == r"${ESCAPED}"

    def test_composite_types(self, env, set_env):
        set_env(
            {
                "ALLOWED_USERS": "god,${USER},root",
                "USER": "gnarvaja",
                "MYCLASS_KARGS": "foo=bar,wget_params=${WGET_PARAMS}",
                "WGET_PARAMS": '--header="Referer: https://radiocut.fm/"',
            }
        )
        assert env.list("ALLOWED_USERS") == ["god", "gnarvaja", "root"]
        assert env.dict("MYCLASS_KARGS") == {
            "foo": "bar",
            "wget_params": '--header="Referer: https://radiocut.fm/"',
        }
