import argparse
import os
import sys
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

from .tools.drive import register_drive_tools
from .resources.drive import register_drive_resources

# Load environment variables
load_dotenv()

# Initialize FastMCP server with HTTP path
mcp = FastMCP("gdrive-mcp-server", transport="http", path_prefix="/mcp-servers/gdrive-mcp-server")

# Global Drive service instance
drive_service: Optional[Any] = None

def initialize_drive_service(credentials_path: str) -> Any:
    """Initialize Google Drive service with service account credentials."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Drive service: {e}")




def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="Google Drive MCP Server")
    parser.add_argument(
        "--service-account",
        type=str,
        required=True,
        help="Path to Google service account credentials JSON file",
        default="korea-agent-google-sa-cred.json"
    )
    
    args = parser.parse_args()
    
    # Verify credentials file exists
    creds_path = Path(args.service_account)
    if not creds_path.exists():
        print(f"Error: Service account credentials file not found: {creds_path}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize Drive service
    global drive_service
    try:
        drive_service = initialize_drive_service(str(creds_path))
        print(f"Successfully initialized Google Drive service with {creds_path}", file=sys.stderr)
        
        # Register tools and resources
        register_drive_tools(mcp, drive_service)
        register_drive_resources(mcp, drive_service)
        print("Registered Google Drive tools and resources", file=sys.stderr)
        
    except Exception as e:
        print(f"Failed to initialize Drive service: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run the MCP server as HTTP on localhost:8000
    # The FastMCP server will handle the /mcp-servers/gdrive-mcp-server/ path
    mcp.settings.host = "127.0.0.1"
    mcp.settings.port = 8000
    mcp.settings.log_level = "info"
    mcp.run("streamable-http")


if __name__ == "__main__":
    main()