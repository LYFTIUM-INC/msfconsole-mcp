# Entrypoint for MSFConsole MCP Server (renamed without _enhanced)
from msf.server import *  # re-export tools and main

if __name__ == "__main__":
    from msf.server import main

    main()