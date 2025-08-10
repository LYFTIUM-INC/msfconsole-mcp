# Entrypoint for MSFConsole MCP Server (renamed without _enhanced)
from msfconsole_mcp_enhanced import *  # re-export tools and main

if __name__ == "__main__":
    # Delegate to the original main execution path
    import msfconsole_mcp_enhanced as _enh
    try:
        _enh.mcp.run(transport="stdio")
    except KeyboardInterrupt:
        pass