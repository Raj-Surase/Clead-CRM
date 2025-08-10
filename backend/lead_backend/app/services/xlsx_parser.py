import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from .file_parser_base import BaseFileParser

logger = logging.getLogger(__name__)

class XLSXParser(BaseFileParser):
    """Parser for XLSX and XLS files"""
    
    def __init__(self, file_path: str, sheet_name: Optional[str] = None):
        super().__init__(file_path)
        self.sheet_name = sheet_name
        
    def parse(self) -> List[Dict[str, Any]]:
        """Parse XLSX/XLS file and return list of dictionaries"""
        try:
            # Read Excel file
            if self.sheet_name:
                df = pd.read_excel(
                    self.file_path,
                    sheet_name=self.sheet_name,
                    na_values=['', 'NULL', 'null', 'N/A', 'n/a', 'NA', 'na'],
                    keep_default_na=True
                )
            else:
                # Read first sheet if no sheet name specified
                df = pd.read_excel(
                    self.file_path,
                    na_values=['', 'NULL', 'null', 'N/A', 'n/a', 'NA', 'na'],
                    keep_default_na=True
                )
            
            # Clean column names
            df.columns = df.columns.astype(str).str.strip()
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Remove completely empty columns
            df = df.dropna(axis=1, how='all')
            
            self.total_rows = len(df)
            logger.info(f"Excel file contains {self.total_rows} rows")
            
            # Convert DataFrame to list of dictionaries
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary and handle NaN values
                    row_dict = row.to_dict()
                    
                    # Replace NaN values with None and clean data
                    cleaned_row = {}
                    for key, value in row_dict.items():
                        if pd.isna(value):
                            cleaned_row[key] = None
                        else:
                            # Handle different data types
                            if isinstance(value, (int, float)):
                                # Keep numeric values as is, but convert float to int if it's a whole number
                                if isinstance(value, float) and value.is_integer():
                                    cleaned_row[key] = int(value)
                                else:
                                    cleaned_row[key] = value
                            else:
                                # Convert to string and strip whitespace
                                cleaned_row[key] = str(value).strip() if value is not None else None
                    
                    # Normalize field names
                    normalized_row = self.normalize_field_names(cleaned_row)
                    
                    # Add row number for tracking (Excel rows start from 1, +1 for header)
                    normalized_row['source_file_row'] = index + 2
                    
                    self.data.append(normalized_row)
                    self.processed_rows += 1
                    
                except Exception as e:
                    error_msg = f"Error processing row {index + 2}: {str(e)}"
                    self.errors.append(error_msg)
                    logger.warning(error_msg)
            
            logger.info(f"Successfully processed {self.processed_rows} out of {self.total_rows} rows")
            return self.data
            
        except Exception as e:
            error_msg = f"Error parsing Excel file: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            raise
    
    def get_sheet_names(self) -> List[str]:
        """Get list of sheet names in the Excel file"""
        try:
            excel_file = pd.ExcelFile(self.file_path)
            return excel_file.sheet_names
        except Exception as e:
            error_msg = f"Error reading sheet names: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return []
    
    def validate_excel_structure(self) -> bool:
        """Validate if the Excel file has a proper structure"""
        try:
            # Check if file can be read
            excel_file = pd.ExcelFile(self.file_path)
            
            if not excel_file.sheet_names:
                self.errors.append("Excel file has no sheets")
                return False
            
            # Check the target sheet
            sheet_to_check = self.sheet_name if self.sheet_name else excel_file.sheet_names[0]
            
            if self.sheet_name and self.sheet_name not in excel_file.sheet_names:
                self.errors.append(f"Sheet '{self.sheet_name}' not found in Excel file")
                return False
            
            # Read a small sample to check structure
            df_sample = pd.read_excel(self.file_path, sheet_name=sheet_to_check, nrows=5)
            
            if df_sample.empty:
                self.errors.append(f"Sheet '{sheet_to_check}' is empty")
                return False
            
            # Check for reasonable number of columns
            if len(df_sample.columns) < 1:
                self.errors.append(f"Sheet '{sheet_to_check}' has no columns")
                return False
            
            return True
            
        except Exception as e:
            error_msg = f"Error validating Excel structure: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return False
    
    def get_sheet_info(self) -> Dict[str, Any]:
        """Get information about all sheets in the Excel file"""
        try:
            excel_file = pd.ExcelFile(self.file_path)
            sheet_info = {}
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(self.file_path, sheet_name=sheet_name, nrows=0)  # Just get headers
                    sheet_info[sheet_name] = {
                        "columns": list(df.columns),
                        "column_count": len(df.columns)
                    }
                    
                    # Get row count
                    df_full = pd.read_excel(self.file_path, sheet_name=sheet_name)
                    sheet_info[sheet_name]["row_count"] = len(df_full)
                    
                except Exception as e:
                    sheet_info[sheet_name] = {"error": str(e)}
            
            return sheet_info
            
        except Exception as e:
            error_msg = f"Error getting sheet info: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return {}

