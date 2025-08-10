from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
from fastapi import HTTPException, status

from outreach_backend.app.models import Lead, OutreachPlatform
from outreach_backend.app.services.conversation_service import conversation_service
from config.settings import settings

class WebhookService:
    def __init__(self):
        pass
    
    def verify_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature for security"""
        expected_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def handle_facebook_webhook(
        self, 
        payload: Dict[str, Any], 
        signature: str,
        db: Session,
        lead_parser_db: Session
    ) -> Dict[str, Any]:
        """Handle Facebook webhook for incoming messages"""
        try:
            # Verify webhook signature
            if not self.verify_webhook_signature(
                json.dumps(payload), 
                signature, 
                settings.webhook_secret
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
            
            # Get platform
            platform = db.query(OutreachPlatform).filter(
                OutreachPlatform.name == "Facebook"
            ).first()
            
            if not platform:
                return {"error": "Facebook platform not configured"}
            
            processed_messages = []
            
            # Process webhook entries
            for entry in payload.get("entry", []):
                for messaging in entry.get("messaging", []):
                    if "message" in messaging:
                        message_data = messaging["message"]
                        sender_id = messaging["sender"]["id"]
                        recipient_id = messaging["recipient"]["id"]
                        
                        # Find lead by Facebook ID
                        lead = lead_parser_db.query(Lead).filter(
                            Lead.facebook_url.contains(sender_id)
                        ).first()
                        
                        if lead:
                            # Store incoming message
                            conversation_message = conversation_service.handle_incoming_message(
                                lead_id=lead.id,
                                platform_id=platform.id,
                                message_content=message_data.get("text", ""),
                                platform_message_id=message_data.get("mid"),
                                sender_identifier=sender_id,
                                recipient_identifier=recipient_id,
                                db=db
                            )
                            
                            processed_messages.append({
                                "lead_id": lead.id,
                                "message_id": conversation_message.id,
                                "content": message_data.get("text", "")
                            })
            
            return {
                "success": True,
                "processed_messages": processed_messages,
                "count": len(processed_messages)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def handle_instagram_webhook(
        self, 
        payload: Dict[str, Any], 
        signature: str,
        db: Session,
        lead_parser_db: Session
    ) -> Dict[str, Any]:
        """Handle Instagram webhook for incoming messages"""
        try:
            # Verify webhook signature
            if not self.verify_webhook_signature(
                json.dumps(payload), 
                signature, 
                settings.webhook_secret
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
            
            # Get platform
            platform = db.query(OutreachPlatform).filter(
                OutreachPlatform.name == "Instagram"
            ).first()
            
            if not platform:
                return {"error": "Instagram platform not configured"}
            
            processed_messages = []
            
            # Process webhook entries
            for entry in payload.get("entry", []):
                for messaging in entry.get("messaging", []):
                    if "message" in messaging:
                        message_data = messaging["message"]
                        sender_id = messaging["sender"]["id"]
                        recipient_id = messaging["recipient"]["id"]
                        
                        # Find lead by Instagram ID
                        lead = lead_parser_db.query(Lead).filter(
                            Lead.instagram_url.contains(sender_id)
                        ).first()
                        
                        if lead:
                            # Store incoming message
                            conversation_message = conversation_service.handle_incoming_message(
                                lead_id=lead.id,
                                platform_id=platform.id,
                                message_content=message_data.get("text", ""),
                                platform_message_id=message_data.get("mid"),
                                sender_identifier=sender_id,
                                recipient_identifier=recipient_id,
                                db=db
                            )
                            
                            processed_messages.append({
                                "lead_id": lead.id,
                                "message_id": conversation_message.id,
                                "content": message_data.get("text", "")
                            })
            
            return {
                "success": True,
                "processed_messages": processed_messages,
                "count": len(processed_messages)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def handle_whatsapp_webhook(
        self, 
        payload: Dict[str, Any], 
        signature: str,
        db: Session,
        lead_parser_db: Session
    ) -> Dict[str, Any]:
        """Handle WhatsApp webhook for incoming messages"""
        try:
            # Verify webhook signature
            if not self.verify_webhook_signature(
                json.dumps(payload), 
                signature, 
                settings.webhook_secret
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
            
            # Get platform
            platform = db.query(OutreachPlatform).filter(
                OutreachPlatform.name == "WhatsApp"
            ).first()
            
            if not platform:
                return {"error": "WhatsApp platform not configured"}
            
            processed_messages = []
            
            # Process webhook entries
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        
                        for message in value.get("messages", []):
                            sender_phone = message.get("from")
                            message_id = message.get("id")
                            message_text = ""
                            
                            if "text" in message:
                                message_text = message["text"]["body"]
                            
                            # Find lead by phone number
                            lead = lead_parser_db.query(Lead).filter(
                                (Lead.phone.contains(sender_phone)) |
                                (Lead.mobile.contains(sender_phone))
                            ).first()
                            
                            if lead:
                                # Store incoming message
                                conversation_message = conversation_service.handle_incoming_message(
                                    lead_id=lead.id,
                                    platform_id=platform.id,
                                    message_content=message_text,
                                    platform_message_id=message_id,
                                    sender_identifier=sender_phone,
                                    recipient_identifier=value.get("metadata", {}).get("phone_number_id"),
                                    db=db
                                )
                                
                                processed_messages.append({
                                    "lead_id": lead.id,
                                    "message_id": conversation_message.id,
                                    "content": message_text
                                })
            
            return {
                "success": True,
                "processed_messages": processed_messages,
                "count": len(processed_messages)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def handle_email_webhook(
        self, 
        payload: Dict[str, Any], 
        signature: str,
        db: Session,
        lead_parser_db: Session
    ) -> Dict[str, Any]:
        """Handle email webhook for incoming messages (if using email service with webhooks)"""
        try:
            # Verify webhook signature
            if not self.verify_webhook_signature(
                json.dumps(payload), 
                signature, 
                settings.webhook_secret
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
            
            # Get platform
            platform = db.query(OutreachPlatform).filter(
                OutreachPlatform.name == "Email"
            ).first()
            
            if not platform:
                return {"error": "Email platform not configured"}
            
            processed_messages = []
            
            # Process email data
            sender_email = payload.get("from")
            subject = payload.get("subject", "")
            content = payload.get("content", "")
            message_id = payload.get("message_id")
            
            # Find lead by email
            lead = lead_parser_db.query(Lead).filter(
                Lead.email == sender_email
            ).first()
            
            if lead:
                # Store incoming message
                conversation_message = conversation_service.handle_incoming_message(
                    lead_id=lead.id,
                    platform_id=platform.id,
                    message_content=f"Subject: {subject}\n\n{content}",
                    platform_message_id=message_id,
                    sender_identifier=sender_email,
                    recipient_identifier=payload.get("to"),
                    db=db
                )
                
                processed_messages.append({
                    "lead_id": lead.id,
                    "message_id": conversation_message.id,
                    "content": content
                })
            
            return {
                "success": True,
                "processed_messages": processed_messages,
                "count": len(processed_messages)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def verify_facebook_webhook(self, verify_token: str, challenge: str) -> Optional[str]:
        """Verify Facebook webhook subscription"""
        if verify_token == settings.webhook_secret:
            return challenge
        return None
    
    def verify_instagram_webhook(self, verify_token: str, challenge: str) -> Optional[str]:
        """Verify Instagram webhook subscription"""
        if verify_token == settings.webhook_secret:
            return challenge
        return None
    
    def verify_whatsapp_webhook(self, verify_token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook subscription"""
        if verify_token == settings.webhook_secret:
            return challenge
        return None

# Initialize the service
webhook_service = WebhookService()

