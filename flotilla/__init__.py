"""Flotilla — plugin marketplace for AI-native projects.

Flotilla is a CLI that installs plugins (each one a git repo or pip
package containing a ``flotilla.yaml`` manifest) and composes their
contributions — Claude Code agents, skills, commands, hooks, and MCP
servers — into a project's ``.claude/`` directory.

Public API is the CLI (``flotilla.cli:main``); the rest of the module
is internal but stable enough for plugin authors to import for testing.
"""

from .__version__ import __version__

__all__ = ["__version__"]
