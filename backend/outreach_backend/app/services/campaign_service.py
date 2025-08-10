from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from fastapi import HTTPException, status

from outreach_backend.app.schemas import (
    OutreachCampaign, OutreachCampaignCreate, OutreachCampaignUpdate,
    CampaignLead, CampaignLeadCreate, CampaignLeadUpdate,
    CampaignLeadBulkCreate,
    OutreachTemplate, OutreachTemplateCreate, OutreachTemplateUpdate
)
from outreach_backend.app.models import (
    OutreachCampaign as OutreachCampaignModel,
    CampaignLead as CampaignLeadModel,
    OutreachTemplate as OutreachTemplateModel,
    Lead as LeadModel,
    OutreachMessage
)
from lead_backend.app.services.lead_crud import LeadCRUD

class CampaignService:
    @staticmethod
    def create_campaign(campaign: OutreachCampaignCreate, db: Session) -> OutreachCampaign:
        """Create a new outreach campaign for a user"""
        if not campaign.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required"
            )
        
        db_campaign = OutreachCampaignModel(**campaign.dict())
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
        return db_campaign

    @staticmethod
    def get_campaigns(user_id: str, skip: int, limit: int, status: str | None, db: Session) -> List[OutreachCampaign]:
        """Get all campaigns for a user with optional filtering and total leads count"""
        query = db.query(
            OutreachCampaignModel,
            func.count(CampaignLeadModel.id).label("total_leads")
        ).outerjoin(
            CampaignLeadModel, OutreachCampaignModel.id == CampaignLeadModel.campaign_id
        ).filter(OutreachCampaignModel.user_id == user_id)
        
        if status:
            query = query.filter(OutreachCampaignModel.status == status)
        
        query = query.group_by(OutreachCampaignModel.id)
        campaigns = query.offset(skip).limit(limit).all()
        
        return [
            OutreachCampaign(
                id=campaign[0].id,
                name=campaign[0].name,
                description=campaign[0].description,
                start_date=campaign[0].start_date,
                end_date=campaign[0].end_date,
                status=campaign[0].status,
                user_id=campaign[0].user_id,
                created_at=campaign[0].created_at,
                updated_at=campaign[0].updated_at,
                total_leads=campaign[1]
            )
            for campaign in campaigns
        ]

    @staticmethod
    def get_campaign(user_id: str, campaign_id: int, db: Session) -> OutreachCampaign:
        """Get a specific campaign by ID for a user with total leads count"""
        query = db.query(
            OutreachCampaignModel,
            func.count(CampaignLeadModel.id).label("total_leads")
        ).outerjoin(
            CampaignLeadModel, OutreachCampaignModel.id == CampaignLeadModel.campaign_id
        ).filter(
            OutreachCampaignModel.id == campaign_id,
            OutreachCampaignModel.user_id == user_id
        ).group_by(
            OutreachCampaignModel.id
        )
        
        campaign = query.first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or not authorized for user"
            )
        
        return OutreachCampaign(
            id=campaign[0].id,
            name=campaign[0].name,
            description=campaign[0].description,
            start_date=campaign[0].start_date,
            end_date=campaign[0].end_date,
            status=campaign[0].status,
            user_id=campaign[0].user_id,
            created_at=campaign[0].created_at,
            updated_at=campaign[0].updated_at,
            total_leads=campaign[1]
        )

    @staticmethod
    def update_campaign(user_id: str, campaign_id: int, campaign_update: OutreachCampaignUpdate, db: Session) -> OutreachCampaign:
        """Update a campaign for a user"""
        campaign = db.query(OutreachCampaignModel).filter(
            OutreachCampaignModel.id == campaign_id,
            OutreachCampaignModel.user_id == user_id
        ).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or not authorized for user"
            )
        
        update_data = campaign_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)
        
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def delete_campaign(user_id: str, campaign_id: int, db: Session) -> Dict[str, str]:
        """Delete a campaign and its associated campaign leads for a user"""
        campaign = db.query(OutreachCampaignModel).filter(
            OutreachCampaignModel.id == campaign_id,
            OutreachCampaignModel.user_id == user_id
        ).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or not authorized for user"
            )
        
        db.query(CampaignLeadModel).filter(CampaignLeadModel.campaign_id == campaign_id).delete()
        db.delete(campaign)
        db.commit()
        return {"message": "Campaign and associated leads deleted successfully"}

    @staticmethod
    def get_campaign_statistics(user_id: str, campaign_id: int, db: Session) -> Dict[str, Any]:
        """Get statistics for a campaign for a user"""
        campaign = db.query(OutreachCampaignModel).filter(
            OutreachCampaignModel.id == campaign_id,
            OutreachCampaignModel.user_id == user_id
        ).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or not authorized for user"
            )
        
        total_leads = db.query(CampaignLeadModel).filter(
            CampaignLeadModel.campaign_id == campaign_id
        ).count()
        
        lead_status_counts = db.query(
            CampaignLeadModel.status,
            func.count(CampaignLeadModel.id)
        ).filter(CampaignLeadModel.campaign_id == campaign_id).group_by(CampaignLeadModel.status).all()
        
        campaign_lead_ids = db.query(CampaignLeadModel.lead_id).filter(
            CampaignLeadModel.campaign_id == campaign_id
        ).subquery()
        
        total_messages = db.query(OutreachMessage).filter(
            OutreachMessage.lead_id.in_(campaign_lead_ids),
            OutreachMessage.user_id == user_id
        ).count()
        
        return {
            "campaign_id": campaign_id,
            "campaign": campaign,
            "total_leads": total_leads,
            "lead_status_breakdown": {status: count for status, count in lead_status_counts},
            "total_messages_sent": total_messages,
            "average_messages_per_lead": (total_messages / total_leads) if total_leads > 0 else 0
        }

class LeadService:
    @staticmethod
    def add_lead_to_campaign(user_id: str, campaign_id: int, campaign_lead: CampaignLeadCreate, db: Session, lead_db: Session) -> CampaignLead:
        """Add a lead to a campaign for a user"""
        campaign = db.query(OutreachCampaignModel).filter(
            OutreachCampaignModel.id == campaign_id,
            OutreachCampaignModel.user_id == user_id
        ).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or not authorized for user"
            )
        
        lead_crud = LeadCRUD(lead_db)
        lead = lead_crud.get(campaign_lead.lead_id, user_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or not authorized for user"
            )
        
        existing = db.query(CampaignLeadModel).filter(
            CampaignLeadModel.campaign_id == campaign_id,
            CampaignLeadModel.lead_id == campaign_lead.lead_id
        ).first()
        
        if existing:
            return existing
        
        db_campaign_lead = CampaignLeadModel(
            campaign_id=campaign_id,
            lead_id=campaign_lead.lead_id,
            status=campaign_lead.status
        )
        db.add(db_campaign_lead)
        db.commit()
        db.refresh(db_campaign_lead)
        return db_campaign_lead

    @staticmethod
    def get_campaign_leads(user_id: str, campaign_id: int, skip: int, limit: int, status: str | None, db: Session, lead_db: Session) -> List[CampaignLead]:
        """Get leads in a campaign with their names for a user"""
        campaign = db.query(OutreachCampaignModel).filter(
            OutreachCampaignModel.id == campaign_id,
            OutreachCampaignModel.user_id == user_id
        ).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or not authorized for user"
            )
        
        query = db.query(CampaignLeadModel).filter(
            CampaignLeadModel.campaign_id == campaign_id
        )
        
        if status:
            query = query.filter(CampaignLeadModel.status == status)
        
        campaign_leads = query.offset(skip).limit(limit).all()
        
        lead_crud = LeadCRUD(lead_db)
        lead_ids = [cl.lead_id for cl in campaign_leads]
        leads = lead_crud.get_multiple(skip=0, limit=len(lead_ids), filters={"user_id": user_id, "ids": lead_ids})
        lead_name_map = {lead.id: lead.full_name for lead in leads}
        
        return [
            CampaignLead(
                id=campaign_lead.id,
                lead_id=campaign_lead.lead_id,
                added_at=campaign_lead.added_at,
                status=campaign_lead.status,
                lead_name=lead_name_map.get(campaign_lead.lead_id)
            )
            for campaign_lead in campaign_leads
        ]

    @staticmethod
    def update_campaign_lead(user_id: str, campaign_id: int, lead_id: int, campaign_lead_update: CampaignLeadUpdate, db: Session, lead_db: Session) -> CampaignLead:
        """Update a lead's status in a campaign for a user"""
        lead_crud = LeadCRUD(lead_db)
        lead = lead_crud.get(lead_id, user_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or not authorized for user"
            )
        
        campaign_lead = db.query(CampaignLeadModel).filter(
            CampaignLeadModel.campaign_id == campaign_id,
            CampaignLeadModel.lead_id == lead_id
        ).first()
        
        if not campaign_lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found in campaign"
            )
        
        update_data = campaign_lead_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign_lead, field, value)
        
        db.commit()
        db.refresh(campaign_lead)
        
        return CampaignLead(
            id=campaign_lead.id,
            lead_id=campaign_lead.lead_id,
            added_at=campaign_lead.added_at,
            status=campaign_lead.status,
            lead_name=lead.full_name
        )

    @staticmethod
    def remove_lead_from_campaign(user_id: str, campaign_id: int, lead_id: int, db: Session, lead_db: Session) -> Dict[str, str]:
        """Remove a lead from a campaign for a user"""
        lead_crud = LeadCRUD(lead_db)
        lead = lead_crud.get(lead_id, user_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or not authorized for user"
            )
        
        campaign_lead = db.query(CampaignLeadModel).filter(
            CampaignLeadModel.campaign_id == campaign_id,
            CampaignLeadModel.lead_id == lead_id
        ).first()
        
        if not campaign_lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found in campaign"
            )
        
        db.delete(campaign_lead)
        db.commit()
        return {"message": "Lead removed from campaign successfully"}

    @staticmethod
    def add_multiple_leads_to_campaign(user_id: str, campaign_id: int, campaign_lead_bulk: CampaignLeadBulkCreate, db: Session, lead_db: Session) -> Dict[str, Any]:
        """Add multiple leads to a campaign for a user"""
        campaign = db.query(OutreachCampaignModel).filter(
            OutreachCampaignModel.id == campaign_id,
            OutreachCampaignModel.user_id == user_id
        ).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or not authorized for user"
            )
        
        lead_crud = LeadCRUD(lead_db)
        valid_leads = lead_crud.get_multiple(skip=0, limit=len(campaign_lead_bulk.lead_ids), filters={"user_id": user_id, "ids": campaign_lead_bulk.lead_ids})
        valid_lead_ids = [lead.id for lead in valid_leads]
        
        if not valid_lead_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid leads found for user"
            )
        
        existing_leads = db.query(CampaignLeadModel.lead_id).filter(
            CampaignLeadModel.campaign_id == campaign_id
        ).all()
        existing_lead_ids = [lead[0] for lead in existing_leads]
        
        new_lead_ids = [lead_id for lead_id in valid_lead_ids if lead_id not in existing_lead_ids]
        
        added_leads = []
        for lead_id in new_lead_ids:
            campaign_lead = CampaignLeadModel(
                campaign_id=campaign_id,
                lead_id=lead_id,
                status="active"
            )
            db.add(campaign_lead)
            added_leads.append(campaign_lead)
        
        db.commit()
        
        return {
            "message": f"Added {len(added_leads)} leads to campaign",
            "added_count": len(added_leads),
            "skipped_count": len(campaign_lead_bulk.lead_ids) - len(added_leads),
            "total_requested": len(campaign_lead_bulk.lead_ids)
        }

class TemplateService:
    @staticmethod
    def create_template(template: OutreachTemplateCreate, db: Session) -> OutreachTemplate:
        """Create a new outreach template for a user"""
        if not template.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required"
            )
        
        db_template = OutreachTemplateModel(**template.dict())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template

    @staticmethod
    def get_templates(user_id: str, skip: int, limit: int, db: Session) -> List[OutreachTemplate]:
        """Get all templates for a specific user"""
        query = db.query(OutreachTemplateModel).filter(OutreachTemplateModel.user_id == user_id)
        templates = query.offset(skip).limit(limit).all()
        return templates

    @staticmethod
    def get_template(user_id: str, template_id: int, db: Session) -> OutreachTemplate:
        """Get a specific template by ID for a user"""
        template = db.query(OutreachTemplateModel).filter(
            OutreachTemplateModel.id == template_id,
            OutreachTemplateModel.user_id == user_id
        ).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or not authorized for user"
            )
        return template

    @staticmethod
    def update_template(user_id: str, template_id: int, template_update: OutreachTemplateUpdate, db: Session) -> OutreachTemplate:
        """Update a template for a user"""
        template = db.query(OutreachTemplateModel).filter(
            OutreachTemplateModel.id == template_id,
            OutreachTemplateModel.user_id == user_id
        ).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or not authorized for user"
            )
        
        update_data = template_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(user_id: str, template_id: int, db: Session) -> Dict[str, str]:
        """Delete a template for a user"""
        template = db.query(OutreachTemplateModel).filter(
            OutreachTemplateModel.id == template_id,
            OutreachTemplateModel.user_id == user_id
        ).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or not authorized for user"
            )
        
        db.delete(template)
        db.commit()
        return {"message": "Template deleted successfully"}