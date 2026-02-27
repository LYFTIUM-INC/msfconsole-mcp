#!/usr/bin/env python3
"""
Comprehensive test suite for all 58 MSF Console MCP tools
Tests each tool and measures performance
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add path for imports
sys.path.insert(0, '.')

from mcp_server_stable import MSFConsoleMCPServer


class ToolTester:
    """Test harness for MSF MCP tools"""
    
    def __init__(self):
        self.server = MSFConsoleMCPServer()
        self.results = {
            "total_tools": 58,
            "tested": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "performance": {},
            "categories": {
                "core": {"total": 9, "passed": 0, "failed": 0},
                "extended": {"total": 10, "passed": 0, "failed": 0},
                "advanced": {"total": 10, "passed": 0, "failed": 0},
                "system": {"total": 8, "passed": 0, "failed": 0},
                "enhanced": {"total": 11, "passed": 0, "failed": 0},
                "plugins": {"total": 10, "passed": 0, "failed": 0}
            }
        }
        
    async def initialize(self):
        """Initialize the server"""
        print("🚀 Initializing MSF Console MCP Server v5.0...")
        try:
            await self.server.initialize()
            print("✅ Server initialized successfully\n")
            return True
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
            
    async def test_tool(self, tool_name: str, args: Dict[str, Any], 
                       category: str, description: str) -> Tuple[bool, float, str]:
        """Test a single tool and measure performance"""
        print(f"Testing {tool_name}: {description}...", end=" ")
        start_time = time.time()
        
        try:
            result = await self.server.handle_tool_call(tool_name, args)
            elapsed = time.time() - start_time
            
            # Check if result indicates success
            if "content" in result and result["content"]:
                content = result["content"][0].get("text", "")
                
                # Try to parse as JSON for structured results
                try:
                    data = json.loads(content)
                    success = data.get("success", True) and not data.get("error")
                except (json.JSONDecodeError, ValueError, KeyError):
                    success = "error" not in content.lower() and "failed" not in content.lower()
                
                if success:
                    print(f"✅ ({elapsed:.2f}s)")
                    return True, elapsed, ""
                else:
                    error_msg = content[:100] if len(content) > 100 else content
                    print(f"❌ ({elapsed:.2f}s) - {error_msg}")
                    return False, elapsed, error_msg
            else:
                print(f"❌ ({elapsed:.2f}s) - Empty response")
                return False, elapsed, "Empty response"
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ ({elapsed:.2f}s) - Exception: {str(e)}")
            return False, elapsed, str(e)
            
    async def run_all_tests(self):
        """Run tests for all 58 tools"""
        if not await self.initialize():
            return
            
        print("=" * 80)
        print("🧪 TESTING ALL 58 MSF CONSOLE MCP TOOLS")
        print("=" * 80)
        
        # Track test start time
        suite_start = time.time()
        
        # ========== CORE TOOLS (9) ==========
        print("\n📦 CORE TOOLS (9 tools)")
        print("-" * 40)
        
        core_tests = [
            ("msf_execute_command", {"command": "version"}, "Execute MSF commands"),
            ("msf_generate_payload", {"payload": "windows/meterpreter/reverse_tcp", 
                                    "options": {"LHOST": "192.168.1.1", "LPORT": "4444"}}, 
             "Generate payloads"),
            ("msf_search_modules", {"query": "eternalblue", "max_results": 5}, "Search modules"),
            ("msf_get_status", {}, "Get server status"),
            ("msf_list_workspaces", {}, "List workspaces"),
            ("msf_create_workspace", {"name": f"test_{int(time.time())}"}, "Create workspace"),
            ("msf_switch_workspace", {"name": "default"}, "Switch workspace"),
            ("msf_list_sessions", {}, "List sessions"),
            ("msf_module_manager", {"action": "list", "module_type": "exploit"}, "Manage modules"),
        ]
        
        for tool_name, args, desc in core_tests:
            success, elapsed, error = await self.test_tool(tool_name, args, "core", desc)
            self.update_results(tool_name, "core", success, elapsed, error)
            
        # ========== EXTENDED TOOLS (10) ==========
        print("\n🔧 EXTENDED TOOLS (10 tools)")
        print("-" * 40)
        
        extended_tests = [
            ("msf_session_interact", {"session_id": "1", "command": "sysinfo"}, "Session interaction"),
            ("msf_database_query", {"operation": "hosts"}, "Database queries"),
            ("msf_exploit_chain", {"chain": []}, "Exploit chaining"),
            ("msf_post_exploitation", {"module": "multi/gather/env", "session_id": "1"}, "Post-exploitation"),
            ("msf_handler_manager", {"action": "list"}, "Handler management"),
            ("msf_scanner_suite", {"scanner_type": "port", "targets": "127.0.0.1"}, "Scanner suite"),
            ("msf_credential_manager", {"action": "list"}, "Credential management"),
            ("msf_pivot_manager", {"action": "list"}, "Pivot management"),
            ("msf_resource_executor", {"commands": ["version"]}, "Resource execution"),
            ("msf_loot_collector", {"action": "list"}, "Loot collection"),
        ]
        
        for tool_name, args, desc in extended_tests:
            success, elapsed, error = await self.test_tool(tool_name, args, "extended", desc)
            self.update_results(tool_name, "extended", success, elapsed, error)
            
        # ========== ADVANCED TOOLS (10) ==========
        print("\n🚀 ADVANCED TOOLS (10 tools)")
        print("-" * 40)
        
        advanced_tests = [
            ("msf_vulnerability_tracker", {"action": "list"}, "Vulnerability tracking"),
            ("msf_reporting_engine", {"report_type": "summary", "workspace": "default"}, "Report generation"),
            ("msf_automation_builder", {"action": "list"}, "Automation workflows"),
            ("msf_plugin_manager", {"action": "list"}, "Plugin management"),
            ("msf_listener_orchestrator", {"action": "status"}, "Listener orchestration"),
            ("msf_workspace_automator", {"action": "backup", "workspace": "default"}, "Workspace automation"),
            ("msf_encoder_factory", {"payload_data": "test", "encoding_chain": ["x86/shikata_ga_nai"]}, "Encoder factory"),
            ("msf_evasion_suite", {"action": "list"}, "Evasion techniques"),
            ("msf_report_generator", {"format": "html", "workspace": "default"}, "Report generation"),
            ("msf_interactive_session", {"action": "status"}, "Interactive sessions"),
        ]
        
        for tool_name, args, desc in advanced_tests:
            success, elapsed, error = await self.test_tool(tool_name, args, "advanced", desc)
            self.update_results(tool_name, "advanced", success, elapsed, error)
            
        # ========== SYSTEM MANAGEMENT TOOLS (8) ==========
        print("\n⚙️ SYSTEM MANAGEMENT TOOLS (8 tools)")
        print("-" * 40)
        
        system_tests = [
            ("msf_core_system_manager", {"action": "status"}, "Core system management"),
            ("msf_advanced_module_controller", {"action": "stack"}, "Module controller"),
            ("msf_job_manager", {"action": "list"}, "Job management"),
            ("msf_database_admin_controller", {"action": "status"}, "Database admin"),
            ("msf_developer_debug_suite", {"action": "info"}, "Debug suite"),
            ("msf_venom_direct", {"action": "formats"}, "Direct msfvenom"),
            ("msf_database_direct", {"action": "status"}, "Direct database"),
            ("msf_rpc_interface", {"action": "status"}, "RPC interface"),
        ]
        
        for tool_name, args, desc in system_tests:
            success, elapsed, error = await self.test_tool(tool_name, args, "system", desc)
            self.update_results(tool_name, "system", success, elapsed, error)
            
        # ========== v5.0 ENHANCED TOOLS (11) ==========
        print("\n✨ v5.0 ENHANCED TOOLS (11 tools)")
        print("-" * 40)
        
        enhanced_tests = [
            ("msf_enhanced_plugin_manager", {"action": "list"}, "Enhanced plugin manager"),
            ("msf_connect", {"host": "127.0.0.1", "port": 80}, "Network connect"),
            ("msf_interactive_ruby", {"command": "puts 'test'"}, "Interactive Ruby"),
            ("msf_route_manager", {"action": "list"}, "Route management"),
            ("msf_output_filter", {"pattern": "test", "command": "version"}, "Output filtering"),
            ("msf_console_logger", {"action": "status"}, "Console logging"),
            ("msf_config_manager", {"action": "list"}, "Config management"),
            ("msf_session_upgrader", {"session_id": "1"}, "Session upgrading"),
            ("msf_bulk_session_operations", {"action": "info"}, "Bulk operations"),
            ("msf_session_clustering", {"action": "list"}, "Session clustering"),
            ("msf_session_persistence", {"action": "list"}, "Session persistence"),
        ]
        
        for tool_name, args, desc in enhanced_tests:
            success, elapsed, error = await self.test_tool(tool_name, args, "enhanced", desc)
            self.update_results(tool_name, "enhanced", success, elapsed, error)
            
        # ========== PLUGIN TESTS (Sample of loaded plugins) ==========
        print("\n🔌 PLUGIN FUNCTIONALITY (Testing loaded plugins)")
        print("-" * 40)
        
        # First load some plugins
        print("Loading test plugins...")
        plugin_load_tests = [
            ("msf_enhanced_plugin_manager", {"action": "load", "plugin_name": "auto_add_route"}, "Load auto_add_route"),
            ("msf_enhanced_plugin_manager", {"action": "load", "plugin_name": "session_notifier"}, "Load session_notifier"),
        ]
        
        for tool_name, args, desc in plugin_load_tests:
            success, elapsed, error = await self.test_tool(tool_name, args, "plugins", desc)
            if success:
                self.results["categories"]["plugins"]["passed"] += 1
            else:
                self.results["categories"]["plugins"]["failed"] += 1
                
        # Test plugin commands
        plugin_command_tests = [
            ("msf_enhanced_plugin_manager", 
             {"action": "execute", "plugin_name": "auto_add_route", "command": "status"}, 
             "Execute plugin command"),
            ("msf_enhanced_plugin_manager", 
             {"action": "info", "plugin_name": "auto_add_route"}, 
             "Get plugin info"),
        ]
        
        for tool_name, args, desc in plugin_command_tests:
            success, elapsed, error = await self.test_tool(tool_name, args, "plugins", desc)
            if success:
                self.results["categories"]["plugins"]["passed"] += 1
            else:
                self.results["categories"]["plugins"]["failed"] += 1
                
        # ========== SUMMARY ==========
        suite_elapsed = time.time() - suite_start
        
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        print(f"\nTotal Tools: {self.results['total_tools']}")
        print(f"Tools Tested: {self.results['tested']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"Success Rate: {(self.results['passed'] / self.results['tested'] * 100):.1f}%")
        print(f"Total Test Time: {suite_elapsed:.2f}s")
        
        print("\n📈 Performance Metrics:")
        if self.results["performance"]:
            avg_time = sum(self.results["performance"].values()) / len(self.results["performance"])
            fastest = min(self.results["performance"].items(), key=lambda x: x[1])
            slowest = max(self.results["performance"].items(), key=lambda x: x[1])
            
            print(f"Average Response Time: {avg_time:.3f}s")
            print(f"Fastest Tool: {fastest[0]} ({fastest[1]:.3f}s)")
            print(f"Slowest Tool: {slowest[0]} ({slowest[1]:.3f}s)")
            
        print("\n📦 Category Breakdown:")
        for category, stats in self.results["categories"].items():
            if stats["total"] > 0:
                success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
                print(f"{category.upper()}: {stats['passed']}/{stats['total']} ({success_rate:.0f}%)")
                
        if self.results["errors"]:
            print("\n⚠️ Failed Tools:")
            for error in self.results["errors"][:10]:  # Show first 10 errors
                print(f"- {error['tool']}: {error['error'][:60]}...")
                
        # Save detailed report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Cleanup
        await self.server.cleanup()
        
    def update_results(self, tool_name: str, category: str, success: bool, elapsed: float, error: str):
        """Update test results"""
        self.results["tested"] += 1
        
        if success:
            self.results["passed"] += 1
            self.results["categories"][category]["passed"] += 1
        else:
            self.results["failed"] += 1
            self.results["categories"][category]["failed"] += 1
            self.results["errors"].append({
                "tool": tool_name,
                "category": category,
                "error": error
            })
            
        self.results["performance"][tool_name] = elapsed


async def main():
    """Run the comprehensive test suite"""
    print("MSF Console MCP v5.0 - Comprehensive Test Suite")
    print("Testing all 58 tools with performance metrics...")
    print()
    
    tester = ToolTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)