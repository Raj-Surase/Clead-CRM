from typing import Dict, Any, List, Optional, Tuple
import logging
from enum import Enum
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class LeadPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class LeadCategory(Enum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"

class OutreachChannel(Enum):
    EMAIL = "email"
    PHONE = "phone"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    MULTIPLE = "multiple"

class LeadClassifier:
    """Lead classification and scoring service"""
    
    def __init__(self):
        self.scoring_weights = {
            'email_valid': 15,
            'phone_valid': 10,
            'has_linkedin': 20,
            'has_company': 15,
            'has_job_title': 10,
            'has_full_name': 10,
            'has_location': 5,
            'social_profiles_count': 5,  # per profile
            'data_completeness': 20,  # percentage based
        }
        
        # Industry scoring modifiers
        self.industry_modifiers = {
            'Technology': 1.2,
            'Financial Services': 1.1,
            'Healthcare': 1.1,
            'Consulting': 1.15,
            'Marketing & Advertising': 1.1,
            'Real Estate': 1.0,
            'Education': 0.9,
            'Non-Profit': 0.8,
            'Government': 0.8,
        }
        
        # Job title scoring modifiers
        self.job_title_modifiers = {
            'ceo': 1.5,
            'cto': 1.4,
            'cfo': 1.4,
            'president': 1.4,
            'founder': 1.3,
            'director': 1.2,
            'manager': 1.1,
            'vp': 1.3,
            'vice president': 1.3,
            'head': 1.2,
            'lead': 1.1,
            'senior': 1.1,
        }
    
    def calculate_lead_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate lead score based on available data"""
        score = 0.0
        
        # Basic data validation scores
        if lead_data.get('email_valid'):
            score += self.scoring_weights['email_valid']
        
        if lead_data.get('phone_valid'):
            score += self.scoring_weights['phone_valid']
        
        if lead_data.get('linkedin_url'):
            score += self.scoring_weights['has_linkedin']
        
        if lead_data.get('company'):
            score += self.scoring_weights['has_company']
        
        if lead_data.get('job_title'):
            score += self.scoring_weights['has_job_title']
        
        if lead_data.get('full_name') or (lead_data.get('first_name') and lead_data.get('last_name')):
            score += self.scoring_weights['has_full_name']
        
        if lead_data.get('city') or lead_data.get('country'):
            score += self.scoring_weights['has_location']
        
        # Social profiles count
        social_count = lead_data.get('social_profiles_count', 0)
        score += social_count * self.scoring_weights['social_profiles_count']
        
        # Data completeness score
        completeness = lead_data.get('data_completeness_score', 0)
        score += (completeness / 100) * self.scoring_weights['data_completeness']
        
        # Apply industry modifier
        industry = lead_data.get('industry')
        if industry and industry in self.industry_modifiers:
            score *= self.industry_modifiers[industry]
        
        # Apply job title modifier
        job_title = lead_data.get('job_title', '').lower()
        for title_keyword, modifier in self.job_title_modifiers.items():
            if title_keyword in job_title:
                score *= modifier
                break  # Apply only the first matching modifier
        
        # Ensure score is between 0 and 100
        return min(100.0, max(0.0, round(score, 2)))
    
    def classify_lead_priority(self, lead_score: float, lead_data: Dict[str, Any]) -> LeadPriority:
        """Classify lead priority based on score and other factors"""
        # High-value indicators that bump priority
        high_value_indicators = [
            lead_data.get('job_title', '').lower() in ['ceo', 'cto', 'cfo', 'president', 'founder'],
            lead_data.get('company') and len(lead_data['company']) > 0,
            lead_data.get('linkedin_url') and 'linkedin.com' in lead_data['linkedin_url'],
            lead_data.get('email_valid', False),
        ]
        
        high_value_count = sum(high_value_indicators)
        
        if lead_score >= 80 or high_value_count >= 3:
            return LeadPriority.URGENT
        elif lead_score >= 60 or high_value_count >= 2:
            return LeadPriority.HIGH
        elif lead_score >= 40 or high_value_count >= 1:
            return LeadPriority.MEDIUM
        else:
            return LeadPriority.LOW
    
    def classify_lead_category(self, lead_data: Dict[str, Any]) -> LeadCategory:
        """Classify lead category based on available data"""
        score = self.calculate_lead_score(lead_data)
        
        # Check for qualification criteria
        has_email = lead_data.get('email_valid', False)
        has_contact = has_email or lead_data.get('phone_valid', False)
        has_company = bool(lead_data.get('company'))
        has_job_title = bool(lead_data.get('job_title'))
        has_social = lead_data.get('social_profiles_count', 0) > 0
        
        # Qualified leads have good contact info and professional details
        if has_contact and has_company and has_job_title and score >= 60:
            return LeadCategory.QUALIFIED
        
        # Hot leads have multiple contact methods and high scores
        if has_email and has_social and score >= 70:
            return LeadCategory.HOT
        
        # Warm leads have some contact info and decent scores
        if has_contact and (has_company or has_social) and score >= 40:
            return LeadCategory.WARM
        
        # Cold leads have minimal info
        if has_contact and score >= 20:
            return LeadCategory.COLD
        
        # Unqualified leads lack basic contact info
        return LeadCategory.UNQUALIFIED
    
    def determine_best_outreach_channels(self, lead_data: Dict[str, Any]) -> List[OutreachChannel]:
        """Determine the best outreach channels for a lead"""
        channels = []
        
        # Email is preferred if valid
        if lead_data.get('email_valid'):
            channels.append(OutreachChannel.EMAIL)
        
        # Phone if valid
        if lead_data.get('phone_valid'):
            channels.append(OutreachChannel.PHONE)
        
        # Social media channels in order of preference for B2B
        if lead_data.get('linkedin_url'):
            channels.append(OutreachChannel.LINKEDIN)
        
        if lead_data.get('twitter_url'):
            channels.append(OutreachChannel.TWITTER)
        
        if lead_data.get('facebook_url'):
            channels.append(OutreachChannel.FACEBOOK)
        
        if lead_data.get('instagram_url'):
            channels.append(OutreachChannel.INSTAGRAM)
        
        return channels if channels else []
    
    def classify_by_social_presence(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify lead based on social media presence"""
        social_platforms = []
        social_strength = 0
        
        social_urls = {
            'LinkedIn': lead_data.get('linkedin_url'),
            'Facebook': lead_data.get('facebook_url'),
            'Instagram': lead_data.get('instagram_url'),
            'Twitter': lead_data.get('twitter_url'),
            'YouTube': lead_data.get('youtube_url'),
            'TikTok': lead_data.get('tiktok_url'),
        }
        
        for platform, url in social_urls.items():
            if url:
                social_platforms.append(platform)
                # LinkedIn gets higher weight for B2B
                if platform == 'LinkedIn':
                    social_strength += 3
                elif platform in ['Twitter', 'Facebook']:
                    social_strength += 2
                else:
                    social_strength += 1
        
        # Classify social presence strength
        if social_strength >= 6:
            social_category = "strong"
        elif social_strength >= 3:
            social_category = "moderate"
        elif social_strength >= 1:
            social_category = "weak"
        else:
            social_category = "none"
        
        return {
            'social_platforms': social_platforms,
            'social_strength': social_strength,
            'social_category': social_category,
            'primary_social_platform': social_platforms[0] if social_platforms else None
        }
    
    def classify_by_company_size(self, company_name: str) -> Optional[str]:
        """Estimate company size category based on company name"""
        if not company_name:
            return None
        
        company_lower = company_name.lower()
        
        # Large enterprise indicators
        enterprise_indicators = [
            'corporation', 'corp', 'inc', 'incorporated', 'ltd', 'limited',
            'international', 'global', 'worldwide', 'group', 'holdings'
        ]
        
        # Small business indicators
        small_business_indicators = [
            'llc', 'consulting', 'services', 'solutions', 'studio', 'agency',
            'freelance', 'independent', 'boutique'
        ]
        
        for indicator in enterprise_indicators:
            if indicator in company_lower:
                return "enterprise"
        
        for indicator in small_business_indicators:
            if indicator in company_lower:
                return "small_business"
        
        # Default to medium if no clear indicators
        return "medium_business"
    
    def generate_lead_tags(self, lead_data: Dict[str, Any]) -> List[str]:
        """Generate relevant tags for a lead"""
        tags = []
        
        # Industry tag
        if lead_data.get('industry'):
            tags.append(f"industry:{lead_data['industry'].lower().replace(' ', '_')}")
        
        # Location tags
        if lead_data.get('country'):
            tags.append(f"country:{lead_data['country'].lower().replace(' ', '_')}")
        
        if lead_data.get('city'):
            tags.append(f"city:{lead_data['city'].lower().replace(' ', '_')}")
        
        # Job level tags
        job_title = lead_data.get('job_title', '').lower()
        if any(title in job_title for title in ['ceo', 'president', 'founder']):
            tags.append("job_level:executive")
        elif any(title in job_title for title in ['director', 'vp', 'vice president']):
            tags.append("job_level:director")
        elif any(title in job_title for title in ['manager', 'head', 'lead']):
            tags.append("job_level:manager")
        elif any(title in job_title for title in ['senior', 'sr']):
            tags.append("job_level:senior")
        else:
            tags.append("job_level:individual_contributor")
        
        # Contact method tags
        if lead_data.get('email_valid'):
            tags.append("contact:email")
        
        if lead_data.get('phone_valid'):
            tags.append("contact:phone")
        
        # Social presence tags
        social_classification = self.classify_by_social_presence(lead_data)
        if social_classification['social_category'] != 'none':
            tags.append(f"social:{social_classification['social_category']}")
        
        for platform in social_classification['social_platforms']:
            tags.append(f"social_platform:{platform.lower()}")
        
        # Company size tag
        company_size = self.classify_by_company_size(lead_data.get('company', ''))
        if company_size:
            tags.append(f"company_size:{company_size}")
        
        # Lead quality tags
        score = self.calculate_lead_score(lead_data)
        if score >= 80:
            tags.append("quality:high")
        elif score >= 60:
            tags.append("quality:medium")
        else:
            tags.append("quality:low")
        
        return tags
    
    def classify_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform complete lead classification"""
        # Calculate lead score
        lead_score = self.calculate_lead_score(lead_data)
        
        # Classify priority and category
        priority = self.classify_lead_priority(lead_score, lead_data)
        category = self.classify_lead_category(lead_data)
        
        # Determine outreach channels
        outreach_channels = self.determine_best_outreach_channels(lead_data)
        
        # Social media classification
        social_classification = self.classify_by_social_presence(lead_data)
        
        # Generate tags
        tags = self.generate_lead_tags(lead_data)
        
        return {
            'lead_score': lead_score,
            'priority': priority.value,
            'category': category.value,
            'outreach_channels': [channel.value for channel in outreach_channels],
            'primary_outreach_channel': outreach_channels[0].value if outreach_channels else None,
            'social_classification': social_classification,
            'generated_tags': tags,
            'company_size_estimate': self.classify_by_company_size(lead_data.get('company', '')),
        }

