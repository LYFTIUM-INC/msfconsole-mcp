#!/usr/bin/env python3
"""
MSF Output Parser
=================
Comprehensive parsing system for Metasploit Console output with:
- Output type detection
- Flexible table parsing
- Section-based parsing for complex outputs
- Robust error handling
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass


class OutputType(Enum):
    TABLE = "table"
    LIST = "list"
    INFO_BLOCK = "info_block"
    ERROR = "error"
    RAW = "raw"
    VERSION_INFO = "version_info"


@dataclass
class ParsedOutput:
    """Structured representation of parsed MSF output"""
    output_type: OutputType
    success: bool
    data: Union[List[Dict], Dict[str, Any], str]
    raw_output: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MSFParser:
    """MSF output parser with intelligent type detection"""

    def __init__(self):
        self.patterns = {
            "error": [
                r"\[-\]\s*Unknown command",
                r"\[-\]\s*.*error.*",
                r"\[-\]\s*.*failed.*",
                r"Error:",
                r"not found",
            ],
            "table": [
                r"^.*\n.*[=]{3,}.*\n",
                r"^\s*#\s+Name\s+.*\n",
                r"^\s*Id\s+Name\s*\n",
                r"^\s*Name\s+Current Setting.*\n",
            ],
            "version_info": [
                r"Framework:\s*\d+\.\d+",
                r"Console\s*:\s*\d+\.\d+",
            ],
            "workspace_list": [
                r"Workspaces\s*\n[=]{3,}",
                r"\*\s+\w+",
            ],
            "info_block": [
                r"^\s*Name:\s*.*\n",
                r"^\s+Module:\s*.*\n",
                r"Basic options:\s*\n",
            ],
        }

    def detect_output_type(self, output: str) -> OutputType:
        for pattern in self.patterns["error"]:
            if re.search(pattern, output, re.IGNORECASE | re.MULTILINE):
                return OutputType.ERROR
        for pattern in self.patterns["version_info"]:
            if re.search(pattern, output, re.IGNORECASE):
                return OutputType.VERSION_INFO
        for pattern in self.patterns["workspace_list"]:
            if re.search(pattern, output, re.IGNORECASE | re.MULTILINE):
                return OutputType.LIST
        for pattern in self.patterns["info_block"]:
            if re.search(pattern, output, re.MULTILINE):
                return OutputType.INFO_BLOCK
        for pattern in self.patterns["table"]:
            if re.search(pattern, output, re.MULTILINE):
                return OutputType.TABLE
        lines = output.split("\n")
        for i in range(len(lines) - 1):
            header_line = lines[i].strip()
            sep_line = lines[i + 1]
            if header_line and len(header_line.split()) >= 2 and re.match(r"^[\s\-_=]{3,}$", sep_line):
                return OutputType.TABLE
        return OutputType.RAW

    def parse_error_output(self, output: str) -> ParsedOutput:
        error_lines = []
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("[-]"):
                error_lines.append(line[3:].strip())
            elif "error" in line.lower() or "failed" in line.lower():
                error_lines.append(line)
        return ParsedOutput(
            output_type=OutputType.ERROR,
            success=False,
            data={"errors": error_lines},
            raw_output=output,
            error_message=" | ".join(error_lines) if error_lines else "Unknown error",
        )

    def parse_version_info(self, output: str) -> ParsedOutput:
        version_data: Dict[str, str] = {}
        patterns = {
            "framework": r"Framework:\s*([^\n\r]+)",
            "console": r"Console\s*:\s*([^\n\r]+)",
            "ruby": r"Ruby\s*:\s*([^\n\r]+)",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                version_data[key] = match.group(1).strip()
        return ParsedOutput(output_type=OutputType.VERSION_INFO, success=True, data=version_data, raw_output=output)

    def parse_table_output(self, output: str) -> ParsedOutput:
        lines = output.split("\n")
        header_idx = -1
        for i, line in enumerate(lines):
            if re.search(r"^\s*#\s+Name", line) or re.search(r"^\s*Name\s+.*Setting", line):
                header_idx = i
            elif re.search(r"^[\s\-=]{10,}$", line) and header_idx != -1:
                break
        if header_idx == -1:
            for i, line in enumerate(lines):
                if len(line.split()) >= 3 and not line.startswith("#"):
                    words = line.split()
                    if all(len(word) > 1 for word in words[:3]):
                        header_idx = i
                        break
        if header_idx == -1:
            return ParsedOutput(output_type=OutputType.RAW, success=False, data=output, raw_output=output, error_message="Could not detect table structure")
        header_line = lines[header_idx].strip()
        if "#" in header_line and "Name" in header_line:
            return self._parse_module_search_table(lines, header_idx)
        elif "Name" in header_line and "Setting" in header_line:
            return self._parse_options_table(lines, header_idx)
        else:
            return self._parse_generic_table(lines, header_idx)

    def _parse_module_search_table(self, lines: List[str], header_idx: int) -> ParsedOutput:
        modules: List[Dict[str, Any]] = []
        data_start = header_idx + 2
        for line in lines[data_start:]:
            line = line.strip()
            if not line or line.startswith("Interact with"):
                break
            parts = line.split(None, 5)
            if len(parts) >= 2:
                module = {
                    "index": parts[0],
                    "name": parts[1] if len(parts) > 1 else "",
                    "disclosure_date": parts[2] if len(parts) > 2 else "",
                    "rank": parts[3] if len(parts) > 3 else "",
                    "check": parts[4] if len(parts) > 4 else "",
                    "description": parts[5] if len(parts) > 5 else "",
                }
                modules.append(module)
        return ParsedOutput(output_type=OutputType.TABLE, success=True, data=modules, raw_output="\n".join(lines), metadata={"table_type": "module_search", "count": len(modules)})

    def _parse_options_table(self, lines: List[str], header_idx: int) -> ParsedOutput:
        options: List[Dict[str, Any]] = []
        data_start = header_idx + 1
        for i in range(header_idx + 1, len(lines)):
            if lines[i].strip() and not re.match(r"^[\s\-=]+$", lines[i]):
                data_start = i
                break
        for line in lines[data_start:]:
            line = line.strip()
            if not line or line.startswith("Description:"):
                break
            parts = line.split(None, 3)
            if len(parts) >= 3:
                option = {
                    "name": parts[0],
                    "current_setting": parts[1] if len(parts) > 1 else "",
                    "required": parts[2] if len(parts) > 2 else "",
                    "description": parts[3] if len(parts) > 3 else "",
                }
                options.append(option)
        return ParsedOutput(output_type=OutputType.TABLE, success=True, data=options, raw_output="\n".join(lines), metadata={"table_type": "options", "count": len(options)})

    def _parse_generic_table(self, lines: List[str], header_idx: int) -> ParsedOutput:
        header_line = lines[header_idx].strip()
        headers = header_line.split()
        data: List[Dict[str, Any]] = []
        data_start = header_idx + 1
        while data_start < len(lines) and re.match(r"^[\s\-=]+$", lines[data_start]):
            data_start += 1
        for line in lines[data_start:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, len(headers) - 1)
            if parts:
                row: Dict[str, Any] = {}
                for i, header in enumerate(headers):
                    row[header.lower()] = parts[i] if i < len(parts) else ""
                data.append(row)
        return ParsedOutput(output_type=OutputType.TABLE, success=True, data=data, raw_output="\n".join(lines), metadata={"table_type": "generic", "headers": headers, "count": len(data)})

    def parse_info_block(self, output: str) -> ParsedOutput:
        sections: Dict[str, Any] = {"metadata": {}, "options": [], "targets": [], "description": ""}
        lines = output.split("\n")
        current_section = "metadata"
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("Basic options:"):
                current_section = "options"
                continue
            elif line.startswith("Available targets:"):
                current_section = "targets"
                continue
            elif line.startswith("Description:"):
                current_section = "description"
                continue
            if current_section == "metadata":
                if ":" in line:
                    key, value = line.split(":", 1)
                    sections["metadata"][key.strip().lower().replace(" ", "_")] = value.strip()
            elif current_section == "options":
                if re.match(r"^[\s\-=]+$", line) or line.startswith("Name"):
                    continue
                parts = line.split(None, 3)
                if len(parts) >= 3:
                    sections["options"].append({
                        "name": parts[0],
                        "current_setting": parts[1],
                        "required": parts[2],
                        "description": parts[3] if len(parts) > 3 else "",
                    })
            elif current_section == "targets":
                if line.startswith("Id") or re.match(r"^[\s\-=]+$", line):
                    continue
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    sections["targets"].append({"id": parts[0], "name": parts[1]})
            elif current_section == "description":
                sections["description"] = (sections["description"] + " " + line).strip()
        return ParsedOutput(output_type=OutputType.INFO_BLOCK, success=True, data=sections, raw_output=output, metadata={"sections": list(sections.keys())})

    def parse_list_output(self, output: str) -> ParsedOutput:
        items: List[Dict[str, Any]] = []
        for line in output.split("\n"):
            line = line.strip()
            if not line or "=" in line or line == "Workspaces":
                continue
            if line.startswith("*"):
                items.append({"name": line[1:].strip(), "current": True})
            else:
                items.append({"name": line, "current": False})
        return ParsedOutput(output_type=OutputType.LIST, success=True, data=items, raw_output=output, metadata={"count": len(items)})

    def parse(self, output: str) -> ParsedOutput:
        if not output or not output.strip():
            return ParsedOutput(output_type=OutputType.RAW, success=False, data="", raw_output=output, error_message="Empty output")
        output_type = self.detect_output_type(output)
        try:
            if output_type == OutputType.ERROR:
                return self.parse_error_output(output)
            elif output_type == OutputType.VERSION_INFO:
                return self.parse_version_info(output)
            elif output_type == OutputType.TABLE:
                return self.parse_table_output(output)
            elif output_type == OutputType.INFO_BLOCK:
                return self.parse_info_block(output)
            elif output_type == OutputType.LIST:
                return self.parse_list_output(output)
            else:
                return ParsedOutput(output_type=OutputType.RAW, success=True, data=output, raw_output=output)
        except Exception as e:
            return ParsedOutput(output_type=OutputType.RAW, success=False, data=output, raw_output=output, error_message=f"Parsing failed: {str(e)}")