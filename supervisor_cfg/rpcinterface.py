import os
from typing import TYPE_CHECKING, Any, Literal

from supervisor.datatypes import list_of_strings
from supervisor.options import UnhosedConfigParser
from supervisor.states import SupervisorStates
from supervisor.xmlrpc import Faults as SupervisorFaults
from supervisor.xmlrpc import RPCError

if TYPE_CHECKING:
    from supervisor.options import ProcessGroupConfig

API_VERSION = "0.1"


class ExtendedSupervisorStates(SupervisorStates):
    """
    Extended Supervisor states for custom behavior.

    Attributes:
        NOT_IN_WHITELIST (int): Represents a state
            where an operation is not whitelisted.
    """

    NOT_IN_WHITELIST = 1001


class CfgNamespaceRPCInterface:
    """
    An RPC interface for managing Supervisor's configuration.

    Attributes:
        supervisord: The Supervisor daemon instance.
        _whitelist (List[str]): List of whitelisted function names.
    """

    def __init__(self, supervisord, whitelist: list[str] = []) -> None:
        """
        Initializes the CfgNamespaceRPCInterface class.

        Args:
            supervisord: Supervisor daemon instance.
            whitelist (List[str], optional): List of whitelisted
                function names. Defaults to empty list.

        Raises:
            TypeError: Raised if whitelist is not a list of strings.
        """
        self.supervisord = supervisord
        self._whitelist = list_of_strings(whitelist)

    def _update(self, func_name: str) -> None:
        """
        Updates the internal state for a specific function call.

        Args:
            func_name (str): Name of the function being invoked.

        Raises:
            RPCError: Raised if the system is in SHUTDOWN state.
            RPCError: Raised if function name is not in the whitelist.
        """
        self.update_text = func_name
        state = self.supervisord.get_state()
        if state == SupervisorStates.SHUTDOWN:
            raise RPCError(SupervisorFaults.SHUTDOWN_STATE)
        if len(self._whitelist):
            if func_name not in self._whitelist:
                raise RPCError(ExtendedSupervisorStates.NOT_IN_WHITELIST, func_name)

    # RPC API methods

    def _config_filename(self) -> str:
        """
        Retrieves the absolute path of the configuration file.

        Returns:
            str: Absolute path of the configuration file.
        """
        return os.path.abspath(self.supervisord.options.configfile)

    def get_config_filename(self) -> str:
        """
        Retrieves the absolute path of the configuration file.

        Returns:
            str: Absolute path of the configuration file.
        """
        self._update("get_config_filename")
        return self._config_filename()

    def _config_file_parser(self) -> UnhosedConfigParser:
        """
        Parses the configuration file and returns its content.

        Returns:
            UnhosedConfigParser: Object representing the parsed
                content of the configuration file.
        """
        config = UnhosedConfigParser(interpolation=None)
        config.read(self._config_filename())
        return config

    def _config_file_dict(self) -> dict[str, dict[str, str]]:
        """
        Converts the parsed configuration file into a dictionary.

        Returns:
            Dict[str, Dict[str, str]]: Dictionary representation
                of the configuration file.
        """
        return {x: dict(y) for x, y in dict(self._config_file_parser()).items()}

    def _set_command(
        self, program: str, command: str
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Sets the command for a specified program in the configuration file.

        Args:
            program (str): Name of the program.
            command (str): The command to set for the program.

        Returns:
            Tuple[List[str], List[str], List[str]]: A tuple of lists indicating
            added, changed, and removed groups by name.

        Raises:
            RPCError: Raised if the operation fails.
        """
        c = self._config_file_parser()
        c[f"program:{program}"] = {"command": command}
        try:
            with open(self._config_filename(), "w") as f:
                c.write(f)
            return self._reload_config()
        except Exception as e:
            raise RPCError(SupervisorFaults.FAILED, str(e)) from e

    def set_command(
        self, program: str, command_or_section: str | dict[str, str]
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Sets the command for a specified program or a section in the configuration file.

        Example:
            set_command('my_program', 'ls -la')
            set_command('my_program', {'command': 'ls -la', 'autostart': 'true'})

        Args:
            program (str): Name of the program.
            command_or_section (Union[str, Dict[str, str]]): Either a string
                representing the command or a dictionary representing
                a section in the configuration.

        Returns:
            Tuple[List[str], List[str], List[str]]: A tuple of lists indicating
                added, changed, and removed groups by name.


        Raises:
            RPCError: Raised if the operation fails or if the
                function name is not whitelisted.
        """
        self._update("set_command")
        if isinstance(command_or_section, str):
            return self._set_command(program, command_or_section)
        else:
            return self._set_section(f"program:{program}", command_or_section)

    def get_config(self) -> dict[str, dict[str, str]]:
        """
        Retrieves the current configuration.

        Returns:
            Dict[str, Dict[str, str]]: The current configuration as a dictionary.

        Raises:
            RPCError: Raised if the operation fails or if the
                function name is not whitelisted.
        """
        self._update("get_config")
        return self._config_file_dict()

    def _set_section(
        self, section: str, settings: dict[str, str]
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Sets a section in the configuration file with provided settings.

        Args:
            section (str): Name of the section (e.g., program:my_program).
            settings (Dict[str, str]): Settings for the section.

        Returns:
            Tuple[List[str], List[str], List[str]]: A tuple of lists indicating
            added, changed, and removed groups by name.

        Raises:
            RPCError: Raised if the operation fails.
        """
        c = self._config_file_parser()
        c[section] = settings
        try:
            with open(self._config_filename(), "w") as f:
                c.write(f)
            return self._reload_config()
        except Exception as e:
            raise RPCError(SupervisorFaults.FAILED, str(e)) from e

    def _reload_config(self) -> tuple[list[str], list[str], list[str]]:
        """
        Reloads the configuration and returns the changes.

        Returns:
            Tuple[List[str], List[str], List[str]]: A tuple of lists indicating
            added, changed, and removed groups by name.

        Raises:
            RPCError: Raised if the operation fails.
        """
        try:
            self.supervisord.options.process_config(do_usage=False)
        except ValueError as msg:
            raise RPCError(SupervisorFaults.CANT_REREAD, msg) from msg

        added: list[ProcessGroupConfig] = []
        changed: list[ProcessGroupConfig] = []
        removed: list[ProcessGroupConfig] = []
        added, changed, removed = self.supervisord.diff_to_active()
        added_group_titles: list[str] = [group.name for group in added]
        changed_group_titles: list[str] = [group.name for group in changed]
        removed_group_titles: list[str] = [group.name for group in removed]

        return added_group_titles, changed_group_titles, removed_group_titles

    def get_program_info(self, program: str) -> dict[str, Any]:
        """
        Retrieves information about a specific program.

        Args:
            program (str): Name of the program.

        Returns:
            Dict[str, Any]: Dictionary containing information about
                the specified program.

        Raises:
            RPCError: Raised if the operation fails or if the function
                name is not whitelisted.
        """
        self._update("get_program_info")
        return self.supervisord.getProcessInfo(program)

    def start_program(self, program: str) -> Literal[True]:
        """
        Starts a specific program.

        Args:
            program (str): Name of the program to start.

        Returns:
            bool: True if the program was started successfully.

        Raises:
            RPCError: Raised if the operation fails or if the function
                name is not whitelisted.
        """
        self._update("start_program")
        try:
            self.supervisord.startProcess(program)
        except Exception as e:
            raise RPCError(SupervisorFaults.FAILED, str(e)) from e
        return True

    def stop_program(self, program: str) -> Literal[True]:
        """
        Stops a specific program.

        Args:
            program (str): Name of the program to stop.

        Returns:
            Union[str, bool]: Either a string indicating a failure or
            True for successful stop.

        Raises:
            RPCError: Raised if the operation fails or if the
                function name is not whitelisted.
        """
        self._update("stop_program")
        try:
            self.supervisord.stopProcess(program)
        except Exception as e:
            raise RPCError(SupervisorFaults.FAILED, str(e)) from e
        return True

    def _set_config(
        self, config: dict[str, dict[str, str]]
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Internal method to set the entire configuration.

        :param config: New configuration as a dictionary.
        :return: Result of the operation: List of Lists with the names (str)
        of added, changed and removed groups.
        """
        c = UnhosedConfigParser(interpolation=None)
        c.read_dict(config)
        try:
            with open(self._config_filename(), "w") as f:
                c.write(f)
            return self._reload_config()
        except Exception as e:
            raise RPCError(SupervisorFaults.FAILED, str(e)) from e

    def set_config(
        self, config: dict[str, dict[str, str]]
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Set the entire configuration.

        :param config: New configuration as a dictionary.
        :return: Result of the operation: List of Lists with the names (str)
        of added, changed and removed groups.
        """
        self._update("set_config")
        return self._set_config(config)

def make_cfg_rpcinterface(supervisord, **config):
    return CfgNamespaceRPCInterface(supervisord, **config)
