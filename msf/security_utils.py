#!/usr/bin/env python3
from typing import Iterable

DEFAULT_ALLOWLIST = (
    "help",
    "version",
    "workspace",
    "search",
    "show",
    "info",
    "use",
    "set",
    "unset",
    "check",
    "run",
    "exploit",
    "back",
    "reload_all",
    "sessions",
    "jobs",
    "route",
    "portfwd",
    "load",
    "unload",
    "creds",
    "loot",
    "notes",
    "hosts",
    "services",
    "vulns",
    "db_",
)


def is_command_allowed(command: str, allowlist: Iterable[str] = DEFAULT_ALLOWLIST) -> bool:
    cmd = command.strip().lower()
    for prefix in allowlist:
        if cmd.startswith(prefix):
            return True
    return False
