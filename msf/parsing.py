from typing import List, Dict
from msf_parser import MSFParser, OutputType

_parser = MSFParser()


def parse_search_results(output: str) -> List[Dict[str, str]]:
    result = _parser.parse(output)
    if result.output_type == OutputType.TABLE and isinstance(result.data, list):
        return result.data  # already list of dicts
    # Fallback: very simple line-based parse similar to legacy behavior
    modules: List[Dict[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "===" in line:
            continue
        if line.startswith("Name") or line.startswith("----") or line.startswith("="):
            continue
        parts = line.split(None, 3)
        if parts:
            modules.append(
                {
                    "name": parts[0],
                    "disclosure_date": parts[1] if len(parts) > 1 else "",
                    "rank": parts[2] if len(parts) > 2 else "",
                    "description": parts[3] if len(parts) > 3 else "",
                }
            )
    return modules


def parse_workspace_list(output: str) -> List[Dict[str, str]]:
    result = _parser.parse(output)
    if result.output_type == OutputType.LIST and isinstance(result.data, list):
        return result.data
    workspaces: List[Dict[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line == "Workspaces" or line.startswith("="):
            continue
        current = line.startswith("*")
        name = line.lstrip("* ").strip()
        if name:
            workspaces.append({"name": name, "current": current})
    return workspaces


def parse_hosts(output: str) -> List[Dict[str, str]]:
    result = _parser.parse(output)
    if result.output_type == OutputType.TABLE and isinstance(result.data, list):
        return result.data
    return []


def parse_services(output: str) -> List[Dict[str, str]]:
    result = _parser.parse(output)
    if result.output_type == OutputType.TABLE and isinstance(result.data, list):
        return result.data
    return []


def parse_vulns(output: str) -> List[Dict[str, str]]:
    result = _parser.parse(output)
    if result.output_type == OutputType.TABLE and isinstance(result.data, list):
        return result.data
    return []


def parse_sessions(output: str) -> List[Dict[str, str]]:
    result = _parser.parse(output)
    if result.output_type == OutputType.TABLE and isinstance(result.data, list):
        return result.data
    return []
