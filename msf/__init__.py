from .parsing import (
    parse_search_results,
    parse_workspace_list,
    parse_hosts,
    parse_services,
    parse_vulns,
    parse_sessions,
)

from msf_parser import MSFParser, OutputType, ParsedOutput

# Re-export core wrapper and tool classes to provide a stable package API
from .core import MSFConsoleStableWrapper, OperationStatus, OperationResult
from .tools_extended import ConsoleExtendedTools, ExtendedToolResult
from .tools_final import ConsoleAdministrationTools, AdministrationToolResult
from .tools_ecosystem import MetasploitEcosystemTools, EcosystemToolResult
from .tools_advanced import EcosystemAdvancedTools, AdvancedToolResult

# Deprecated aliases for backward compatibility
import warnings as _warnings

MSFExtendedTools = ConsoleExtendedTools  # deprecated
MSFFinalFiveTools = ConsoleAdministrationTools  # deprecated
MSFEcosystemTools = MetasploitEcosystemTools  # deprecated
MSFAdvancedTools = EcosystemAdvancedTools  # deprecated
ExtendedOperationResult = ExtendedToolResult  # deprecated
FinalOperationResult = AdministrationToolResult  # deprecated
EcosystemResult = EcosystemToolResult  # deprecated
AdvancedResult = AdvancedToolResult  # deprecated

for _name in [
    ("MSFExtendedTools", "ConsoleExtendedTools"),
    ("MSFFinalFiveTools", "ConsoleAdministrationTools"),
    ("MSFEcosystemTools", "MetasploitEcosystemTools"),
    ("MSFAdvancedTools", "EcosystemAdvancedTools"),
    ("ExtendedOperationResult", "ExtendedToolResult"),
    ("FinalOperationResult", "AdministrationToolResult"),
    ("EcosystemResult", "EcosystemToolResult"),
    ("AdvancedResult", "AdvancedToolResult"),
]:
    _warnings.warn(
        f"{_name[0]} is deprecated; use {_name[1]} instead",
        DeprecationWarning,
        stacklevel=2,
    )

__all__ = [
    # parsing
    "MSFParser",
    "OutputType",
    "ParsedOutput",
    "parse_search_results",
    "parse_workspace_list",
    "parse_hosts",
    "parse_services",
    "parse_vulns",
    "parse_sessions",
    # core wrapper and tools
    "MSFConsoleStableWrapper",
    "OperationStatus",
    "OperationResult",
    "ConsoleExtendedTools",
    "ExtendedToolResult",
    "ConsoleAdministrationTools",
    "AdministrationToolResult",
    "MetasploitEcosystemTools",
    "EcosystemToolResult",
    "EcosystemAdvancedTools",
    "AdvancedToolResult",
]
