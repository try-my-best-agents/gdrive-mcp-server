import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
import uvicorn
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

from .tools.sheets import register_sheets_tools
from .tools.drive import register_drive_tools
from .resources.drive import register_drive_resources

# Load environment variables
load_dotenv()

# Initialize FastMCP server with HTTP path
mcp = FastMCP("gdrive-test-server", transport="http", path_prefix="/mcp-servers/gdrive-test-server")

# Global Drive service instance
drive_service: Optional[Any] = None

# Get folder ID from environment
FOLDER_ID = os.getenv("FOLDER_ID")


def initialize_drive_service(credentials_path: str) -> Any:
    """Initialize Google Drive service with service account credentials."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=[
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/drive.file'  # For creating files
            ]
        )
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Drive service: {e}")


def handle_api_error(error: HttpError) -> Dict[str, Any]:
    """Convert Google API HTTP errors to user-friendly error messages."""
    error_details = {
        "error": "API request failed",
        "status_code": error.resp.status,
        "reason": error.resp.reason
    }
    
    # Common error handling
    if error.resp.status == 403:
        error_details["error"] = "Permission denied"
        error_details["suggestion"] = "Check service account permissions and folder access"
    elif error.resp.status == 404:
        error_details["error"] = "Resource not found"
        error_details["suggestion"] = "Verify the file/folder ID exists and is accessible"
    elif error.resp.status == 429:
        error_details["error"] = "Rate limit exceeded"
        error_details["suggestion"] = "Too many requests, please try again later"
    elif error.resp.status == 400:
        error_details["error"] = "Invalid request"
        error_details["suggestion"] = "Check request parameters"
    
    # Try to get more details from error content
    try:
        if hasattr(error, 'content'):
            import json
            error_content = json.loads(error.content.decode('utf-8'))
            if 'error' in error_content and 'message' in error_content['error']:
                error_details["details"] = error_content['error']['message']
    except:
        pass
    
    return error_details


@mcp.tool()
async def list_files(
    folder_id: Optional[str] = None,
    mime_type: Optional[str] = None,
    page_size: int = 100
) -> Dict[str, Any]:
    """
    List all files in a Google Drive folder.
    
    Args:
        folder_id: Folder ID to list files from (defaults to FOLDER_ID env var)
        mime_type: Optional MIME type filter
        page_size: Number of files to return per page (max 1000)
        
    Returns:
        Dictionary containing list of files and metadata
    """
    if not drive_service:
        return {"error": "Drive service not initialized"}
    
    # Use provided folder_id or fall back to environment variable
    target_folder = folder_id or FOLDER_ID
    if not target_folder:
        return {"error": "No folder ID provided and FOLDER_ID environment variable not set"}
    
    try:
        # Build query
        query_parts = [f"'{target_folder}' in parents"]
        if mime_type:
            query_parts.append(f"mimeType = '{mime_type}'")
        query = " and ".join(query_parts)
        
        # Ensure page_size is within limits
        page_size = min(max(page_size, 1), 1000)
        
        all_files = []
        page_token = None
        
        while True:
            try:
                results = drive_service.files().list(
                    q=query,
                    pageSize=page_size,
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, parents)",
                    pageToken=page_token
                ).execute()
                
                files = results.get('files', [])
                all_files.extend(files)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
            except HttpError as e:
                return handle_api_error(e)
        
        return {
            "folder_id": target_folder,
            "count": len(all_files),
            "files": all_files
        }
        
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def create_sheet(
    name: str,
    folder_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Google Sheet in the specified folder.
    
    Args:
        name: Name for the new spreadsheet
        folder_id: Target folder ID (defaults to FOLDER_ID env var)
        
    Returns:
        Dictionary containing created sheet metadata
    """
    if not drive_service:
        return {"error": "Drive service not initialized"}
    
    # Use provided folder_id or fall back to environment variable
    target_folder = folder_id or FOLDER_ID
    if not target_folder:
        return {"error": "No folder ID provided and FOLDER_ID environment variable not set"}
    
    try:
        # Prepare file metadata
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            'parents': [target_folder]
        }
        
        # Create the sheet
        try:
            sheet = drive_service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink, createdTime'
            ).execute()
            
            return {
                "success": True,
                "sheet": {
                    "id": sheet.get('id'),
                    "name": sheet.get('name'),
                    "webViewLink": sheet.get('webViewLink'),
                    "createdTime": sheet.get('createdTime')
                }
            }
            
        except HttpError as e:
            return handle_api_error(e)
            
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def get_folder_metadata(
    folder_id: Optional[str] = None,
    include_subfolders: bool = False
) -> Dict[str, Any]:
    """
    Get comprehensive metadata about all files in a folder.
    
    Args:
        folder_id: Folder ID to analyze (defaults to FOLDER_ID env var)
        include_subfolders: Whether to include files from subfolders recursively
        
    Returns:
        Dictionary containing detailed metadata for all files
    """
    if not drive_service:
        return {"error": "Drive service not initialized"}
    
    # Use provided folder_id or fall back to environment variable
    target_folder = folder_id or FOLDER_ID
    if not target_folder:
        return {"error": "No folder ID provided and FOLDER_ID environment variable not set"}
    
    try:
        # Get folder details first
        try:
            folder_info = drive_service.files().get(
                fileId=target_folder,
                fields='id, name, mimeType, createdTime, modifiedTime, owners'
            ).execute()
        except HttpError as e:
            return handle_api_error(e)
        
        # Build query
        if include_subfolders:
            # This requires a more complex implementation to traverse folder tree
            # For now, just get direct children
            query = f"'{target_folder}' in parents"
        else:
            query = f"'{target_folder}' in parents"
        
        all_files = []
        page_token = None
        
        # Comprehensive field list for metadata
        fields = (
            "nextPageToken, "
            "files(id, name, mimeType, size, createdTime, modifiedTime, "
            "webViewLink, webContentLink, parents, description, "
            "starred, trashed, version, originalFilename, "
            "owners, lastModifyingUser, shared, viewers, "
            "sharingUser, permissions(id, type, role, emailAddress), "
            "capabilities(canEdit, canComment, canShare, canDownload, canReadRevisions))"
        )
        
        while True:
            try:
                results = drive_service.files().list(
                    q=query,
                    pageSize=100,
                    fields=fields,
                    pageToken=page_token
                ).execute()
                
                files = results.get('files', [])
                all_files.extend(files)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
            except HttpError as e:
                return handle_api_error(e)
        
        # Calculate folder statistics
        total_size = sum(int(f.get('size', 0)) for f in all_files if f.get('size'))
        mime_type_counts = {}
        for f in all_files:
            mime_type = f.get('mimeType', 'unknown')
            mime_type_counts[mime_type] = mime_type_counts.get(mime_type, 0) + 1
        
        return {
            "folder": {
                "id": folder_info.get('id'),
                "name": folder_info.get('name'),
                "createdTime": folder_info.get('createdTime'),
                "modifiedTime": folder_info.get('modifiedTime'),
                "owners": folder_info.get('owners', [])
            },
            "statistics": {
                "total_files": len(all_files),
                "total_size_bytes": total_size,
                "total_size_readable": format_bytes(total_size),
                "mime_type_distribution": mime_type_counts
            },
            "files": all_files
        }
        
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def format_bytes(bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"


def main():
    """Main entry point for the test MCP server."""
    parser = argparse.ArgumentParser(description="Google Drive Test MCP Server")
    parser.add_argument(
        "--service-account",
        type=str,
        required=True,
        help="Path to Google service account credentials JSON file"
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
        if FOLDER_ID:
            print(f"Using folder ID from environment: {FOLDER_ID}", file=sys.stderr)
        else:
            print("Warning: No FOLDER_ID set in environment", file=sys.stderr)
        
        # Register all tools and resources
        register_drive_tools(mcp, drive_service)
        register_drive_resources(mcp, drive_service)
        register_sheets_tools(mcp, drive_service)
        print("Registered Google Drive and Sheets tools", file=sys.stderr)
        
    except Exception as e:
        print(f"Failed to initialize Drive service: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run the MCP server as HTTP on localhost:8001 (different port for test server)
    app = mcp.get_asgi_app()
    uvicorn.run(
        app,
        host="127.0.0.1",  # Only localhost connections
        port=8001,
        log_level="info"
    )


if __name__ == "__main__":
    main()