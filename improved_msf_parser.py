#!/usr/bin/env python3
"""
Improved MSF Output Parser
=========================
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

class ImprovedMSFParser:
    """Enhanced MSF output parser with intelligent type detection"""
    
    def __init__(self):
        # Patterns for output type detection
        self.patterns = {
            "error": [
                r"\[-\]\s*Unknown command",
                r"\[-\]\s*.*error.*",
                r"\[-\]\s*.*failed.*",
                r"Error:",
                r"not found"
            ],
            "table": [
                r"^.*\n.*[=]{3,}.*\n",  # Header with separator
                r"^\s*#\s+Name\s+.*\n",  # Module search table
                r"^\s*Id\s+Name\s*\n",   # Targets table
                r"^\s*Name\s+Current Setting.*\n"  # Options table
            ],
            "version_info": [
                r"Framework:\s*\d+\.\d+",
                r"Console\s*:\s*\d+\.\d+"
            ],
            "workspace_list": [
                r"Workspaces\s*\n[=]{3,}",
                r"\*\s+\w+"  # Current workspace marker
            ],
            "info_block": [
                r"^\s*Name:\s*.*\n",
                r"^\s+Module:\s*.*\n",
                r"Basic options:\s*\n"
            ]
        }
    
    def detect_output_type(self, output: str) -> OutputType:
        """Detect the type of MSF output"""
        output_lower = output.lower()
        
        # Check for errors first
        for pattern in self.patterns["error"]:
            if re.search(pattern, output, re.IGNORECASE | re.MULTILINE):
                return OutputType.ERROR
        
        # Check for version info
        for pattern in self.patterns["version_info"]:
            if re.search(pattern, output, re.IGNORECASE):
                return OutputType.VERSION_INFO
        
        # Check for workspace list
        for pattern in self.patterns["workspace_list"]:
            if re.search(pattern, output, re.IGNORECASE | re.MULTILINE):
                return OutputType.LIST
        
        # Check for info blocks first (before tables)
        for pattern in self.patterns["info_block"]:
            if re.search(pattern, output, re.MULTILINE):
                return OutputType.INFO_BLOCK

        # Check for tables (known patterns)
        for pattern in self.patterns["table"]:
            if re.search(pattern, output, re.MULTILINE):
                return OutputType.TABLE

        # Heuristic: generic table with header followed by dashed separator
        lines = output.split('\n')
        for i in range(len(lines) - 1):
            header_line = lines[i].strip()
            sep_line = lines[i + 1]
            if header_line and len(header_line.split()) >= 2 and re.match(r"^[\s\-_=]{3,}$", sep_line):
                return OutputType.TABLE
        
        # Default to raw
        return OutputType.RAW
    
    def parse_error_output(self, output: str) -> ParsedOutput:
        """Parse error output"""
        error_lines = []
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('[-]'):
                error_lines.append(line[3:].strip())  # Remove [-] prefix
            elif 'error' in line.lower() or 'failed' in line.lower():
                error_lines.append(line)
        
        return ParsedOutput(
            output_type=OutputType.ERROR,
            success=False,
            data={"errors": error_lines},
            raw_output=output,
            error_message=" | ".join(error_lines) if error_lines else "Unknown error"
        )
    
    def parse_version_info(self, output: str) -> ParsedOutput:
        """Parse version information"""
        version_data = {}
        
        # Extract version components
        patterns = {
            "framework": r"Framework:\s*([^\n\r]+)",
            "console": r"Console\s*:\s*([^\n\r]+)",
            "ruby": r"Ruby\s*:\s*([^\n\r]+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                version_data[key] = match.group(1).strip()
        
        return ParsedOutput(
            output_type=OutputType.VERSION_INFO,
            success=True,
            data=version_data,
            raw_output=output
        )
    
    def parse_table_output(self, output: str) -> ParsedOutput:
        """Parse tabular output with dynamic column detection"""
        lines = output.split('\n')
        
        # Find header and separator
        header_idx = -1
        separator_idx = -1
        
        for i, line in enumerate(lines):
            # Look for table headers
            if re.search(r'^\s*#\s+Name', line) or re.search(r'^\s*Name\s+.*Setting', line):
                header_idx = i
            elif re.search(r'^[\s\-=]{10,}$', line) and header_idx != -1:
                separator_idx = i
                break
        
        if header_idx == -1:
            # Fallback: look for any line with multiple columns
            for i, line in enumerate(lines):
                if len(line.split()) >= 3 and not line.startswith('#'):
                    words = line.split()
                    if all(len(word) > 1 for word in words[:3]):  # Reasonable column headers
                        header_idx = i
                        break
        
        if header_idx == -1:
            return ParsedOutput(
                output_type=OutputType.RAW,
                success=False,
                data=output,
                raw_output=output,
                error_message="Could not detect table structure"
            )
        
        # Extract headers
        header_line = lines[header_idx].strip()
        
        # Determine if this is a module search table
        if '#' in header_line and 'Name' in header_line:
            return self._parse_module_search_table(lines, header_idx)
        elif 'Name' in header_line and 'Setting' in header_line:
            return self._parse_options_table(lines, header_idx)
        else:
            return self._parse_generic_table(lines, header_idx)
    
    def _parse_module_search_table(self, lines: List[str], header_idx: int) -> ParsedOutput:
        """Parse module search results table"""
        modules = []
        
        # Skip header and separator, start parsing data
        data_start = header_idx + 2
        
        for line in lines[data_start:]:
            line = line.strip()
            if not line or line.startswith('Interact with'):
                break
            
            # Parse module search format: # Name Date Rank Check Description
            parts = line.split(None, 5)  # Split into max 6 parts
            if len(parts) >= 2:
                module = {
                    "index": parts[0],
                    "name": parts[1] if len(parts) > 1 else "",
                    "disclosure_date": parts[2] if len(parts) > 2 else "",
                    "rank": parts[3] if len(parts) > 3 else "",
                    "check": parts[4] if len(parts) > 4 else "",
                    "description": parts[5] if len(parts) > 5 else ""
                }
                modules.append(module)
        
        return ParsedOutput(
            output_type=OutputType.TABLE,
            success=True,
            data=modules,
            raw_output='\n'.join(lines),
            metadata={"table_type": "module_search", "count": len(modules)}
        )
    
    def _parse_options_table(self, lines: List[str], header_idx: int) -> ParsedOutput:
        """Parse module options table"""
        options = []
        
        # Find start of data (after headers and separators)
        data_start = header_idx + 1
        for i in range(header_idx + 1, len(lines)):
            if lines[i].strip() and not re.match(r'^[\s\-=]+$', lines[i]):
                data_start = i
                break
        
        for line in lines[data_start:]:
            line = line.strip()
            if not line or line.startswith('Description:'):
                break
            
            # Parse options format: Name Current_Setting Required Description
            parts = line.split(None, 3)
            if len(parts) >= 3:
                option = {
                    "name": parts[0],
                    "current_setting": parts[1] if len(parts) > 1 else "",
                    "required": parts[2] if len(parts) > 2 else "",
                    "description": parts[3] if len(parts) > 3 else ""
                }
                options.append(option)
        
        return ParsedOutput(
            output_type=OutputType.TABLE,
            success=True,
            data=options,
            raw_output='\n'.join(lines),
            metadata={"table_type": "options", "count": len(options)}
        )
    
    def _parse_generic_table(self, lines: List[str], header_idx: int) -> ParsedOutput:
        """Parse generic table format"""
        header_line = lines[header_idx].strip()
        headers = header_line.split()
        
        data = []
        data_start = header_idx + 1
        
        # Skip separator lines
        while data_start < len(lines) and re.match(r'^[\s\-=]+$', lines[data_start]):
            data_start += 1
        
        for line in lines[data_start:]:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(None, len(headers) - 1)  # Split into max header count
            if parts:
                row = {}
                for i, header in enumerate(headers):
                    row[header.lower()] = parts[i] if i < len(parts) else ""
                data.append(row)
        
        return ParsedOutput(
            output_type=OutputType.TABLE,
            success=True,
            data=data,
            raw_output='\n'.join(lines),
            metadata={"table_type": "generic", "headers": headers, "count": len(data)}
        )
    
    def parse_info_block(self, output: str) -> ParsedOutput:
        """Parse info block output (like module info)"""
        info_data = {}
        current_section = "metadata"
        sections = {"metadata": {}, "options": [], "targets": [], "description": ""}
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section changes
            if line.startswith('Basic options:'):
                current_section = "options"
                continue
            elif line.startswith('Available targets:'):
                current_section = "targets"
                continue
            elif line.startswith('Description:'):
                current_section = "description"
                continue
            
            # Parse based on current section
            if current_section == "metadata":
                # Parse key: value pairs
                if ':' in line:
                    key, value = line.split(':', 1)
                    sections["metadata"][key.strip().lower().replace(' ', '_')] = value.strip()
            
            elif current_section == "options":
                # Parse options table
                # Skip separator/header lines
                if re.match(r'^[\s\-=]+$', line) or line.startswith('Name'):
                    continue
                parts = line.split(None, 3)
                if len(parts) >= 3:
                    option = {
                        "name": parts[0],
                        "current_setting": parts[1],
                        "required": parts[2],
                        "description": parts[3] if len(parts) > 3 else ""
                    }
                    sections["options"].append(option)
            
            elif current_section == "targets":
                # Parse targets table
                # Skip header/separator lines
                if line.startswith('Id') or re.match(r'^[\s\-=]+$', line):
                    continue
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    target = {
                        "id": parts[0],
                        "name": parts[1]
                    }
                    sections["targets"].append(target)
            
            elif current_section == "description":
                # Accumulate description text
                if sections["description"]:
                    sections["description"] += " " + line
                else:
                    sections["description"] = line
        
        return ParsedOutput(
            output_type=OutputType.INFO_BLOCK,
            success=True,
            data=sections,
            raw_output=output,
            metadata={"sections": list(sections.keys())}
        )
    
    def parse_list_output(self, output: str) -> ParsedOutput:
        """Parse list output (like workspace list)"""
        items = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or '=' in line or line == 'Workspaces':
                continue
            
            # Handle workspace format with current marker
            if line.startswith('*'):
                items.append({
                    "name": line[1:].strip(),
                    "current": True
                })
            else:
                items.append({
                    "name": line,
                    "current": False
                })
        
        return ParsedOutput(
            output_type=OutputType.LIST,
            success=True,
            data=items,
            raw_output=output,
            metadata={"count": len(items)}
        )
    
    def parse(self, output: str) -> ParsedOutput:
        """Main parsing method - detects type and parses accordingly"""
        if not output or not output.strip():
            return ParsedOutput(
                output_type=OutputType.RAW,
                success=False,
                data="",
                raw_output=output,
                error_message="Empty output"
            )
        
        # Detect output type
        output_type = self.detect_output_type(output)
        
        # Parse based on type
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
                # Fallback to raw
                return ParsedOutput(
                    output_type=OutputType.RAW,
                    success=True,
                    data=output,
                    raw_output=output
                )
        
        except Exception as e:
            # Parsing failed, return raw with error
            return ParsedOutput(
                output_type=OutputType.RAW,
                success=False,
                data=output,
                raw_output=output,
                error_message=f"Parsing failed: {str(e)}"
            )

# Test the improved parser
def test_improved_parser():
    """Test the improved parser with sample outputs"""
    from test_current_parsing import SAMPLE_OUTPUTS
    
    parser = ImprovedMSFParser()
    
    print("🧪 Testing Improved MSF Parser")
    print("=" * 50)
    
    for name, sample_output in SAMPLE_OUTPUTS.items():
        print(f"\n📋 Testing: {name}")
        print("-" * 30)
        
        result = parser.parse(sample_output)
        
        print(f"Type: {result.output_type.value}")
        print(f"Success: {result.success}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        if result.metadata:
            print(f"Metadata: {json.dumps(result.metadata, indent=2)}")
        
        if isinstance(result.data, list) and result.data:
            print(f"Data sample: {json.dumps(result.data[0], indent=2)}")
            print(f"Total items: {len(result.data)}")
        elif isinstance(result.data, dict):
            print(f"Data: {json.dumps(result.data, indent=2)}")
        else:
            print(f"Data (raw): {str(result.data)[:100]}...")

if __name__ == "__main__":
    test_improved_parser()