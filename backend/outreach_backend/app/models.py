from sqlalchemy import Boolean, Column, Date, Integer, String, Text, DateTime, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from outreach_backend.app.database import Base

class OutreachPlatform(Base):
    __tablename__ = "outreach_platforms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    credentials = relationship("UserPlatformCredential", back_populates="platform")
    messages = relationship("OutreachMessage", back_populates="platform")
    conversations = relationship("Conversation", back_populates="platform")
    validations = relationship("LeadPlatformValidation", back_populates="platform")
    bulk_message_groups = relationship("BulkMessageGroup", back_populates="platform")

class UserPlatformCredential(Base):
    __tablename__ = "user_platform_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    platform_id = Column(Integer, ForeignKey("outreach_platforms.id"), nullable=False)
    username = Column(String(255), nullable=False)
    password = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    platform = relationship("OutreachPlatform", back_populates="credentials")
    sent_messages = relationship("OutreachMessage", back_populates="sender")

class BulkMessageGroup(Base):
    __tablename__ = "bulk_message_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    platform_id = Column(Integer, ForeignKey("outreach_platforms.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("outreach_campaigns.id"), nullable=True)
    total_leads = Column(Integer, nullable=False)
    success_count = Column(Integer, nullable=False)
    failed_count = Column(Integer, nullable=False)
    subject = Column(String(255), nullable=True)
    is_resend = Column(Boolean, default=False)
    parent_group_id = Column(Integer, ForeignKey("bulk_message_groups.id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    platform = relationship("OutreachPlatform", back_populates="bulk_message_groups")
    campaign = relationship("OutreachCampaign", back_populates="bulk_message_groups")
    messages = relationship("OutreachMessage", back_populates="bulk_message_group")

class OutreachMessage(Base):
    __tablename__ = "outreach_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False)
    platform_id = Column(Integer, ForeignKey("outreach_platforms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("user_platform_credentials.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("outreach_campaigns.id"), nullable=True)
    bulk_group_id = Column(Integer, ForeignKey("bulk_message_groups.id"), nullable=True)
    message_content = Column(Text, nullable=False)
    subject = Column(String(255), nullable=True)
    sent_at = Column(TIMESTAMP, server_default=func.now())
    status = Column(String(50), nullable=False)
    platform_message_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    user_id = Column(String(255), nullable=False)
    
    platform = relationship("OutreachPlatform", back_populates="messages")
    sender = relationship("UserPlatformCredential", back_populates="sent_messages")
    campaign = relationship("OutreachCampaign", back_populates="messages")
    bulk_message_group = relationship("BulkMessageGroup", back_populates="messages")
    conversation_message = relationship("ConversationMessage", back_populates="outreach_message")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False)
    platform_id = Column(Integer, ForeignKey("outreach_platforms.id"), nullable=False)
    last_message_at = Column(TIMESTAMP, nullable=True)
    status = Column(String(50), nullable=False)
    subject = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    user_id = Column(String(255), nullable=False)
    
    platform = relationship("OutreachPlatform", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    outreach_message_id = Column(Integer, ForeignKey("outreach_messages.id"), nullable=True)
    direction = Column(String(10), nullable=False)
    message_content = Column(Text, nullable=False)
    sent_at = Column(TIMESTAMP, server_default=func.now())
    platform_message_id = Column(String(255), nullable=True)
    sender_identifier = Column(String(255), nullable=True)
    recipient_identifier = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    conversation = relationship("Conversation", back_populates="messages")
    outreach_message = relationship("OutreachMessage", back_populates="conversation_message")

class LeadPlatformValidation(Base):
    __tablename__ = "lead_platform_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False)
    platform_id = Column(Integer, ForeignKey("outreach_platforms.id"), nullable=False)
    is_valid = Column(Boolean, nullable=False)
    validation_date = Column(TIMESTAMP, server_default=func.now())
    details = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    platform = relationship("OutreachPlatform", back_populates="validations")

class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    user_id = Column(String(255), nullable=False)
    
    campaign_leads = relationship("CampaignLead", back_populates="campaign")
    messages = relationship("OutreachMessage", back_populates="campaign")
    bulk_message_groups = relationship("BulkMessageGroup", back_populates="campaign")

class CampaignLead(Base):
    __tablename__ = "campaign_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("outreach_campaigns.id"), nullable=False)
    lead_id = Column(Integer, nullable=False)
    added_at = Column(TIMESTAMP, server_default=func.now())
    status = Column(String(50), nullable=False)
    
    campaign = relationship("OutreachCampaign", back_populates="campaign_leads")

class OutreachTemplate(Base):
    __tablename__ = "outreach_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    user_id = Column(String(255), nullable=False)

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    first_name = Column(String(100), nullable=True, index=True)
    last_name = Column(String(100), nullable=True, index=True)
    full_name = Column(String(200), nullable=True, index=True)
    company = Column(String(200), nullable=True, index=True)
    job_title = Column(String(200), nullable=True)
    industry = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    facebook_url = Column(String(500), nullable=True)
    instagram_url = Column(String(500), nullable=True)
    twitter_url = Column(String(500), nullable=True)
    youtube_url = Column(String(500), nullable=True)
    tiktok_url = Column(String(500), nullable=True)
    additional_data = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    source_file_name = Column(String(255), nullable=True)
    source_file_row = Column(Integer, nullable=True)
    file_upload_id = Column(Integer, ForeignKey('file_uploads.id'), nullable=True)
    
    def __repr__(self):
        return f"<Lead(id={self.id}, name='{self.full_name}', email='{self.email}', user_id='{self.user_id}')>"

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    timezone = Column(String(50), nullable=True)
    all_day = Column(Boolean, nullable=False, default=False)
    event_type = Column(String(50), nullable=True)
    status = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    user_id = Column(String(255), nullable=True)
    lead_id = Column(Integer, nullable=True)