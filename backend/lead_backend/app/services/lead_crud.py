from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
import redis
import json
from lead_backend.app.models.lead import Lead
from lead_backend.app.models.schemas import LeadCreate, LeadResponse, LeadUpdate
from datetime import datetime
from config.settings import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class LeadCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, lead_data: LeadCreate, source_file_name: Optional[str] = None, source_file_row: Optional[int] = None, file_upload_id: Optional[int] = None) -> Lead:
        db_lead = Lead(**lead_data.dict(exclude_unset=True))
        
        if source_file_name:
            db_lead.source_file_name = source_file_name
        if source_file_row:
            db_lead.source_file_row = source_file_row
        if file_upload_id:
            db_lead.file_upload_id = file_upload_id
        
        self.db.add(db_lead)
        self.db.commit()
        self.db.refresh(db_lead)

        redis_client.setex(
            f"lead:{lead_data.user_id}:{db_lead.id}",
            settings.REDIS_CACHE_TTL,
            LeadResponse.from_orm(db_lead).json()
        )
        redis_client.delete(f"leads:{lead_data.user_id}")
        return db_lead

    def get_from_cache(self, lead_id: int, user_id: str) -> Optional[LeadResponse]:
        """Return a cached LeadResponse for read-only usage"""
        cached_lead = redis_client.get(f"lead:{user_id}:{lead_id}")
        if cached_lead:
            try:
                return LeadResponse(**json.loads(cached_lead))
            except Exception:
                return None
        return None

    def get(self, lead_id: int, user_id: str) -> Optional[Lead]:
        """Always return a DB-bound Lead instance (used for update/delete)"""
        lead = self.db.query(Lead).filter(and_(Lead.id == lead_id, Lead.user_id == user_id)).first()
        if lead:
            redis_client.setex(
                f"lead:{user_id}:{lead_id}",
                settings.REDIS_CACHE_TTL,
                LeadResponse.from_orm(lead).json()
            )
        return lead

    def get_by_email(self, email: str, user_id: str) -> Optional[Lead]:
        cache_key = f"lead_email:{user_id}:{email}"
        cached_lead = redis_client.get(cache_key)
        
        if cached_lead:
            try:
                return LeadResponse(**json.loads(cached_lead))
            except Exception:
                pass

        lead = self.db.query(Lead).filter(and_(Lead.email == email, Lead.user_id == user_id)).first()
        if lead:
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                LeadResponse.from_orm(lead).json()
            )
        return lead

    def get_multiple(self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[Lead]:
        cache_key = f"leads:{filters.get('user_id')}:{skip}:{limit}:{json.dumps(filters, sort_keys=True)}"
        cached_leads = redis_client.get(cache_key)

        if cached_leads:
            try:
                leads = json.loads(cached_leads)
                return [LeadResponse(**lead) for lead in leads]
            except Exception:
                pass

        query = self.db.query(Lead)

        if filters:
            query = query.filter(Lead.user_id == filters.get("user_id"))
            if filters.get("company"):
                query = query.filter(Lead.company.ilike(f"%{filters['company']}%"))
            if filters.get("industry"):
                query = query.filter(Lead.industry.ilike(f"%{filters['industry']}%"))
            if filters.get("city"):
                query = query.filter(Lead.city.ilike(f"%{filters['city']}%"))
            if filters.get("country"):
                query = query.filter(Lead.country.ilike(f"%{filters['country']}%"))
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Lead.full_name.ilike(search_term),
                        Lead.first_name.ilike(search_term),
                        Lead.last_name.ilike(search_term),
                        Lead.email.ilike(search_term),
                        Lead.company.ilike(search_term)
                    )
                )

        leads = query.offset(skip).limit(limit).all()
        if leads:
            json_data = '[' + ','.join([LeadResponse.from_orm(lead).json() for lead in leads]) + ']'
            redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, json_data)

        return leads

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        cache_key = f"lead_count:{filters.get('user_id')}:{json.dumps(filters, sort_keys=True)}"
        cached_count = redis_client.get(cache_key)
        if cached_count:
            return int(cached_count)

        query = self.db.query(Lead)
        if filters:
            query = query.filter(Lead.user_id == filters.get("user_id"))
            if filters.get("company"):
                query = query.filter(Lead.company.ilike(f"%{filters['company']}%"))
            if filters.get("industry"):
                query = query.filter(Lead.industry.ilike(f"%{filters['industry']}%"))
            if filters.get("city"):
                query = query.filter(Lead.city.ilike(f"%{filters['city']}%"))
            if filters.get("country"):
                query = query.filter(Lead.country.ilike(f"%{filters['country']}%"))
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Lead.full_name.ilike(search_term),
                        Lead.first_name.ilike(search_term),
                        Lead.last_name.ilike(search_term),
                        Lead.email.ilike(search_term),
                        Lead.company.ilike(search_term)
                    )
                )

        count = query.count()
        redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, str(count))
        return count

    def update(self, lead_id: int, lead_data: LeadUpdate, user_id: str) -> Optional[Lead]:
        db_lead = self.get(lead_id, user_id)  # always DB-bound
        if not db_lead:
            return None

        update_data = lead_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field != 'user_id':
                setattr(db_lead, field, value)

        db_lead.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_lead)

        redis_client.setex(
            f"lead:{user_id}:{lead_id}",
            settings.REDIS_CACHE_TTL,
            LeadResponse.from_orm(db_lead).json()
        )
        redis_client.delete(f"leads:{user_id}")
        return db_lead

    def delete(self, lead_id: int, user_id: str) -> bool:
        db_lead = self.get(lead_id, user_id)  # always DB-bound
        if not db_lead:
            return False

        self.db.delete(db_lead)
        self.db.commit()

        redis_client.delete(f"lead:{user_id}:{lead_id}")
        redis_client.delete(f"leads:{user_id}")
        return True
