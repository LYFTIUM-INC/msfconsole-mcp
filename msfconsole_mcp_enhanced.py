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
from typing import Dict, Optional, List
from dataclasses import asdict

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("msfconsole_mcp_enhanced.log"),
        logging.StreamHandler(sys.stderr)  # Use stderr to avoid stdout pollution
    ]
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
    "default": 75
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
                timeout=30
            )
            
            dual_mode_handler = MSFDualModeHandler(rpc_config)
            
            # Initialize with timeout
            init_result = await asyncio.wait_for(dual_mode_handler.initialize(), timeout=45)
            if not init_result:
                raise RuntimeError("Failed to initialize Metasploit dual-mode handler")
            
            logger.info("MSF Enhanced MCP Server initialized successfully")
            
        except asyncio.TimeoutError:
            logger.error("Initialization timed out")
            raise RuntimeError("Metasploit initialization timed out - server may be slow or unavailable")
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize Metasploit integration: {e}")

# MCP Tools

@mcp.tool()
async def get_msf_status(ctx: Context) -> str:
    """
    Get comprehensive status of the Metasploit integration.
    
    Returns:
        Detailed status information including RPC connection, available modes, etc.
    """
    await ctx.info("Getting MSF integration status")
    
    try:
        # Check if already initialized
        if dual_mode_handler is None:
            # Try basic initialization with timeout
            logger.info("Attempting basic status check without full initialization")
            return json.dumps({
                "status": "initializing",
                "version": VERSION,
                "message": "Metasploit handler not yet fully initialized",
                "initialization_required": True
            }, indent=2)
        
        # Get status from existing handler
        status = dual_mode_handler.get_status()
        
        return json.dumps({
            "status": "operational",
            "version": VERSION,
            "integration_details": status
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return json.dumps({
            "status": "error",
            "error": str(e),
            "version": VERSION
        }, indent=2)

@mcp.tool()
async def execute_msf_command(ctx: Context, command: str, workspace: str = "default", timeout: int = None) -> str:
    """
    Execute a Metasploit Framework command with enhanced security and adaptive timeout.
    
    Args:
        command: The MSF command to execute (e.g., 'hosts', 'search ms17_010')
        workspace: Metasploit workspace to use (default: 'default')
        timeout: Command timeout in seconds (auto-detected based on command type if None)
    
    Returns:
        JSON formatted result with output, execution details, and metadata
    """
    # Use adaptive timeout if not specified
    if timeout is None:
        timeout = get_adaptive_timeout(command)
    
    await ctx.info(f"Executing MSF command: {command[:50]}... (timeout: {timeout}s)")
    
    try:
        # Security validation
        if security_manager:
            validation_result = await security_manager.validate_command(command, {"workspace": workspace})
            if not validation_result["valid"]:
                return json.dumps({
                    "success": False,
                    "error": "Command blocked by security validation",
                    "command": command,
                    "security_details": validation_result
                }, indent=2)
            command = validation_result["sanitized_command"]
        else:
            # Basic validation fallback
            command = command.replace('\x00', '').replace('\r', '').strip()
            if len(command) > 1000:
                command = command[:1000]
        
        # Try initialization with timeout
        try:
            await asyncio.wait_for(ensure_initialized(), timeout=60)
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": "Metasploit initialization timeout",
                "message": "The Metasploit framework is taking too long to initialize. Please try again later."
            }, indent=2)
        
        # Execute command with context
        context = {
            "workspace": workspace,
            "timeout": timeout
        }
        
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
                "workspace": workspace
            },
            "metadata": result.metadata or {}
        }
        
        # Add parsed or raw output based on parsing success
        if parsed_result.success and parsed_result.output_type != OutputType.RAW:
            response_data["parsed_output"] = {
                "type": parsed_result.output_type.value,
                "data": parsed_result.data,
                "metadata": parsed_result.metadata
            }
            # Keep raw output for reference when parsed successfully
            response_data["raw_output"] = result.output
        else:
            # Use raw output when parsing fails
            response_data["output"] = result.output
            if parsed_result.error_message:
                response_data["parsing_info"] = {
                    "attempted": True,
                    "error": parsed_result.error_message
                }
        
        if result.error:
            response_data["error"] = result.error
        
        return json.dumps(response_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        await ctx.error(f"Command execution failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "command": command
        }, indent=2)

@mcp.tool()
async def search_modules(ctx: Context, query: str, module_type: str = "all") -> str:
    """
    Search for Metasploit modules with advanced filtering.
    
    Args:
        query: Search query (e.g., 'ms17_010', 'type:exploit platform:windows')
        module_type: Filter by module type (exploit, auxiliary, payload, encoder, nop, post, all)
    
    Returns:
        JSON formatted search results with module details
    """
    await ctx.info(f"Searching modules: {query}")
    
    try:
        # Try initialization with timeout
        try:
            await asyncio.wait_for(ensure_initialized(), timeout=60)
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": "Metasploit initialization timeout",
                "message": "The Metasploit framework is taking too long to initialize. Please try again later."
            }, indent=2)
        
        # Build search command
        search_cmd = f"search {query}"
        if module_type != "all":
            search_cmd += f" type:{module_type}"
        
        result = await dual_mode_handler.execute_command(search_cmd)
        
        # Use improved parser for better formatting
        parsed_result = msf_parser.parse(result.output)
        
        if parsed_result.success and parsed_result.output_type == OutputType.TABLE:
            return json.dumps({
                "success": True,
                "query": query,
                "module_type": module_type,
                "results_count": len(parsed_result.data),
                "modules": parsed_result.data,
                "parsing_metadata": parsed_result.metadata
            }, indent=2)
        else:
            # Fallback to adapter-based parsing or raw output
            from msf.parsing import parse_search_results
            parsed_modules = parse_search_results(result.output)
            return json.dumps({
                "success": result.success,
                "query": query,
                "module_type": module_type,
                "results_count": len(parsed_modules),
                "modules": parsed_modules,
                "raw_output": result.output,
                "parsing_error": parsed_result.error_message
            }, indent=2)
        
    except Exception as e:
        logger.error(f"Error searching modules: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "query": query
        }, indent=2)

@mcp.tool()
async def manage_workspaces(ctx: Context, action: str, workspace_name: str = "") -> str:
    """
    Manage Metasploit workspaces with full lifecycle support.
    
    Args:
        action: Action to perform (list, create, delete, switch, rename)
        workspace_name: Name of workspace for create/delete/switch/rename actions
    
    Returns:
        JSON formatted workspace operation results
    """
    await ctx.info(f"Managing workspace: {action}")
    
    try:
        # Try initialization with timeout
        try:
            await asyncio.wait_for(ensure_initialized(), timeout=60)
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": "Metasploit initialization timeout",
                "message": "The Metasploit framework is taking too long to initialize. Please try again later."
            }, indent=2)
        
        # Build workspace command
        if action == "list":
            command = "workspace"
        elif action == "create" and workspace_name:
            command = f"workspace -a {workspace_name}"
        elif action == "delete" and workspace_name:
            command = f"workspace -d {workspace_name}"
        elif action == "switch" and workspace_name:
            command = f"workspace {workspace_name}"
        elif action == "rename" and workspace_name:
            # This requires current workspace name as well
            command = f"workspace -r {workspace_name}"
        else:
            return json.dumps({
                "success": False,
                "error": "Invalid action or missing workspace name",
                "valid_actions": ["list", "create", "delete", "switch", "rename"]
            }, indent=2)
        
        result = await dual_mode_handler.execute_command(command)
        
        # Parse workspace list if listing
        workspaces = []
        if action == "list" and result.success:
            from msf.parsing import parse_workspace_list
            workspaces = parse_workspace_list(result.output)
        
        return json.dumps({
            "success": result.success,
            "action": action,
            "workspace_name": workspace_name,
            "workspaces": workspaces,
            "output": result.output,
            "error": result.error
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error managing workspace: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "action": action
        }, indent=2)

@mcp.tool()
async def database_operations(ctx: Context, operation: str, filters: str = "") -> str:
    """
    Perform database operations with advanced querying capabilities.
    
    Args:
        operation: Database operation (hosts, services, vulns, creds, loot, notes, sessions)
        filters: Optional filters for the query (e.g., 'address:192.168.1.0/24')
    
    Returns:
        JSON formatted database results with parsed data
    """
    await ctx.info(f"Database operation: {operation}")
    
    try:
        # Try initialization with timeout
        try:
            await asyncio.wait_for(ensure_initialized(), timeout=60)
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": "Metasploit initialization timeout",
                "message": "The Metasploit framework is taking too long to initialize. Please try again later."
            }, indent=2)
        
        # Build database command
        valid_operations = ["hosts", "services", "vulns", "creds", "loot", "notes", "sessions"]
        if operation not in valid_operations:
            return json.dumps({
                "success": False,
                "error": f"Invalid operation: {operation}",
                "valid_operations": valid_operations
            }, indent=2)
        
        command = operation
        if filters:
            command += f" {filters}"
        
        result = await dual_mode_handler.execute_command(command)
        
        # Parse results based on operation type
        parsed_data = []
        if result.success:
            from msf.parsing import parse_hosts, parse_services, parse_vulns, parse_sessions
            if operation == "hosts":
                parsed_data = parse_hosts(result.output)
            elif operation == "services":
                parsed_data = parse_services(result.output)
            elif operation == "vulns":
                parsed_data = parse_vulns(result.output)
            elif operation == "sessions":
                parsed_data = parse_sessions(result.output)
        
        return json.dumps({
            "success": result.success,
            "operation": operation,
            "filters": filters,
            "count": len(parsed_data),
            "data": parsed_data,
            "raw_output": result.output,
            "error": result.error
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error in database operation: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "operation": operation
        }, indent=2)

@mcp.tool()
async def session_management(ctx: Context, action: str, session_id: str = "", command: str = "") -> str:
    """
    Advanced session management with interactive capabilities.
    
    Args:
        action: Action to perform (list, interact, execute, kill, upgrade)
        session_id: Session ID for interact/execute/kill/upgrade actions
        command: Command to execute in session (for execute action)
    
    Returns:
        JSON formatted session management results
    """
    await ctx.info(f"Session management: {action}")
    
    try:
        # Try initialization with timeout
        try:
            await asyncio.wait_for(ensure_initialized(), timeout=60)
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": "Metasploit initialization timeout",
                "message": "The Metasploit framework is taking too long to initialize. Please try again later."
            }, indent=2)
        
        # Build session command
        if action == "list":
            command_str = "sessions -l"
        elif action == "interact" and session_id:
            command_str = f"sessions -i {session_id}"
        elif action == "execute" and session_id and command:
            # Validate command for session execution
            if security_manager:
                command = security_manager._sanitize_command(command)
                validation_result = await security_manager.validate_command(command)
                if not validation_result.get("allowed", True):
                    return json.dumps({
                        "success": False,
                        "error": f"Command blocked by security validation: {validation_result.get('reason', 'Unknown')}"
                    }, indent=2)
            command_str = f"sessions -c '{command}' {session_id}"
        elif action == "kill" and session_id:
            command_str = f"sessions -k {session_id}"
        elif action == "upgrade" and session_id:
            command_str = f"sessions -u {session_id}"
        else:
            return json.dumps({
                "success": False,
                "error": "Invalid action or missing required parameters",
                "valid_actions": ["list", "interact", "execute", "kill", "upgrade"]
            }, indent=2)
        
        result = await dual_mode_handler.execute_command(command_str)
        
        # Parse session list if listing
        sessions = []
        if action == "list" and result.success:
            from msf.parsing import parse_sessions
            sessions = parse_sessions(result.output)
        
        return json.dumps({
            "success": result.success,
            "action": action,
            "session_id": session_id,
            "sessions": sessions,
            "output": result.output,
            "error": result.error
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error in session management: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "action": action
        }, indent=2)

@mcp.tool()
async def module_operations(ctx: Context, action: str, module_path: str = "", options: Dict[str, str] = None) -> str:
    """
    Advanced module operations with configuration and execution.
    
    Args:
        action: Action to perform (info, use, options, set, execute, search_payloads)
        module_path: Path to the module (e.g., 'exploit/windows/smb/ms17_010_eternalblue')
        options: Dictionary of module options to set
    
    Returns:
        JSON formatted module operation results
    """
    await ctx.info(f"Module operation: {action}")
    
    try:
        # Try initialization with timeout
        try:
            await asyncio.wait_for(ensure_initialized(), timeout=60)
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": "Metasploit initialization timeout",
                "action": action,
                "message": "The Metasploit framework is taking too long to initialize. Please try again later."
            }, indent=2)
        
        options = options or {}
        
        if action == "info" and module_path:
            # Use direct info command which is more reliable
            command = f"info {module_path}"
        elif action == "use" and module_path:
            command = f"use {module_path}"
        elif action == "options" and module_path:
            # Show options for a specific module
            command = f"use {module_path}; show options"
        elif action == "set" and module_path and options:
            commands = [f"use {module_path}"]
            for key, value in options.items():
                commands.append(f"set {key} {value}")
            commands.append("options")  # Show final options
            result = await dual_mode_handler.execute_batch_commands(commands)
            
            return json.dumps({
                "success": all(r.success for r in result),
                "action": action,
                "module_path": module_path,
                "options_set": options,
                "results": [asdict(r) for r in result]
            }, indent=2)
            
        elif action == "execute" and module_path:
            commands = [f"use {module_path}"]
            for key, value in options.items():
                commands.append(f"set {key} {value}")
            commands.append("exploit")
            
            result = await dual_mode_handler.execute_batch_commands(commands)
            
            return json.dumps({
                "success": all(r.success for r in result),
                "action": action,
                "module_path": module_path,
                "options_used": options,
                "results": [asdict(r) for r in result]
            }, indent=2)
            
        elif action == "search_payloads" and module_path:
            command = f"use {module_path}; show payloads"
        else:
            return json.dumps({
                "success": False,
                "error": "Invalid action or missing required parameters",
                "valid_actions": ["info", "use", "options", "set", "execute", "search_payloads"]
            }, indent=2)
        
        result = await dual_mode_handler.execute_command(command)
        
        return json.dumps({
            "success": result.success,
            "action": action,
            "module_path": module_path,
            "output": result.output,
            "error": result.error,
            "execution_details": {
                "mode_used": result.mode_used,
                "execution_time": result.execution_time
            }
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error in module operation: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "action": action
        }, indent=2)

@mcp.tool()
async def payload_generation(ctx: Context, payload_type: str, options: Dict[str, str] = None, output_format: str = "raw") -> str:
    """
    Generate payloads using msfvenom with comprehensive options support.
    
    Args:
        payload_type: Type of payload (e.g., 'windows/meterpreter/reverse_tcp')
        options: Dictionary of payload options (LHOST, LPORT, etc.)
        output_format: Output format (raw, exe, elf, macho, etc.)
    
    Returns:
        JSON formatted payload generation results
    """
    await ctx.info(f"Generating payload: {payload_type}")
    
    try:
        # Try initialization with timeout
        try:
            await asyncio.wait_for(ensure_initialized(), timeout=60)
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": "Metasploit initialization timeout",
                "payload_type": payload_type,
                "message": "The Metasploit framework is taking too long to initialize. Please try again later."
            }, indent=2)
        
        options = options or {}
        
        # Try different approaches for payload generation
        approaches = [
            # Approach 1: Use generate command in msfconsole (if available)
            {
                "method": "generate_command",
                "command": f"use payload/{payload_type}",
                "description": "Using MSF console generate command"
            },
            # Approach 2: Use external msfvenom via subprocess  
            {
                "method": "external_msfvenom",
                "command": None,  # Will be handled separately
                "description": "Using external msfvenom command"
            }
        ]
        
        result = None
        final_approach = None
        
        # Try approach 1: MSF console generate command
        try:
            # Set up payload module
            setup_commands = [
                f"use payload/{payload_type}"
            ]
            
            # Set payload options
            for key, value in options.items():
                setup_commands.append(f"set {key} {value}")
            
            # Generate payload
            setup_commands.append("generate")
            
            # Execute as batch
            batch_result = await dual_mode_handler.execute_batch_commands(setup_commands)
            
            if batch_result and any(r.success for r in batch_result):
                # Find the generate result
                generate_result = None
                for r in batch_result:
                    if "generate" in r.output.lower() or len(r.output) > 100:  # Payload output is usually long
                        generate_result = r
                        break
                
                if generate_result:
                    result = generate_result
                    final_approach = approaches[0]
                    
        except Exception as e:
            logger.warning(f"MSF console generate failed: {e}")
        
        # Try approach 2: External msfvenom if console approach failed
        if not result:
            try:
                import subprocess
                
                # Build msfvenom command for external execution
                command_parts = ["msfvenom", "-p", payload_type]
                
                # Add options
                for key, value in options.items():
                    command_parts.append(f"{key}={value}")
                
                # Add output format
                if output_format != "raw":
                    command_parts.extend(["-f", output_format])
                
                # Execute msfvenom externally
                _ = " ".join(command_parts)  # command string for logging if needed
                proc_result = subprocess.run(
                    command_parts,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # Create result-like object
                class ExternalResult:
                    def __init__(self, success, output, error):
                        self.success = success
                        self.output = output
                        self.error = error
                        self.execution_time = 0
                        self.mode_used = "external_subprocess"
                
                result = ExternalResult(
                    success=proc_result.returncode == 0,
                    output=proc_result.stdout,
                    error=proc_result.stderr
                )
                final_approach = approaches[1]
                
            except Exception as e:
                logger.error(f"External msfvenom failed: {e}")
                return json.dumps({
                    "success": False,
                    "error": f"All payload generation methods failed. Console error: MSF generate not available. External error: {str(e)}",
                    "payload_type": payload_type,
                    "approaches_tried": [a["description"] for a in approaches]
                }, indent=2)
        
        return json.dumps({
            "success": result.success if result else False,
            "payload_type": payload_type,
            "options": options,
            "output_format": output_format,
            "method_used": final_approach["description"] if final_approach else "Unknown",
            "output": result.output if result else "",
            "error": result.error if result else "No successful generation method",
            "execution_time": getattr(result, 'execution_time', 0) if result else 0
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating payload: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "payload_type": payload_type
        }, indent=2)

@mcp.tool()
async def resource_script_execution(ctx: Context, script_commands: List[str], workspace: str = "default") -> str:
    """
    Execute a series of commands as a resource script for automation.
    
    Args:
        script_commands: List of MSF commands to execute in sequence
        workspace: Workspace to execute in
    
    Returns:
        JSON formatted batch execution results
    """
    await ctx.info(f"Executing resource script with {len(script_commands)} commands")
    
    try:
        # Try initialization with timeout
        try:
            await asyncio.wait_for(ensure_initialized(), timeout=60)
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": "Metasploit initialization timeout",
                "message": "The Metasploit framework is taking too long to initialize. Please try again later."
            }, indent=2)
        
        # Validate all commands
        validated_commands = []
        for cmd in script_commands:
            if security_manager:
                sanitized = security_manager._sanitize_command(cmd)
                validation_result = await security_manager.validate_command(sanitized)
                if validation_result.get("allowed", True):
                    validated_commands.append(sanitized)
                else:
                    return json.dumps({
                        "success": False,
                        "error": f"Command blocked by security validation: {cmd}",
                        "reason": validation_result.get("reason", "Unknown"),
                        "validated_commands": validated_commands
                    }, indent=2)
            else:
                # Basic sanitization if security manager not available
                sanitized = cmd.strip()
                validated_commands.append(sanitized)
        
        # Execute as batch
        context = {"workspace": workspace, "batch_mode": True}
        results = await dual_mode_handler.execute_batch_commands(validated_commands, context)
        
        return json.dumps({
            "success": all(r.success for r in results),
            "commands_executed": len(validated_commands),
            "workspace": workspace,
            "results": [asdict(r) for r in results],
            "total_execution_time": sum(r.execution_time for r in results)
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error executing resource script: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "commands": script_commands
        }, indent=2)

# Initialize global parser
msf_parser = MSFParser()

# Legacy parsing helper functions have been centralized in msf.parsing to reduce duplication.

# Startup and cleanup handlers will be handled in main()

if __name__ == "__main__":
    logger.info(f"Enhanced Metasploit MCP Server v{VERSION} starting...")
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)