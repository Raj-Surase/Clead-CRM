import pandas as pd
import json
import csv
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseFileParser(ABC):
    """Base class for file parsers"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.total_rows = 0
        self.processed_rows = 0
        
    @abstractmethod
    def parse(self) -> List[Dict[str, Any]]:
        """Parse the file and return list of dictionaries"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        return {
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "errors": self.errors,
            "success_rate": (self.processed_rows / self.total_rows * 100) if self.total_rows > 0 else 0
        }
    
    def normalize_field_names(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field names to match our schema"""
        field_mapping = {
            # Name variations
            'name': 'full_name',
            'fullname': 'full_name',
            'full_name': 'full_name',
            'firstname': 'first_name',
            'first_name': 'first_name',
            'fname': 'first_name',
            'lastname': 'last_name',
            'last_name': 'last_name',
            'lname': 'last_name',
            'surname': 'last_name',
            
            # Contact variations
            'email_address': 'email',
            'email': 'email',
            'e_mail': 'email',
            'mail': 'email',
            'phone_number': 'phone',
            'phone': 'phone',
            'tel': 'phone',
            'telephone': 'phone',
            'mobile_number': 'mobile',
            'mobile': 'mobile',
            'cell': 'mobile',
            'cellphone': 'mobile',
            
            # Company variations
            'company_name': 'company',
            'company': 'company',
            'organization': 'company',
            'org': 'company',
            'employer': 'company',
            'business': 'company',
            
            # Job variations
            'job_title': 'job_title',
            'title': 'job_title',
            'position': 'job_title',
            'role': 'job_title',
            'designation': 'job_title',
            
            # Location variations
            'address': 'address',
            'street_address': 'address',
            'city': 'city',
            'state': 'state',
            'province': 'state',
            'country': 'country',
            'postal_code': 'postal_code',
            'zip_code': 'postal_code',
            'zip': 'postal_code',
            
            # Social media variations
            'linkedin': 'linkedin_url',
            'linkedin_url': 'linkedin_url',
            'linkedin_profile': 'linkedin_url',
            'facebook': 'facebook_url',
            'facebook_url': 'facebook_url',
            'facebook_profile': 'facebook_url',
            'instagram': 'instagram_url',
            'instagram_url': 'instagram_url',
            'instagram_profile': 'instagram_url',
            'twitter': 'twitter_url',
            'twitter_url': 'twitter_url',
            'twitter_profile': 'twitter_url',
            'youtube': 'youtube_url',
            'youtube_url': 'youtube_url',
            'youtube_channel': 'youtube_url',
            'tiktok': 'tiktok_url',
            'tiktok_url': 'tiktok_url',
            'tiktok_profile': 'tiktok_url',
            
            # Website variations
            'website': 'website',
            'website_url': 'website',
            'web': 'website',
            'url': 'website',
            'homepage': 'website',
            
            # Industry variations
            'industry': 'industry',
            'sector': 'industry',
            'business_type': 'industry',
            
            # Notes variations
            'notes': 'notes',
            'comments': 'notes',
            'remarks': 'notes',
            'description': 'notes',
        }
        
        normalized_data = {}
        additional_data = {}
        
        for key, value in data.items():
            # Convert key to lowercase and remove spaces/underscores for matching
            normalized_key = key.lower().replace(' ', '_').replace('-', '_')
            
            if normalized_key in field_mapping:
                mapped_field = field_mapping[normalized_key]
                normalized_data[mapped_field] = value
            else:
                # Store unmapped fields in additional_data
                additional_data[key] = value
        
        # Add additional_data if there are unmapped fields
        if additional_data:
            normalized_data['additional_data'] = additional_data
            
        return normalized_data

