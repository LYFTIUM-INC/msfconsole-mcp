#!/usr/bin/env python3

"""
MSFConsole Stable Integration
----------------------------
Reliability-focused MSFConsole integration with gradual performance enhancements.
Priority: Stability (95%+ success rate) > Performance gains.
"""

import asyncio
import logging
import time
import subprocess
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import psutil
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OperationStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


@dataclass
class OperationResult:
    status: OperationStatus
    data: Any
    execution_time: float
    error: Optional[str] = None
    warnings: List[str] = None


class MSFConsoleStableWrapper:
    """Stable, reliable MSFConsole wrapper with enhanced error handling."""

    def __init__(self):
        self.session_active = False
        self.initialization_status = "not_started"
        self.performance_stats = {
            "operations_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "total_execution_time": 0.0,
        }
        self.config = self._load_stable_config()
        self.process_monitor = None

    def _load_stable_config(self) -> Dict[str, Any]:
        """Load stability-focused configuration."""
        return {
            "timeouts": {
                "initialization": 60.0,
                "command_execution": 30.0,
                "payload_generation": 90.0,
                "module_search": 60.0,
                "cleanup": 10.0,
            },
            "retry_settings": {"max_retries": 3, "retry_delay": 2.0, "backoff_multiplier": 1.5},
            "stability_features": {
                "pre_validation": True,
                "post_validation": True,
                "graceful_degradation": True,
                "resource_monitoring": True,
                "automatic_recovery": True,
            },
            "process_settings": {
                "nice_priority": 10,
                "memory_limit_mb": 1024,
                "cpu_limit_percent": 50,
            },
        }

    async def initialize(self) -> OperationResult:
        start_time = time.time()
        self.initialization_status = "in_progress"

        try:
            logger.info("Initializing MSFConsole with stability focus...")

            if not await self._pre_initialization_checks():
                return OperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error="Pre-initialization checks failed",
                )

            initialization_attempts = [
                self._attempt_standard_initialization,
                self._attempt_minimal_initialization,
                self._attempt_offline_initialization,
            ]

            for attempt_num, init_method in enumerate(initialization_attempts, 1):
                logger.info(f"Initialization attempt {attempt_num}/3...")

                try:
                    result = await asyncio.wait_for(
                        init_method(), timeout=self.config["timeouts"]["initialization"]
                    )

                    if result:
                        self.initialization_status = "completed"
                        self.session_active = True
                        logger.info(f"MSFConsole initialized successfully (attempt {attempt_num})")

                        return OperationResult(
                            status=OperationStatus.SUCCESS,
                            data={
                                "initialization_method": init_method.__name__,
                                "attempt": attempt_num,
                            },
                            execution_time=time.time() - start_time,
                        )

                except asyncio.TimeoutError:
                    logger.warning(f"Initialization attempt {attempt_num} timed out")
                    continue
                except Exception as e:
                    logger.warning(f"Initialization attempt {attempt_num} failed: {e}")
                    continue

            self.initialization_status = "failed"
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error="All initialization attempts failed",
            )

        except Exception as e:
            self.initialization_status = "error"
            logger.error(f"Critical initialization error: {e}")
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Critical error: {str(e)}",
            )

    async def _pre_initialization_checks(self) -> bool:
        logger.debug("Performing pre-initialization checks...")

        checks = [
            ("MSFConsole binary available", self._check_msfconsole_binary),
            ("System resources adequate", self._check_system_resources),
            ("Required directories accessible", self._check_directories),
            ("Network connectivity", self._check_network_connectivity),
        ]

        all_passed = True
        for check_name, check_func in checks:
            try:
                if await check_func():
                    logger.debug(f"✓ {check_name}")
                else:
                    logger.warning(f"✗ {check_name}")
                    all_passed = False
            except Exception as e:
                logger.warning(f"✗ {check_name}: {e}")
                all_passed = False

        return all_passed

    async def _check_msfconsole_binary(self) -> bool:
        try:
            result = subprocess.run(
                ["which", "msfconsole"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    async def _check_system_resources(self) -> bool:
        try:
            memory = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            return memory.available > 2 * 1024 * 1024 * 1024 and cpu_count >= 2
        except Exception:
            return False

    async def _check_directories(self) -> bool:
        try:
            home_dir = Path.home()
            msf_dirs = [
                home_dir / ".msf4",
                Path("/usr/share/metasploit-framework"),
                Path("/opt/metasploit-framework"),
            ]
            return any(path.exists() and path.is_dir() for path in msf_dirs)
        except Exception:
            return False

    async def _check_network_connectivity(self) -> bool:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "3", "8.8.8.8"], capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return True

    async def _attempt_standard_initialization(self) -> bool:
        try:
            logger.debug("Attempting standard initialization...")
            result = subprocess.run(
                ["msfconsole", "--version"], capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                db_result = subprocess.run(
                    ["msfconsole", "-q", "-x", "db_status; exit"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                return db_result.returncode == 0
            return False
        except subprocess.TimeoutExpired:
            logger.warning("Standard initialization timed out")
            return False
        except Exception as e:
            logger.warning(f"Standard initialization failed: {e}")
            return False

    async def _attempt_minimal_initialization(self) -> bool:
        try:
            logger.debug("Attempting minimal initialization...")
            result = subprocess.run(
                ["msfconsole", "-h"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0 and "Usage:" in result.stdout
        except Exception as e:
            logger.warning(f"Minimal initialization failed: {e}")
            return False

    async def _attempt_offline_initialization(self) -> bool:
        try:
            logger.debug("Attempting offline initialization...")
            result = subprocess.run(
                ["msfvenom", "--list", "platforms"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0 and len(result.stdout) > 0
        except Exception as e:
            logger.warning(f"Offline initialization failed: {e}")
            return False

    def _should_paginate_command_output(self, command: str, output: str) -> bool:
        large_output_commands = ["help", "show", "search", "info", "options"]
        for cmd in large_output_commands:
            if cmd in command.lower():
                if len(output) > 10000:
                    return True
        return False

    def _paginate_text_output(self, output: str, max_length: int = 15000) -> Dict[str, Any]:
        if len(output) <= max_length:
            return {"output": output, "truncated": False, "total_length": len(output)}
        truncated_output = output[:max_length]
        last_newline = truncated_output.rfind("\n")
        if last_newline > max_length * 0.8:
            truncated_output = truncated_output[:last_newline]
        return {
            "output": truncated_output,
            "truncated": True,
            "total_length": len(output),
            "showing_length": len(truncated_output),
            "truncation_note": f"Output truncated. Showing {len(truncated_output)} of {len(output)} characters. Use more specific commands to get complete results.",
        }

    async def execute_command(
        self, command: str, timeout: Optional[float] = None
    ) -> OperationResult:
        if not self.session_active:
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=0,
                error="MSFConsole not initialized",
            )
        start_time = time.time()
        timeout = timeout or self.config["timeouts"]["command_execution"]
        self.performance_stats["operations_count"] += 1
        try:
            if not self._validate_command(command):
                self.performance_stats["failure_count"] += 1
                return OperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error="Command validation failed",
                )
            for attempt in range(self.config["retry_settings"]["max_retries"]):
                try:
                    logger.debug(f"Executing command (attempt {attempt + 1}): {command}")
                    result = await self._execute_with_timeout(command, timeout)
                    if self._validate_result(result):
                        execution_time = time.time() - start_time
                        self.performance_stats["success_count"] += 1
                        self.performance_stats["total_execution_time"] += execution_time
                        return OperationResult(
                            status=OperationStatus.SUCCESS,
                            data=result,
                            execution_time=execution_time,
                        )
                    else:
                        logger.warning(f"Result validation failed for: {command}")
                except asyncio.TimeoutError:
                    logger.warning(f"Command timeout (attempt {attempt + 1}): {command}")
                    if attempt == self.config["retry_settings"]["max_retries"] - 1:
                        self.performance_stats["failure_count"] += 1
                        return OperationResult(
                            status=OperationStatus.TIMEOUT,
                            data=None,
                            execution_time=time.time() - start_time,
                            error=f"Command timed out after {timeout}s",
                        )
                if attempt < self.config["retry_settings"]["max_retries"] - 1:
                    delay = self.config["retry_settings"]["retry_delay"] * (
                        self.config["retry_settings"]["backoff_multiplier"] ** attempt
                    )
                    await asyncio.sleep(delay)
            self.performance_stats["failure_count"] += 1
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error="All retry attempts failed",
            )
        except Exception as e:
            self.performance_stats["failure_count"] += 1
            logger.error(f"Command execution error: {e}")
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Execution error: {str(e)}",
            )

    def _validate_command(self, command: str) -> bool:
        if not command or not command.strip():
            return False
        dangerous_commands = ["rm -rf", "del /", "format c:", "shutdown", "reboot", "killall"]
        command_lower = command.lower()
        if any(dangerous in command_lower for dangerous in dangerous_commands):
            logger.warning(f"Potentially dangerous command blocked: {command}")
            return False
        return True

    def _validate_result(self, result: Dict[str, Any]) -> bool:
        if not isinstance(result, dict):
            return False
        if result.get("returncode", 0) != 0:
            stderr = result.get("stderr", "")
            if "fatal" in stderr.lower() or "critical" in stderr.lower():
                return False
        return True

    async def _execute_with_timeout(self, command: str, timeout: float) -> Dict[str, Any]:
        full_command = ["msfconsole", "-q", "-x", f"{command}; exit"]
        env = os.environ.copy()
        env.update({"MSF_DATABASE_CONFIG": "/dev/null", "LANG": "en_US.UTF-8"})
        process = await asyncio.create_subprocess_exec(
            *full_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": process.returncode,
            }
        except asyncio.TimeoutError:
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            raise

    async def generate_payload(
        self,
        payload: str,
        options: Dict[str, str],
        output_format: str = "raw",
        encoder: Optional[str] = None,
    ) -> OperationResult:
        start_time = time.time()
        timeout = self.config["timeouts"]["payload_generation"]
        try:
            cmd = ["msfvenom", "-p", payload]
            for key, value in options.items():
                cmd.extend([f"{key}={value}"])
            cmd.extend(["-f", output_format])
            if encoder:
                cmd.extend(["-e", encoder])
            logger.debug(f"Generating payload: {' '.join(cmd)}")
            for attempt in range(3):
                try:
                    process = await asyncio.create_subprocess_exec(
                        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                    if process.returncode == 0 and stdout:
                        return OperationResult(
                            status=OperationStatus.SUCCESS,
                            data={
                                "payload_data": stdout.decode("utf-8", errors="replace"),
                                "size_bytes": len(stdout),
                                "format": output_format,
                                "encoder": encoder,
                            },
                            execution_time=time.time() - start_time,
                        )
                    else:
                        logger.warning(f"Payload generation attempt {attempt + 1} failed")
                        if attempt < 2:
                            await asyncio.sleep(2)
                except asyncio.TimeoutError:
                    logger.warning(f"Payload generation timeout (attempt {attempt + 1})")
                    if attempt < 2:
                        await asyncio.sleep(2)
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error="Payload generation failed after 3 attempts",
            )
        except Exception as e:
            logger.error(f"Payload generation error: {e}")
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Generation error: {str(e)}",
            )

    def get_adaptive_search_timeout(self, query: str, limit: int = 25) -> float:
        base_timeout = self.config["timeouts"]["module_search"]
        complexity_factors = 0
        if "platform:" in query:
            complexity_factors += 1
        if "type:" in query:
            complexity_factors += 0.5
        if limit > 100:
            complexity_factors += 1
        criteria_count = query.count(":") + query.count("AND") + query.count("OR")
        complexity_factors += criteria_count * 0.3
        adaptive_timeout = base_timeout + (complexity_factors * 15)
        return min(adaptive_timeout, 120.0)

    async def _handle_search_timeout(self, query: str, execution_time: float) -> Dict[str, Any]:
        logger.warning(f"Search timeout for query '{query}' after {execution_time:.1f}s")
        suggestions = []
        if "platform:" in query and "type:" in query:
            suggestions.append("Try searching with only platform or type filter")
        if len(query.split()) > 3:
            suggestions.append("Try using more specific search terms")
        return {
            "status": "timeout",
            "execution_time": execution_time,
            "search_results": None,
            "error": f"Search timed out after {execution_time:.1f}s",
            "suggestions": suggestions,
            "success": False,
        }

    def _apply_smart_result_limiting(
        self, modules: List[Dict[str, Any]], limit: int, target_tokens: int = 20000
    ) -> Tuple[List[Dict[str, Any]], bool]:
        if not modules:
            return modules, False
        current_limit = min(limit, len(modules))
        while current_limit > 0:
            limited_modules = modules[:current_limit]
            estimated_tokens = self._estimate_response_tokens(limited_modules)
            if estimated_tokens <= target_tokens:
                break
            current_limit = max(1, int(current_limit * 0.8))
        final_modules = modules[:current_limit]
        was_limited = current_limit < limit
        if was_limited:
            print(
                f"Smart limiting: Reduced from {limit} to {current_limit} results (estimated {self._estimate_response_tokens(final_modules)} tokens)"
            )
        return final_modules, was_limited

    async def search_modules(self, query: str, limit: int = 25, page: int = 1) -> OperationResult:
        start_time = time.time()
        try:
            if limit > 50:
                limit = 50
                logger.info(f"Reduced limit to {limit} to prevent token overflow")
            search_command = f"search {query}"
            adaptive_timeout = self.get_adaptive_search_timeout(query, limit)
            logger.info(f"Using adaptive search timeout: {adaptive_timeout}s for query: '{query}'")
            result = await self.execute_command(search_command, timeout=adaptive_timeout)
            if result.status == OperationStatus.SUCCESS:
                all_modules = self._parse_search_output_full(result.data["stdout"])
                total_count = len(all_modules)
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                paginated_modules = all_modules[start_idx:end_idx]
                final_modules, was_limited = self._apply_smart_result_limiting(
                    paginated_modules, len(paginated_modules)
                )
                total_pages = (total_count + limit - 1) // limit
                estimated_tokens = self._estimate_response_tokens(final_modules)
                return OperationResult(
                    status=OperationStatus.SUCCESS,
                    data={
                        "query": query,
                        "modules": final_modules,
                        "pagination": {
                            "current_page": page,
                            "total_pages": total_pages,
                            "page_size": limit,
                            "total_count": total_count,
                            "has_next": page < total_pages,
                            "has_previous": page > 1,
                            "token_limit_applied": was_limited,
                            "final_result_count": len(final_modules),
                            "estimated_tokens": estimated_tokens,
                        },
                        "search_tips": {
                            "narrow_search": "Use more specific terms to reduce results",
                            "pagination": f"Use page parameter (1-{total_pages}) to navigate",
                            "examples": [
                                "exploit platform:windows type:local",
                                "auxiliary scanner",
                                "post gather platform:linux",
                            ],
                        },
                    },
                    execution_time=time.time() - start_time,
                )
            else:
                return result
        except Exception as e:
            logger.error(f"Module search error: {e}")
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Search error: {str(e)}",
            )

    def _estimate_response_tokens(self, modules: List[Dict[str, Any]]) -> int:
        if not modules:
            return 500
        total_chars = 0
        base_overhead = 1000
        for module in modules:
            module_chars = 0
            module_chars += len(module.get("name", "")) + 20
            module_chars += len(module.get("description", "")) + 20
            module_chars += len(module.get("type", "")) + 20
            module_chars += 50
            total_chars += module_chars
        metadata_overhead = 800
        total_chars += base_overhead + metadata_overhead
        estimated_tokens = total_chars // 3
        return estimated_tokens

    def _parse_search_output_full(self, output: str) -> List[Dict[str, Any]]:
        import re

        modules = []
        if "\n" in output:
            output = output.replace("\n", "\n")
        ansi_escape = re.compile(
            r"\x1b\[[0-9;]*[mGK]|\033\[[0-9;]*[mGK]|\[\d+[mGK]|\[45m|\[0m|\[32m"
        )
        clean_output = ansi_escape.sub("", output)
        lines = clean_output.split("\n")
        for line in lines:
            line = line.strip()
            if (
                not line
                or line.startswith("=")
                or line.startswith("[")
                or "Matching" in line
                or line.startswith("#")
                or line.startswith("-")
            ):
                continue
            if "Interact with a module" in line or "After interacting" in line:
                continue
            match = re.match(
                r"^\s*(\d+)\s+(\w+/[^\s]+)\s+(\S+|\.)\s+(\S+)\s+(Yes|No)\s+(.*)$", line
            )
            if match:
                index = match.group(1)
                module_name = match.group(2).strip()
                date = match.group(3)
                rank = match.group(4)
                check = match.group(5)
                description = match.group(6).strip()
                if "/" in module_name and module_name.count("/") >= 2:
                    if not (line.strip().startswith("\\_") or "target:" in line):
                        if len(description) > 80:
                            description = description[:80] + "..."
                        module_entry = {
                            "name": module_name,
                            "description": description,
                            "type": self._extract_module_type(module_name),
                            "index": int(index),
                            "rank": rank,
                            "check": check,
                        }
                        if date and date != ".":
                            module_entry["disclosure_date"] = date
                        modules.append(module_entry)
        if not modules:
            print("No modules found with strict parsing, trying lenient approach...")
            for line in lines:
                line = line.strip()
                if (
                    "exploit/" in line or "auxiliary/" in line or "post/" in line
                ) and not line.startswith("\\_"):
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "/" in part and (
                            "exploit" in part or "auxiliary" in part or "post" in part
                        ):
                            module_name = part
                            desc_parts = parts[i + 4 :] if len(parts) > i + 4 else []
                            description = (
                                " ".join(desc_parts)[:80] + "..."
                                if len(" ".join(desc_parts)) > 80
                                else " ".join(desc_parts)
                            )
                            if not description:
                                description = "No description available"
                            modules.append(
                                {
                                    "name": module_name,
                                    "description": description,
                                    "type": self._extract_module_type(module_name),
                                    "index": len(modules),
                                }
                            )
                            break
        return modules

    def _parse_search_output(self, output: str, limit: int) -> List[Dict[str, Any]]:
        all_modules = self._parse_search_output_full(output)
        return all_modules[:limit]

    def _extract_module_type(self, module_name: str) -> str:
        if "/" not in module_name:
            return "unknown"
        type_part = module_name.split("/")[0]
        return (
            type_part
            if type_part in ["exploit", "auxiliary", "post", "payload", "encoder", "nop"]
            else "unknown"
        )

    def get_status(self) -> Dict[str, Any]:
        success_rate = 0
        if self.performance_stats["operations_count"] > 0:
            success_rate = (
                self.performance_stats["success_count"] / self.performance_stats["operations_count"]
            )
        avg_execution_time = 0
        if self.performance_stats["success_count"] > 0:
            avg_execution_time = (
                self.performance_stats["total_execution_time"]
                / self.performance_stats["success_count"]
            )
        return {
            "initialization_status": self.initialization_status,
            "session_active": self.session_active,
            "performance_stats": {
                **self.performance_stats,
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
            },
            "system_resources": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "process_memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            },
            "stability_rating": self._calculate_stability_rating(),
        }

    def _calculate_stability_rating(self) -> int:
        if self.performance_stats["operations_count"] == 0:
            return 10 if self.initialization_status == "completed" else 5
        success_rate = (
            self.performance_stats["success_count"] / self.performance_stats["operations_count"]
        )
        if success_rate >= 0.95:
            return 10
        elif success_rate >= 0.90:
            return 9
        elif success_rate >= 0.80:
            return 8
        elif success_rate >= 0.70:
            return 7
        elif success_rate >= 0.60:
            return 6
        elif success_rate >= 0.50:
            return 5
        else:
            return max(1, int(success_rate * 10))

    async def cleanup(self):
        logger.info("Cleaning up MSFConsole integration...")
        try:
            if self.process_monitor:
                self.process_monitor.stop()
            self.session_active = False
            self.initialization_status = "cleanup"
            status = self.get_status()
            logger.info(f"Final stability rating: {status['stability_rating']}/10")
            logger.info(f"Total operations: {status['performance_stats']['operations_count']}")
            logger.info(f"Success rate: {status['performance_stats']['success_rate']:.1%}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def create_stable_msf_console() -> MSFConsoleStableWrapper:
    return MSFConsoleStableWrapper()
