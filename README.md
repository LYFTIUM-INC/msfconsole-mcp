# MSFConsole MCP Server

A Model Context Protocol (MCP) server providing comprehensive Metasploit Framework integration for AI assistants. Enables secure, structured access to MSF capabilities for defensive security analysis and penetration testing.

## ✨ Features

- 38+ comprehensive tools across console and ecosystem coverage
- Production-ready reliability with strong test coverage
- Intelligent output parsing with adaptive timeout management
- Secure command execution with robust error handling
- Advanced module, database, session and payload workflows

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Metasploit Framework (6.4+)
- MCP-compatible client

### Installation

1. Clone the repository:
```bash
git clone https://github.com/lyftium/msfconsole-mcp.git
cd msfconsole-mcp
```

2. Install dependencies (use a venv):
```bash
python3 -m venv .venv && source .venv/bin/activate
pip3 install -r dev-requirements.txt -r requirements.txt
```

3. Register MCP server (example):
```bash
# Thin entrypoint wraps internal package server
python3 msfconsole_mcp.py
```

## 🛠️ Tool Modules

- `msf/tools_ecosystem.py`:
  - Class: `MetasploitEcosystemTools`
  - Result: `EcosystemToolResult`
- `msf/tools_extended.py`:
  - Class: `ConsoleExtendedTools`
  - Result: `ExtendedToolResult`
- `msf/tools_final.py`:
  - Class: `ConsoleAdministrationTools`
  - Result: `AdministrationToolResult`
- `msf/tools_advanced.py`:
  - Class: `EcosystemAdvancedTools`
  - Result: `AdvancedToolResult`

Core wrapper: `msf/core.py` exports `MSFConsoleStableWrapper`, `OperationStatus`, `OperationResult`.

## 📊 Testing

Run the full test suite (pytest):
```bash
python3 -m pytest -q
```
Lint and format checks:
```bash
python3 -m ruff check .
python3 -m black --check .
```

## 🔧 Configuration

See `msf/server.py` and `pyproject.toml` for runtime and tooling configuration. Coverage is enforced via `pytest.ini` and `pyproject.toml`.

## 📚 Usage Examples

```python
# Example import of tools
from msf import (
  MSFConsoleStableWrapper,
  MetasploitEcosystemTools,
  ConsoleExtendedTools,
  ConsoleAdministrationTools,
  EcosystemAdvancedTools,
)
```

## 🏗️ Project Structure

- `msf/` package contains all runtime modules and tools
- Root contains thin entrypoints and developer tooling
- CI runs lint, format and tests with coverage

## 📄 License

MIT License (see `LICENSE`).