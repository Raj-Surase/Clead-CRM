import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
from datetime import datetime
import redis
from config.settings import settings

from outreach_backend.app.models import (
    OutreachCampaign, OutreachMessage, UserPlatformCredential, OutreachPlatform, 
    LeadPlatformValidation, Lead, CampaignLead, BulkMessageGroup
)
from outreach_backend.app.schemas import OutreachMessageCreate, MessageStatus, SendMessageRequest
from outreach_backend.app.services.auth_service import auth_service

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class MessageSendingService:
    def __init__(self):
        pass
    
    async def send_email(self, lead: Lead, message_content: str, credential: UserPlatformCredential, subject: str = None) -> Dict[str, Any]:
        """Send email message to a lead"""
        try:
            if not lead.email:
                return {"success": False, "error": "Missing email address"}
            
            smtp_password = credential.password
            smtp_username = credential.username
            
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = lead.email
            msg['Subject'] = subject or f"Outreach from {lead.company or 'Our Team'}"
            
            msg.attach(MIMEText(message_content, 'plain'))
            
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_username, lead.email, text)
            server.quit()
            
            return {
                "success": True,
                "platform_message_id": f"email_{datetime.utcnow().timestamp()}",
                "status": MessageStatus.SENT
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "status": MessageStatus.FAILED}
    
    async def send_facebook_message(self, lead: Lead, message_content: str, credential: UserPlatformCredential) -> Dict[str, Any]:
        """Send Facebook message to a lead"""
        try:
            if not lead.facebook_url:
                return {"success": False, "error": "No Facebook URL found for lead"}
            
            facebook_id = lead.facebook_url.split('/')[-1]
            access_token = auth_service.decrypt_token(credential.access_token)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://graph.facebook.com/v18.0/{credential.platform_user_id}/messages",
                    json={
                        "recipient": {"id": facebook_id},
                        "message": {"text": message_content}
                    },
                    params={"access_token": access_token}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "platform_message_id": result.get("message_id"),
                        "status": MessageStatus.SENT
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Facebook API error: {response.text}",
                        "status": MessageStatus.FAILED
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e), "status": MessageStatus.FAILED}
    
    async def send_instagram_message(self, lead: Lead, message_content: str, credential: UserPlatformCredential) -> Dict[str, Any]:
        """Send Instagram message to a lead"""
        try:
            if not lead.instagram_url:
                return {"success": False, "error": "No Instagram URL found for lead"}
            
            instagram_username = lead.instagram_url.split('/')[-1]
            access_token = auth_service.decrypt_token(credential.access_token)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://graph.facebook.com/v18.0/{credential.platform_user_id}/messages",
                    json={
                        "recipient": {"username": instagram_username},
                        "message": {"text": message_content}
                    },
                    params={"access_token": access_token}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "platform_message_id": result.get("message_id"),
                        "status": MessageStatus.SENT
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Instagram API error: {response.text}",
                        "status": MessageStatus.FAILED
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e), "status": MessageStatus.FAILED}
    
    async def send_whatsapp_message(self, lead: Lead, message_content: str, credential: UserPlatformCredential) -> Dict[str, Any]:
        """Send WhatsApp message to a lead"""
        try:
            if not lead.phone and not lead.mobile:
                return {"success": False, "error": "No phone number found for lead"}
            
            phone_number = lead.mobile or lead.phone
            phone_number = ''.join(filter(str.isdigit, phone_number))
            if not phone_number.startswith('1') and len(phone_number) == 10:
                phone_number = '1' + phone_number
            
            access_token = auth_service.decrypt_token(credential.access_token)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://graph.facebook.com/v18.0/{settings.whatsapp_business_account_id}/messages",
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone_number,
                        "type": "text",
                        "text": {"body": message_content}
                    },
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "platform_message_id": result.get("messages", [{}])[0].get("id"),
                        "status": MessageStatus.SENT
                    }
                else:
                    return {
                        "success": False,
                        "error": f"WhatsApp API error: {response.text}",
                        "status": MessageStatus.FAILED
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e), "status": MessageStatus.FAILED}
    
    async def send_linkedin_message(self, lead: Lead, message_content: str, credential: UserPlatformCredential) -> Dict[str, Any]:
        """Send LinkedIn message to a lead"""
        try:
            if not lead.linkedin_url:
                return {"success": False, "error": "No LinkedIn URL found for lead"}
            
            linkedin_id = lead.linkedin_url.split('/')[-1]
            access_token = auth_service.decrypt_token(credential.access_token)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.linkedin.com/v2/messages",
                    json={
                        "recipients": [linkedin_id],
                        "message": {"body": message_content}
                    },
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 201:
                    result = response.json()
                    return {
                        "success": True,
                        "platform_message_id": result.get("id"),
                        "status": MessageStatus.SENT
                    }
                else:
                    return {
                        "success": False,
                        "error": f"LinkedIn API error: {response.text}",
                        "status": MessageStatus.FAILED
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e), "status": MessageStatus.FAILED}
    
    async def send_message_to_lead(
        self, 
        lead: Lead, 
        platform: OutreachPlatform, 
        credential: UserPlatformCredential,
        message_content: str,
        db: Session,
        user_id: str,
        campaign_id: Optional[int] = None,
        bulk_group_id: Optional[int] = None,
        subject: Optional[str] = None
    ) -> OutreachMessage:
        """Send a message to a lead via specified platform"""
        rate_limit_key = f"rate_limit:send_message:{user_id}:{platform.id}"
        if redis_client.get(rate_limit_key):
            count = int(redis_client.get(rate_limit_key))
            if count >= settings.REDIS_MAX_REQUESTS:
                raise ValueError("Message sending rate limit exceeded")
            redis_client.incr(rate_limit_key)
        else:
            redis_client.setex(rate_limit_key, settings.REDIS_RATE_LIMIT_WINDOW, 1)
        
        if platform.user_id != user_id:
            raise ValueError("Platform not authorized for user")
        
        result = await self.send_email(lead, message_content, credential, subject)
        
        message_data = OutreachMessageCreate(
            lead_id=lead.id,
            platform_id=platform.id,
            sender_id=credential.id,
            message_content=message_content,
            campaign_id=campaign_id,
            bulk_group_id=bulk_group_id,
            subject=subject,
            user_id=user_id
        )
        
        db_message = OutreachMessage(**message_data.dict())
        db_message.status = result.get("status", MessageStatus.FAILED)
        db_message.platform_message_id = result.get("platform_message_id")
        db_message.error_message = result.get("error") if not result.get("success") else None
        
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        # Invalidate lead cache
        redis_client.delete(f"lead:{user_id}:{lead.id}")
        redis_client.delete(f"lead_contact_status:{lead.id}")
        
        return db_message
    
    async def send_bulk_messages(
        self,
        message_request: SendMessageRequest,
        db: Session,
        lead_parser_db: Session
    ) -> Dict[str, Any]:
        """Send messages to multiple leads"""
        rate_limit_key = f"rate_limit:bulk_messages:{message_request.user_id}"
        if redis_client.get(rate_limit_key):
            count = int(redis_client.get(rate_limit_key))
            if count >= settings.REDIS_MAX_REQUESTS:
                return {"success": False, "error": "Bulk message rate limit exceeded"}
            redis_client.incr(rate_limit_key)
        else:
            redis_client.setex(rate_limit_key, settings.REDIS_RATE_LIMIT_WINDOW, 1)
        
        platform = db.query(OutreachPlatform).filter(
            OutreachPlatform.id == message_request.platform_id,
            OutreachPlatform.user_id == message_request.user_id
        ).first()
        if not platform:
            return {"success": False, "error": "Platform not found or not authorized for user"}
        
        credential = db.query(UserPlatformCredential).filter(
            UserPlatformCredential.user_id == message_request.user_id,
            UserPlatformCredential.platform_id == message_request.platform_id
        ).first()
        if not credential:
            return {"success": False, "error": "Platform not connected for user"}
        
        if message_request.campaign_id:
            campaign = db.query(OutreachCampaign).filter(
                OutreachCampaign.id == message_request.campaign_id,
                OutreachCampaign.user_id == message_request.user_id
            ).first()
            if not campaign:
                return {"success": False, "error": "Campaign not found or not authorized for user"}
            
            campaign_leads = db.query(CampaignLead).filter(CampaignLead.campaign_id == message_request.campaign_id).all()
            lead_ids = [cl.lead_id for cl in campaign_leads]
            
            if not lead_ids:
                return {"success": False, "error": "No leads found in campaign"}
        else:
            lead_ids = message_request.lead_ids
        
        leads = lead_parser_db.query(Lead).filter(
            Lead.id.in_(lead_ids),
            Lead.user_id == message_request.user_id
        ).all()
        
        results = {
            "success_count": 0,
            "failed_count": 0,
            "messages": [],
            "errors": []
        }
        
        for lead in leads:
            try:
                message = await self.send_message_to_lead(
                    lead, 
                    platform, 
                    credential, 
                    message_request.message_content, 
                    db, 
                    message_request.user_id,
                    message_request.campaign_id, 
                    message_request.bulk_group_id, 
                    message_request.subject
                )
                
                if message.status == MessageStatus.SENT:
                    results["success_count"] += 1
                else:
                    results["failed_count"] += 1
                    if message.error_message:
                        results["errors"].append(f"Lead {lead.id}: {message.error_message}")
                
                results["messages"].append(message.__dict__)
                
            except Exception as e:
                results["failed_count"] += 1
                results["errors"].append(f"Lead {lead.id}: {str(e)}")
        
        # Cache results
        cache_key = f"bulk_messages:{message_request.user_id}:{message_request.platform_id}"
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(results, default=str)
        )
        
        return results
    
    async def validate_lead_for_platform(self, lead: Lead, platform: OutreachPlatform, db: Session) -> bool:
        """Validate if a lead has valid contact information for a platform"""
        cache_key = f"lead_validation:{lead.id}:{platform.id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        existing_validation = db.query(LeadPlatformValidation).filter(
            LeadPlatformValidation.lead_id == lead.id,
            LeadPlatformValidation.platform_id == platform.id
        ).first()
        
        if existing_validation:
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps(existing_validation.is_valid)
            )
            return existing_validation.is_valid
        
        is_valid = False
        details = ""
        
        if platform.name == "Email":
            is_valid = bool(lead.email and lead.email_valid)
            details = "Valid email required" if not is_valid else "Email is valid"
        elif platform.name == "Facebook":
            is_valid = bool(lead.facebook_url)
            details = "Facebook URL required" if not is_valid else "Facebook URL found"
        elif platform.name == "Instagram":
            is_valid = bool(lead.instagram_url)
            details = "Instagram URL required" if not is_valid else "Instagram URL found"
        elif platform.name == "WhatsApp":
            is_valid = bool((lead.phone or lead.mobile) and lead.phone_valid)
            details = "Valid phone number required" if not is_valid else "Phone number is valid"
        elif platform.name == "LinkedIn":
            is_valid = bool(lead.linkedin_url)
            details = "LinkedIn URL required" if not is_valid else "LinkedIn URL found"
        
        validation = LeadPlatformValidation(
            lead_id=lead.id,
            platform_id=platform.id,
            is_valid=is_valid,
            details=details
        )
        db.add(validation)
        db.commit()
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(is_valid)
        )
        
        return is_valid
    
    def get_invalid_leads_for_platform(self, user_id: str, platform_id: int, db: Session) -> List[int]:
        """Get list of lead IDs that are invalid for a platform for a user"""
        cache_key = f"invalid_leads:{user_id}:{platform_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        invalid_validations = db.query(LeadPlatformValidation).join(
            OutreachPlatform,
            LeadPlatformValidation.platform_id == OutreachPlatform.id
        ).filter(
            OutreachPlatform.user_id == user_id,
            LeadPlatformValidation.platform_id == platform_id,
            LeadPlatformValidation.is_valid == False
        ).all()
        
        result = [v.lead_id for v in invalid_validations]
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(result)
        )
        
        return result
    
    def remove_invalid_leads(self, lead_ids: List[int], user_id: str, platform_id: int, db: Session) -> List[int]:
        """Remove invalid lead IDs from a list for a specific platform and user"""
        invalid_lead_ids = self.get_invalid_leads_for_platform(user_id, platform_id, db)
        return [lead_id for lead_id in lead_ids if lead_id not in invalid_lead_ids]

message_service = MessageSendingService()