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
import os
import sys
from typing import Optional

from msf_parser import MSFParser, OutputType

try:
    from mcp.server.fastmcp import FastMCP, Context
except ImportError as e:
    sys.stderr.write(f"Error importing MCP SDK: {e}\n")
    sys.stderr.write("Please install the MCP SDK: pip install mcp\n")
    sys.exit(1)

from .security_utils import is_command_allowed
from .policy import is_denied, RateLimiter

# Logging configuration via env
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "plain")  # plain|json

if LOG_FORMAT == "json":

    class JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage(),
            }
            return json.dumps(payload)

    formatter = JSONFormatter()
    handlers = [logging.StreamHandler(sys.stderr)]
    for h in handlers:
        h.setFormatter(formatter)
    logging.basicConfig(level=LOG_LEVEL, handlers=handlers)
else:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("msfconsole_mcp_enhanced.log"),
            logging.StreamHandler(sys.stderr),
        ],
    )
logger = logging.getLogger(__name__)

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

VERSION = "2.0.0"
mcp = FastMCP("msfconsole-enhanced", version=VERSION)
PREFER_RPC = os.getenv("PREFER_RPC", "false").lower() == "true"

COMMAND_TIMEOUTS = {
    "help": 45,
    "db_status": 30,
    "workspace": 30,
    "version": 75,
    "show": 60,
    "info": 75,
    "search": 90,
    "use": 90,
    "exploit": 120,
    "generate": 90,
    "default": 75,
}


def get_adaptive_timeout(command: str) -> int:
    command_lower = command.lower().strip()
    for pattern, timeout in COMMAND_TIMEOUTS.items():
        if pattern in command_lower:
            return timeout
    return COMMAND_TIMEOUTS["default"]


dual_mode_handler: Optional[MSFDualModeHandler] = None
security_manager: Optional[MSFSecurityManager] = None
rate_limiter = RateLimiter(
    max_calls=int(os.getenv("MCP_RATE_MAX", "30")),
    window_secs=int(os.getenv("MCP_RATE_WINDOW", "60")),
)


async def ensure_initialized():
    global dual_mode_handler, security_manager
    if dual_mode_handler is None:
        try:
            logger.info("Initializing Metasploit framework...")
            _ = await asyncio.wait_for(get_initializer(), timeout=30)
            try:
                from msf_security import SecurityPolicy

                security_manager = MSFSecurityManager(SecurityPolicy())
            except ImportError:
                logger.warning("Security manager not available, using basic validation")
                security_manager = None
            rpc_config = RPCConfig(
                host=os.getenv("MSF_RPC_HOST", "127.0.0.1"),
                port=int(os.getenv("MSF_RPC_PORT", "55552")),
                username=os.getenv("MSF_RPC_USER", "msf"),
                password=os.getenv("MSF_RPC_PASS", "msf123"),
                ssl=os.getenv("MSF_RPC_SSL", "false").lower() == "true",
                timeout=int(os.getenv("MSF_RPC_TIMEOUT", "30")),
            )
            dual_mode_handler = MSFDualModeHandler(rpc_config)
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


@mcp.tool()
async def get_msf_status(ctx: Context) -> str:
    await ctx.info("Getting MSF integration status")
    try:
        if dual_mode_handler is None:
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
        status = dual_mode_handler.get_status()
        return json.dumps(
            {
                "status": "operational",
                "version": VERSION,
                "integration_details": status,
            },
            indent=2,
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return json.dumps({"status": "error", "error": str(e), "version": VERSION}, indent=2)


@mcp.tool()
async def get_rpc_status(
    ctx: Context,
    host: str = None,
    port: int = None,
    ssl: bool = True,
    username: str = "msf",
    password: str = None,
) -> str:
    await ctx.info("Checking MSF RPC connectivity")
    try:
        from .rpc_client import MSFRPCClient

        client = MSFRPCClient(
            host=host or os.getenv("MSF_RPC_HOST", "127.0.0.1"),
            port=port or int(os.getenv("MSF_RPC_PORT", "55553")),
            ssl=ssl,
            username=username,
            password=password or os.getenv("MSF_RPC_PASS"),
        )
        ok_connect = await client.connect()
        ok_auth = await client.authenticate() if ok_connect else False
        return json.dumps({"connected": ok_connect, "authenticated": ok_auth}, indent=2)
    except Exception as e:
        logger.error(f"RPC status error: {e}")
        return json.dumps({"connected": False, "error": str(e)}, indent=2)


@mcp.tool()
async def execute_msf_command(
    ctx: Context, command: str, workspace: str = "default", timeout: int = None
) -> str:
    if timeout is None:
        timeout = get_adaptive_timeout(command)
    await ctx.info(f"Executing MSF command: {command[:50]}... (timeout: {timeout}s)")
    try:
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
            # Fallback policy allowlist when no security manager is present
            if not is_command_allowed(command):
                return json.dumps(
                    {
                        "success": False,
                        "error": "Command not allowed by fallback policy",
                        "command": command,
                    },
                    indent=2,
                )
            if is_denied(command):
                return json.dumps(
                    {
                        "success": False,
                        "error": "Command denied by policy",
                        "command": command,
                    },
                    indent=2,
                )
            if not rate_limiter.allow():
                return json.dumps(
                    {
                        "success": False,
                        "error": "Rate limit exceeded",
                        "command": command,
                    },
                    indent=2,
                )
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
        context = {"workspace": workspace, "timeout": timeout}
        if PREFER_RPC:
            logger.info(
                "PREFER_RPC is enabled, but RPC execution path not wired; falling back to console."
            )
        result = await dual_mode_handler.execute_command(command, context)
        await ctx.info(f"Command executed successfully using {result.mode_used} mode")
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


msf_parser = MSFParser()


def main() -> None:
    logger.info(f"Enhanced Metasploit MCP Server v{VERSION} starting...")
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
