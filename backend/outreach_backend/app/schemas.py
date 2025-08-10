from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class MessageStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"

class ConversationStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    PENDING_REPLY = "pending_reply"

class CampaignStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class MessageDirection(str, Enum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"

class LeadStatus(str, Enum):
    ACTIVE = "active"
    CONTACTED = "contacted"
    CONVERTED = "converted"

class OutreachPlatformBase(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: str
    username: Optional[EmailStr] = None
    password: Optional[str] = None

class OutreachPlatformCreate(OutreachPlatformBase):
    pass

class OutreachPlatformUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    user_id: str
    username: Optional[EmailStr] = None
    password: Optional[str] = None

class OutreachPlatform(OutreachPlatformBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserPlatformCredentialBase(BaseModel):
    user_id: str
    platform_id: int
    username: EmailStr

class UserPlatformCredentialCreate(UserPlatformCredentialBase):
    password: str
    user_id: str

class UserPlatformCredentialUpdate(BaseModel):
    username: Optional[EmailStr] = None
    password: Optional[str] = None
    user_id: str

class UserPlatformCredential(UserPlatformCredentialBase):
    id: int
    created_at: datetime
    updated_at: datetime
    platform: OutreachPlatform

    class Config:
        from_attributes = True

class OutreachMessageBase(BaseModel):
    lead_id: int
    platform_id: int
    message_content: str
    campaign_id: Optional[int] = None
    bulk_group_id: Optional[int] = None
    subject: Optional[str] = None
    user_id: str

class OutreachMessageCreate(OutreachMessageBase):
    sender_id: int
    user_id: str

class OutreachMessageUpdate(BaseModel):
    status: Optional[MessageStatus] = None
    platform_message_id: Optional[str] = None
    error_message: Optional[str] = None
    campaign_id: Optional[int] = None
    bulk_group_id: Optional[int] = None
    subject: Optional[str] = None
    user_id: str

class OutreachMessage(OutreachMessageBase):
    id: int
    sender_id: int
    sent_at: datetime
    status: MessageStatus
    platform_message_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    platform: OutreachPlatform
    bulk_message_group: Optional["BulkMessageGroup"] = None

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    lead_id: int
    platform_id: int
    subject: Optional[str] = None

class ConversationCreate(ConversationBase):
    subject: str
    status: ConversationStatus = ConversationStatus.OPEN

class ConversationUpdate(BaseModel):
    status: Optional[ConversationStatus] = None
    subject: Optional[str] = None
    last_message_at: Optional[datetime] = None

class Conversation(ConversationBase):
    id: int
    last_message_at: Optional[datetime] = None
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    platform: OutreachPlatform

    class Config:
        from_attributes = True

class ConversationMessageBase(BaseModel):
    conversation_id: int
    direction: MessageDirection
    message_content: str
    sender_identifier: Optional[str] = None
    recipient_identifier: Optional[str] = None

class ConversationMessageCreate(ConversationMessageBase):
    outreach_message_id: Optional[int] = None
    platform_message_id: Optional[str] = None

class ConversationMessageUpdate(BaseModel):
    platform_message_id: Optional[str] = None

class ConversationMessage(ConversationMessageBase):
    id: int
    outreach_message_id: Optional[int] = None
    sent_at: datetime
    platform_message_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LeadPlatformValidationBase(BaseModel):
    lead_id: int
    platform_id: int
    is_valid: bool
    details: Optional[str] = None

class LeadPlatformValidationCreate(LeadPlatformValidationBase):
    pass

class LeadPlatformValidationUpdate(BaseModel):
    is_valid: Optional[bool] = None
    details: Optional[str] = None

class LeadPlatformValidation(LeadPlatformValidationBase):
    id: int
    validation_date: datetime
    created_at: datetime
    updated_at: datetime
    platform: OutreachPlatform

    class Config:
        from_attributes = True

class OutreachCampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    user_id: str

class OutreachCampaignCreate(OutreachCampaignBase):
    status: CampaignStatus = CampaignStatus.ACTIVE
    user_id: str

class OutreachCampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[CampaignStatus] = None
    user_id: str

class OutreachCampaign(OutreachCampaignBase):
    id: int
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime
    total_leads: int = 0

    class Config:
        from_attributes = True

class CampaignLeadBase(BaseModel):
    lead_id: int

class CampaignLeadCreate(CampaignLeadBase):
    status: LeadStatus = LeadStatus.ACTIVE

class CampaignLeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None

class CampaignLead(CampaignLeadBase):
    id: int
    added_at: datetime
    status: LeadStatus
    lead_name: Optional[str] = None

    class Config:
        from_attributes = True

class CampaignLeadBulkCreate(BaseModel):
    lead_ids: List[int]

class OutreachTemplateBase(BaseModel):
    name: str
    subject: Optional[str] = None
    content: str
    user_id: str

class OutreachTemplateCreate(OutreachTemplateBase):
    user_id: str

class OutreachTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    user_id: str

class OutreachTemplate(OutreachTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Lead(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    lead_score: Optional[int] = None
    lead_status: Optional[str] = None
    lead_source: Optional[str] = None
    priority: Optional[str] = None
    email_valid: Optional[bool] = None
    phone_valid: Optional[bool] = None
    social_profiles_count: Optional[int] = None
    data_completeness_score: Optional[int] = None
    contacted_via_email: Optional[bool] = None
    contacted_via_phone: Optional[bool] = None
    contacted_via_linkedin: Optional[bool] = None
    contacted_via_facebook: Optional[bool] = None
    contacted_via_instagram: Optional[bool] = None
    last_contact_date: Optional[datetime] = None
    additional_data: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None
    source_file_name: Optional[str] = None
    source_file_row: Optional[int] = None
    is_duplicate: Optional[bool] = None
    duplicate_of: Optional[int] = None

    class Config:
        from_attributes = True

class Event(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    timezone: Optional[str] = None
    all_day: bool = False
    event_type: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None

    class Config:
        from_attributes = True

class SendMessageRequest(BaseModel):
    lead_ids: List[int]
    platform_id: int
    message_content: str
    subject: Optional[str] = None
    template_id: Optional[int] = None
    campaign_id: Optional[int] = None
    bulk_group_id: Optional[int] = None
    user_id: str

class LeadGroupingRequest(BaseModel):
    group_by: str
    filters: Optional[dict] = None
    user_id: str

class LeadGroupingResponse(BaseModel):
    groups: dict
    total_leads: int

class PlatformAuthRequest(BaseModel):
    platform_id: int
    username: Optional[EmailStr] = None
    password: Optional[str] = None
    user_id: str

class PlatformAuthResponse(BaseModel):
    success: bool
    message: str
    credential_id: Optional[int] = None

class BulkMessageGroup(BaseModel):
    id: int
    user_id: str
    platform_id: int
    campaign_id: Optional[int] = None
    total_leads: int
    success_count: int
    failed_count: int
    subject: Optional[str] = None
    is_resend: bool = False
    parent_group_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    platform: OutreachPlatform
    campaign: Optional[OutreachCampaign] = None

    class Config:
        from_attributes = True

class SendMessageResponse(BaseModel):
    success_count: int
    failed_count: int
    messages: List[OutreachMessage]
    errors: List[str]