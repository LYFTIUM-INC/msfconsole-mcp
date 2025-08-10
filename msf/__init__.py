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
from msf_stable_integration import MSFConsoleStableWrapper, OperationStatus, OperationResult
from msf_extended_tools import MSFExtendedTools, ExtendedOperationResult
from msf_final_five_tools import MSFFinalFiveTools, FinalOperationResult
from msf_ecosystem_tools import MSFEcosystemTools, EcosystemResult
from msf_advanced_tools import MSFAdvancedTools, AdvancedResult

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