#!/usr/bin/env python3
"""
MSF Console MCP Extended Tools Implementation
============================================
Implements 15 additional MCP tools to achieve 95% MSFConsole coverage.
Built on top of the existing MSFConsoleStableWrapper foundation.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import re

# Import existing stable wrapper
from msf import (
    MSFConsoleStableWrapper,
    OperationStatus,
    OperationResult,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("msf_extended_tools")

# Extended result for additional metadata
@dataclass
class ExtendedOperationResult(OperationResult):
    """Extended result with additional metadata"""
    metadata: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    pagination: Dict[str, Any] = field(default_factory=dict)

class ModuleAction(Enum):
    """Module manager actions"""
    USE = "use"
    INFO = "info"
    OPTIONS = "options"
    SET = "set"
    UNSET = "unset"
    CHECK = "check"
    RUN = "run"
    EXPLOIT = "exploit"
    BACK = "back"
    RELOAD = "reload_all"

class SessionAction(Enum):
    """Session interaction actions"""
    LIST = "list"
    INTERACT = "interact"
    EXECUTE = "execute"
    UPGRADE = "upgrade"
    KILL = "kill"
    BACKGROUND = "background"
    DETACH = "detach"

class DatabaseAction(Enum):
    """Database query actions"""
    LIST = "list"
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    EXPORT = "export"

class MSFExtendedTools(MSFConsoleStableWrapper):
    """Extended MSF tools implementation"""
    
    def __init__(self):
        super().__init__()
        self.module_context = None  # Current module context
        self.session_context = {}   # Active session contexts
        
    # ==================== TOOL 1: Module Manager ====================
    
    async def msf_module_manager(
        self, 
        action: str,
        module_path: str = None,
        options: Dict[str, str] = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Comprehensive module management tool.
        Actions: use, info, options, set, unset, check, run, exploit, back, reload
        """
        start_time = time.time()
        
        try:
            # Validate action
            try:
                module_action = ModuleAction(action.lower())
            except ValueError:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error=f"Invalid action: {action}. Valid actions: {[a.value for a in ModuleAction]}"
                )
            
            # Execute action
            if module_action == ModuleAction.USE:
                if not module_path:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Module path required for 'use' action"
                    )
                
                result = await self.execute_command(f"use {module_path}", timeout)
                if result.status == OperationStatus.SUCCESS:
                    self.module_context = module_path
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"module": module_path, "loaded": True},
                        execution_time=result.execution_time,
                        metadata={"context": self.module_context}
                    )
                
            elif module_action == ModuleAction.INFO:
                cmd = f"info {module_path}" if module_path else "info"
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    # Parse module info
                    info = self._parse_module_info(result.data.get("stdout", ""))
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data=info,
                        execution_time=result.execution_time
                    )
                    
            elif module_action == ModuleAction.OPTIONS:
                result = await self.execute_command("show options", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    # Parse options
                    options_data = self._parse_options(result.data.get("stdout", ""))
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data=options_data,
                        execution_time=result.execution_time
                    )
                    
            elif module_action == ModuleAction.SET:
                if not options:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Options required for 'set' action"
                    )
                
                # Set multiple options
                success_count = 0
                errors = []
                
                for key, value in options.items():
                    result = await self.execute_command(f"set {key} {value}", timeout)
                    if result.status == OperationStatus.SUCCESS:
                        success_count += 1
                    else:
                        errors.append(f"{key}: {result.error}")
                
                return ExtendedOperationResult(
                    status=OperationStatus.SUCCESS if not errors else OperationStatus.PARTIAL,
                    data={"set_count": success_count, "errors": errors},
                    execution_time=time.time() - start_time
                )
                
            elif module_action in [ModuleAction.RUN, ModuleAction.EXPLOIT]:
                # Check if module is loaded
                if not self.module_context:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="No module loaded. Use 'use' action first"
                    )
                
                # Use longer timeout for exploitation
                exploit_timeout = timeout or 120.0
                result = await self.execute_command(action, exploit_timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    # Check for session creation
                    session_info = self._extract_session_info(result.data.get("stdout", ""))
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"executed": True, "session": session_info},
                        execution_time=result.execution_time,
                        metadata={"module": self.module_context}
                    )
                    
            elif module_action == ModuleAction.CHECK:
                result = await self.execute_command("check", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    # Parse check result
                    check_result = self._parse_check_result(result.data.get("stdout", ""))
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data=check_result,
                        execution_time=result.execution_time
                    )
                    
            elif module_action == ModuleAction.BACK:
                result = await self.execute_command("back", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    self.module_context = None
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"context": "msf"},
                        execution_time=result.execution_time
                    )
                    
            elif module_action == ModuleAction.RELOAD:
                result = await self.execute_command("reload_all", timeout or 60.0)
                
                return ExtendedOperationResult(
                    status=result.status,
                    data={"reloaded": result.status == OperationStatus.SUCCESS},
                    execution_time=result.execution_time
                )
            
            # Fallback for unhandled actions
            return ExtendedOperationResult(
                status=result.status,
                data=result.data,
                execution_time=result.execution_time,
                error=result.error
            )
            
        except Exception as e:
            logger.error(f"Module manager error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 2: Session Interact ====================
    
    async def msf_session_interact(
        self,
        session_id: int = None,
        action: str = "list",
        command: str = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Advanced session interaction tool.
        Actions: list, interact, execute, upgrade, kill, background, detach
        """
        start_time = time.time()
        
        try:
            # Validate action
            try:
                session_action = SessionAction(action.lower())
            except ValueError:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error=f"Invalid action: {action}. Valid actions: {[a.value for a in SessionAction]}"
                )
            
            if session_action == SessionAction.LIST:
                result = await self.execute_command("sessions -l", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    sessions = self._parse_sessions(result.data.get("stdout", ""))
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"sessions": sessions, "count": len(sessions)},
                        execution_time=result.execution_time
                    )
                    
            elif session_action == SessionAction.INTERACT:
                if session_id is None:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Session ID required for interact action"
                    )
                
                # Note: Interactive sessions require special handling
                # For now, we'll return session info
                result = await self.execute_command(f"sessions -i {session_id}", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    self.session_context[session_id] = True
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"session_id": session_id, "interactive": True},
                        execution_time=result.execution_time,
                        metadata={"note": "Use execute action to run commands"}
                    )
                    
            elif session_action == SessionAction.EXECUTE:
                if session_id is None or command is None:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Session ID and command required for execute action"
                    )
                
                # Execute command in session
                cmd = f"sessions -C '{command}' -i {session_id}"
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "session_id": session_id,
                            "command": command,
                            "output": result.data.get("stdout", "")
                        },
                        execution_time=result.execution_time
                    )
                    
            elif session_action == SessionAction.UPGRADE:
                if session_id is None:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Session ID required for upgrade action"
                    )
                
                # Upgrade shell to meterpreter
                result = await self.execute_command(f"sessions -u {session_id}", timeout or 60.0)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"session_id": session_id, "upgraded": True},
                        execution_time=result.execution_time
                    )
                    
            elif session_action == SessionAction.KILL:
                if session_id is None:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Session ID required for kill action"
                    )
                
                result = await self.execute_command(f"sessions -k {session_id}", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    if session_id in self.session_context:
                        del self.session_context[session_id]
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"session_id": session_id, "killed": True},
                        execution_time=result.execution_time
                    )
            
            # Return result for other actions
            return ExtendedOperationResult(
                status=result.status,
                data=result.data,
                execution_time=result.execution_time,
                error=result.error
            )
            
        except Exception as e:
            logger.error(f"Session interact error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 3: Database Query ====================
    
    async def msf_database_query(
        self,
        table: str,
        action: str = "list",
        filters: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Database operations for hosts, services, vulns, creds, loot.
        Actions: list, add, update, delete, search, export
        """
        start_time = time.time()
        
        try:
            # Validate action
            try:
                db_action = DatabaseAction(action.lower())
            except ValueError:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error=f"Invalid action: {action}. Valid actions: {[a.value for a in DatabaseAction]}"
                )
            
            # Validate table
            valid_tables = ["hosts", "services", "vulns", "creds", "loot", "notes"]
            if table not in valid_tables:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error=f"Invalid table: {table}. Valid tables: {valid_tables}"
                )
            
            if db_action == DatabaseAction.LIST:
                # Build command with filters
                cmd = table
                if filters:
                    filter_args = self._build_filter_args(filters)
                    cmd += f" {filter_args}"
                
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    parsed_data = self._parse_database_output(table, result.data.get("stdout", ""))
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={table: parsed_data, "count": len(parsed_data)},
                        execution_time=result.execution_time
                    )
                    
            elif db_action == DatabaseAction.ADD:
                if not data:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Data required for add action"
                    )
                
                # Build add command based on table
                cmd = self._build_add_command(table, data)
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"added": True, "table": table},
                        execution_time=result.execution_time
                    )
                    
            elif db_action == DatabaseAction.DELETE:
                if not filters:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Filters required for delete action (safety)"
                    )
                
                # Build delete command
                filter_args = self._build_filter_args(filters)
                cmd = f"{table} -d {filter_args}"
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"deleted": True, "table": table, "filters": filters},
                        execution_time=result.execution_time
                    )
                    
            elif db_action == DatabaseAction.SEARCH:
                if not filters:
                    filters = {}
                
                # Use search-specific parsing
                search_term = filters.get("search", "")
                cmd = f"{table} -S {search_term}" if search_term else table
                
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    parsed_data = self._parse_database_output(table, result.data.get("stdout", ""))
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"results": parsed_data, "count": len(parsed_data)},
                        execution_time=result.execution_time
                    )
                    
            elif db_action == DatabaseAction.EXPORT:
                # Export database
                export_format = filters.get("format", "xml") if filters else "xml"
                cmd = f"db_export -f {export_format}"
                
                result = await self.execute_command(cmd, timeout or 60.0)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"exported": True, "format": export_format},
                        execution_time=result.execution_time
                    )
            
            # Return result
            return ExtendedOperationResult(
                status=result.status,
                data=result.data,
                execution_time=result.execution_time,
                error=result.error
            )
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 4: Exploit Chain ====================
    
    async def msf_exploit_chain(
        self,
        target: str,
        exploit_module: str,
        payload: str,
        options: Dict[str, str],
        auto_execute: bool = False,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Complete exploitation workflow automation.
        Combines: search → use → set options → check → exploit → session management
        """
        start_time = time.time()
        workflow_steps = []
        
        try:
            # Step 1: Load exploit module
            use_result = await self.msf_module_manager("use", exploit_module)
            workflow_steps.append({
                "step": "load_module",
                "status": use_result.status.value,
                "time": use_result.execution_time
            })
            
            if use_result.status != OperationStatus.SUCCESS:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data={"workflow": workflow_steps},
                    execution_time=time.time() - start_time,
                    error=f"Failed to load module: {use_result.error}"
                )
            
            # Step 2: Set payload
            payload_result = await self.execute_command(f"set payload {payload}")
            workflow_steps.append({
                "step": "set_payload",
                "status": payload_result.status.value,
                "time": payload_result.execution_time
            })
            
            # Step 3: Set options
            options["RHOSTS"] = target  # Ensure target is set
            set_result = await self.msf_module_manager("set", options=options)
            workflow_steps.append({
                "step": "set_options",
                "status": set_result.status.value,
                "time": set_result.execution_time
            })
            
            # Step 4: Check if vulnerable (optional)
            check_result = await self.msf_module_manager("check")
            workflow_steps.append({
                "step": "check_vulnerable",
                "status": check_result.status.value,
                "result": check_result.data,
                "time": check_result.execution_time
            })
            
            # Step 5: Execute exploit if auto_execute or check passed
            if auto_execute or (check_result.data and check_result.data.get("vulnerable")):
                exploit_result = await self.msf_module_manager("exploit", timeout=timeout or 120.0)
                workflow_steps.append({
                    "step": "exploit",
                    "status": exploit_result.status.value,
                    "session": exploit_result.data.get("session") if exploit_result.data else None,
                    "time": exploit_result.execution_time
                })
                
                # Step 6: Check for new sessions
                if exploit_result.status == OperationStatus.SUCCESS:
                    sessions_result = await self.msf_session_interact(action="list")
                    workflow_steps.append({
                        "step": "session_check",
                        "status": sessions_result.status.value,
                        "sessions": sessions_result.data.get("count", 0) if sessions_result.data else 0,
                        "time": sessions_result.execution_time
                    })
                    
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "workflow": workflow_steps,
                            "success": True,
                            "sessions": sessions_result.data
                        },
                        execution_time=time.time() - start_time,
                        metadata={
                            "exploit": exploit_module,
                            "target": target,
                            "payload": payload
                        }
                    )
            else:
                return ExtendedOperationResult(
                    status=OperationStatus.SUCCESS,
                    data={
                        "workflow": workflow_steps,
                        "success": False,
                        "reason": "Target not vulnerable or auto_execute disabled"
                    },
                    execution_time=time.time() - start_time
                )
            
            # Return partial success if we got this far
            return ExtendedOperationResult(
                status=OperationStatus.PARTIAL,
                data={"workflow": workflow_steps},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Exploit chain error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data={"workflow": workflow_steps},
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 5: Post Exploitation ====================
    
    async def msf_post_exploitation(
        self,
        session_id: int,
        module: str,
        options: Dict[str, str] = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Post-exploitation module execution.
        Modules: gather/*, escalate/*, manage/*
        """
        start_time = time.time()
        
        try:
            # Load post module
            use_result = await self.msf_module_manager("use", module)
            
            if use_result.status != OperationStatus.SUCCESS:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error=f"Failed to load post module: {use_result.error}"
                )
            
            # Set session
            session_result = await self.execute_command(f"set SESSION {session_id}")
            
            if session_result.status != OperationStatus.SUCCESS:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error="Failed to set session"
                )
            
            # Set additional options
            if options:
                set_result = await self.msf_module_manager("set", options=options)
                if set_result.status != OperationStatus.SUCCESS:
                    logger.warning(f"Some options failed to set: {set_result.data}")
            
            # Run post module
            run_result = await self.msf_module_manager("run", timeout=timeout)
            
            if run_result.status == OperationStatus.SUCCESS:
                # Parse post module output
                output = run_result.data.get("stdout", "") if run_result.data else ""
                post_data = self._parse_post_module_output(module, output)
                
                return ExtendedOperationResult(
                    status=OperationStatus.SUCCESS,
                    data={
                        "module": module,
                        "session_id": session_id,
                        "results": post_data
                    },
                    execution_time=time.time() - start_time
                )
            
            return ExtendedOperationResult(
                status=run_result.status,
                data=run_result.data,
                execution_time=time.time() - start_time,
                error=run_result.error
            )
            
        except Exception as e:
            logger.error(f"Post exploitation error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 6: Handler Manager ====================
    
    async def msf_handler_manager(
        self,
        action: str,
        payload: str = None,
        options: Dict[str, str] = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Payload handler management.
        Actions: start, stop, list, multi_handler
        """
        start_time = time.time()
        
        try:
            if action == "start":
                if not payload or not options:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Payload and options required for start action"
                    )
                
                # Use multi/handler
                use_result = await self.msf_module_manager("use", "exploit/multi/handler")
                
                if use_result.status == OperationStatus.SUCCESS:
                    # Set payload
                    await self.execute_command(f"set payload {payload}")
                    
                    # Set options
                    await self.msf_module_manager("set", options=options)
                    
                    # Start handler as job
                    handler_result = await self.execute_command("exploit -j", timeout)
                    
                    if handler_result.status == OperationStatus.SUCCESS:
                        # Extract job ID
                        job_id = self._extract_job_id(handler_result.data.get("stdout", ""))
                        
                        return ExtendedOperationResult(
                            status=OperationStatus.SUCCESS,
                            data={
                                "handler_started": True,
                                "job_id": job_id,
                                "payload": payload
                            },
                            execution_time=time.time() - start_time
                        )
                        
            elif action == "list":
                # List jobs
                result = await self.execute_command("jobs", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    jobs = self._parse_jobs(result.data.get("stdout", ""))
                    
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"jobs": jobs, "count": len(jobs)},
                        execution_time=result.execution_time
                    )
                    
            elif action == "stop":
                job_id = options.get("job_id") if options else None
                if not job_id:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="job_id required in options for stop action"
                    )
                
                result = await self.execute_command(f"jobs -k {job_id}", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"stopped": True, "job_id": job_id},
                        execution_time=result.execution_time
                    )
                    
            elif action == "multi_handler":
                # Set up persistent multi-handler
                use_result = await self.msf_module_manager("use", "exploit/multi/handler")
                
                if use_result.status == OperationStatus.SUCCESS:
                    # Set ExitOnSession false for persistent handler
                    await self.execute_command("set ExitOnSession false")
                    
                    # Set payload if provided
                    if payload:
                        await self.execute_command(f"set payload {payload}")
                    
                    # Set options if provided
                    if options:
                        await self.msf_module_manager("set", options=options)
                    
                    # Start persistent handler
                    handler_result = await self.execute_command("exploit -j -z", timeout)
                    
                    if handler_result.status == OperationStatus.SUCCESS:
                        return ExtendedOperationResult(
                            status=OperationStatus.SUCCESS,
                            data={
                                "multi_handler": True,
                                "persistent": True
                            },
                            execution_time=time.time() - start_time
                        )
            
            # Invalid action
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Invalid action: {action}. Valid actions: start, stop, list, multi_handler"
            )
            
        except Exception as e:
            logger.error(f"Handler manager error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 7: Scanner Suite ====================
    
    async def msf_scanner_suite(
        self,
        scan_type: str,
        targets: str,
        options: Dict[str, str] = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Integrated scanning capabilities.
        Types: port, smb, http, ssh, ftp, snmp, discovery
        """
        start_time = time.time()
        
        try:
            # Map scan types to modules
            scanner_modules = {
                "port": "auxiliary/scanner/portscan/tcp",
                "smb": "auxiliary/scanner/smb/smb_version",
                "http": "auxiliary/scanner/http/http_version",
                "ssh": "auxiliary/scanner/ssh/ssh_version",
                "ftp": "auxiliary/scanner/ftp/ftp_version",
                "snmp": "auxiliary/scanner/snmp/snmp_enum",
                "discovery": "auxiliary/scanner/discovery/arp_sweep"
            }
            
            if scan_type not in scanner_modules:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error=f"Invalid scan type: {scan_type}. Valid types: {list(scanner_modules.keys())}"
                )
            
            # Load scanner module
            module = scanner_modules[scan_type]
            use_result = await self.msf_module_manager("use", module)
            
            if use_result.status != OperationStatus.SUCCESS:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error=f"Failed to load scanner module: {use_result.error}"
                )
            
            # Set targets
            await self.execute_command(f"set RHOSTS {targets}")
            
            # Set additional options
            if options:
                await self.msf_module_manager("set", options=options)
            
            # Run scan
            scan_timeout = timeout or 60.0
            scan_result = await self.msf_module_manager("run", timeout=scan_timeout)
            
            if scan_result.status == OperationStatus.SUCCESS:
                # Parse scan results
                output = scan_result.data.get("stdout", "") if scan_result.data else ""
                scan_data = self._parse_scan_output(scan_type, output)
                
                return ExtendedOperationResult(
                    status=OperationStatus.SUCCESS,
                    data={
                        "scan_type": scan_type,
                        "targets": targets,
                        "results": scan_data,
                        "hosts_found": len(scan_data)
                    },
                    execution_time=time.time() - start_time
                )
            
            return ExtendedOperationResult(
                status=scan_result.status,
                data=scan_result.data,
                execution_time=time.time() - start_time,
                error=scan_result.error
            )
            
        except Exception as e:
            logger.error(f"Scanner suite error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 8: Credential Manager ====================
    
    async def msf_credential_manager(
        self,
        action: str,
        cred_data: Dict[str, Any] = None,
        filters: Dict[str, Any] = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Credential management.
        Actions: add, list, crack, validate, export
        """
        start_time = time.time()
        
        try:
            if action == "list":
                # List credentials with optional filters
                cmd = "creds"
                if filters:
                    if "service" in filters:
                        cmd += f" -s {filters['service']}"
                    if "host" in filters:
                        cmd += f" -h {filters['host']}"
                
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    creds = self._parse_credentials(result.data.get("stdout", ""))
                    
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"credentials": creds, "count": len(creds)},
                        execution_time=result.execution_time
                    )
                    
            elif action == "add":
                if not cred_data:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Credential data required for add action"
                    )
                
                # Build creds add command
                cmd = "creds add"
                if "user" in cred_data:
                    cmd += f" user:{cred_data['user']}"
                if "password" in cred_data:
                    cmd += f" password:{cred_data['password']}"
                if "host" in cred_data:
                    cmd += f" host:{cred_data['host']}"
                if "service" in cred_data:
                    cmd += f" service:{cred_data['service']}"
                
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"added": True, "credential": cred_data},
                        execution_time=result.execution_time
                    )
                    
            elif action == "validate":
                # Validate credentials using appropriate module
                if not cred_data or "service" not in cred_data:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Service type required for credential validation"
                    )
                
                # Map services to validation modules
                validation_modules = {
                    "ssh": "auxiliary/scanner/ssh/ssh_login",
                    "smb": "auxiliary/scanner/smb/smb_login",
                    "ftp": "auxiliary/scanner/ftp/ftp_login",
                    "mysql": "auxiliary/scanner/mysql/mysql_login",
                    "postgres": "auxiliary/scanner/postgres/postgres_login"
                }
                
                service = cred_data["service"].lower()
                if service not in validation_modules:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error=f"No validation module for service: {service}"
                    )
                
                # Load validation module
                module = validation_modules[service]
                await self.msf_module_manager("use", module)
                
                # Set credentials
                options = {
                    "RHOSTS": cred_data.get("host", ""),
                    "USERNAME": cred_data.get("user", ""),
                    "PASSWORD": cred_data.get("password", "")
                }
                
                await self.msf_module_manager("set", options=options)
                
                # Run validation
                validate_result = await self.msf_module_manager("run", timeout=timeout)
                
                if validate_result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "validated": True,
                            "credential": cred_data,
                            "valid": "Success" in str(validate_result.data)
                        },
                        execution_time=time.time() - start_time
                    )
                    
            elif action == "export":
                # Export credentials
                export_format = filters.get("format", "csv") if filters else "csv"
                result = await self.execute_command(f"creds -o /tmp/creds.{export_format}", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"exported": True, "format": export_format, "path": f"/tmp/creds.{export_format}"},
                        execution_time=result.execution_time
                    )
            
            # Invalid action
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Invalid action: {action}. Valid actions: list, add, validate, export"
            )
            
        except Exception as e:
            logger.error(f"Credential manager error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 9: Pivot Manager ====================
    
    async def msf_pivot_manager(
        self,
        session_id: int,
        action: str,
        options: Dict[str, Any] = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Network pivoting and routing.
        Actions: add_route, list_routes, portfwd, socks_proxy
        """
        start_time = time.time()
        
        try:
            if action == "add_route":
                if not options or "subnet" not in options:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Subnet required in options for add_route"
                    )
                
                subnet = options["subnet"]
                netmask = options.get("netmask", "255.255.255.0")
                
                cmd = f"route add {subnet} {netmask} {session_id}"
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "route_added": True,
                            "subnet": subnet,
                            "netmask": netmask,
                            "session": session_id
                        },
                        execution_time=result.execution_time
                    )
                    
            elif action == "list_routes":
                result = await self.execute_command("route print", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    routes = self._parse_routes(result.data.get("stdout", ""))
                    
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"routes": routes, "count": len(routes)},
                        execution_time=result.execution_time
                    )
                    
            elif action == "portfwd":
                if not options:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Options required for port forwarding"
                    )
                
                # Build portfwd command
                cmd = f"sessions -i {session_id} -c 'portfwd add"
                
                if "local_port" in options:
                    cmd += f" -l {options['local_port']}"
                if "remote_host" in options:
                    cmd += f" -p {options['remote_host']}"
                if "remote_port" in options:
                    cmd += f" -r {options['remote_port']}"
                
                cmd += "'"
                
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "portfwd_added": True,
                            "session": session_id,
                            "forwarding": options
                        },
                        execution_time=result.execution_time
                    )
                    
            elif action == "socks_proxy":
                # Set up SOCKS proxy
                use_result = await self.msf_module_manager("use", "auxiliary/server/socks_proxy")
                
                if use_result.status == OperationStatus.SUCCESS:
                    # Set options
                    proxy_options = {
                        "SRVPORT": options.get("port", "1080") if options else "1080",
                        "VERSION": options.get("version", "5") if options else "5"
                    }
                    
                    await self.msf_module_manager("set", options=proxy_options)
                    
                    # Start SOCKS proxy
                    proxy_result = await self.execute_command("run -j", timeout)
                    
                    if proxy_result.status == OperationStatus.SUCCESS:
                        return ExtendedOperationResult(
                            status=OperationStatus.SUCCESS,
                            data={
                                "socks_proxy": True,
                                "port": proxy_options["SRVPORT"],
                                "version": proxy_options["VERSION"]
                            },
                            execution_time=time.time() - start_time
                        )
            
            # Invalid action
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Invalid action: {action}. Valid actions: add_route, list_routes, portfwd, socks_proxy"
            )
            
        except Exception as e:
            logger.error(f"Pivot manager error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 10: Resource Executor ====================
    
    async def msf_resource_executor(
        self,
        script_path: str = None,
        commands: List[str] = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Resource script execution.
        Can use file path or command list.
        """
        start_time = time.time()
        
        try:
            if script_path:
                # Execute resource file
                result = await self.execute_command(f"resource {script_path}", timeout or 60.0)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "executed": True,
                            "script": script_path,
                            "output": result.data.get("stdout", "") if result.data else ""
                        },
                        execution_time=result.execution_time
                    )
                    
            elif commands:
                # Execute commands sequentially
                results = []
                total_time = 0
                
                for cmd in commands:
                    cmd_result = await self.execute_command(cmd, timeout)
                    results.append({
                        "command": cmd,
                        "status": cmd_result.status.value,
                        "output": cmd_result.data.get("stdout", "") if cmd_result.data else "",
                        "time": cmd_result.execution_time
                    })
                    total_time += cmd_result.execution_time
                    
                    # Stop on failure
                    if cmd_result.status == OperationStatus.FAILURE:
                        break
                
                # Determine overall status
                failed = any(r["status"] == "failure" for r in results)
                
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE if failed else OperationStatus.SUCCESS,
                    data={
                        "executed": not failed,
                        "commands": len(commands),
                        "results": results
                    },
                    execution_time=total_time
                )
            else:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error="Either script_path or commands list required"
                )
                
        except Exception as e:
            logger.error(f"Resource executor error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 11: Loot Collector ====================
    
    async def msf_loot_collector(
        self,
        session_id: int = None,
        loot_type: str = None,
        action: str = "list",
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Data collection and management.
        Types: files, screenshots, keystrokes, passwords
        Actions: list, collect, export
        """
        start_time = time.time()
        
        try:
            if action == "list":
                # List loot
                cmd = "loot"
                if loot_type:
                    cmd += f" -t {loot_type}"
                
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    loot_items = self._parse_loot(result.data.get("stdout", ""))
                    
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"loot": loot_items, "count": len(loot_items)},
                        execution_time=result.execution_time
                    )
                    
            elif action == "collect":
                if not session_id:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Session ID required for collect action"
                    )
                
                # Map loot types to post modules
                loot_modules = {
                    "files": "post/windows/gather/enum_files",
                    "screenshots": "post/windows/gather/screen_spy",
                    "keystrokes": "post/windows/capture/keylog_recorder",
                    "passwords": "post/windows/gather/credentials/credential_collector",
                    "browser": "post/multi/gather/firefox_creds",
                    "system": "post/windows/gather/enum_system"
                }
                
                if loot_type and loot_type in loot_modules:
                    # Use specific loot module
                    module = loot_modules[loot_type]
                    
                    post_result = await self.msf_post_exploitation(
                        session_id=session_id,
                        module=module,
                        timeout=timeout
                    )
                    
                    if post_result.status == OperationStatus.SUCCESS:
                        return ExtendedOperationResult(
                            status=OperationStatus.SUCCESS,
                            data={
                                "collected": True,
                                "type": loot_type,
                                "session": session_id,
                                "results": post_result.data
                            },
                            execution_time=time.time() - start_time
                        )
                else:
                    # General loot collection
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "message": "Use specific loot_type for targeted collection",
                            "available_types": list(loot_modules.keys())
                        },
                        execution_time=time.time() - start_time
                    )
                    
            elif action == "export":
                # Export loot
                result = await self.execute_command("loot -o /tmp/loot_export.txt", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"exported": True, "path": "/tmp/loot_export.txt"},
                        execution_time=result.execution_time
                    )
            
            # Invalid action
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Invalid action: {action}. Valid actions: list, collect, export"
            )
            
        except Exception as e:
            logger.error(f"Loot collector error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 12: Vulnerability Tracker ====================
    
    async def msf_vulnerability_tracker(
        self,
        action: str,
        vuln_data: Dict[str, Any] = None,
        filters: Dict[str, Any] = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Vulnerability management.
        Actions: import, analyze, correlate, report
        """
        start_time = time.time()
        
        try:
            if action == "list":
                # List vulnerabilities
                cmd = "vulns"
                if filters:
                    if "host" in filters:
                        cmd += f" -h {filters['host']}"
                    if "service" in filters:
                        cmd += f" -s {filters['service']}"
                
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    vulns = self._parse_vulnerabilities(result.data.get("stdout", ""))
                    
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"vulnerabilities": vulns, "count": len(vulns)},
                        execution_time=result.execution_time
                    )
                    
            elif action == "import":
                if not vuln_data or "file" not in vuln_data:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="File path required in vuln_data for import"
                    )
                
                # Import vulnerability scan
                result = await self.execute_command(f"db_import {vuln_data['file']}", timeout or 60.0)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"imported": True, "file": vuln_data['file']},
                        execution_time=result.execution_time
                    )
                    
            elif action == "analyze":
                # Analyze vulnerabilities for exploitability
                vulns_result = await self.execute_command("vulns", timeout)
                
                if vulns_result.status == OperationStatus.SUCCESS:
                    vulns = self._parse_vulnerabilities(vulns_result.data.get("stdout", ""))
                    
                    # Search for exploits for each vulnerability
                    exploitable = []
                    
                    for vuln in vulns[:10]:  # Limit to prevent timeout
                        if "name" in vuln:
                            search_result = await self.search_modules(vuln["name"], limit=5)
                            
                            if search_result.data and search_result.data.get("modules"):
                                exploitable.append({
                                    "vulnerability": vuln,
                                    "exploits": search_result.data["modules"]
                                })
                    
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "analyzed": True,
                            "total_vulns": len(vulns),
                            "exploitable": len(exploitable),
                            "results": exploitable
                        },
                        execution_time=time.time() - start_time
                    )
                    
            elif action == "correlate":
                # Correlate vulnerabilities with available exploits
                result = await self.execute_command("analyze", timeout or 60.0)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "correlated": True,
                            "output": result.data.get("stdout", "") if result.data else ""
                        },
                        execution_time=result.execution_time
                    )
                    
            elif action == "report":
                # Generate vulnerability report
                report_data = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "vulnerabilities": [],
                    "statistics": {}
                }
                
                # Get vulnerabilities
                vulns_result = await self.execute_command("vulns", timeout)
                
                if vulns_result.status == OperationStatus.SUCCESS:
                    vulns = self._parse_vulnerabilities(vulns_result.data.get("stdout", ""))
                    report_data["vulnerabilities"] = vulns
                    
                    # Calculate statistics
                    report_data["statistics"] = {
                        "total": len(vulns),
                        "by_severity": self._count_by_severity(vulns),
                        "by_service": self._count_by_service(vulns)
                    }
                    
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"report": report_data},
                        execution_time=time.time() - start_time
                    )
            
            # Invalid action
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Invalid action: {action}. Valid actions: list, import, analyze, correlate, report"
            )
            
        except Exception as e:
            logger.error(f"Vulnerability tracker error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 13: Reporting Engine ====================
    
    async def msf_reporting_engine(
        self,
        report_type: str,
        filters: Dict[str, Any] = None,
        format: str = "json",
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Comprehensive reporting.
        Types: hosts, services, vulns, exploitation_timeline, executive_summary
        Formats: json, xml, html, text
        """
        start_time = time.time()
        
        try:
            report_data = {
                "type": report_type,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "data": {}
            }
            
            if report_type == "hosts":
                # Get hosts report
                hosts_result = await self.msf_database_query("hosts", "list", filters)
                
                if hosts_result.status == OperationStatus.SUCCESS:
                    report_data["data"] = hosts_result.data
                    
            elif report_type == "services":
                # Get services report
                services_result = await self.msf_database_query("services", "list", filters)
                
                if services_result.status == OperationStatus.SUCCESS:
                    report_data["data"] = services_result.data
                    
            elif report_type == "vulns":
                # Get vulnerabilities report
                vulns_result = await self.msf_vulnerability_tracker("list", filters=filters)
                
                if vulns_result.status == OperationStatus.SUCCESS:
                    report_data["data"] = vulns_result.data
                    
            elif report_type == "exploitation_timeline":
                # Get exploitation timeline
                sessions_result = await self.msf_session_interact(action="list")
                loot_result = await self.msf_loot_collector(action="list")
                
                report_data["data"] = {
                    "sessions": sessions_result.data if sessions_result.data else {},
                    "loot": loot_result.data if loot_result.data else {},
                    "timeline": self._build_exploitation_timeline(sessions_result.data, loot_result.data)
                }
                
            elif report_type == "executive_summary":
                # Build executive summary
                hosts_result = await self.msf_database_query("hosts", "list")
                services_result = await self.msf_database_query("services", "list")
                vulns_result = await self.msf_vulnerability_tracker("list")
                sessions_result = await self.msf_session_interact(action="list")
                
                report_data["data"] = {
                    "summary": {
                        "total_hosts": hosts_result.data.get("count", 0) if hosts_result.data else 0,
                        "total_services": services_result.data.get("count", 0) if services_result.data else 0,
                        "total_vulnerabilities": vulns_result.data.get("count", 0) if vulns_result.data else 0,
                        "active_sessions": sessions_result.data.get("count", 0) if sessions_result.data else 0
                    },
                    "risk_assessment": self._calculate_risk_score(vulns_result.data),
                    "recommendations": self._generate_recommendations(vulns_result.data)
                }
            else:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error=f"Invalid report type: {report_type}"
                )
            
            # Format report
            formatted_report = self._format_report(report_data, format)
            
            return ExtendedOperationResult(
                status=OperationStatus.SUCCESS,
                data={
                    "report": formatted_report,
                    "format": format,
                    "type": report_type
                },
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Reporting engine error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 14: Automation Builder ====================
    
    async def msf_automation_builder(
        self,
        workflow_name: str,
        steps: List[Dict[str, Any]],
        execute: bool = False,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Build and execute complex workflows.
        Example: recon → exploit → post-exploit → report
        """
        start_time = time.time()
        workflow_results = []
        
        try:
            # Validate workflow
            if not steps:
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error="No steps provided for workflow"
                )
            
            # Build workflow script
            workflow_script = []
            
            for i, step in enumerate(steps):
                if "tool" not in step or "params" not in step:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error=f"Step {i} missing required fields: tool, params"
                    )
                
                # Add step to workflow
                workflow_script.append({
                    "step": i + 1,
                    "tool": step["tool"],
                    "params": step["params"],
                    "description": step.get("description", f"Step {i + 1}")
                })
            
            if execute:
                # Execute workflow
                for step_info in workflow_script:
                    tool = step_info["tool"]
                    params = step_info["params"]
                    
                    # Execute tool based on name
                    if tool == "scanner":
                        result = await self.msf_scanner_suite(**params)
                    elif tool == "exploit":
                        result = await self.msf_exploit_chain(**params)
                    elif tool == "post":
                        result = await self.msf_post_exploitation(**params)
                    elif tool == "loot":
                        result = await self.msf_loot_collector(**params)
                    elif tool == "report":
                        result = await self.msf_reporting_engine(**params)
                    else:
                        result = ExtendedOperationResult(
                            status=OperationStatus.FAILURE,
                            data=None,
                            execution_time=0,
                            error=f"Unknown tool: {tool}"
                        )
                    
                    workflow_results.append({
                        "step": step_info["step"],
                        "tool": tool,
                        "status": result.status.value,
                        "data": result.data,
                        "time": result.execution_time,
                        "error": result.error
                    })
                    
                    # Stop on failure if not configured otherwise
                    if result.status == OperationStatus.FAILURE and not step.get("continue_on_error", False):
                        break
                
                # Determine overall status
                failed = any(r["status"] == "failure" for r in workflow_results)
                
                return ExtendedOperationResult(
                    status=OperationStatus.FAILURE if failed else OperationStatus.SUCCESS,
                    data={
                        "workflow": workflow_name,
                        "executed": True,
                        "steps": len(workflow_script),
                        "results": workflow_results
                    },
                    execution_time=time.time() - start_time
                )
            else:
                # Just return the workflow definition
                return ExtendedOperationResult(
                    status=OperationStatus.SUCCESS,
                    data={
                        "workflow": workflow_name,
                        "executed": False,
                        "script": workflow_script
                    },
                    execution_time=time.time() - start_time
                )
            
        except Exception as e:
            logger.error(f"Automation builder error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data={"workflow": workflow_name, "results": workflow_results},
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== TOOL 15: Plugin Manager ====================
    
    async def msf_plugin_manager(
        self,
        action: str,
        plugin_name: str = None,
        options: Dict[str, Any] = None,
        timeout: Optional[float] = None
    ) -> ExtendedOperationResult:
        """
        Plugin management.
        Actions: load, unload, list, info
        Popular: openvas, nexpose, nessus, nmap
        """
        start_time = time.time()
        
        try:
            if action == "list":
                # List loaded plugins
                result = await self.execute_command("load -l", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    plugins = self._parse_plugins(result.data.get("stdout", ""))
                    
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"plugins": plugins, "loaded_count": len(plugins)},
                        execution_time=result.execution_time
                    )
                    
            elif action == "load":
                if not plugin_name:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Plugin name required for load action"
                    )
                
                # Load plugin with options
                cmd = f"load {plugin_name}"
                if options:
                    for key, value in options.items():
                        cmd += f" {key}={value}"
                
                result = await self.execute_command(cmd, timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "loaded": True,
                            "plugin": plugin_name,
                            "options": options
                        },
                        execution_time=result.execution_time
                    )
                    
            elif action == "unload":
                if not plugin_name:
                    return ExtendedOperationResult(
                        status=OperationStatus.FAILURE,
                        data=None,
                        execution_time=time.time() - start_time,
                        error="Plugin name required for unload action"
                    )
                
                result = await self.execute_command(f"unload {plugin_name}", timeout)
                
                if result.status == OperationStatus.SUCCESS:
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"unloaded": True, "plugin": plugin_name},
                        execution_time=result.execution_time
                    )
                    
            elif action == "info":
                if not plugin_name:
                    # Show available plugins
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={
                            "available_plugins": [
                                "aggregator", "alias", "auto_add_route", "beholder",
                                "db_credcollect", "db_tracker", "event_tester",
                                "ffautoregen", "ips_filter", "lab", "libnotify",
                                "msfd", "msgrpc", "nessus", "nexpose", "openvas",
                                "pcap_log", "request", "rssfeed", "sample",
                                "session_notifier", "session_tagger", "socket_logger",
                                "sounds", "sqlmap", "thread", "token_adduser",
                                "token_hunter", "wiki", "wmap"
                            ]
                        },
                        execution_time=time.time() - start_time
                    )
                else:
                    # Get plugin info
                    plugin_info = self._get_plugin_info(plugin_name)
                    
                    return ExtendedOperationResult(
                        status=OperationStatus.SUCCESS,
                        data={"plugin": plugin_name, "info": plugin_info},
                        execution_time=time.time() - start_time
                    )
            
            # Invalid action
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Invalid action: {action}. Valid actions: load, unload, list, info"
            )
            
        except Exception as e:
            logger.error(f"Plugin manager error: {e}")
            return ExtendedOperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # ==================== Helper Methods ====================
    
    def _parse_module_info(self, output: str) -> Dict[str, Any]:
        """Parse module info output"""
        info = {
            "name": "",
            "description": "",
            "author": [],
            "references": [],
            "platform": "",
            "targets": []
        }
        
        lines = output.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if "Name:" in line:
                info["name"] = line.split("Name:", 1)[1].strip()
            elif "Description:" in line:
                current_section = "description"
            elif "Author:" in line:
                current_section = "author"
            elif "References:" in line:
                current_section = "references"
            elif "Platform:" in line:
                info["platform"] = line.split("Platform:", 1)[1].strip()
            elif "Available targets:" in line:
                current_section = "targets"
            elif current_section and line:
                if current_section == "description":
                    info["description"] += line + " "
                elif current_section == "author" and line.startswith("-"):
                    info["author"].append(line[1:].strip())
                elif current_section == "references" and line.startswith("-"):
                    info["references"].append(line[1:].strip())
                elif current_section == "targets" and line.startswith("Id"):
                    continue  # Skip header
                elif current_section == "targets" and line[0].isdigit():
                    info["targets"].append(line)
        
        return info
    
    def _parse_options(self, output: str) -> Dict[str, Any]:
        """Parse module options output"""
        options = {
            "module_options": [],
            "payload_options": [],
            "advanced_options": []
        }
        
        lines = output.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if "Module options" in line:
                current_section = "module_options"
            elif "Payload options" in line:
                current_section = "payload_options"
            elif "Advanced options" in line:
                current_section = "advanced_options"
            elif current_section and line and not line.startswith("=") and not line.startswith("-"):
                # Parse option line
                parts = line.split()
                if len(parts) >= 4:
                    option = {
                        "name": parts[0],
                        "current_setting": parts[1] if parts[1] != "no" else "",
                        "required": parts[2] == "yes",
                        "description": " ".join(parts[3:])
                    }
                    options[current_section].append(option)
        
        return options
    
    def _extract_session_info(self, output: str) -> Optional[Dict[str, Any]]:
        """Extract session information from exploit output"""
        session_info = None
        
        # Look for session creation messages
        if "session" in output.lower():
            lines = output.split('\n')
            for line in lines:
                if "session" in line.lower() and "opened" in line.lower():
                    # Extract session ID
                    match = re.search(r'session (\d+) opened', line, re.IGNORECASE)
                    if match:
                        session_info = {
                            "id": int(match.group(1)),
                            "type": "meterpreter" if "meterpreter" in line.lower() else "shell"
                        }
                        break
        
        return session_info
    
    def _parse_check_result(self, output: str) -> Dict[str, Any]:
        """Parse check command result"""
        result = {
            "vulnerable": False,
            "status": "unknown",
            "details": ""
        }
        
        output_lower = output.lower()
        
        if "vulnerable" in output_lower:
            result["vulnerable"] = True
            result["status"] = "vulnerable"
        elif "not vulnerable" in output_lower:
            result["vulnerable"] = False
            result["status"] = "safe"
        elif "detected" in output_lower:
            result["status"] = "detected"
        elif "unknown" in output_lower:
            result["status"] = "unknown"
        
        result["details"] = output.strip()
        
        return result
    
    def _parse_sessions(self, output: str) -> List[Dict[str, Any]]:
        """Parse sessions list output"""
        sessions = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip headers and empty lines
            if not line or line.startswith("Active sessions") or line.startswith("=") or line.startswith("Id"):
                continue
            
            # Parse session line
            parts = line.split()
            if len(parts) >= 5 and parts[0].isdigit():
                session = {
                    "id": int(parts[0]),
                    "type": parts[1],
                    "info": parts[2],
                    "connection": " ".join(parts[3:])
                }
                sessions.append(session)
        
        return sessions
    
    def _build_filter_args(self, filters: Dict[str, Any]) -> str:
        """Build filter arguments for database commands"""
        args = []
        
        if "address" in filters:
            args.append(f"-a {filters['address']}")
        if "port" in filters:
            args.append(f"-p {filters['port']}")
        if "service" in filters:
            args.append(f"-s {filters['service']}")
        if "host" in filters:
            args.append(f"-h {filters['host']}")
        
        return " ".join(args)
    
    def _build_add_command(self, table: str, data: Dict[str, Any]) -> str:
        """Build add command for database tables"""
        if table == "hosts":
            cmd = f"hosts -a {data.get('address', '')}"
            if "name" in data:
                cmd += f" -n {data['name']}"
            if "os" in data:
                cmd += f" -o {data['os']}"
            return cmd
        elif table == "services":
            return f"services -a -p {data.get('port', '')} -r {data.get('proto', 'tcp')} {data.get('host', '')}"
        elif table == "creds":
            return f"creds add user:{data.get('user', '')} password:{data.get('password', '')} host:{data.get('host', '')}"
        else:
            return ""
    
    def _parse_database_output(self, table: str, output: str) -> List[Dict[str, Any]]:
        """Parse database table output"""
        items = []
        
        lines = output.split('\n')
        headers = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and separators
            if not line or line.startswith("="):
                continue
            
            # Parse headers
            if line.startswith("address") or line.startswith("host") or line.startswith("port"):
                headers = line.split()
                continue
            
            # Parse data lines
            if headers and line:
                parts = line.split()
                if len(parts) >= len(headers):
                    item = {}
                    for i, header in enumerate(headers):
                        if i < len(parts):
                            item[header] = parts[i]
                    items.append(item)
        
        return items
    
    def _parse_post_module_output(self, module: str, output: str) -> Dict[str, Any]:
        """Parse post-exploitation module output"""
        results = {
            "success": True,
            "data": [],
            "raw_output": output
        }
        
        # Parse based on module type
        if "enum_files" in module:
            # Parse file enumeration
            lines = output.split('\n')
            for line in lines:
                if line.strip() and "/" in line:
                    results["data"].append({"file": line.strip()})
        elif "screen_spy" in module:
            # Parse screenshot info
            if "Screenshot saved" in output:
                results["data"].append({"screenshot": "saved"})
        elif "credential" in module.lower():
            # Parse credentials
            if "Username" in output and "Password" in output:
                results["data"].append({"credentials": "found"})
        
        return results
    
    def _extract_job_id(self, output: str) -> Optional[int]:
        """Extract job ID from handler output"""
        match = re.search(r'Job (\d+)', output)
        if match:
            return int(match.group(1))
        return None
    
    def _parse_jobs(self, output: str) -> List[Dict[str, Any]]:
        """Parse jobs list output"""
        jobs = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip headers
            if not line or line.startswith("Jobs") or line.startswith("=") or line.startswith("Id"):
                continue
            
            # Parse job line
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit():
                job = {
                    "id": int(parts[0]),
                    "name": " ".join(parts[1:])
                }
                jobs.append(job)
        
        return jobs
    
    def _parse_scan_output(self, scan_type: str, output: str) -> List[Dict[str, Any]]:
        """Parse scanner output based on scan type"""
        results = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Parse based on scan type
            if scan_type == "port":
                if "open" in line.lower():
                    parts = line.split()
                    if len(parts) >= 3:
                        results.append({
                            "host": parts[0],
                            "port": parts[1],
                            "state": "open"
                        })
            elif scan_type in ["smb", "http", "ssh", "ftp"]:
                if "detected" in line.lower() or "version" in line.lower():
                    results.append({"service": scan_type, "info": line})
            elif scan_type == "discovery":
                if "host" in line.lower() and "up" in line.lower():
                    parts = line.split()
                    if parts:
                        results.append({"host": parts[0], "status": "up"})
        
        return results
    
    def _parse_credentials(self, output: str) -> List[Dict[str, Any]]:
        """Parse credentials output"""
        creds = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip headers and empty lines
            if not line or line.startswith("Credentials") or line.startswith("=") or line.startswith("host"):
                continue
            
            # Parse credential line
            parts = line.split()
            if len(parts) >= 4:
                cred = {
                    "host": parts[0],
                    "service": parts[1],
                    "username": parts[2],
                    "password": parts[3] if len(parts) > 3 else "",
                    "type": parts[4] if len(parts) > 4 else "password"
                }
                creds.append(cred)
        
        return creds
    
    def _parse_routes(self, output: str) -> List[Dict[str, Any]]:
        """Parse routes output"""
        routes = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip headers
            if not line or line.startswith("IPv4 Active Routing") or line.startswith("=") or line.startswith("Subnet"):
                continue
            
            # Parse route line
            parts = line.split()
            if len(parts) >= 3:
                route = {
                    "subnet": parts[0],
                    "netmask": parts[1],
                    "gateway": parts[2]
                }
                routes.append(route)
        
        return routes
    
    def _parse_loot(self, output: str) -> List[Dict[str, Any]]:
        """Parse loot output"""
        loot_items = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip headers
            if not line or line.startswith("Loot") or line.startswith("=") or line.startswith("host"):
                continue
            
            # Parse loot line
            parts = line.split()
            if len(parts) >= 4:
                loot = {
                    "host": parts[0],
                    "service": parts[1],
                    "type": parts[2],
                    "path": parts[3] if len(parts) > 3 else ""
                }
                loot_items.append(loot)
        
        return loot_items
    
    def _parse_vulnerabilities(self, output: str) -> List[Dict[str, Any]]:
        """Parse vulnerabilities output"""
        vulns = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip headers
            if not line or line.startswith("Vulnerabilities") or line.startswith("=") or line.startswith("Timestamp"):
                continue
            
            # Parse vulnerability line
            parts = line.split()
            if len(parts) >= 4:
                vuln = {
                    "host": parts[1] if len(parts) > 1 else "",
                    "name": parts[2] if len(parts) > 2 else "",
                    "references": parts[3] if len(parts) > 3 else ""
                }
                vulns.append(vuln)
        
        return vulns
    
    def _count_by_severity(self, vulns: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count vulnerabilities by severity"""
        severity_count = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for vuln in vulns:
            # Simple severity classification based on name
            name = vuln.get("name", "").lower()
            if "critical" in name or "rce" in name:
                severity_count["critical"] += 1
            elif "high" in name or "exploit" in name:
                severity_count["high"] += 1
            elif "medium" in name:
                severity_count["medium"] += 1
            elif "low" in name:
                severity_count["low"] += 1
            else:
                severity_count["info"] += 1
        
        return severity_count
    
    def _count_by_service(self, vulns: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count vulnerabilities by service"""
        service_count = {}
        
        for vuln in vulns:
            # Extract service from vulnerability name
            name = vuln.get("name", "")
            for service in ["smb", "http", "ssh", "ftp", "mysql", "postgres", "rdp"]:
                if service in name.lower():
                    service_count[service] = service_count.get(service, 0) + 1
                    break
        
        return service_count
    
    def _build_exploitation_timeline(self, sessions_data: Dict, loot_data: Dict) -> List[Dict[str, Any]]:
        """Build exploitation timeline"""
        timeline = []
        
        # Add session events
        if sessions_data and "sessions" in sessions_data:
            for session in sessions_data["sessions"]:
                timeline.append({
                    "timestamp": "N/A",  # Would need actual timestamps
                    "event": "session_opened",
                    "details": f"Session {session['id']} opened ({session['type']})"
                })
        
        # Add loot events
        if loot_data and "loot" in loot_data:
            for loot in loot_data["loot"]:
                timeline.append({
                    "timestamp": "N/A",
                    "event": "loot_collected",
                    "details": f"Collected {loot['type']} from {loot['host']}"
                })
        
        return timeline
    
    def _calculate_risk_score(self, vulns_data: Dict) -> Dict[str, Any]:
        """Calculate overall risk score"""
        if not vulns_data or "vulnerabilities" not in vulns_data:
            return {"score": 0, "level": "low"}
        
        vulns = vulns_data["vulnerabilities"]
        severity_count = self._count_by_severity(vulns)
        
        # Simple risk calculation
        score = (
            severity_count["critical"] * 10 +
            severity_count["high"] * 5 +
            severity_count["medium"] * 3 +
            severity_count["low"] * 1
        )
        
        # Determine risk level
        if score >= 50:
            level = "critical"
        elif score >= 30:
            level = "high"
        elif score >= 15:
            level = "medium"
        else:
            level = "low"
        
        return {
            "score": score,
            "level": level,
            "breakdown": severity_count
        }
    
    def _generate_recommendations(self, vulns_data: Dict) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if not vulns_data or "vulnerabilities" not in vulns_data:
            return ["Perform comprehensive vulnerability assessment"]
        
        vulns = vulns_data["vulnerabilities"]
        severity_count = self._count_by_severity(vulns)
        
        if severity_count["critical"] > 0:
            recommendations.append(f"URGENT: Patch {severity_count['critical']} critical vulnerabilities immediately")
        
        if severity_count["high"] > 0:
            recommendations.append(f"HIGH PRIORITY: Address {severity_count['high']} high-severity vulnerabilities")
        
        # Service-specific recommendations
        service_count = self._count_by_service(vulns)
        for service, count in service_count.items():
            if count > 0:
                recommendations.append(f"Review and harden {service.upper()} service configuration ({count} vulnerabilities)")
        
        recommendations.append("Implement regular vulnerability scanning schedule")
        recommendations.append("Establish patch management process")
        
        return recommendations
    
    def _format_report(self, report_data: Dict, format: str) -> Union[str, Dict]:
        """Format report based on requested format"""
        if format == "json":
            return report_data
        elif format == "text":
            # Convert to text format
            text = f"Report Type: {report_data['type']}\n"
            text += f"Generated: {report_data['timestamp']}\n"
            text += "=" * 50 + "\n"
            text += json.dumps(report_data['data'], indent=2)
            return text
        elif format == "xml":
            # Simple XML conversion
            xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml += f'<report type="{report_data["type"]}" timestamp="{report_data["timestamp"]}">\n'
            xml += '  <data>\n'
            # Would need proper XML serialization
            xml += f'    {json.dumps(report_data["data"])}\n'
            xml += '  </data>\n'
            xml += '</report>'
            return xml
        else:
            # Default to JSON
            return report_data
    
    def _parse_plugins(self, output: str) -> List[Dict[str, Any]]:
        """Parse loaded plugins output"""
        plugins = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip headers and empty lines
            if not line or line.startswith("Loaded plugins") or line.startswith("="):
                continue
            
            # Parse plugin line
            if line:
                plugins.append({
                    "name": line,
                    "loaded": True
                })
        
        return plugins
    
    def _get_plugin_info(self, plugin_name: str) -> Dict[str, str]:
        """Get plugin information"""
        # Plugin descriptions
        plugin_info = {
            "nessus": "Nessus vulnerability scanner integration",
            "nexpose": "Rapid7 Nexpose vulnerability management",
            "openvas": "OpenVAS vulnerability scanner integration",
            "nmap": "Nmap network scanner integration",
            "sqlmap": "SQL injection testing integration",
            "wmap": "Web application scanner",
            "db_tracker": "Track database changes",
            "session_notifier": "Notify on new sessions",
            "sounds": "Audio notifications for events",
            "msgrpc": "MessagePack RPC service"
        }
        
        return {
            "description": plugin_info.get(plugin_name, "Plugin for enhanced functionality"),
            "status": "available"
        }


# Testing the implementation
if __name__ == "__main__":
    async def test_extended_tools():
        """Test the extended tools implementation"""
        tools = MSFExtendedTools()
        
        # Initialize
        print("Initializing MSF Extended Tools...")
        init_result = await tools.initialize()
        print(f"Initialization: {init_result.status.value}")
        
        if init_result.status == OperationStatus.SUCCESS:
            # Test module manager
            print("\n1. Testing Module Manager...")
            module_result = await tools.msf_module_manager(
                action="info",
                module_path="exploit/windows/smb/ms17_010_eternalblue"
            )
            print(f"Module info: {module_result.status.value}")
            
            # Test session interact
            print("\n2. Testing Session Interact...")
            session_result = await tools.msf_session_interact(action="list")
            print(f"Sessions: {session_result.data}")
            
            # Clean up
            await tools.cleanup()
            print("\nTests completed!")
    
    # Run tests
    # asyncio.run(test_extended_tools())