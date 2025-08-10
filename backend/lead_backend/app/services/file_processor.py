from typing import List, Dict, Any, Optional, Type
import logging
from pathlib import Path
from .file_parser_base import BaseFileParser
from .csv_parser import CSVParser
from .json_parser import JSONParser
from .xlsx_parser import XLSXParser

logger = logging.getLogger(__name__)

class FileParserFactory:
    """Factory class to create appropriate file parsers based on file type"""
    
    SUPPORTED_EXTENSIONS = {
        '.csv': CSVParser,
        '.json': JSONParser,
        '.xlsx': XLSXParser,
        '.xls': XLSXParser,
    }
    
    @classmethod
    def create_parser(cls, file_path: str, **kwargs) -> BaseFileParser:
        """Create appropriate parser based on file extension"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {extension}. Supported types: {list(cls.SUPPORTED_EXTENSIONS.keys())}")
        
        parser_class = cls.SUPPORTED_EXTENSIONS[extension]
        
        # Pass additional arguments to parser constructor
        if extension == '.csv':
            encoding = kwargs.get('encoding', 'utf-8')
            delimiter = kwargs.get('delimiter', ',')
            return parser_class(file_path, encoding=encoding, delimiter=delimiter)
        elif extension == '.json':
            encoding = kwargs.get('encoding', 'utf-8')
            return parser_class(file_path, encoding=encoding)
        elif extension in ['.xlsx', '.xls']:
            sheet_name = kwargs.get('sheet_name', None)
            return parser_class(file_path, sheet_name=sheet_name)
        else:
            return parser_class(file_path)
    
    @classmethod
    def is_supported_file(cls, file_path: str) -> bool:
        """Check if file type is supported"""
        path = Path(file_path)
        extension = path.suffix.lower()
        return extension in cls.SUPPORTED_EXTENSIONS
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of supported file extensions"""
        return list(cls.SUPPORTED_EXTENSIONS.keys())

class FileProcessor:
    """High-level file processing service"""
    
    def __init__(self):
        self.parser: Optional[BaseFileParser] = None
        self.processed_data: List[Dict[str, Any]] = []
        self.processing_stats: Dict[str, Any] = {}
    
    def process_file(self, file_path: str, **parser_kwargs) -> Dict[str, Any]:
        """Process a file and return the results"""
        try:
            # Validate file exists
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Create appropriate parser
            self.parser = FileParserFactory.create_parser(file_path, **parser_kwargs)
            
            # Validate file structure before parsing
            if hasattr(self.parser, 'validate_csv_structure'):
                if not self.parser.validate_csv_structure():
                    raise ValueError("Invalid CSV file structure")
            elif hasattr(self.parser, 'validate_json_structure'):
                if not self.parser.validate_json_structure():
                    raise ValueError("Invalid JSON file structure")
            elif hasattr(self.parser, 'validate_excel_structure'):
                if not self.parser.validate_excel_structure():
                    raise ValueError("Invalid Excel file structure")
            
            # Parse the file
            logger.info(f"Starting to parse file: {file_path}")
            self.processed_data = self.parser.parse()
            
            # Get processing statistics
            self.processing_stats = self.parser.get_stats()
            self.processing_stats['file_path'] = file_path
            self.processing_stats['file_type'] = Path(file_path).suffix.lower()
            
            logger.info(f"File processing completed. Processed {len(self.processed_data)} records")
            
            return {
                'success': True,
                'data': self.processed_data,
                'stats': self.processing_stats,
                'errors': self.parser.errors
            }
            
        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'data': [],
                'stats': self.processing_stats,
                'errors': [error_msg] + (self.parser.errors if self.parser else [])
            }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file without fully parsing it"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_info = {
                'file_name': path.name,
                'file_size': path.stat().st_size,
                'file_type': path.suffix.lower(),
                'is_supported': FileParserFactory.is_supported_file(file_path)
            }
            
            if not file_info['is_supported']:
                return file_info
            
            # Get type-specific information
            if path.suffix.lower() in ['.xlsx', '.xls']:
                parser = XLSXParser(file_path)
                file_info['sheets'] = parser.get_sheet_names()
                file_info['sheet_info'] = parser.get_sheet_info()
            elif path.suffix.lower() == '.csv':
                parser = CSVParser(file_path)
                file_info['detected_delimiter'] = parser.detect_delimiter()
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return {
                'error': str(e),
                'file_name': Path(file_path).name if Path(file_path).exists() else 'unknown'
            }

