"""Sub-command implementations.

Each module owns one sub-command; the CLI wires them up by name. The
split keeps each function small and individually unit-testable.
"""

from .doctor import cmd_doctor
from .info import cmd_info
from .init import cmd_init
from .install import cmd_install
from .list_cmd import cmd_list
from .remove import cmd_remove
from .search import cmd_search
from .sync import cmd_sync
from .upgrade import cmd_upgrade
from .validate import cmd_validate

__all__ = [
    "cmd_doctor",
    "cmd_info",
    "cmd_init",
    "cmd_install",
    "cmd_list",
    "cmd_remove",
    "cmd_search",
    "cmd_sync",
    "cmd_upgrade",
    "cmd_validate",
]
