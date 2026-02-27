"""Shared pytest fixtures for MSF Console MCP Server tests."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for tests that don't need real MSF."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "msfconsole"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_create_subprocess():
    """Mock asyncio.create_subprocess_exec for async command execution."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b"Framework: 6.3.0\nConsole  : 6.3.0\n",
            b"",
        )
        mock_process.returncode = 0
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()
        mock_exec.return_value = mock_process
        yield mock_exec, mock_process
