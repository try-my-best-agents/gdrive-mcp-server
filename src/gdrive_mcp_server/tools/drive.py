"""Google Drive tools for MCP server."""
import base64
import io
import os
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


def register_drive_tools(mcp: FastMCP, drive_service: Any) -> None:
    """Register Google Drive tools with the MCP server."""
    
    # Get folder ID from environment
    FOLDER_ID = os.getenv("FOLDER_ID")
    
    @mcp.tool()
    async def gdrive_search(query: str) -> Dict[str, Any]:
        """
        Search for files in Google Drive.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary containing search results
        """
        if not drive_service:
            return {"error": "Drive service not initialized"}
        
        try:
            # Escape single quotes in query and create full-text search
            escaped_query = query.replace("'", "\\'")
            search_query = f"fullText contains '{escaped_query}'"
            
            # Add folder restriction if FOLDER_ID is set
            if FOLDER_ID:
                search_query = f"'{FOLDER_ID}' in parents and {search_query}"
            
            results = drive_service.files().list(
                q=search_query,
                pageSize=20,
                fields="files(id, name, mimeType, modifiedTime, size, webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            
            return {
                "results": files,
                "count": len(files)
            }
        except HttpError as e:
            return {"error": f"Search failed: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {e}"}
    
    
    @mcp.tool()
    async def gdrive_read_file(file_id: str) -> Dict[str, Any]:
        """
        Read the contents of a file from Google Drive.
        
        Args:
            file_id: The ID of the file to read
            
        Returns:
            Dictionary containing file content or error
        """
        if not drive_service:
            return {"error": "Drive service not initialized"}
        
        try:
            # Get file metadata
            file_metadata = drive_service.files().get(fileId=file_id).execute()
            mime_type = file_metadata.get('mimeType', '')
            file_name = file_metadata.get('name', 'Unknown')
            
            # Handle Google Workspace files with export
            export_mime_types = {
                'application/vnd.google-apps.document': 'text/markdown',
                'application/vnd.google-apps.spreadsheet': 'text/csv',
                'application/vnd.google-apps.presentation': 'text/plain',
                'application/vnd.google-apps.drawing': 'image/png'
            }
            
            if mime_type in export_mime_types:
                export_type = export_mime_types[mime_type]
                request = drive_service.files().export_media(
                    fileId=file_id,
                    mimeType=export_type
                )
            else:
                # Regular file download
                request = drive_service.files().get_media(fileId=file_id)
            
            # Download file content
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)
            done = False
            
            while not done:
                _, done = downloader.next_chunk()
            
            file_buffer.seek(0)
            content_bytes = file_buffer.read()
            
            # Try to decode as text, otherwise return base64
            try:
                if mime_type.startswith('text/') or mime_type in ['application/json'] or mime_type in export_mime_types:
                    content = content_bytes.decode('utf-8')
                    return {
                        "file_id": file_id,
                        "name": file_name,
                        "mime_type": mime_type,
                        "content": content,
                        "encoding": "utf-8"
                    }
                else:
                    # Binary content
                    content = base64.b64encode(content_bytes).decode('utf-8')
                    return {
                        "file_id": file_id,
                        "name": file_name,
                        "mime_type": mime_type,
                        "content": content,
                        "encoding": "base64"
                    }
            except UnicodeDecodeError:
                # Fallback to base64 if text decode fails
                content = base64.b64encode(content_bytes).decode('utf-8')
                return {
                    "file_id": file_id,
                    "name": file_name,
                    "mime_type": mime_type,
                    "content": content,
                    "encoding": "base64"
                }
                
        except HttpError as e:
            return {"error": f"Failed to read file: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {e}"}