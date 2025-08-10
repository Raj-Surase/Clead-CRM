import re
import validators
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import NumberParseException
from typing import Optional, Dict, Any, Tuple
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DataValidator:
    """Data validation and cleaning service"""
    
    def __init__(self):
        self.email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.phone_regex = re.compile(r'[\+]?[1-9]?[\d\s\-\(\)\.]{7,15}')
        
    def validate_and_clean_email(self, email: str) -> Tuple[Optional[str], bool]:
        """Validate and clean email address"""
        if not email or not isinstance(email, str):
            return None, False
        
        # Clean the email
        cleaned_email = email.strip().lower()
        
        # Remove any surrounding quotes or brackets
        cleaned_email = cleaned_email.strip('"\'<>')
        
        try:
            # Use email-validator library for comprehensive validation
            valid = validate_email(cleaned_email)
            return valid.email, True
        except EmailNotValidError:
            # Fallback to regex validation
            if self.email_regex.match(cleaned_email):
                return cleaned_email, True
            return cleaned_email, False
    
    def validate_and_clean_phone(self, phone: str, default_country: str = 'US') -> Tuple[Optional[str], bool]:
        """Validate and clean phone number"""
        if not phone or not isinstance(phone, str):
            return None, False
        
        # Clean the phone number
        cleaned_phone = phone.strip()
        
        # Remove common non-numeric characters but keep + for international numbers
        cleaned_phone = re.sub(r'[^\d\+\-\(\)\s\.]', '', cleaned_phone)
        
        try:
            # Parse the phone number
            parsed_number = phonenumbers.parse(cleaned_phone, default_country)
            
            # Check if the number is valid
            if phonenumbers.is_valid_number(parsed_number):
                # Format in international format
                formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                return formatted_number, True
            else:
                # Return cleaned version even if not valid
                return cleaned_phone, False
                
        except NumberParseException:
            # If parsing fails, try to clean manually
            digits_only = re.sub(r'[^\d]', '', cleaned_phone)
            
            # Basic validation - should have 7-15 digits
            if 7 <= len(digits_only) <= 15:
                return cleaned_phone, False
            
            return cleaned_phone, False
    
    def validate_and_clean_url(self, url: str) -> Tuple[Optional[str], bool]:
        """Validate and clean URL"""
        if not url or not isinstance(url, str):
            return None, False
        
        # Clean the URL
        cleaned_url = url.strip()
        
        # Add protocol if missing
        if not cleaned_url.startswith(('http://', 'https://')):
            cleaned_url = 'https://' + cleaned_url
        
        # Validate URL
        try:
            result = validators.url(cleaned_url)
            return cleaned_url if result else None, bool(result)
        except Exception:
            return cleaned_url, False
    
    def validate_social_media_url(self, url: str, platform: str) -> Tuple[Optional[str], bool]:
        """Validate and clean social media URL for specific platform"""
        if not url or not isinstance(url, str):
            return None, False
        
        # Clean the URL first
        cleaned_url, is_valid_url = self.validate_and_clean_url(url)
        
        if not cleaned_url:
            return None, False
        
        # Platform-specific validation
        platform_patterns = {
            'linkedin': [
                r'linkedin\.com/in/',
                r'linkedin\.com/company/',
                r'linkedin\.com/pub/',
            ],
            'facebook': [
                r'facebook\.com/',
                r'fb\.com/',
                r'fb\.me/',
            ],
            'instagram': [
                r'instagram\.com/',
                r'instagr\.am/',
            ],
            'twitter': [
                r'twitter\.com/',
                r'x\.com/',
            ],
            'youtube': [
                r'youtube\.com/',
                r'youtu\.be/',
            ],
            'tiktok': [
                r'tiktok\.com/',
                r'vm\.tiktok\.com/',
            ]
        }
        
        platform_lower = platform.lower()
        if platform_lower in platform_patterns:
            patterns = platform_patterns[platform_lower]
            for pattern in patterns:
                if re.search(pattern, cleaned_url, re.IGNORECASE):
                    return cleaned_url, True
            
            # URL is valid but doesn't match platform
            return cleaned_url, False
        
        # Unknown platform, just return URL validation result
        return cleaned_url, is_valid_url
    
    def clean_name(self, name: str) -> Optional[str]:
        """Clean and standardize name"""
        if not name or not isinstance(name, str):
            return None
        
        # Remove extra whitespace and convert to title case
        cleaned_name = ' '.join(name.strip().split())
        
        # Remove special characters but keep hyphens, apostrophes, and periods
        cleaned_name = re.sub(r'[^\w\s\-\'\.]', '', cleaned_name)
        
        # Convert to title case
        cleaned_name = cleaned_name.title()
        
        return cleaned_name if cleaned_name else None
    
    def clean_company_name(self, company: str) -> Optional[str]:
        """Clean and standardize company name"""
        if not company or not isinstance(company, str):
            return None
        
        # Remove extra whitespace
        cleaned_company = ' '.join(company.strip().split())
        
        # Remove special characters except common business ones
        cleaned_company = re.sub(r'[^\w\s\-\'\.\,\&\(\)]', '', cleaned_company)
        
        return cleaned_company if cleaned_company else None
    
    def clean_address(self, address: str) -> Optional[str]:
        """Clean and standardize address"""
        if not address or not isinstance(address, str):
            return None
        
        # Remove extra whitespace and normalize
        cleaned_address = ' '.join(address.strip().split())
        
        # Remove excessive special characters but keep common address ones
        cleaned_address = re.sub(r'[^\w\s\-\'\.\,\#\(\)]', '', cleaned_address)
        
        return cleaned_address if cleaned_address else None
    
    def extract_domain_from_email(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        if not email or '@' not in email:
            return None
        
        try:
            domain = email.split('@')[1].lower()
            return domain
        except IndexError:
            return None
    
    def extract_username_from_social_url(self, url: str) -> Optional[str]:
        """Extract username from social media URL"""
        if not url:
            return None
        
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path.strip('/')
            
            # Remove common path prefixes
            prefixes_to_remove = ['in', 'company', 'pub', 'user', 'profile', '@']
            
            for prefix in prefixes_to_remove:
                if path.startswith(prefix + '/'):
                    path = path[len(prefix) + 1:]
                    break
            
            # Get the first part of the path as username
            username = path.split('/')[0] if path else None
            
            # Clean username
            if username:
                username = re.sub(r'[^\w\.\-_]', '', username)
                return username if username else None
            
            return None
            
        except Exception:
            return None

