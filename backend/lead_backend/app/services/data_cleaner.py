from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from difflib import SequenceMatcher
from .data_validator import DataValidator
from lead_backend.app.models.schemas import LeadCreate

logger = logging.getLogger(__name__)

class DataCleaner:
    """Data cleaning and normalization service"""
    
    def __init__(self):
        self.validator = DataValidator()
        self.processed_emails: Set[str] = set()
        self.processed_phones: Set[str] = set()
        self.duplicate_threshold = 0.85  # Similarity threshold for duplicate detection
    
    def clean_lead_data(self, raw_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Clean and validate a single lead's data"""
        cleaned_data = {}
        warnings = []
        
        # Clean name fields
        if raw_data.get('first_name'):
            cleaned_data['first_name'] = self.validator.clean_name(raw_data['first_name'])
        
        if raw_data.get('last_name'):
            cleaned_data['last_name'] = self.validator.clean_name(raw_data['last_name'])
        
        if raw_data.get('full_name'):
            cleaned_data['full_name'] = self.validator.clean_name(raw_data['full_name'])
        elif cleaned_data.get('first_name') and cleaned_data.get('last_name'):
            # Generate full name if not provided
            cleaned_data['full_name'] = f"{cleaned_data['first_name']} {cleaned_data['last_name']}"
        
        # Clean company information
        if raw_data.get('company'):
            cleaned_data['company'] = self.validator.clean_company_name(raw_data['company'])
        
        if raw_data.get('job_title'):
            cleaned_data['job_title'] = raw_data['job_title'].strip() if raw_data['job_title'] else None
        
        if raw_data.get('industry'):
            cleaned_data['industry'] = raw_data['industry'].strip() if raw_data['industry'] else None
        
        # Clean and validate email
        if raw_data.get('email'):
            cleaned_email, is_valid = self.validator.validate_and_clean_email(raw_data['email'])
            if cleaned_email:
                cleaned_data['email'] = cleaned_email
                cleaned_data['email_valid'] = is_valid
                if not is_valid:
                    warnings.append(f"Email '{raw_data['email']}' appears to be invalid")
            else:
                warnings.append(f"Could not clean email '{raw_data['email']}'")
        
        # Clean and validate phone numbers
        if raw_data.get('phone'):
            cleaned_phone, is_valid = self.validator.validate_and_clean_phone(raw_data['phone'])
            if cleaned_phone:
                cleaned_data['phone'] = cleaned_phone
                cleaned_data['phone_valid'] = is_valid
                if not is_valid:
                    warnings.append(f"Phone '{raw_data['phone']}' appears to be invalid")
        
        if raw_data.get('mobile'):
            cleaned_mobile, is_valid = self.validator.validate_and_clean_phone(raw_data['mobile'])
            if cleaned_mobile:
                cleaned_data['mobile'] = cleaned_mobile
                # Update phone_valid if mobile is valid and phone wasn't
                if is_valid and not cleaned_data.get('phone_valid', False):
                    cleaned_data['phone_valid'] = True
        
        # Clean address information
        if raw_data.get('address'):
            cleaned_data['address'] = self.validator.clean_address(raw_data['address'])
        
        for field in ['city', 'state', 'country', 'postal_code']:
            if raw_data.get(field):
                cleaned_data[field] = raw_data[field].strip()
        
        # Clean and validate website
        if raw_data.get('website'):
            cleaned_url, is_valid = self.validator.validate_and_clean_url(raw_data['website'])
            if cleaned_url:
                cleaned_data['website'] = cleaned_url
                if not is_valid:
                    warnings.append(f"Website URL '{raw_data['website']}' appears to be invalid")
        
        # Clean and validate social media URLs
        social_platforms = {
            'linkedin_url': 'linkedin',
            'facebook_url': 'facebook',
            'instagram_url': 'instagram',
            'twitter_url': 'twitter',
            'youtube_url': 'youtube',
            'tiktok_url': 'tiktok'
        }
        
        social_count = 0
        for field, platform in social_platforms.items():
            if raw_data.get(field):
                cleaned_url, is_valid = self.validator.validate_social_media_url(
                    raw_data[field], platform
                )
                if cleaned_url:
                    cleaned_data[field] = cleaned_url
                    if is_valid:
                        social_count += 1
                    else:
                        warnings.append(f"{platform.title()} URL '{raw_data[field]}' doesn't match expected format")
        
        cleaned_data['social_profiles_count'] = social_count
        
        # Handle additional data
        if raw_data.get('additional_data'):
            cleaned_data['additional_data'] = raw_data['additional_data']
        
        # Copy other fields as-is
        for field in ['notes', 'tags', 'lead_source', 'priority']:
            if raw_data.get(field):
                cleaned_data[field] = raw_data[field]
        
        # Copy source file information
        if raw_data.get('source_file_row'):
            cleaned_data['source_file_row'] = raw_data['source_file_row']
        
        return cleaned_data, warnings
    
    def clean_batch_data(self, raw_data_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Clean a batch of lead data"""
        cleaned_data_list = []
        all_warnings = []
        stats = {
            'total_records': len(raw_data_list),
            'cleaned_records': 0,
            'records_with_warnings': 0,
            'total_warnings': 0,
            'duplicate_records': 0
        }
        
        # Reset tracking sets for this batch
        self.processed_emails.clear()
        self.processed_phones.clear()
        
        for i, raw_data in enumerate(raw_data_list):
            try:
                cleaned_data, warnings = self.clean_lead_data(raw_data)
                
                # Check for duplicates within this batch
                is_duplicate = self._check_for_duplicates(cleaned_data)
                if is_duplicate:
                    cleaned_data['is_duplicate'] = True
                    stats['duplicate_records'] += 1
                    warnings.append("Potential duplicate record detected")
                
                cleaned_data_list.append(cleaned_data)
                stats['cleaned_records'] += 1
                
                if warnings:
                    stats['records_with_warnings'] += 1
                    stats['total_warnings'] += len(warnings)
                    all_warnings.extend([f"Record {i+1}: {w}" for w in warnings])
                
                # Track processed emails and phones for duplicate detection
                if cleaned_data.get('email'):
                    self.processed_emails.add(cleaned_data['email'].lower())
                if cleaned_data.get('phone'):
                    self.processed_phones.add(cleaned_data['phone'])
                
            except Exception as e:
                error_msg = f"Error cleaning record {i+1}: {str(e)}"
                logger.error(error_msg)
                all_warnings.append(error_msg)
        
        stats['warnings'] = all_warnings
        return cleaned_data_list, stats
    
    def _check_for_duplicates(self, lead_data: Dict[str, Any]) -> bool:
        """Check if lead data is a duplicate of previously processed data"""
        email = lead_data.get('email', '').lower()
        phone = lead_data.get('phone', '')
        
        # Check email duplicates
        if email and email in self.processed_emails:
            return True
        
        # Check phone duplicates
        if phone and phone in self.processed_phones:
            return True
        
        return False
    
    def find_similar_leads(self, lead_data: Dict[str, Any], existing_leads: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """Find similar leads in existing data"""
        similar_leads = []
        
        lead_name = lead_data.get('full_name', '').lower()
        lead_email = lead_data.get('email', '').lower()
        lead_company = lead_data.get('company', '').lower()
        
        for existing_lead in existing_leads:
            similarity_score = 0.0
            factors = 0
            
            # Compare names
            if lead_name and existing_lead.get('full_name'):
                name_similarity = SequenceMatcher(None, lead_name, existing_lead['full_name'].lower()).ratio()
                similarity_score += name_similarity * 0.4
                factors += 0.4
            
            # Compare emails (exact match gets high score)
            if lead_email and existing_lead.get('email'):
                if lead_email == existing_lead['email'].lower():
                    similarity_score += 0.5
                factors += 0.5
            
            # Compare companies
            if lead_company and existing_lead.get('company'):
                company_similarity = SequenceMatcher(None, lead_company, existing_lead['company'].lower()).ratio()
                similarity_score += company_similarity * 0.1
                factors += 0.1
            
            # Calculate final similarity score
            if factors > 0:
                final_score = similarity_score / factors
                if final_score >= self.duplicate_threshold:
                    similar_leads.append((existing_lead, final_score))
        
        # Sort by similarity score (highest first)
        similar_leads.sort(key=lambda x: x[1], reverse=True)
        return similar_leads
    
    def normalize_industry(self, industry: str) -> Optional[str]:
        """Normalize industry names to standard categories"""
        if not industry:
            return None
        
        industry_lower = industry.lower().strip()
        
        # Industry mapping for common variations
        industry_mapping = {
            'tech': 'Technology',
            'technology': 'Technology',
            'software': 'Technology',
            'it': 'Technology',
            'information technology': 'Technology',
            'healthcare': 'Healthcare',
            'health care': 'Healthcare',
            'medical': 'Healthcare',
            'finance': 'Financial Services',
            'financial': 'Financial Services',
            'banking': 'Financial Services',
            'insurance': 'Financial Services',
            'real estate': 'Real Estate',
            'realestate': 'Real Estate',
            'education': 'Education',
            'manufacturing': 'Manufacturing',
            'retail': 'Retail',
            'consulting': 'Consulting',
            'marketing': 'Marketing & Advertising',
            'advertising': 'Marketing & Advertising',
            'legal': 'Legal',
            'law': 'Legal',
            'construction': 'Construction',
            'automotive': 'Automotive',
            'energy': 'Energy',
            'telecommunications': 'Telecommunications',
            'telecom': 'Telecommunications',
            'media': 'Media & Entertainment',
            'entertainment': 'Media & Entertainment',
            'nonprofit': 'Non-Profit',
            'non-profit': 'Non-Profit',
            'government': 'Government',
            'agriculture': 'Agriculture',
            'transportation': 'Transportation',
            'logistics': 'Transportation',
            'hospitality': 'Hospitality',
            'travel': 'Hospitality',
            'food': 'Food & Beverage',
            'restaurant': 'Food & Beverage',
        }
        
        # Check for exact matches first
        if industry_lower in industry_mapping:
            return industry_mapping[industry_lower]
        
        # Check for partial matches
        for key, value in industry_mapping.items():
            if key in industry_lower:
                return value
        
        # Return original if no mapping found
        return industry.title()

