from msfconsole_mcp_enhanced import *  # noqa: F401,F403


def main() -> None:
    import msfconsole_mcp_enhanced as _enh

    try:
        _enh.mcp.run(transport="stdio")
    except KeyboardInterrupt:
        pass