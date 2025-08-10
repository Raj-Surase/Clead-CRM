from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, distinct
from collections import defaultdict
import redis
import json
from config.settings import settings

from outreach_backend.app.models import Lead, OutreachPlatform, LeadPlatformValidation, OutreachMessage, Conversation
from outreach_backend.app.schemas import LeadGroupingRequest, LeadGroupingResponse

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class LeadService:
    def __init__(self):
        pass
    
    def get_leads(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        filters: Dict[str, Any] = None,
        lead_parser_db: Session = None
    ) -> List[Lead]:
        """Get leads with optional filtering for a specific user"""
        cache_key = f"leads:{user_id}:{skip}:{limit}:{json.dumps(filters or {})}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return [Lead(**lead) for lead in json.loads(cached_data)]
            
        query = lead_parser_db.query(Lead).filter(Lead.user_id == user_id)
        
        if filters:
            if filters.get("industry"):
                query = query.filter(Lead.industry == filters["industry"])
            
            if filters.get("lead_status"):
                query = query.filter(Lead.lead_status == filters["lead_status"])
            
            if filters.get("lead_source"):
                query = query.filter(Lead.lead_source == filters["lead_source"])
            
            if filters.get("priority"):
                query = query.filter(Lead.priority == filters["priority"])
            
            if filters.get("country"):
                query = query.filter(Lead.country == filters["country"])
            
            if filters.get("state"):
                query = query.filter(Lead.state == filters["state"])
            
            if filters.get("city"):
                query = query.filter(Lead.city == filters["city"])
            
            if filters.get("company"):
                query = query.filter(Lead.company.contains(filters["company"]))
            
            if filters.get("job_title"):
                query = query.filter(Lead.job_title.contains(filters["job_title"]))
            
            if filters.get("email_valid") is not None:
                query = query.filter(Lead.email_valid == filters["email_valid"])
            
            if filters.get("phone_valid") is not None:
                query = query.filter(Lead.phone_valid == filters["phone_valid"])
            
            if filters.get("min_lead_score"):
                query = query.filter(Lead.lead_score >= filters["min_lead_score"])
            
            if filters.get("max_lead_score"):
                query = query.filter(Lead.lead_score <= filters["max_lead_score"])
            
            if filters.get("min_data_completeness"):
                query = query.filter(Lead.data_completeness_score >= filters["min_data_completeness"])
            
            if filters.get("has_social_profiles"):
                if filters["has_social_profiles"]:
                    query = query.filter(
                        or_(
                            Lead.linkedin_url.isnot(None),
                            Lead.facebook_url.isnot(None),
                            Lead.instagram_url.isnot(None),
                            Lead.twitter_url.isnot(None),
                            Lead.youtube_url.isnot(None),
                            Lead.tiktok_url.isnot(None)
                        )
                    )
                else:
                    query = query.filter(
                        and_(
                            Lead.linkedin_url.is_(None),
                            Lead.facebook_url.is_(None),
                            Lead.instagram_url.is_(None),
                            Lead.twitter_url.is_(None),
                            Lead.youtube_url.is_(None),
                            Lead.tiktok_url.is_(None)
                        )
                    )
            
            if filters.get("contacted"):
                if filters["contacted"]:
                    query = query.filter(
                        or_(
                            Lead.contacted_via_email == True,
                            Lead.contacted_via_phone == True,
                            Lead.contacted_via_linkedin == True,
                            Lead.contacted_via_facebook == True,
                            Lead.contacted_via_instagram == True
                        )
                    )
                else:
                    query = query.filter(
                        and_(
                            Lead.contacted_via_email != True,
                            Lead.contacted_via_phone != True,
                            Lead.contacted_via_linkedin != True,
                            Lead.contacted_via_facebook != True,
                            Lead.contacted_via_instagram != True
                        )
                    )
        
        leads = query.offset(skip).limit(limit).all()
        
        # Cache results
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps([lead.__dict__ for lead in leads], default=str)
        )
        
        return leads
    
    def get_lead(self, user_id: str, lead_id: int, lead_parser_db: Session) -> Optional[Lead]:
        """Get a specific lead by ID for a user"""
        cache_key = f"lead:{user_id}:{lead_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return Lead(**json.loads(cached_data))
            
        lead = lead_parser_db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.user_id == user_id
        ).first()
        
        if lead:
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps(lead.__dict__, default=str)
            )
        
        return lead
    
    def search_leads(
        self,
        user_id: str,
        search_term: str,
        search_fields: List[str] = None,
        lead_parser_db: Session = None
    ) -> List[Lead]:
        """Search leads by term in specified fields for a user"""
        cache_key = f"lead_search:{user_id}:{search_term}:{':'.join(search_fields or [])}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return [Lead(**lead) for lead in json.loads(cached_data)]
            
        if not search_fields:
            search_fields = ["full_name", "company", "email", "job_title"]
        
        query = lead_parser_db.query(Lead).filter(Lead.user_id == user_id)
        conditions = []
        for field in search_fields:
            if hasattr(Lead, field):
                conditions.append(getattr(Lead, field).contains(search_term))
        
        if conditions:
            leads = query.filter(or_(*conditions)).all()
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps([lead.__dict__ for lead in leads], default=str)
            )
            return leads
        
        return []
    
    def group_leads_by_industry(self, user_id: str, filters: Dict[str, Any] = None, lead_parser_db: Session = None) -> Dict[str, Any]:
        """Group leads by industry for a user"""
        cache_key = f"lead_groups:industry:{user_id}:{json.dumps(filters or {})}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        query = lead_parser_db.query(Lead.industry, func.count(Lead.id)).filter(Lead.user_id == user_id)
        
        if filters:
            query = self._apply_filters_to_query(query, filters)
        
        results = query.group_by(Lead.industry).all()
        
        groups = {}
        total_leads = 0
        for industry, count in results:
            industry_name = industry or "Unknown"
            groups[industry_name] = count
            total_leads += count
        
        result = {
            "groups": groups,
            "total_leads": total_leads,
            "group_type": "industry"
        }
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(result)
        )
        
        return result
    
    def group_leads_by_status(self, user_id: str, filters: Dict[str, Any] = None, lead_parser_db: Session = None) -> Dict[str, Any]:
        """Group leads by status for a user"""
        cache_key = f"lead_groups:status:{user_id}:{json.dumps(filters or {})}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        query = lead_parser_db.query(Lead.lead_status, func.count(Lead.id)).filter(Lead.user_id == user_id)
        
        if filters:
            query = self._apply_filters_to_query(query, filters)
        
        results = query.group_by(Lead.lead_status).all()
        
        groups = {}
        total_leads = 0
        for status, count in results:
            status_name = status or "Unknown"
            groups[status_name] = count
            total_leads += count
        
        result = {
            "groups": groups,
            "total_leads": total_leads,
            "group_type": "status"
        }
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(result)
        )
        
        return result
    
    def group_leads_by_source(self, user_id: str, filters: Dict[str, Any] = None, lead_parser_db: Session = None) -> Dict[str, Any]:
        """Group leads by source for a user"""
        cache_key = f"lead_groups:source:{user_id}:{json.dumps(filters or {})}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        query = lead_parser_db.query(Lead.lead_source, func.count(Lead.id)).filter(Lead.user_id == user_id)
        
        if filters:
            query = self._apply_filters_to_query(query, filters)
        
        results = query.group_by(Lead.lead_source).all()
        
        groups = {}
        total_leads = 0
        for source, count in results:
            source_name = source or "Unknown"
            groups[source_name] = count
            total_leads += count
        
        result = {
            "groups": groups,
            "total_leads": total_leads,
            "group_type": "source"
        }
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(result)
        )
        
        return result
    
    def group_leads_by_location(self, user_id: str, filters: Dict[str, Any] = None, lead_parser_db: Session = None) -> Dict[str, Any]:
        """Group leads by location (country/state/city) for a user"""
        cache_key = f"lead_groups:location:{user_id}:{json.dumps(filters or {})}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        query = lead_parser_db.query(Lead.country, Lead.state, Lead.city, func.count(Lead.id)).filter(Lead.user_id == user_id)
        
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
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(result)
        )
        
        return result
    
    def group_leads_by_platform_connectivity(
        self, 
        user_id: str,
        filters: Dict[str, Any] = None, 
        lead_parser_db: Session = None,
        outreach_db: Session = None
    ) -> Dict[str, Any]:
        """Group leads by platform connectivity for a user"""
        cache_key = f"lead_groups:platform:{user_id}:{json.dumps(filters or {})}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        query = lead_parser_db.query(Lead).filter(Lead.user_id == user_id)
        
        if filters:
            query = self._apply_filters_to_query(query, filters)
        
        leads = query.all()
        
        groups = {
            "email_available": 0,
            "phone_available": 0,
            "linkedin_available": 0,
            "facebook_available": 0,
            "instagram_available": 0,
            "twitter_available": 0,
            "youtube_available": 0,
            "tiktok_available": 0,
            "multiple_platforms": 0,
            "no_contact_info": 0
        }
        
        for lead in leads:
            platform_count = 0
            
            if lead.email and lead.email_valid:
                groups["email_available"] += 1
                platform_count += 1
            
            if (lead.phone or lead.mobile) and lead.phone_valid:
                groups["phone_available"] += 1
                platform_count += 1
            
            if lead.linkedin_url:
                groups["linkedin_available"] += 1
                platform_count += 1
            
            if lead.facebook_url:
                groups["facebook_available"] += 1
                platform_count += 1
            
            if lead.instagram_url:
                groups["instagram_available"] += 1
                platform_count += 1
            
            if lead.twitter_url:
                groups["twitter_available"] += 1
                platform_count += 1
            
            if lead.youtube_url:
                groups["youtube_available"] += 1
                platform_count += 1
            
            if lead.tiktok_url:
                groups["tiktok_available"] += 1
                platform_count += 1
            
            if platform_count > 1:
                groups["multiple_platforms"] += 1
            elif platform_count == 0:
                groups["no_contact_info"] += 1
        
        result = {
            "groups": groups,
            "total_leads": len(leads),
            "group_type": "platform_connectivity"
        }
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(result)
        )
        
        return result
    
    def group_leads_by_engagement(
        self, 
        user_id: str,
        filters: Dict[str, Any] = None, 
        lead_parser_db: Session = None,
        outreach_db: Session = None
    ) -> Dict[str, Any]:
        """Group leads by engagement level for a user"""
        cache_key = f"lead_groups:engagement:{user_id}:{json.dumps(filters or {})}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        query = lead_parser_db.query(Lead).filter(Lead.user_id == user_id)
        
        if filters:
            query = self._apply_filters_to_query(query, filters)
        
        leads = query.all()
        lead_ids = [lead.id for lead in leads]
        
        message_counts = outreach_db.query(
            OutreachMessage.lead_id,
            func.count(OutreachMessage.id)
        ).filter(
            OutreachMessage.lead_id.in_(lead_ids),
            OutreachMessage.user_id == user_id
        ).group_by(OutreachMessage.lead_id).all()
        
        conversation_counts = outreach_db.query(
            Conversation.lead_id,
            func.count(Conversation.id)
        ).filter(
            Conversation.lead_id.in_(lead_ids),
            Conversation.user_id == user_id
        ).group_by(Conversation.lead_id).all()
        
        message_dict = dict(message_counts)
        conversation_dict = dict(conversation_counts)
        
        groups = {
            "not_contacted": 0,
            "contacted_no_response": 0,
            "active_conversations": 0,
            "high_engagement": 0
        }
        
        for lead in leads:
            message_count = message_dict.get(lead.id, 0)
            conversation_count = conversation_dict.get(lead.id, 0)
            
            if message_count == 0:
                groups["not_contacted"] += 1
            elif conversation_count == 0:
                groups["contacted_no_response"] += 1
            elif conversation_count <= 2:
                groups["active_conversations"] += 1
            else:
                groups["high_engagement"] += 1
        
        result = {
            "groups": groups,
            "total_leads": len(leads),
            "group_type": "engagement"
        }
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(result)
        )
        
        return result
    
    def group_leads(
        self, 
        request: LeadGroupingRequest, 
        lead_parser_db: Session,
        outreach_db: Session = None
    ) -> LeadGroupingResponse:
        """Group leads based on the specified criteria for a user"""
        if request.group_by == "industry":
            result = self.group_leads_by_industry(request.user_id, request.filters, lead_parser_db)
        elif request.group_by == "status":
            result = self.group_leads_by_status(request.user_id, request.filters, lead_parser_db)
        elif request.group_by == "source":
            result = self.group_leads_by_source(request.user_id, request.filters, lead_parser_db)
        elif request.group_by == "location":
            result = self.group_leads_by_location(request.user_id, request.filters, lead_parser_db)
        elif request.group_by == "platform":
            result = self.group_leads_by_platform_connectivity(request.user_id, request.filters, lead_parser_db, outreach_db)
        elif request.group_by == "engagement":
            result = self.group_leads_by_engagement(request.user_id, request.filters, lead_parser_db, outreach_db)
        else:
            raise ValueError(f"Unsupported grouping criteria: {request.group_by}")
        
        return LeadGroupingResponse(**result)
    
    def _apply_filters_to_query(self, query, filters: Dict[str, Any]):
        """Apply filters to a SQLAlchemy query"""
        if filters.get("industry"):
            query = query.filter(Lead.industry == filters["industry"])
        
        if filters.get("lead_status"):
            query = query.filter(Lead.lead_status == filters["lead_status"])
        
        if filters.get("lead_source"):
            query = query.filter(Lead.lead_source == filters["lead_source"])
        
        if filters.get("priority"):
            query = query.filter(Lead.priority == filters["priority"])
        
        if filters.get("country"):
            query = query.filter(Lead.country == filters["country"])
        
        if filters.get("email_valid") is not None:
            query = query.filter(Lead.email_valid == filters["email_valid"])
        
        if filters.get("phone_valid") is not None:
            query = query.filter(Lead.phone_valid == filters["phone_valid"])
        
        return query
    
    def get_lead_statistics(self, user_id: str, lead_parser_db: Session, outreach_db: Session = None) -> Dict[str, Any]:
        """Get overall lead statistics for a user"""
        cache_key = f"lead_stats:{user_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        total_leads = lead_parser_db.query(Lead).filter(Lead.user_id == user_id).count()
        
        email_valid_count = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.email_valid == True
        ).count()
        phone_valid_count = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.phone_valid == True
        ).count()
        
        linkedin_count = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.linkedin_url.isnot(None)
        ).count()
        facebook_count = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.facebook_url.isnot(None)
        ).count()
        instagram_count = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.instagram_url.isnot(None)
        ).count()
        twitter_count = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.twitter_url.isnot(None)
        ).count()
        youtube_count = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.youtube_url.isnot(None)
        ).count()
        tiktok_count = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.tiktok_url.isnot(None)
        ).count()
        
        contacted_email = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.contacted_via_email == True
        ).count()
        contacted_phone = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.contacted_via_phone == True
        ).count()
        contacted_linkedin = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.contacted_via_linkedin == True
        ).count()
        contacted_facebook = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.contacted_via_facebook == True
        ).count()
        contacted_instagram = lead_parser_db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.contacted_via_instagram == True
        ).count()
        
        stats = {
            "total_leads": total_leads,
            "contact_info": {
                "email_valid": email_valid_count,
                "phone_valid": phone_valid_count,
                "email_percentage": (email_valid_count / total_leads * 100) if total_leads > 0 else 0,
                "phone_percentage": (phone_valid_count / total_leads * 100) if total_leads > 0 else 0
            },
            "social_profiles": {
                "linkedin": linkedin_count,
                "facebook": facebook_count,
                "instagram": instagram_count,
                "twitter": twitter_count,
                "youtube": youtube_count,
                "tiktok": tiktok_count,
                "linkedin_percentage": (linkedin_count / total_leads * 100) if total_leads > 0 else 0,
                "facebook_percentage": (facebook_count / total_leads * 100) if total_leads > 0 else 0,
                "instagram_percentage": (instagram_count / total_leads * 100) if total_leads > 0 else 0,
                "twitter_percentage": (twitter_count / total_leads * 100) if total_leads > 0 else 0,
                "youtube_percentage": (youtube_count / total_leads * 100) if total_leads > 0 else 0,
                "tiktok_percentage": (tiktok_count / total_leads * 100) if total_leads > 0 else 0
            },
            "contacted": {
                "email": contacted_email,
                "phone": contacted_phone,
                "linkedin": contacted_linkedin,
                "facebook": contacted_facebook,
                "instagram": contacted_instagram,
                "total_contacted": contacted_email + contacted_phone + contacted_linkedin + contacted_facebook + contacted_instagram
            }
        }
        
        if outreach_db:
            total_messages = outreach_db.query(OutreachMessage).filter(
                OutreachMessage.user_id == user_id
            ).count()
            total_conversations = outreach_db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).count()
            
            stats["outreach"] = {
                "total_messages": total_messages,
                "total_conversations": total_conversations,
                "average_messages_per_lead": (total_messages / total_leads) if total_leads > 0 else 0
            }
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(stats)
        )
        
        return stats

lead_service = LeadService()