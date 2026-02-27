"""
MSF Enhanced Tools v5.0 - Plugin System and Core Commands
Provides enhanced plugin management and missing core commands
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from msf_stable_integration import MSFConsoleStableWrapper, OperationResult, OperationStatus
from msf_extended_tools import ExtendedOperationResult
from msf_plugin_system import PluginManager, PluginCategory

logger = logging.getLogger(__name__)


class MSFEnhancedTools(MSFConsoleStableWrapper):
    """Enhanced tools for MSF Console MCP v5.0"""
    
    def __init__(self):
        super().__init__()
        self.plugin_manager: Optional[PluginManager] = None
        self._console_log_file = None
        self._console_log_enabled = False
        self._grep_context = {"before": 0, "after": 0}
        self._saved_configs = {}
        self._route_manager = {"routes": {}, "auto_route": True}
        
    async def initialize_enhanced_features(self) -> OperationResult:
        """Initialize enhanced features including plugin system"""
        start_time = time.time()
        try:
            # Initialize plugin manager
            self.plugin_manager = PluginManager(self)
            plugin_dirs = [
                Path(__file__).parent / "plugins",
                Path.home() / ".msf_plugins"  # User plugins directory
            ]
            
            result = await self.plugin_manager.initialize(plugin_dirs)
            
            if result.status == OperationStatus.SUCCESS:
                logger.info(f"Enhanced features initialized: {result.data}")
                return OperationResult(
                    OperationStatus.SUCCESS,
                    result.data,
                    time.time() - start_time
                )
            else:
                return OperationResult(
                    OperationStatus.FAILURE,
                    None,
                    time.time() - start_time,
                    "Plugin initialization failed"
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize enhanced features: {e}")
            return OperationResult(
                OperationStatus.FAILURE,
                None,
                time.time() - start_time,
                str(e)
            )
    
    # ==================== PLUGIN MANAGEMENT ====================
    
    async def msf_enhanced_plugin_manager(
        self,
        action: str,
        plugin_name: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        **kwargs
    ) -> ExtendedOperationResult:
        """Enhanced plugin manager with 20+ core plugins"""
        try:
            if not self.plugin_manager:
                await self.initialize_enhanced_features()
                
            if action == "list":
                # List plugins
                cat = PluginCategory(category) if category else None
                plugins = self.plugin_manager.list_plugins(category=cat, loaded_only=False)
                
                return ExtendedOperationResult(
                    success=True,
                    data={"plugins": plugins},
                    metadata={"action": "list_plugins", "count": len(plugins)},
                    extended_data={"categories": [c.value for c in PluginCategory]}
                )
                
            elif action == "load":
                # Load a plugin
                if not plugin_name:
                    return ExtendedOperationResult(
                        success=False,
                        data=None,
                        error="Plugin name required for load action"
                    )
                    
                result = await self.plugin_manager.load_plugin(plugin_name)
                return ExtendedOperationResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    metadata=result.metadata,
                    extended_data={"plugin_info": self.plugin_manager.get_plugin_info(plugin_name)}
                )
                
            elif action == "unload":
                # Unload a plugin
                if not plugin_name:
                    return ExtendedOperationResult(
                        success=False,
                        data=None,
                        error="Plugin name required for unload action"
                    )
                    
                result = await self.plugin_manager.unload_plugin(plugin_name)
                return ExtendedOperationResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    metadata=result.metadata
                )
                
            elif action == "reload":
                # Reload a plugin
                if not plugin_name:
                    return ExtendedOperationResult(
                        success=False,
                        data=None,
                        error="Plugin name required for reload action"
                    )
                    
                result = await self.plugin_manager.reload_plugin(plugin_name)
                return ExtendedOperationResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    metadata=result.metadata
                )
                
            elif action == "execute":
                # Execute plugin command
                if not plugin_name or not command:
                    return ExtendedOperationResult(
                        success=False,
                        data=None,
                        error="Plugin name and command required for execute action"
                    )
                    
                result = await self.plugin_manager.execute_command(plugin_name, command, args or {})
                return ExtendedOperationResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    metadata=result.metadata
                )
                
            elif action == "info":
                # Get plugin information
                if not plugin_name:
                    return ExtendedOperationResult(
                        success=False,
                        data=None,
                        error="Plugin name required for info action"
                    )
                    
                info = self.plugin_manager.get_plugin_info(plugin_name)
                if info:
                    return ExtendedOperationResult(
                        success=True,
                        data=info,
                        metadata={"action": "plugin_info"}
                    )
                else:
                    return ExtendedOperationResult(
                        success=False,
                        data=None,
                        error=f"Plugin not found: {plugin_name}"
                    )
                    
            else:
                return ExtendedOperationResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Plugin manager error: {e}")
            return ExtendedOperationResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"action": action}
            )
    
    # ==================== CORE COMMANDS ====================
    
    async def msf_connect(
        self,
        host: str,
        port: int = 0,
        ssl: bool = False,
        proxies: Optional[str] = None,
        timeout: int = 30,
        **kwargs
    ) -> ExtendedOperationResult:
        """Network connection utility (connect command)"""
        try:
            # Build connect command
            cmd_parts = ["connect", host]
            
            if port:
                cmd_parts.append(str(port))
                
            if ssl:
                cmd_parts.append("-s")
                
            if proxies:
                cmd_parts.extend(["-p", proxies])
                
            if timeout != 30:
                cmd_parts.extend(["-w", str(timeout)])
                
            # Execute connect command
            result = await self.execute_command(" ".join(cmd_parts))
            
            return ExtendedOperationResult(
                success=result.success,
                data={
                    "host": host,
                    "port": port,
                    "connected": "Connected" in result.output
                },
                output=result.output,
                metadata={"command": "connect", "timeout": timeout}
            )
            
        except Exception as e:
            logger.error(f"Connect error: {e}")
            return ExtendedOperationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def msf_interactive_ruby(
        self,
        command: Optional[str] = None,
        script: Optional[str] = None,
        **kwargs
    ) -> ExtendedOperationResult:
        """Interactive Ruby shell integration (irb command)"""
        try:
            if script:
                # Execute Ruby script
                with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
                    f.write(script)
                    script_path = f.name
                    
                result = await self.execute_command(f"irb -f {script_path}")
                os.unlink(script_path)
                
            elif command:
                # Execute single Ruby command
                result = await self.execute_command(f"irb -e '{command}'")
                
            else:
                # Interactive mode notice
                return ExtendedOperationResult(
                    success=True,
                    data={
                        "mode": "interactive",
                        "note": "Use 'irb' command in MSF console for interactive Ruby shell"
                    },
                    metadata={"command": "irb"}
                )
                
            return ExtendedOperationResult(
                success=result.success,
                data={"output": result.output},
                output=result.output,
                metadata={"command": "irb", "type": "script" if script else "command"}
            )
            
        except Exception as e:
            logger.error(f"IRB error: {e}")
            return ExtendedOperationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def msf_route_manager(
        self,
        action: str,
        subnet: Optional[str] = None,
        session_id: Optional[str] = None,
        netmask: Optional[str] = None,
        **kwargs
    ) -> ExtendedOperationResult:
        """Advanced network routing management (route command)"""
        try:
            if action == "add":
                # Add route
                if not subnet or not session_id:
                    return ExtendedOperationResult(
                        success=False,
                        data=None,
                        error="Subnet and session_id required for add action"
                    )
                    
                cmd = f"route add {subnet}"
                if netmask:
                    cmd += f" {netmask}"
                cmd += f" {session_id}"
                
                result = await self.execute_command(cmd)
                
                # Track route
                route_key = f"{subnet}/{netmask or '255.255.255.0'}"
                self._route_manager["routes"][route_key] = {
                    "session_id": session_id,
                    "added": datetime.now().isoformat()
                }
                
                return ExtendedOperationResult(
                    success="Route added" in result.output,
                    data={
                        "action": "add",
                        "subnet": subnet,
                        "session_id": session_id,
                        "route": route_key
                    },
                    output=result.output,
                    metadata={"command": "route"}
                )
                
            elif action == "remove":
                # Remove route
                if not subnet or not session_id:
                    return ExtendedOperationResult(
                        success=False,
                        data=None,
                        error="Subnet and session_id required for remove action"
                    )
                    
                cmd = f"route remove {subnet}"
                if netmask:
                    cmd += f" {netmask}"
                cmd += f" {session_id}"
                
                result = await self.execute_command(cmd)
                
                # Remove from tracking
                route_key = f"{subnet}/{netmask or '255.255.255.0'}"
                self._route_manager["routes"].pop(route_key, None)
                
                return ExtendedOperationResult(
                    success="Route removed" in result.output or result.success,
                    data={
                        "action": "remove",
                        "subnet": subnet,
                        "session_id": session_id
                    },
                    output=result.output,
                    metadata={"command": "route"}
                )
                
            elif action == "list":
                # List routes
                result = await self.execute_command("route")
                
                # Parse routes from output
                routes = self._parse_routes(result.output)
                
                return ExtendedOperationResult(
                    success=True,
                    data={"routes": routes, "tracked_routes": self._route_manager["routes"]},
                    output=result.output,
                    metadata={"command": "route", "count": len(routes)}
                )
                
            elif action == "flush":
                # Flush all routes
                result = await self.execute_command("route flush")
                self._route_manager["routes"].clear()
                
                return ExtendedOperationResult(
                    success=True,
                    data={"action": "flush", "flushed": True},
                    output=result.output,
                    metadata={"command": "route"}
                )
                
            else:
                return ExtendedOperationResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Route manager error: {e}")
            return ExtendedOperationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def msf_output_filter(
        self,
        pattern: str,
        command: str,
        before: int = 0,
        after: int = 0,
        invert: bool = False,
        case_sensitive: bool = True,
        **kwargs
    ) -> ExtendedOperationResult:
        """Output filtering functionality (grep command)"""
        try:
            # Execute command and capture output
            result = await self.execute_command(command)
            
            if not result.success:
                return ExtendedOperationResult(
                    success=False,
                    data=None,
                    error=f"Command failed: {command}",
                    output=result.output
                )
                
            # Filter output
            lines = result.output.split('\n')
            filtered_lines = []
            
            import re
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
            
            for i, line in enumerate(lines):
                match = regex.search(line)
                
                if (match and not invert) or (not match and invert):
                    # Add context lines
                    start = max(0, i - before)
                    end = min(len(lines), i + after + 1)
                    
                    for j in range(start, end):
                        if lines[j] not in filtered_lines:
                            filtered_lines.append(lines[j])
                            
            filtered_output = '\n'.join(filtered_lines)
            
            return ExtendedOperationResult(
                success=True,
                data={
                    "pattern": pattern,
                    "matches": len(filtered_lines),
                    "total_lines": len(lines)
                },
                output=filtered_output,
                metadata={
                    "command": "grep",
                    "original_command": command,
                    "context": {"before": before, "after": after}
                }
            )
            
        except Exception as e:
            logger.error(f"Output filter error: {e}")
            return ExtendedOperationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def msf_console_logger(
        self,
        action: str,
        filename: Optional[str] = None,
        **kwargs
    ) -> ExtendedOperationResult:
        """Console output logging (spool command)"""
        try:
            if action == "start":
                # Start logging
                if not filename:
                    filename = f"msf_console_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                    
                self._console_log_file = filename
                self._console_log_enabled = True
                
                # Execute spool command
                result = await self.execute_command(f"spool {filename}")
                
                return ExtendedOperationResult(
                    success=True,
                    data={
                        "action": "start",
                        "filename": filename,
                        "logging": True
                    },
                    output=result.output,
                    metadata={"command": "spool"}
                )
                
            elif action == "stop":
                # Stop logging
                result = await self.execute_command("spool off")
                
                self._console_log_enabled = False
                old_file = self._console_log_file
                self._console_log_file = None
                
                return ExtendedOperationResult(
                    success=True,
                    data={
                        "action": "stop",
                        "filename": old_file,
                        "logging": False
                    },
                    output=result.output,
                    metadata={"command": "spool"}
                )
                
            elif action == "status":
                # Get logging status
                return ExtendedOperationResult(
                    success=True,
                    data={
                        "logging": self._console_log_enabled,
                        "filename": self._console_log_file
                    },
                    metadata={"command": "spool"}
                )
                
            else:
                return ExtendedOperationResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Console logger error: {e}")
            return ExtendedOperationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def msf_config_manager(
        self,
        action: str,
        config_name: Optional[str] = None,
        **kwargs
    ) -> ExtendedOperationResult:
        """Configuration save/load functionality (save command)"""
        try:
            if action == "save":
                # Save current configuration
                if not config_name:
                    config_name = "default"
                    
                # Get current settings
                config = {
                    "timestamp": datetime.now().isoformat(),
                    "workspace": await self._get_current_workspace(),
                    "routes": self._route_manager["routes"],
                    "loaded_plugins": [],
                    "console_settings": {}
                }
                
                # Get loaded plugins
                if self.plugin_manager:
                    loaded = self.plugin_manager.list_plugins(loaded_only=True)
                    config["loaded_plugins"] = [p["name"] for p in loaded]
                    
                # Save configuration
                self._saved_configs[config_name] = config
                
                # Also save to file
                config_path = Path.home() / f".msf_config_{config_name}.json"
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                    
                return ExtendedOperationResult(
                    success=True,
                    data={
                        "action": "save",
                        "config_name": config_name,
                        "saved_items": list(config.keys())
                    },
                    metadata={"command": "save", "path": str(config_path)}
                )
                
            elif action == "load":
                # Load configuration
                if not config_name:
                    config_name = "default"
                    
                # Try to load from memory first
                if config_name in self._saved_configs:
                    config = self._saved_configs[config_name]
                else:
                    # Load from file
                    config_path = Path.home() / f".msf_config_{config_name}.json"
                    if not config_path.exists():
                        return ExtendedOperationResult(
                            success=False,
                            data=None,
                            error=f"Configuration not found: {config_name}"
                        )
                        
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        
                # Apply configuration
                applied = []
                
                # Switch workspace
                if config.get("workspace"):
                    await self.execute_command(f"workspace {config['workspace']}")
                    applied.append("workspace")
                    
                # Restore routes
                for route_key, route_info in config.get("routes", {}).items():
                    subnet = route_key.split('/')[0]
                    await self.execute_command(f"route add {subnet} {route_info['session_id']}")
                    applied.append(f"route:{route_key}")
                    
                # Load plugins
                if self.plugin_manager:
                    for plugin_name in config.get("loaded_plugins", []):
                        await self.plugin_manager.load_plugin(plugin_name)
                        applied.append(f"plugin:{plugin_name}")
                        
                return ExtendedOperationResult(
                    success=True,
                    data={
                        "action": "load",
                        "config_name": config_name,
                        "applied": applied
                    },
                    metadata={"command": "save", "timestamp": config.get("timestamp")}
                )
                
            elif action == "list":
                # List saved configurations
                configs = []
                
                # In-memory configs
                for name, config in self._saved_configs.items():
                    configs.append({
                        "name": name,
                        "timestamp": config.get("timestamp"),
                        "location": "memory"
                    })
                    
                # File-based configs
                for config_file in Path.home().glob(".msf_config_*.json"):
                    name = config_file.stem.replace(".msf_config_", "")
                    if name not in self._saved_configs:
                        configs.append({
                            "name": name,
                            "location": "file",
                            "path": str(config_file)
                        })
                        
                return ExtendedOperationResult(
                    success=True,
                    data={"configurations": configs},
                    metadata={"command": "save", "count": len(configs)}
                )
                
            else:
                return ExtendedOperationResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Config manager error: {e}")
            return ExtendedOperationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    # ==================== HELPER METHODS ====================
    
    def _parse_routes(self, output: str) -> List[Dict[str, Any]]:
        """Parse route list from MSF output"""
        import re
        routes = []
        lines = output.strip().split('\n')
        skip_patterns = ['Subnet', '===', '---', 'Routing', 'Table', 'Netmask', 'Gateway']

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if any(pat in stripped for pat in skip_patterns):
                continue
            if re.match(r'^[\-=\s]+$', stripped):
                continue

            parts = stripped.split()
            if len(parts) >= 3 and re.match(r'\d+\.\d+\.\d+\.\d+', parts[0]):
                routes.append({
                    "subnet": parts[0],
                    "netmask": parts[1],
                    "gateway": " ".join(parts[2:]),
                })

        return routes
    
    async def _get_current_workspace(self) -> str:
        """Get current workspace name"""
        result = await self.execute_command("workspace")
        
        for line in result.output.split('\n'):
            if line.strip().startswith('*'):
                return line.strip()[1:].strip()
                
        return "default"