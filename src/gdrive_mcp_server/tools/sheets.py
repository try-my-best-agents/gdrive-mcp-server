"""Google Sheets specific tools for expense tracking and recordkeeping."""
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def register_sheets_tools(mcp: FastMCP, drive_service: Any) -> None:
    """Register all Google Sheets tools with the MCP server."""
    
    # Build sheets service using the same credentials
    creds = drive_service._http.credentials
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    @mcp.tool()
    async def create_expense_sheet(
        name: str,
        folder_id: Optional[str] = None,
        categories: Optional[List[str]] = None,
        initial_headers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Google Sheet optimized for expense tracking.
        
        Args:
            name: Name for the new spreadsheet
            folder_id: Target folder ID (defaults to FOLDER_ID env var)
            categories: List of expense categories for dropdown validation
            initial_headers: Column headers (defaults to expense tracking headers)
            
        Returns:
            Dictionary containing sheet ID, URL, and setup details
        """
        try:
            # Default categories for expense tracking
            if categories is None:
                categories = [
                    "Food & Dining",
                    "Transportation",
                    "Shopping",
                    "Bills & Utilities",
                    "Healthcare",
                    "Entertainment",
                    "Travel",
                    "Education",
                    "Personal Care",
                    "Other"
                ]
            
            # Default headers for expense tracking
            if initial_headers is None:
                initial_headers = [
                    "Date",
                    "Description",
                    "Category",
                    "Amount",
                    "Payment Method",
                    "Notes",
                    "Tags"
                ]
            
            # Create the sheet first using Drive API
            import os
            target_folder = folder_id or os.getenv("FOLDER_ID")
            
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.spreadsheet',
            }
            if target_folder:
                file_metadata['parents'] = [target_folder]
            
            sheet_file = drive_service.files().create(
                body=file_metadata,
                fields='id, webViewLink'
            ).execute()
            
            spreadsheet_id = sheet_file['id']
            
            # Now set up the sheet structure
            requests = []
            
            # Add headers
            requests.append({
                'updateCells': {
                    'rows': [{
                        'values': [{'userEnteredValue': {'stringValue': h}} for h in initial_headers]
                    }],
                    'fields': 'userEnteredValue',
                    'start': {'sheetId': 0, 'rowIndex': 0, 'columnIndex': 0}
                }
            })
            
            # Format header row
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
                            'textFormat': {
                                'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat'
                }
            })
            
            # Add data validation for category column (column C, index 2)
            if "Category" in initial_headers:
                category_col = initial_headers.index("Category")
                requests.append({
                    'setDataValidation': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': 1,
                            'startColumnIndex': category_col,
                            'endColumnIndex': category_col + 1
                        },
                        'rule': {
                            'condition': {
                                'type': 'ONE_OF_LIST',
                                'values': [{'userEnteredValue': cat} for cat in categories]
                            },
                            'showCustomUi': True
                        }
                    }
                })
            
            # Format amount column as currency (column D, index 3)
            if "Amount" in initial_headers:
                amount_col = initial_headers.index("Amount")
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': 1,
                            'startColumnIndex': amount_col,
                            'endColumnIndex': amount_col + 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'numberFormat': {
                                    'type': 'CURRENCY',
                                    'pattern': '$#,##0.00'
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.numberFormat'
                    }
                })
            
            # Format date column (column A, index 0)
            if "Date" in initial_headers:
                date_col = initial_headers.index("Date")
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': 1,
                            'startColumnIndex': date_col,
                            'endColumnIndex': date_col + 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'numberFormat': {
                                    'type': 'DATE',
                                    'pattern': 'yyyy-mm-dd'
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.numberFormat'
                    }
                })
            
            # Auto-resize columns
            requests.append({
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': len(initial_headers)
                    }
                }
            })
            
            # Add developer metadata for expense tracking
            requests.append({
                'createDeveloperMetadata': {
                    'developerMetadata': {
                        'metadataKey': 'sheet_type',
                        'metadataValue': 'expense_tracker',
                        'location': {
                            'spreadsheet': True
                        },
                        'visibility': 'DOCUMENT'
                    }
                }
            })
            
            # Store categories as metadata
            requests.append({
                'createDeveloperMetadata': {
                    'developerMetadata': {
                        'metadataKey': 'expense_categories',
                        'metadataValue': json.dumps(categories),
                        'location': {
                            'spreadsheet': True
                        },
                        'visibility': 'DOCUMENT'
                    }
                }
            })
            
            # Execute all requests
            batch_update_response = sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            return {
                "success": True,
                "sheet": {
                    "id": spreadsheet_id,
                    "name": name,
                    "webViewLink": sheet_file.get('webViewLink'),
                    "headers": initial_headers,
                    "categories": categories,
                    "setup_complete": True
                }
            }
            
        except HttpError as e:
            return {"error": f"Failed to create sheet: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    
    @mcp.tool()
    async def read_sheet_cells(
        spreadsheet_id: str,
        range_notation: str = "A1:Z1000"
    ) -> Dict[str, Any]:
        """
        Read cells from a Google Sheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_notation: A1 notation range (e.g., "A1:D10", "Sheet1!A:A")
            
        Returns:
            Dictionary containing cell values and metadata
        """
        try:
            # Get values
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_notation,
                valueRenderOption='UNFORMATTED_VALUE',
                dateTimeRenderOption='FORMATTED_STRING'
            ).execute()
            
            values = result.get('values', [])
            
            # Get sheet metadata
            sheet_metadata = sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields="properties.title,sheets.properties"
            ).execute()
            
            return {
                "spreadsheet_id": spreadsheet_id,
                "spreadsheet_title": sheet_metadata['properties']['title'],
                "range": range_notation,
                "values": values,
                "rows": len(values),
                "columns": max(len(row) for row in values) if values else 0
            }
            
        except HttpError as e:
            return {"error": f"Failed to read sheet: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    
    @mcp.tool()
    async def update_sheet_cells(
        spreadsheet_id: str,
        range_notation: str,
        values: List[List[Union[str, float, int]]],
        value_input_option: str = "USER_ENTERED"
    ) -> Dict[str, Any]:
        """
        Update cells in a Google Sheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_notation: A1 notation range (e.g., "A2:D2")
            values: 2D array of values to write
            value_input_option: How to interpret values (USER_ENTERED or RAW)
            
        Returns:
            Dictionary containing update results
        """
        try:
            body = {
                'values': values
            }
            
            result = sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_notation,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            return {
                "success": True,
                "updated_cells": result.get('updatedCells', 0),
                "updated_rows": result.get('updatedRows', 0),
                "updated_columns": result.get('updatedColumns', 0),
                "updated_range": result.get('updatedRange', '')
            }
            
        except HttpError as e:
            return {"error": f"Failed to update sheet: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    
    @mcp.tool()
    async def append_expense_row(
        spreadsheet_id: str,
        date: str,
        description: str,
        category: str,
        amount: float,
        payment_method: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Append a new expense row to the sheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            date: Date of expense (YYYY-MM-DD format)
            description: Description of the expense
            category: Expense category
            amount: Amount spent
            payment_method: Payment method used
            notes: Additional notes
            tags: Comma-separated tags
            
        Returns:
            Dictionary containing append results
        """
        try:
            # Prepare row data
            row_data = [
                date,
                description,
                category,
                amount,
                payment_method or "",
                notes or "",
                tags or ""
            ]
            
            body = {
                'values': [row_data]
            }
            
            result = sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='A:G',  # Assumes standard expense tracking columns
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            return {
                "success": True,
                "updated_range": result.get('updates', {}).get('updatedRange', ''),
                "updated_rows": result.get('updates', {}).get('updatedRows', 0),
                "expense": {
                    "date": date,
                    "description": description,
                    "category": category,
                    "amount": amount
                }
            }
            
        except HttpError as e:
            return {"error": f"Failed to append expense: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    
    @mcp.tool()
    async def set_sheet_metadata(
        spreadsheet_id: str,
        key: str,
        value: str,
        location_type: str = "spreadsheet"
    ) -> Dict[str, Any]:
        """
        Set developer metadata on a sheet for tracking custom properties.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            key: Metadata key (e.g., "budget_limit", "fiscal_year")
            value: Metadata value
            location_type: Where to attach metadata ("spreadsheet" or "sheet")
            
        Returns:
            Dictionary containing metadata creation results
        """
        try:
            location = {}
            if location_type == "spreadsheet":
                location['spreadsheet'] = True
            else:
                location['sheetId'] = 0  # First sheet
            
            request = {
                'createDeveloperMetadata': {
                    'developerMetadata': {
                        'metadataKey': key,
                        'metadataValue': value,
                        'location': location,
                        'visibility': 'DOCUMENT'
                    }
                }
            }
            
            result = sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
            return {
                "success": True,
                "metadata_key": key,
                "metadata_value": value,
                "location_type": location_type
            }
            
        except HttpError as e:
            return {"error": f"Failed to set metadata: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    
    @mcp.tool()
    async def get_sheet_metadata(
        spreadsheet_id: str,
        key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get developer metadata from a sheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            key: Optional specific key to search for
            
        Returns:
            Dictionary containing metadata
        """
        try:
            data_filters = []
            if key:
                data_filters.append({
                    'developerMetadataLookup': {
                        'metadataKey': key
                    }
                })
            
            request_body = {}
            if data_filters:
                request_body['dataFilters'] = data_filters
            
            result = sheets_service.spreadsheets().developerMetadata().search(
                spreadsheetId=spreadsheet_id,
                body=request_body
            ).execute()
            
            metadata_items = []
            for item in result.get('matchedDeveloperMetadata', []):
                metadata = item.get('developerMetadata', {})
                metadata_items.append({
                    'key': metadata.get('metadataKey'),
                    'value': metadata.get('metadataValue'),
                    'location': metadata.get('location', {}),
                    'id': metadata.get('metadataId')
                })
            
            return {
                "spreadsheet_id": spreadsheet_id,
                "metadata": metadata_items,
                "count": len(metadata_items)
            }
            
        except HttpError as e:
            return {"error": f"Failed to get metadata: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    
    @mcp.tool()
    async def add_category_validation(
        spreadsheet_id: str,
        column: str,
        categories: List[str],
        start_row: int = 2
    ) -> Dict[str, Any]:
        """
        Add dropdown validation to a column for expense categories.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            column: Column letter (e.g., "C")
            categories: List of allowed categories
            start_row: Starting row for validation (default 2, after headers)
            
        Returns:
            Dictionary containing validation setup results
        """
        try:
            # Convert column letter to index
            col_index = ord(column.upper()) - ord('A')
            
            request = {
                'setDataValidation': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': start_row - 1,
                        'startColumnIndex': col_index,
                        'endColumnIndex': col_index + 1
                    },
                    'rule': {
                        'condition': {
                            'type': 'ONE_OF_LIST',
                            'values': [{'userEnteredValue': cat} for cat in categories]
                        },
                        'showCustomUi': True,
                        'strict': True
                    }
                }
            }
            
            result = sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
            return {
                "success": True,
                "column": column,
                "categories": categories,
                "start_row": start_row
            }
            
        except HttpError as e:
            return {"error": f"Failed to add validation: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    
    @mcp.tool()
    async def get_expense_summary(
        spreadsheet_id: str,
        date_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of expenses from the sheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            date_range: Optional date range filter (e.g., "2024-01-01:2024-12-31")
            
        Returns:
            Dictionary containing expense summary by category
        """
        try:
            # Read all data
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='A:G',
                valueRenderOption='UNFORMATTED_VALUE'
            ).execute()
            
            values = result.get('values', [])
            if len(values) < 2:  # No data beyond headers
                return {
                    "total": 0,
                    "by_category": {},
                    "transaction_count": 0
                }
            
            # Skip header row
            headers = values[0]
            data_rows = values[1:]
            
            # Find column indices
            date_idx = headers.index("Date") if "Date" in headers else 0
            category_idx = headers.index("Category") if "Category" in headers else 2
            amount_idx = headers.index("Amount") if "Amount" in headers else 3
            
            # Process data
            total = 0
            by_category = {}
            transaction_count = 0
            
            for row in data_rows:
                if len(row) > amount_idx:
                    try:
                        amount = float(row[amount_idx])
                        category = row[category_idx] if len(row) > category_idx else "Uncategorized"
                        
                        # Apply date filter if provided
                        if date_range and len(row) > date_idx:
                            date_str = str(row[date_idx])
                            start_date, end_date = date_range.split(':')
                            if not (start_date <= date_str <= end_date):
                                continue
                        
                        total += amount
                        transaction_count += 1
                        
                        if category not in by_category:
                            by_category[category] = {"amount": 0, "count": 0}
                        by_category[category]["amount"] += amount
                        by_category[category]["count"] += 1
                        
                    except (ValueError, TypeError):
                        continue
            
            return {
                "spreadsheet_id": spreadsheet_id,
                "total": round(total, 2),
                "by_category": {k: {"amount": round(v["amount"], 2), "count": v["count"]} 
                               for k, v in by_category.items()},
                "transaction_count": transaction_count,
                "date_range": date_range
            }
            
        except HttpError as e:
            return {"error": f"Failed to get summary: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}