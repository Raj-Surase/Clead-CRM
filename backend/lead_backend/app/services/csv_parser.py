import csv
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from .file_parser_base import BaseFileParser

logger = logging.getLogger(__name__)

class CSVParser(BaseFileParser):
    """Parser for CSV files"""
    
    def __init__(self, file_path: str, encoding: str = 'utf-8', delimiter: str = ','):
        super().__init__(file_path)
        self.encoding = encoding
        self.delimiter = delimiter
        
    def parse(self) -> List[Dict[str, Any]]:
        """Parse CSV file and return list of dictionaries"""
        try:
            # Try to detect encoding if utf-8 fails
            encodings_to_try = [self.encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            df = None
            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(
                        self.file_path,
                        encoding=encoding,
                        delimiter=self.delimiter,
                        na_values=['', 'NULL', 'null', 'N/A', 'n/a', 'NA', 'na'],
                        keep_default_na=True
                    )
                    logger.info(f"Successfully read CSV with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Failed to read CSV with encoding {encoding}: {str(e)}")
                    continue
            
            if df is None:
                raise Exception("Could not read CSV file with any supported encoding")
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            self.total_rows = len(df)
            logger.info(f"CSV file contains {self.total_rows} rows")
            
            # Convert DataFrame to list of dictionaries
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary and handle NaN values
                    row_dict = row.to_dict()
                    
                    # Replace NaN values with None
                    cleaned_row = {}
                    for key, value in row_dict.items():
                        if pd.isna(value):
                            cleaned_row[key] = None
                        else:
                            # Convert to string and strip whitespace
                            cleaned_row[key] = str(value).strip() if value is not None else None
                    
                    # Normalize field names
                    normalized_row = self.normalize_field_names(cleaned_row)
                    
                    # Add row number for tracking
                    normalized_row['source_file_row'] = index + 2  # +2 because pandas is 0-indexed and CSV has header
                    
                    self.data.append(normalized_row)
                    self.processed_rows += 1
                    
                except Exception as e:
                    error_msg = f"Error processing row {index + 2}: {str(e)}"
                    self.errors.append(error_msg)
                    logger.warning(error_msg)
            
            logger.info(f"Successfully processed {self.processed_rows} out of {self.total_rows} rows")
            return self.data
            
        except Exception as e:
            error_msg = f"Error parsing CSV file: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            raise
    
    def detect_delimiter(self) -> str:
        """Detect the delimiter used in the CSV file"""
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as file:
                # Read first few lines to detect delimiter
                sample = file.read(1024)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                logger.info(f"Detected delimiter: '{delimiter}'")
                return delimiter
        except Exception as e:
            logger.warning(f"Could not detect delimiter, using default comma: {str(e)}")
            return ','
    
    def validate_csv_structure(self) -> bool:
        """Validate if the CSV file has a proper structure"""
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as file:
                reader = csv.reader(file)
                header = next(reader)
                
                # Check if header exists and has reasonable number of columns
                if not header or len(header) < 1:
                    self.errors.append("CSV file has no header or invalid structure")
                    return False
                
                # Check for duplicate column names
                if len(header) != len(set(header)):
                    self.errors.append("CSV file has duplicate column names")
                    return False
                
                return True
                
        except Exception as e:
            error_msg = f"Error validating CSV structure: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return False

