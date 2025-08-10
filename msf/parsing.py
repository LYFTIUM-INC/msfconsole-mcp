from typing import List, Dict
from dataclasses import dataclass
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


# Typed parsers for extended tables
@dataclass
class Route:
    subnet: str
    netmask: str
    gateway: str


def parse_routes(output: str) -> List[Route]:
    routes: List[Route] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("IPv4") or line.startswith("=") or line.startswith("Subnet"):
            continue
        parts = line.split()
        if len(parts) >= 3:
            routes.append(Route(subnet=parts[0], netmask=parts[1], gateway=parts[2]))
    return routes


@dataclass
class Credential:
    host: str
    service: str
    username: str
    secret: str
    ctype: str


def parse_creds(output: str) -> List[Credential]:
    creds: List[Credential] = []
    for line in output.splitlines():
        line = line.strip()
        if (
            not line
            or line.startswith("Credentials")
            or line.startswith("=")
            or line.startswith("host")
        ):
            continue
        parts = line.split()
        if len(parts) >= 4:
            creds.append(
                Credential(
                    host=parts[0],
                    service=parts[1],
                    username=parts[2],
                    secret=parts[3] if len(parts) > 3 else "",
                    ctype=parts[4] if len(parts) > 4 else "password",
                )
            )
    return creds


@dataclass
class LootItem:
    host: str
    service: str
    ltype: str
    name: str
    path: str


def parse_loot(output: str) -> List[LootItem]:
    items: List[LootItem] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("Loot") or line.startswith("=") or line.startswith("host"):
            continue
        parts = line.split()
        if len(parts) >= 5:
            items.append(
                LootItem(
                    host=parts[0], service=parts[1], ltype=parts[2], name=parts[3], path=parts[4]
                )
            )
    return items


@dataclass
class Job:
    job_id: str
    name: str


def parse_jobs(output: str) -> List[Job]:
    jobs: List[Job] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("Jobs") or line.startswith("=") or line.startswith("Id"):
            continue
        parts = line.split()
        if parts and parts[0].isdigit():
            jobs.append(Job(job_id=parts[0], name=" ".join(parts[1:])))
    return jobs
