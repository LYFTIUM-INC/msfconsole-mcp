# MSF Console MCP Server v5.1

Production-ready Model Context Protocol (MCP) server for Metasploit Framework Console, providing 48 specialized penetration testing tools through a structured AI assistant interface.

## Features

### Core Capabilities (48 Tools)
- **Command Execution** - Direct MSFConsole command execution with retry logic
- **Payload Generation** - msfvenom integration for payload creation
- **Module Management** - Complete module lifecycle (load, configure, validate, execute)
- **Session Management** - Advanced session interaction, upgrading, clustering, persistence
- **Post-Exploitation** - Privilege escalation, persistence, lateral movement modules
- **Network Analysis** - Scanning, enumeration, service discovery
- **Vulnerability Assessment** - Automated vulnerability tracking and correlation
- **Credential Management** - Centralized credential storage and testing
- **Reporting Engine** - Professional penetration testing reports
- **Evasion Suite** - AV bypass and obfuscation techniques
- **Plugin System** - Dynamic plugin architecture with auto-discovery

### Architecture

| Component | Description |
|---|---|
| `mcp_server_stable.py` | Main MCP server with 48 tools and JSON-RPC handler |
| `msf_stable_integration.py` | Core MSF console wrapper with retry and timeout logic |
| `msf_extended_tools.py` | Extended tools: module manager, session interaction, database, exploits |
| `msf_advanced_tools.py` | Advanced tools: evasion, listener orchestration, encoding |
| `msf_final_five_tools.py` | System tools: core system, job manager, debug suite |
| `msf_ecosystem_tools.py` | Ecosystem tools: msfvenom direct, database direct, RPC |
| `msf_enhanced_tools.py` | v5 tools: plugin manager, routing, grep, spool, config |
| `msf_advanced_session_manager.py` | Session upgrading, bulk ops, clustering, persistence |
| `msf_plugin_system.py` | Plugin framework with registry and lifecycle management |
| `improved_msf_parser.py` | Structured output parsing for MSF console output |
| `config.py` | Configuration management |
| `safe_context.py` | Safe MCP context wrapper |

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/LYFTIUM-INC/msfconsole-mcp.git
cd msfconsole-mcp
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Prerequisites:**
   - Python 3.8+
   - Metasploit Framework installed (`msfconsole` and `msfvenom` in PATH)
   - PostgreSQL (for MSF database features)

4. **Configure your MCP client:**

Add to your MCP client configuration (e.g., Claude Desktop):
```json
{
  "msfconsole": {
    "command": "python",
    "args": ["/path/to/msfconsole-mcp/mcp_server_stable.py"]
  }
}
```

## Available Tools (48 Total)

### Primary Operations (8)
| Tool | Description |
|---|---|
| `msf_execute_command` | Execute MSFConsole commands |
| `msf_generate_payload` | Generate payloads via msfvenom |
| `msf_search_modules` | Search modules with pagination |
| `msf_get_status` | Server status and metrics |
| `msf_list_workspaces` | List MSF workspaces |
| `msf_create_workspace` | Create a new workspace |
| `msf_switch_workspace` | Switch active workspace |
| `msf_list_sessions` | List active sessions |

### Extended Operations (11)
| Tool | Description |
|---|---|
| `msf_module_manager` | Module lifecycle management |
| `msf_session_interact` | Advanced session interaction |
| `msf_database_query` | Database operations and analysis |
| `msf_exploit_chain` | Multi-stage exploitation workflows |
| `msf_post_exploitation` | Post-exploitation module management |
| `msf_handler_manager` | Payload handler management |
| `msf_scanner_suite` | Comprehensive scanning |
| `msf_credential_manager` | Credential management |
| `msf_pivot_manager` | Network pivoting and routing |
| `msf_resource_executor` | Resource script execution |
| `msf_loot_collector` | Automated loot collection |

### Advanced Operations (9)
| Tool | Description |
|---|---|
| `msf_vulnerability_tracker` | Vulnerability tracking |
| `msf_reporting_engine` | Report generation |
| `msf_automation_builder` | Workflow automation |
| `msf_plugin_manager` | Plugin management |
| `msf_evasion_suite` | AV bypass techniques |
| `msf_listener_orchestrator` | Listener management |
| `msf_workspace_automator` | Workspace automation |
| `msf_encoder_factory` | Payload encoding |
| `msf_report_generator` | Professional reports |

### System Management (8)
| Tool | Description |
|---|---|
| `msf_core_system_manager` | Core system functions |
| `msf_advanced_module_controller` | Module stack operations |
| `msf_job_manager` | Job lifecycle management |
| `msf_database_admin_controller` | Database administration |
| `msf_developer_debug_suite` | Debug and development |
| `msf_venom_direct` | Direct msfvenom access |
| `msf_database_direct` | Direct database management |
| `msf_rpc_interface` | MSF RPC interface |

### v5 Enhanced Operations (12)
| Tool | Description |
|---|---|
| `msf_enhanced_plugin_manager` | Plugin system with auto-discovery |
| `msf_connect` | Network connection utility |
| `msf_interactive_ruby` | IRB shell integration |
| `msf_interactive_session` | Interactive session management |
| `msf_route_manager` | Network routing management |
| `msf_output_filter` | Output grep/filtering |
| `msf_console_logger` | Console output logging |
| `msf_config_manager` | Configuration save/load |
| `msf_session_upgrader` | Shell to Meterpreter upgrade |
| `msf_bulk_session_operations` | Bulk session operations |
| `msf_session_clustering` | Session grouping |
| `msf_session_persistence` | Persistence mechanisms |

## Testing

Run the test suite:
```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

Run with coverage:
```bash
pip install pytest-cov
python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

## Security Notice

**IMPORTANT**: This tool is for authorized security testing only.

- Only use on systems you own or have explicit permission to test
- Ensure proper network isolation during testing
- Use workspaces to separate engagements
- Review all commands before execution
- Comply with all applicable laws and regulations
- Workspace names are sanitized to prevent injection attacks
- Dangerous system commands (rm, shutdown, etc.) are blocked

## License

For authorized security testing and educational purposes only. Users are responsible for compliance with all applicable laws and regulations.

---
**Version**: 5.1.0
**Tools**: 48 Specialized MSF Console Tools
**Framework**: Metasploit Framework Integration via MCP
