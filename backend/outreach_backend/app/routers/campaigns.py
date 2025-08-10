from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from outreach_backend.app.database import get_db, get_lead_parser_db
from outreach_backend.app.schemas import (
    OutreachCampaign, OutreachCampaignCreate, OutreachCampaignUpdate,
    CampaignLead, CampaignLeadCreate, CampaignLeadUpdate,
    CampaignLeadBulkCreate,
    OutreachTemplate, OutreachTemplateCreate, OutreachTemplateUpdate
)
from outreach_backend.app.services.campaign_service import CampaignService, LeadService, TemplateService
from lead_backend.app.services.lead_crud import LeadCRUD

router = APIRouter()

# Template endpoints
@router.post("/templates", response_model=OutreachTemplate)
async def create_template(
    template: OutreachTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new outreach template for a user"""
    return TemplateService.create_template(template, db)

@router.get("/user/{user_id}/templates", response_model=List[OutreachTemplate])
async def get_templates(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all templates for a specific user"""
    return TemplateService.get_templates(user_id, skip, limit, db)

@router.get("/user/{user_id}/templates/{template_id}", response_model=OutreachTemplate)
async def get_template(
    user_id: str,
    template_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific template by ID for a user"""
    return TemplateService.get_template(user_id, template_id, db)

@router.put("/user/{user_id}/templates/{template_id}", response_model=OutreachTemplate)
async def update_template(
    user_id: str,
    template_id: int,
    template_update: OutreachTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a template for a user"""
    return TemplateService.update_template(user_id, template_id, template_update, db)

@router.delete("/user/{user_id}/templates/{template_id}")
async def delete_template(
    user_id: str,
    template_id: int,
    db: Session = Depends(get_db)
):
    """Delete a template for a user"""
    return TemplateService.delete_template(user_id, template_id, db)

@router.get("/user/{user_id}/campaigns/{campaign_id}/statistics")
async def get_campaign_statistics(
    user_id: str,
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Get statistics for a campaign for a user"""
    return CampaignService.get_campaign_statistics(user_id, campaign_id, db)

@router.post("/user/{user_id}/campaigns/{campaign_id}/leads", response_model=CampaignLead)
async def add_lead_to_campaign(
    user_id: str,
    campaign_id: int,
    campaign_lead: CampaignLeadCreate,
    db: Session = Depends(get_db),
    lead_db: Session = Depends(get_lead_parser_db)
):
    """Add a lead to a campaign for a user"""
    return LeadService.add_lead_to_campaign(user_id, campaign_id, campaign_lead, db, lead_db)

@router.post("/campaigns", response_model=OutreachCampaign)
async def create_campaign(
    campaign: OutreachCampaignCreate,
    db: Session = Depends(get_db)
):
    """Create a new outreach campaign for a user"""
    return CampaignService.create_campaign(campaign, db)

@router.get("/user/{user_id}/campaigns", response_model=List[OutreachCampaign])
async def get_campaigns(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Get all campaigns for a user with optional filtering and total leads count"""
    return CampaignService.get_campaigns(user_id, skip, limit, status, db)

@router.get("/user/{user_id}/campaigns/{campaign_id}", response_model=OutreachCampaign)
async def get_campaign(
    user_id: str,
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific campaign by ID for a user with total leads count"""
    return CampaignService.get_campaign(user_id, campaign_id, db)

@router.put("/user/{user_id}/campaigns/{campaign_id}", response_model=OutreachCampaign)
async def update_campaign(
    user_id: str,
    campaign_id: int,
    campaign_update: OutreachCampaignUpdate,
    db: Session = Depends(get_db)
):
    """Update a campaign for a user"""
    return CampaignService.update_campaign(user_id, campaign_id, campaign_update, db)

@router.delete("/user/{user_id}/campaigns/{campaign_id}")
async def delete_campaign(
    user_id: str,
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Delete a campaign and its associated campaign leads for a user"""
    return CampaignService.delete_campaign(user_id, campaign_id, db)

@router.get("/user/{user_id}/campaigns/{campaign_id}/leads", response_model=List[CampaignLead])
async def get_campaign_leads(
    user_id: str,
    campaign_id: int,
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    lead_db: Session = Depends(get_lead_parser_db)
):
    """Get leads in a campaign with their names for a user"""
    return LeadService.get_campaign_leads(user_id, campaign_id, skip, limit, status, db, lead_db)

@router.put("/user/{user_id}/campaigns/{campaign_id}/leads/{lead_id}", response_model=CampaignLead)
async def update_campaign_lead(
    user_id: str,
    campaign_id: int,
    lead_id: int,
    campaign_lead_update: CampaignLeadUpdate,
    db: Session = Depends(get_db),
    lead_db: Session = Depends(get_lead_parser_db)
):
    """Update a lead's status in a campaign for a user"""
    return LeadService.update_campaign_lead(user_id, campaign_id, lead_id, campaign_lead_update, db, lead_db)

@router.delete("/user/{user_id}/campaigns/{campaign_id}/leads/{lead_id}")
async def remove_lead_from_campaign(
    user_id: str,
    campaign_id: int,
    lead_id: int,
    db: Session = Depends(get_db),
    lead_db: Session = Depends(get_lead_parser_db)
):
    """Remove a lead from a campaign for a user"""
    return LeadService.remove_lead_from_campaign(user_id, campaign_id, lead_id, db, lead_db)

@router.post("/user/{user_id}/campaigns/{campaign_id}/leads/bulk")
async def add_multiple_leads_to_campaign(
    user_id: str,
    campaign_id: int,
    campaign_lead_bulk: CampaignLeadBulkCreate,
    db: Session = Depends(get_db),
    lead_db: Session = Depends(get_lead_parser_db)
):
    """Add multiple leads to a campaign for a user"""
    return LeadService.add_multiple_leads_to_campaign(user_id, campaign_id, campaign_lead_bulk, db, lead_db)