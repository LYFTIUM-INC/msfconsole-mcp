#!/usr/bin/env python3

"""
Enhanced Metasploit Framework Console MCP Server
------------------------------------------------
Comprehensive MCP integration with dual-mode operation, advanced security,
and full feature coverage of Metasploit Framework capabilities.
"""

import asyncio
import logging
import json
import sys
from typing import Optional

# Import parser at top for availability and import ordering
from msf_parser import MSFParser, OutputType

# Import MCP SDK
try:
    from mcp.server.fastmcp import FastMCP, Context
except ImportError as e:
    # Use stderr to avoid breaking MCP JSON protocol
    sys.stderr.write(f"Error importing MCP SDK: {e}\n")
    sys.stderr.write("Please install the MCP SDK: pip install mcp\n")
    sys.exit(1)

# Set up logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("msfconsole_mcp_enhanced.log"),
        logging.StreamHandler(sys.stderr),  # Use stderr to avoid stdout pollution
    ],
)
logger = logging.getLogger(__name__)

# Import our enhanced modules
try:
    from msf_rpc_manager import RPCConfig  # noqa: F401
    from msf_dual_mode import MSFDualModeHandler  # noqa: F401
    from msf_security import MSFSecurityManager
    from msf_config import get_config  # noqa: F401
    from msf_init import get_initializer
except ImportError as e:
    logger.error(f"Failed to import enhanced modules: {e}")
    sys.stderr.write(f"Import error: {e}\n")
    sys.stderr.write("Make sure all required files are present in the directory.\n")
    sys.exit(1)

# Initialize FastMCP server
VERSION = "2.0.0"
mcp = FastMCP("msfconsole-enhanced", version=VERSION)

# Enhanced timeout configuration for execute_msf_command
COMMAND_TIMEOUTS = {
    # Fast commands - basic status and help
    "help": 45,
    "db_status": 30,
    "workspace": 30,
    # Medium commands - information retrieval
    "version": 75,
    "show": 60,
    "info": 75,
    # Complex commands - operations and searches
    "search": 90,
    "use": 90,
    "exploit": 120,
    "generate": 90,
    # Default for unknown commands
    "default": 75,
}


def get_adaptive_timeout(command: str) -> int:
    """Get adaptive timeout based on command type"""
    command_lower = command.lower().strip()

    # Check for specific command patterns
    for pattern, timeout in COMMAND_TIMEOUTS.items():
        if pattern in command_lower:
            return timeout

    # Default timeout
    return COMMAND_TIMEOUTS["default"]


# Global dual-mode handler
dual_mode_handler: Optional[MSFDualModeHandler] = None

# Global security manager instance
security_manager: Optional[MSFSecurityManager] = None


async def ensure_initialized():
    """Ensure the dual-mode handler is initialized."""
    global dual_mode_handler, security_manager

    if dual_mode_handler is None:
        try:
            # Initialize Metasploit framework first
            logger.info("Initializing Metasploit framework...")
            _ = await asyncio.wait_for(get_initializer(), timeout=30)

            # Initialize security manager
            try:
                from msf_security import SecurityPolicy

                security_manager = MSFSecurityManager(SecurityPolicy())
            except ImportError:
                logger.warning("Security manager not available, using basic validation")
                security_manager = None

            # Configure RPC settings
            rpc_config = RPCConfig(
                host="127.0.0.1",
                port=55552,
                username="msf",
                password="msf123",
                ssl=False,
                timeout=30,
            )

            dual_mode_handler = MSFDualModeHandler(rpc_config)

            # Initialize with timeout
            init_result = await asyncio.wait_for(dual_mode_handler.initialize(), timeout=45)
            if not init_result:
                raise RuntimeError("Failed to initialize Metasploit dual-mode handler")

            logger.info("MSF Enhanced MCP Server initialized successfully")

        except asyncio.TimeoutError:
            logger.error("Initialization timed out")
            raise RuntimeError(
                "Metasploit initialization timed out - server may be slow or unavailable"
            )
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize Metasploit integration: {e}")


# MCP Tools


@mcp.tool()
async def get_msf_status(ctx: Context) -> str:
    await ctx.info("Getting MSF integration status")

    try:
        # Check if already initialized
        if dual_mode_handler is None:
            # Try basic initialization with timeout
            logger.info("Attempting basic status check without full initialization")
            return json.dumps(
                {
                    "status": "initializing",
                    "version": VERSION,
                    "message": "Metasploit handler not yet fully initialized",
                    "initialization_required": True,
                },
                indent=2,
            )

        # Get status from existing handler
        status = dual_mode_handler.get_status()

        return json.dumps(
            {"status": "operational", "version": VERSION, "integration_details": status}, indent=2
        )

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return json.dumps({"status": "error", "error": str(e), "version": VERSION}, indent=2)


@mcp.tool()
async def execute_msf_command(
    ctx: Context, command: str, workspace: str = "default", timeout: int = None
) -> str:
    # Use adaptive timeout if not specified
    if timeout is None:
        timeout = get_adaptive_timeout(command)

    await ctx.info(f"Executing MSF command: {command[:50]}... (timeout: {timeout}s)")

    try:
        # Security validation
        if security_manager:
            validation_result = await security_manager.validate_command(
                command, {"workspace": workspace}
            )
            if not validation_result["valid"]:
                return json.dumps(
                    {
                        "success": False,
                        "error": "Command blocked by security validation",
                        "command": command,
                        "security_details": validation_result,
                    },
                    indent=2,
                )
            command = validation_result["sanitized_command"]
        else:
            command = command.replace("\x00", "").replace("\r", "").strip()
            if len(command) > 1000:
                command = command[:1000]

        # Try initialization with timeout
        try:
            await asyncio.wait_for(ensure_initialized(), timeout=60)
        except asyncio.TimeoutError:
            return json.dumps(
                {
                    "success": False,
                    "error": "Metasploit initialization timeout",
                    "message": "The Metasploit framework is taking too long to initialize. Please try again later.",
                },
                indent=2,
            )

        # Execute command with context
        context = {"workspace": workspace, "timeout": timeout}

        result = await dual_mode_handler.execute_command(command, context)

        await ctx.info(f"Command executed successfully using {result.mode_used} mode")

        # Use improved parser for better output structure
        parsed_result = msf_parser.parse(result.output)

        response_data = {
            "success": result.success,
            "command": command,
            "execution_details": {
                "mode_used": result.mode_used,
                "execution_time": result.execution_time,
                "workspace": workspace,
            },
            "metadata": result.metadata or {},
        }

        # Add parsed or raw output based on parsing success
        if parsed_result.success and parsed_result.output_type != OutputType.RAW:
            response_data["parsed_output"] = {
                "type": parsed_result.output_type.value,
                "data": parsed_result.data,
                "metadata": parsed_result.metadata,
            }
            response_data["raw_output"] = result.output
        else:
            response_data["output"] = result.output
            if parsed_result.error_message:
                response_data["parsing_info"] = {
                    "attempted": True,
                    "error": parsed_result.error_message,
                }

        if result.error:
            response_data["error"] = result.error

        return json.dumps(response_data, indent=2)

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        await ctx.error(f"Command execution failed: {e}")
        return json.dumps({"success": False, "error": str(e), "command": command}, indent=2)


# Other tool endpoints omitted for brevity (search_modules, manage_workspaces, database_operations, session_management, module_operations, payload_generation, resource_script_execution).

# Initialize global parser
msf_parser = MSFParser()

if __name__ == "__main__":
    logger.info(f"Enhanced Metasploit MCP Server v{VERSION} starting...")
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
