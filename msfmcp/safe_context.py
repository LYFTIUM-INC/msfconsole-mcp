#!/usr/bin/env python3

"""
SafeContext for MSFConsole MCP
Enhanced error handling and context management for MCP
"""

import sys
import logging
import traceback
from typing import Any, Optional, Callable, Dict, Type, TypeVar, cast

# Setup logging
logger = logging.getLogger(__name__)

# Type variable for the wrapped function
T = TypeVar('T')

class SafeContext:
    """
    A context manager for safer MCP functions with better error handling.
    Wraps MCP context operations and provides consistent error handling.
    """
    
    def __init__(self, ctx=None, suppress_errors=False):
        """
        Initialize SafeContext
        
        Args:
            ctx: MCP context object (can be None for testing)
            suppress_errors: Whether to suppress errors (default: False)
        """
        self.ctx = ctx
        self.suppress_errors = suppress_errors
        self.error_occurred = False
    
    async def info(self, message: str) -> None:
        """
        Log an info message to the MCP context
        
        Args:
            message: Message to log
        """
        logger.info(message)
        if self.ctx:
            try:
                await self.ctx.info(message)
            except Exception as e:
                logger.error(f"Error sending info to context: {e}")
    
    async def warning(self, message: str) -> None:
        """
        Log a warning message to the MCP context
        
        Args:
            message: Warning message
        """
        logger.warning(message)
        if self.ctx:
            try:
                await self.ctx.warning(message)
            except Exception as e:
                logger.error(f"Error sending warning to context: {e}")
    
    async def error(self, message: str, exception: Optional[Exception] = None) -> None:
        """
        Log an error message to the MCP context
        
        Args:
            message: Error message
            exception: Optional exception that caused the error
        """
        error_text = message
        self.error_occurred = True
        
        if exception:
            error_text = f"{message}: {str(exception)}"
            logger.error(error_text, exc_info=True)
        else:
            logger.error(error_text)
            
        if self.ctx:
            try:
                await self.ctx.error(error_text)
            except Exception as e:
                logger.error(f"Error sending error to context: {e}")
    
    async def progress(self, message: str, percentage: int) -> None:
        """
        Update progress in the MCP context
        
        Args:
            message: Progress message
            percentage: Progress percentage (0-100)
        """
        if percentage < 0:
            percentage = 0
        elif percentage > 100:
            percentage = 100
            
        logger.debug(f"Progress: {percentage}% - {message}")
        
        if self.ctx:
            try:
                await self.ctx.progress(message, percentage)
            except Exception as e:
                logger.error(f"Error sending progress to context: {e}")
    
    async def report_progress(self, current: int, total: int, message: Optional[str] = None) -> None:
        """
        Report progress to the context using the newer API format
        
        Args:
            current: Current progress value
            total: Total progress value
            message: Optional progress message
        """
        if not self.ctx:
            return
            
        try:
            percentage = int((current / total) * 100) if total > 0 else 0
            
            # Handle different parameter counts for report_progress
            # The newer API might take only 2 params (current, total) or 3 (with message)
            if message:
                try:
                    # Try with 3 params first
                    await self.ctx.report_progress(current, total, message)
                except TypeError:
                    try:
                        # If that fails, try with 2 params
                        await self.ctx.report_progress(current, total)
                        # Log the message separately
                        if message:
                            await self.info(message)
                    except Exception as e:
                        logger.error(f"Error reporting progress with 2 params: {e}")
            else:
                # No message, just use 2 params
                await self.ctx.report_progress(current, total)
                
        except Exception as e:
            logger.error(f"Error reporting progress to context: {e}")
            # Fall back to the simpler progress method
            if message:
                await self.progress(message, percentage)
    
    @staticmethod
    def wrap_function(func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator to wrap a function with SafeContext error handling
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function with error handling
        """
        async def wrapper(*args, **kwargs):
            ctx = kwargs.get('ctx', None)
            safe_ctx = SafeContext(ctx)
            
            try:
                await safe_ctx.info(f"Starting {func.__name__}")
                result = await func(*args, **kwargs)
                await safe_ctx.info(f"Completed {func.__name__}")
                return result
            except Exception as e:
                error_message = f"Error in {func.__name__}"
                await safe_ctx.error(error_message, e)
                tb = traceback.format_exc()
                logger.error(f"{error_message}\n{tb}")
                
                # Return a friendly error message
                return f"An error occurred: {str(e)}. Please check the logs for more details."
                
        return cast(T, wrapper)

# Function to safely import MCP
def safely_import_mcp():
    """
    Safely import MCP and handle compatibility issues
    
    Returns:
        Tuple of (FastMCP, Context) or (None, None) if import fails
    """
    try:
        import mcp.server.fastmcp
        return mcp.server.fastmcp.FastMCP, mcp.server.fastmcp.Context
    except ImportError as e:
        logger.error(f"Failed to import MCP: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error importing MCP: {e}")
        return None, None

# Python version compatibility check
def check_python_version():
    """
    Check if the Python version is compatible
    
    Returns:
        Tuple of (major, minor, micro) version numbers
    """
    import platform
    version_info = platform.python_version_tuple()
    major, minor, micro = int(version_info[0]), int(version_info[1]), int(version_info[2])
    
    if major != 3 or minor < 8:
        logger.warning(f"Python {major}.{minor}.{micro} may not be compatible. Python 3.8+ is recommended.")
    
    if minor >= 11:
        logger.warning(f"Python {major}.{minor}.{micro} may have asyncio compatibility issues.")
    
    return (major, minor, micro)
