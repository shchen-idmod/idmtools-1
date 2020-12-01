import re
import shlex
from typing import TypeVar, Dict, Any, List
from dataclasses import dataclass, field, InitVar


@dataclass(init=False)
class CommandLine:
    """
        A class to construct command line strings from executable, options, and params
        """
    #: The executable portion of the command
    _executable: str = None
    #: Options for the command
    _options: Dict[str, Any] = field(default_factory=dict)
    #: Arguments for the command
    _args: List[Any] = field(default_factory=list)
    #: Raw Arguments. These arguments are not quoted, so if you need quotes, you have to do that manually
    _raw_args: List[Any] = field(default_factory=list)
    #: Is this a command line for a windows system
    is_windows: bool = field(default=False)

    def __init__(self, executable=None, *args, is_windows: bool = False, raw_args: List[Any] = None, **kwargs):
        # If there is a space in executable, we probably need to split it
        self._executable = executable
        self._options = kwargs or {}
        self._args = list(args) if args else []
        self.is_windows = is_windows
        self._raw_args = list(raw_args) if raw_args else []
        # check if user is providing a full command line
        if executable and " " in executable:
            other = self.from_string(executable)
            self._executable = other._executable
            if other._args:
                self._args += other._args
            if other.options:
                self._options += other._options

    @property
    def executable(self) -> str:
        return self._executable.replace('/', "\\") if self.is_windows else self._executable

    @executable.setter
    def executable(self, executable):
        self._executable = executable

    def add_argument(self, arg):
        self._args.append(arg)

    def add_raw_argument(self, arg):
        """
        Add an argument that won't be quote on format

        Args:
            arg:arg

        Returns:

        """
        self._raw_args.append(arg)

    def add_option(self, option, value):
        self._options[option] = value

    @property
    def options(self):
        options = []
        for k, v in self._options.items():
            # Handles spaces
            value = '"%s"' % v if ' ' in str(v) else str(v)
            if k[-1] == ':':
                options.append(k + value)  # if the option ends in ':', don't insert a space
            else:
                options.extend([k, value])  # otherwise let join (below) add a space

        if self.is_windows:
            return ' '.join([self.__quote_windows(s) for s in options if s])
        else:
            return ' '.join([shlex.quote(s) for s in options if s])

    @staticmethod
    def __quote_windows(s):
        """
        Quote a parameter for windows command line

        Args:
            s:

        Returns:

        """
        n = s.replace('"', '\\"')
        if re.search(r'(["\s])', s):
            return f'"{n}"'
        return n

    @property
    def arguments(self):
        quote_fn = self.__quote_windows if self.is_windows else self.__quote_linux
        qargs = ' '.join([quote_fn(s) for s in self._args if s])
        qargs += ' ' + self.raw_arguments
        return qargs

    def __quote_linux(self, s):
        return shlex.quote(s)

    @property
    def raw_arguments(self):
        return ' '.join(self._raw_args)

    @property
    def cmd(self):
        return ' '.join(filter(None, [self._executable.strip(), self.options.strip(), self.arguments.strip()]))

    def __str__(self):
        return self.cmd

    @staticmethod
    def from_string(command: str, as_raw_args: bool = False) -> 'CommandLine':
        """
        Creates a command line object from string

        Args:
            command: Command
            as_raw_args: When set to true, arguments will preserve the quoting provided

        Returns:
            CommandLine object from string
        """
        parts = shlex.split(command.replace("\\", "/"))
        arguments = parts[1:] if len(parts) > 1 else []
        cl = CommandLine(parts[0], *arguments if not as_raw_args else [])
        if as_raw_args:
            # replace executable
            remaining = command.replace(parts[0], "", 1)
            cl.add_raw_argument(remaining)
        return cl


TCommandLine = TypeVar("TCommandLine", bound=CommandLine)
