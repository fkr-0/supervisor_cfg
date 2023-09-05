import tempfile

import pytest
from supervisor.datatypes import integer
from supervisor.options import Options
from supervisor.states import SupervisorStates
from supervisor.tests.base import DummyOptions, DummyPGroupConfig, DummySupervisor
from supervisor.xmlrpc import RPCError

from supervisor_cfg.rpcinterface import CfgNamespaceRPCInterface


@pytest.fixture
def dummy_options():
    class DummyCfgFileOptions(Options, DummyOptions):
        master = {"other": 41}

        def __init__(self, *args, read_error=False, **kw):
            self.read_error = read_error

            super().__init__(*args, **kw)
            super(Options, self).__init__(*args, **kw)
            super(DummyOptions, self).__init__(*args, **kw)
            super().__init__(*args, **kw)

            class Foo:
                pass

            self.configroot = Foo()
            # make tmpfile

            with tempfile.NamedTemporaryFile() as f:
                self.configfile = f.name
                lines_of_cfg = map(
                    lambda x: x.encode("utf-8"),
                    [
                        "[supervisord]\n",
                        "mood=good\n",
                        "[program:foo]\n",
                        "command=/bin/cat\n",
                        "priority=1\n",
                        "autostart=true\n",
                    ],
                )
                f.write(b"".join(lines_of_cfg))

        def _get_file(self):
            return self.configfile

        def read_config(self, _):
            if self.read_error:
                raise ValueError(self.read_error)
            self.configroot.__dict__.update(self.default_map)
            self.configroot.__dict__.update(self.master)

    options = DummyCfgFileOptions()
    # options.add("mood",
    options.add(
        name="anoption",
        confname="anoption",
        short="o",
        long="option",
        default="default",
    )
    options.add(
        name="other",
        confname="other",
        env="OTHER",
        short="p:",
        long="other=",
        handler=integer,
    )
    return options


@pytest.fixture
def dummy_supervisor(dummy_options):
    class DummySupervisorWithOptions(DummySupervisor):
        def __init__(self, options):
            self.options = options
            super().__init__(options=self.options)

    return DummySupervisorWithOptions(options=dummy_options)


def test_add_flag_not_None_handler_not_None(dummy_options):
    with pytest.raises(ValueError):
        dummy_options.add(flag=True, handler=True)


def test_add_flag_not_None_long_false_short_false(dummy_options):
    with pytest.raises(ValueError):
        dummy_options.add(flag=True, long=False, short=False)


# Now you can use dummy_supervisor in your CfgNamespaceRPCInterface tests
def test_ctor_assigns_supervisord(dummy_supervisor):
    interface = CfgNamespaceRPCInterface(dummy_supervisor)
    assert interface.supervisord is not None


@pytest.fixture
def interface(dummy_supervisor):
    return CfgNamespaceRPCInterface(dummy_supervisor)


# def test_ctor_assigns_supervisord(interface):
#     assert interface.supervisord is not None


def test_updater_raises_shutdown_error_if_supervisord_in_shutdown_state():
    supervisord = DummySupervisor(state=SupervisorStates.SHUTDOWN)
    interface = CfgNamespaceRPCInterface(supervisord)
    with pytest.raises(RPCError):
        interface.get_config()


def test_get_config_returns_config(interface: CfgNamespaceRPCInterface):
    config = interface.get_config()
    assert isinstance(config, dict)


def test_get_config_filename_returns_filename(interface):
    filename = interface.get_config_filename()
    assert isinstance(filename, str)


def test_set_command_sets_command(interface):
    options = DummyOptions()
    changes = [
        [DummyPGroupConfig(options, name="added")],
        [DummyPGroupConfig(options, name="changed")],
        [DummyPGroupConfig(options, name="dropped")],
    ]

    interface.supervisord.diff_to_active = lambda: changes
    result = interface.set_command("program_name", "new_command")
    assert isinstance(result, tuple)


def test_set_command_sets_section(interface):
    options = DummyOptions()
    changes = [
        [DummyPGroupConfig(options, name="added")],
        [DummyPGroupConfig(options, name="changed")],
        [DummyPGroupConfig(options, name="dropped")],
    ]

    interface.supervisord.diff_to_active = lambda: changes
    result = interface.set_command("section_name", {"command": "new_command"})
    assert isinstance(result, tuple)


def test_set_config_sets_config(interface):
    new_config = {"section": {"name": "value"}}
    interface.supervisord.diff_to_active = lambda: [[new_config], [], []]

    options = DummyOptions()
    changes = [
        [DummyPGroupConfig(options, name="added")],
        [DummyPGroupConfig(options, name="changed")],
        [DummyPGroupConfig(options, name="dropped")],
    ]

    interface.supervisord.diff_to_active = lambda: changes
    result = interface.set_config(new_config)
    assert isinstance(result, tuple)  # Assuming _reload_config returns a tuple


def test_set_config_raises_rpc_error_if_reload_config_raises_value_error(interface):
    def raise_value_error():
        raise ValueError("test")

    interface._reload_config = raise_value_error
    with pytest.raises(RPCError):
        interface.set_config({})


def test_set_config_raises_rpc_error_if_reload_config_raises_exception(interface):
    def raise_exception():
        raise RuntimeError("test")

    interface._reload_config = raise_exception
    with pytest.raises(RPCError):
        interface.set_config({})
