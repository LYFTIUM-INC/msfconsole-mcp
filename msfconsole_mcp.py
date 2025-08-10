# Entrypoint for MSFConsole MCP Server (renamed without _enhanced)
from msf.server import main  # re-export main only

if __name__ == "__main__":
    from msf.server import main

    main()
