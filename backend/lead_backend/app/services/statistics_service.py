from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from collections import defaultdict
import redis
import json
from config.settings import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

from lead_backend.app.models.lead import Lead

class StatisticsService:
    def __init__(self):
        pass
    
    def get_lead_statistics(self, user_id: str, db: Session) -> Dict[str, Any]:
        """Get overall lead statistics for a user"""
        cache_key = f"stats:{user_id}"
        cached_stats = redis_client.get(cache_key)
        
        if cached_stats:
            return json.loads(cached_stats)
        
        total_leads = db.query(Lead).filter(Lead.user_id == user_id).count()
        
        # Contact information statistics
        email_count = db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.email.isnot(None)
        ).count()
        phone_count = db.query(Lead).filter(
            Lead.user_id == user_id,
            or_(Lead.phone.isnot(None), Lead.mobile.isnot(None))
        ).count()
        
        # Social profile statistics
        linkedin_count = db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.linkedin_url.isnot(None)
        ).count()
        facebook_count = db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.facebook_url.isnot(None)
        ).count()
        instagram_count = db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.instagram_url.isnot(None)
        ).count()
        twitter_count = db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.twitter_url.isnot(None)
        ).count()
        youtube_count = db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.youtube_url.isnot(None)
        ).count()
        tiktok_count = db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.tiktok_url.isnot(None)
        ).count()
        
        stats = {
            "total_leads": total_leads,
            "contact_info": {
                "email_valid": email_count,
                "phone_valid": phone_count,
                "email_percentage": (email_count / total_leads * 100) if total_leads > 0 else 0,
                "phone_percentage": (phone_count / total_leads * 100) if total_leads > 0 else 0
            },
            "social_profiles": {
                "linkedin": linkedin_count,
                "facebook": facebook_count,
                "instagram": instagram_count,
                "linkedin_percentage": (linkedin_count / total_leads * 100) if total_leads > 0 else 0,
            }
        }
        
        redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, json.dumps(stats))
        
        return stats
    
    def group_leads_by_location(self, user_id: str, filters: Dict[str, Any] = None, db: Session = None) -> Dict[str, Any]:
        """Group leads by location (country/state/city) for a user"""
        cache_key = f"location_groups:{user_id}:{json.dumps(filters, sort_keys=True)}"
        cached_result = redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        query = db.query(Lead.country, Lead.state, Lead.city, func.count(Lead.id)).filter(Lead.user_id == user_id)
        
        if filters:
            query = self._apply_filters_to_query(query, filters)
        
        results = query.group_by(Lead.country, Lead.state, Lead.city).all()
        
        groups = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        total_leads = 0
        
        for country, state, city, count in results:
            country_name = country or "Unknown"
            state_name = state or "Unknown"
            city_name = city or "Unknown"
            groups[country_name][state_name][city_name] = count
            total_leads += count
        
        result = {
            "groups": dict(groups),
            "total_leads": total_leads,
            "group_type": "location"
        }
        
        redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, json.dumps(result))
        
        return result
    
    def group_leads_by_engagement(self, user_id: str, filters: Dict[str, Any] = None, db: Session = None) -> Dict[str, Any]:
        """Group leads by engagement level based on contact information availability for a user"""
        cache_key = f"engagement_groups:{user_id}:{json.dumps(filters, sort_keys=True)}"
        cached_result = redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        query = db.query(Lead).filter(Lead.user_id == user_id)
        
        if filters:
            query = self._apply_filters_to_query(query, filters)
        
        leads = query.all()
        
        groups = {
            "no_contact_info": 0,
            "basic_contact_info": 0,
            "multiple_contact_points": 0
        }
        
        for lead in leads:
            contact_points = 0
            
            if lead.email:
                contact_points += 1
            if lead.phone or lead.mobile:
                contact_points += 1
            if lead.linkedin_url:
                contact_points += 1
            if lead.facebook_url:
                contact_points += 1
            if lead.instagram_url:
                contact_points += 1
            if lead.twitter_url:
                contact_points += 1
            if lead.youtube_url:
                contact_points += 1
            if lead.tiktok_url:
                contact_points += 1
            
            if contact_points == 0:
                groups["no_contact_info"] += 1
            elif contact_points <= 2:
                groups["basic_contact_info"] += 1
            else:
                groups["multiple_contact_points"] += 1
        
        result = {
            "groups": groups,
            "total_leads": len(leads),
            "group_type": "engagement"
        }
        
        redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, json.dumps(result))
        
        return result
    
    def _apply_filters_to_query(self, query, filters: Dict[str, Any]):
        """Apply filters to a SQLAlchemy query"""
        if filters.get("industry"):
            query = query.filter(Lead.industry == filters["industry"])
        
        if filters.get("company"):
            query = query.filter(Lead.company.contains(filters["company"]))
        
        if filters.get("job_title"):
            query = query.filter(Lead.job_title.contains(filters["job_title"]))
        
        if filters.get("country"):
            query = query.filter(Lead.country == filters["country"])
        
        if filters.get("state"):
            query = query.filter(Lead.state == filters["state"])
        
        if filters.get("city"):
            query = query.filter(Lead.city == filters["city"])
        
        return query

statistics_service = StatisticsService()