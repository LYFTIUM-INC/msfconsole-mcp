#!/usr/bin/env python3

import asyncio
import logging
import json
import sys
from typing import Optional

from msf_parser import MSFParser

try:
    from mcp.server.fastmcp import FastMCP, Context
except ImportError as e:
    sys.stderr.write(f"Error importing MCP SDK: {e}\n")
    sys.stderr.write("Please install the MCP SDK: pip install mcp\n")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
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
                host="127.0.0.1",
                port=55552,
                username="msf",
                password="msf123",
                ssl=False,
                timeout=30,
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


# ... rest of tool endpoints copied from enhanced server ...

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
