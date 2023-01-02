import os
from typing import Union

from supervisor.datatypes import list_of_strings
from supervisor.options import UnhosedConfigParser
from supervisor.states import SupervisorStates
from supervisor.xmlrpc import Faults as SupervisorFaults
from supervisor.xmlrpc import RPCError

API_VERSION = "0.1"


class CfgNamespaceRPCInterface:
    """A supervisor rpc interface that facilitates persistent
    manipulation of supervisor's configuration.
    """

    def __init__(self, supervisord, whitelist=[]):
        self.supervisord = supervisord
        self._whitelist = list_of_strings(whitelist)

    def _update(self, func_name):
        self.update_text = func_name

        state = self.supervisord.get_state()
        if state == SupervisorStates.SHUTDOWN:
            raise RPCError(SupervisorFaults.SHUTDOWN_STATE)

        if len(self._whitelist):
            if func_name not in self._whitelist:
                raise RPCError(SupervisorFaults.NOT_IN_WHITELIST, func_name)

    # RPC API methods
    def _config_filename(self) -> str:
        return os.path.abspath(self.supervisord.options.configfile)

    def _config_file_parser(self) -> UnhosedConfigParser:
        config = UnhosedConfigParser(interpolation=None)
        config.read(self._config_filename())
        return config

    def _config_file_dict(self) -> dict:
        return {x: dict(y) for x, y in dict(self._config_file_parser()).items()}

    def _set_command(self, program: str, command: str):
        c = self._config_file_parser()
        c[f"program:{program}"] = {"command": command}
        try:
            with open(self._config_filename(), "w") as f:
                c.write(f)
            return self._reload_config()
        except Exception as e:
            return str(e)

    def set_command(self, program: str, command_or_section: Union[str, dict]):
        """Set command

        @param program string program name
        @param command string command
        @return list [added, changed, removed]
        """
        self._update("set_command")
        if isinstance(command_or_section, str):
            return self._set_command(program, command_or_section)
        else:
            return self._set_section(f"program:{program}", command_or_section)

    def get_config(self):
        """Get config

        @return dict config
        """
        self._update("get_config")
        return self._config_file_dict()

    def get_config_filename(self):
        """Return config filename

        @return string config filename
        """
        self._update("get_config_filename")
        return self._config_filename()

    def set_config(self, config: dict):
        """Set config

        @param config dict config
        @return list [added, changed, removed]
        """
        self._update("set_config")
        return self._set_config(config)

    def set_section(self, section_name: str, content: dict):
        """Set section

        @param section_name string section name
        @param content dict section content
        @return list [added, changed, removed]
        """
        self._update("set_section")
        return self._set_section(section_name, content)

    def _set_section(self, section: str, content: dict):
        c = self._config_file_parser()
        c[section] = content
        try:
            with open(self._config_filename(), "w") as f:
                c.write(f)
            return self._reload_config()
        except Exception as e:
            return str(e)

    def stop_and_remove_program(self, program: str):
        """Stop and remove program

        @param program string program name
        @return list [added, changed, removed]
        """
        self._update("stop_and_remove_program")
        return self._stop_and_remove(program)

    def _stop_and_remove(self, program: str):
        c = self._config_file_dict()
        c.pop(f"program:{program}")
        # del c[f"program:{program}"]
        return self._set_config(c)

    def _set_config(self, config: dict):
        c = UnhosedConfigParser(interpolation=None)
        c.read_dict(config)
        try:
            with open(self._config_filename(), "w") as f:
                c.write(f)
            return self._reload_config()
        except Exception as e:
            return str(e)

    def _reload_config(self):
        # from default rpcinterface
        try:
            self.supervisord.options.process_config(do_usage=False)
        except ValueError as msg:
            raise RPCError(SupervisorFaults.CANT_REREAD, msg)

        added, changed, removed = self.supervisord.diff_to_active()

        added = [group.name for group in added]
        changed = [group.name for group in changed]
        removed = [group.name for group in removed]
        return [added, changed, removed]  # cannot return len > 1, apparently


def make_cfg_rpcinterface(supervisord, **config):
    return CfgNamespaceRPCInterface(supervisord, **config)
