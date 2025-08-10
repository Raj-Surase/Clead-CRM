import json
from typing import List, Dict, Any, Optional, Union
import logging
from .file_parser_base import BaseFileParser

logger = logging.getLogger(__name__)

class JSONParser(BaseFileParser):
    """Parser for JSON files"""
    
    def __init__(self, file_path: str, encoding: str = 'utf-8'):
        super().__init__(file_path)
        self.encoding = encoding
        
    def parse(self) -> List[Dict[str, Any]]:
        """Parse JSON file and return list of dictionaries"""
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as file:
                data = json.load(file)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # JSON array of objects
                self.total_rows = len(data)
                self._process_json_array(data)
            elif isinstance(data, dict):
                # Single JSON object or nested structure
                if self._is_single_lead_object(data):
                    # Single lead object
                    self.total_rows = 1
                    self._process_single_object(data)
                else:
                    # Nested structure - try to find the leads array
                    leads_data = self._extract_leads_from_nested_json(data)
                    if leads_data:
                        self.total_rows = len(leads_data)
                        self._process_json_array(leads_data)
                    else:
                        # Treat as single object
                        self.total_rows = 1
                        self._process_single_object(data)
            else:
                raise ValueError("JSON file must contain an object or array")
            
            logger.info(f"Successfully processed {self.processed_rows} out of {self.total_rows} JSON records")
            return self.data
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Error parsing JSON file: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            raise
    
    def _process_json_array(self, data: List[Dict[str, Any]]) -> None:
        """Process JSON array of objects"""
        for index, item in enumerate(data):
            try:
                if not isinstance(item, dict):
                    error_msg = f"Item at index {index} is not a valid object"
                    self.errors.append(error_msg)
                    continue
                
                # Flatten nested objects if needed
                flattened_item = self._flatten_json_object(item)
                
                # Normalize field names
                normalized_item = self.normalize_field_names(flattened_item)
                
                # Add row number for tracking
                normalized_item['source_file_row'] = index + 1
                
                self.data.append(normalized_item)
                self.processed_rows += 1
                
            except Exception as e:
                error_msg = f"Error processing JSON item at index {index}: {str(e)}"
                self.errors.append(error_msg)
                logger.warning(error_msg)
    
    def _process_single_object(self, data: Dict[str, Any]) -> None:
        """Process single JSON object"""
        try:
            # Flatten nested objects if needed
            flattened_data = self._flatten_json_object(data)
            
            # Normalize field names
            normalized_data = self.normalize_field_names(flattened_data)
            
            # Add row number for tracking
            normalized_data['source_file_row'] = 1
            
            self.data.append(normalized_data)
            self.processed_rows += 1
            
        except Exception as e:
            error_msg = f"Error processing JSON object: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
    
    def _flatten_json_object(self, obj: Dict[str, Any], parent_key: str = '', separator: str = '_') -> Dict[str, Any]:
        """Flatten nested JSON object"""
        items = []
        
        for key, value in obj.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                items.extend(self._flatten_json_object(value, new_key, separator).items())
            elif isinstance(value, list):
                # Handle arrays
                if value and isinstance(value[0], dict):
                    # Array of objects - flatten each object
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            items.extend(self._flatten_json_object(item, f"{new_key}_{i}", separator).items())
                        else:
                            items.append((f"{new_key}_{i}", item))
                else:
                    # Array of primitives - join as string
                    items.append((new_key, ', '.join(map(str, value)) if value else None))
            else:
                items.append((new_key, value))
        
        return dict(items)
    
    def _is_single_lead_object(self, data: Dict[str, Any]) -> bool:
        """Check if the JSON object represents a single lead"""
        # Look for common lead fields
        lead_indicators = [
            'name', 'full_name', 'first_name', 'last_name',
            'email', 'phone', 'company', 'linkedin'
        ]
        
        keys = [key.lower() for key in data.keys()]
        return any(indicator in keys for indicator in lead_indicators)
    
    def _extract_leads_from_nested_json(self, data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Try to extract leads array from nested JSON structure"""
        # Common keys that might contain leads data
        possible_keys = [
            'leads', 'contacts', 'people', 'users', 'customers',
            'prospects', 'data', 'results', 'items', 'records'
        ]
        
        for key in possible_keys:
            if key in data and isinstance(data[key], list):
                logger.info(f"Found leads data in '{key}' field")
                return data[key]
        
        # Try case-insensitive search
        for key, value in data.items():
            if key.lower() in possible_keys and isinstance(value, list):
                logger.info(f"Found leads data in '{key}' field (case-insensitive)")
                return value
        
        return None
    
    def validate_json_structure(self) -> bool:
        """Validate if the JSON file has a proper structure"""
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as file:
                data = json.load(file)
            
            if not isinstance(data, (dict, list)):
                self.errors.append("JSON file must contain an object or array")
                return False
            
            if isinstance(data, list) and len(data) == 0:
                self.errors.append("JSON array is empty")
                return False
            
            if isinstance(data, dict) and len(data) == 0:
                self.errors.append("JSON object is empty")
                return False
            
            return True
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return False
        except Exception as e:
            error_msg = f"Error validating JSON structure: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return False

