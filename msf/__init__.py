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
from .tools_extended import MSFExtendedTools, ExtendedOperationResult
from .tools_final import MSFFinalFiveTools, FinalOperationResult
from .tools_ecosystem import MSFEcosystemTools, EcosystemResult
from .tools_advanced import MSFAdvancedTools, AdvancedResult

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
    "MSFExtendedTools",
    "ExtendedOperationResult",
    "MSFFinalFiveTools",
    "FinalOperationResult",
    "MSFEcosystemTools",
    "EcosystemResult",
    "MSFAdvancedTools",
    "AdvancedResult",
]
