from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime

from outreach_backend.app.models import (
    Conversation, ConversationMessage, OutreachMessage, 
    OutreachPlatform, Lead
)
from outreach_backend.app.schemas import (
    ConversationCreate, ConversationUpdate, ConversationMessageCreate,
    ConversationStatus, MessageDirection
)

class ConversationService:
    def __init__(self):
        pass
    
    def create_conversation(self, conversation_data: ConversationCreate, db: Session) -> Conversation:
        """Create a new conversation"""
        db_conversation = Conversation(**conversation_data.dict())
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    
    def get_conversation(self, conversation_id: int, db: Session) -> Optional[Conversation]:
        """Get a conversation by ID"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def get_conversation_by_lead_platform(self, lead_id: int, platform_id: int, db: Session) -> Optional[Conversation]:
        """Get or create conversation for a lead and platform"""
        conversation = db.query(Conversation).filter(
            and_(
                Conversation.lead_id == lead_id,
                Conversation.platform_id == platform_id
            )
        ).first()
        
        if not conversation:
            # Fetch lead and platform for subject
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            platform = db.query(OutreachPlatform).filter(OutreachPlatform.id == platform_id).first()
            lead_name = lead.full_name or "Unknown Lead" if lead else "Unknown Lead"
            platform_name = platform.name if platform else "Unknown Platform"
            subject = f"Conversation with {lead_name} on {platform_name}"
            
            # Create new conversation
            conversation_data = ConversationCreate(
                lead_id=lead_id,
                platform_id=platform_id,
                status=ConversationStatus.OPEN,
                subject=subject
            )
            conversation = self.create_conversation(conversation_data, db)
        
        return conversation
    
    def get_conversations(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        lead_id: int = None,
        platform_id: int = None,
        status: ConversationStatus = None,
        db: Session = None
    ) -> List[Conversation]:
        """Get conversations with optional filtering"""
        query = db.query(Conversation)
        
        if lead_id:
            query = query.filter(Conversation.lead_id == lead_id)
        
        if platform_id:
            query = query.filter(Conversation.platform_id == platform_id)
        
        if status:
            query = query.filter(Conversation.status == status)
        
        return query.order_by(desc(Conversation.last_message_at)).offset(skip).limit(limit).all()
    
    def update_conversation(self, conversation_id: int, conversation_data: ConversationUpdate, db: Session) -> Optional[Conversation]:
        """Update a conversation"""
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return None
        
        update_data = conversation_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)
        
        db.commit()
        db.refresh(conversation)
        return conversation
    
    def add_message_to_conversation(
        self, 
        conversation_id: int, 
        message_data: ConversationMessageCreate, 
        db: Session
    ) -> ConversationMessage:
        """Add a message to a conversation"""
        db_message = ConversationMessage(**message_data.dict())
        db.add(db_message)
        
        # Update conversation last_message_at
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.last_message_at = datetime.utcnow()
            if message_data.direction == MessageDirection.INCOMING:
                conversation.status = ConversationStatus.PENDING_REPLY
        
        db.commit()
        db.refresh(db_message)
        return db_message
    
    def get_conversation_messages(
        self, 
        conversation_id: int, 
        skip: int = 0, 
        limit: int = 100, 
        db: Session = None
    ) -> List[ConversationMessage]:
        """Get messages for a conversation"""
        return db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.sent_at).offset(skip).limit(limit).all()
    
    def handle_outgoing_message(self, outreach_message: OutreachMessage, db: Session) -> ConversationMessage:
        """Handle an outgoing message by adding it to the conversation"""
        # Get or create conversation
        conversation = self.get_conversation_by_lead_platform(
            outreach_message.lead_id,
            outreach_message.platform_id,
            db
        )
        
        # Create conversation message
        message_data = ConversationMessageCreate(
            conversation_id=conversation.id,
            outreach_message_id=outreach_message.id,
            direction=MessageDirection.OUTGOING,
            message_content=outreach_message.message_content,
            platform_message_id=outreach_message.platform_message_id,
            sender_identifier=outreach_message.sender.platform_user_id if outreach_message.sender else None
        )
        
        return self.add_message_to_conversation(conversation.id, message_data, db)
    
    def handle_incoming_message(
        self,
        lead_id: int,
        platform_id: int,
        message_content: str,
        platform_message_id: str,
        sender_identifier: str,
        recipient_identifier: str,
        db: Session
    ) -> ConversationMessage:
        """Handle an incoming message from a lead"""
        # Get or create conversation
        conversation = self.get_conversation_by_lead_platform(lead_id, platform_id, db)
        
        # Create conversation message
        message_data = ConversationMessageCreate(
            conversation_id=conversation.id,
            direction=MessageDirection.INCOMING,
            message_content=message_content,
            platform_message_id=platform_message_id,
            sender_identifier=sender_identifier,
            recipient_identifier=recipient_identifier
        )
        
        return self.add_message_to_conversation(conversation.id, message_data, db)
    
    def close_conversation(self, conversation_id: int, db: Session) -> Optional[Conversation]:
        """Close a conversation"""
        conversation_update = ConversationUpdate(status=ConversationStatus.CLOSED)
        return self.update_conversation(conversation_id, conversation_update, db)
    
    def reopen_conversation(self, conversation_id: int, db: Session) -> Optional[Conversation]:
        """Reopen a conversation"""
        conversation_update = ConversationUpdate(status=ConversationStatus.OPEN)
        return self.update_conversation(conversation_id, conversation_update, db)
    
    def get_conversation_summary(self, conversation_id: int, db: Session) -> Dict[str, Any]:
        """Get a summary of a conversation"""
        conversation = self.get_conversation(conversation_id, db)
        if not conversation:
            return None
        
        messages = self.get_conversation_messages(conversation_id, db=db)
        
        # Count messages by direction
        outgoing_count = sum(1 for msg in messages if msg.direction == MessageDirection.OUTGOING)
        incoming_count = sum(1 for msg in messages if msg.direction == MessageDirection.INCOMING)
        
        # Get first and last message times
        first_message = messages[0] if messages else None
        last_message = messages[-1] if messages else None
        
        return {
            "conversation": conversation,
            "total_messages": len(messages),
            "outgoing_messages": outgoing_count,
            "incoming_messages": incoming_count,
            "first_message_at": first_message.sent_at if first_message else None,
            "last_message_at": last_message.sent_at if last_message else None,
            "response_rate": (incoming_count / outgoing_count * 100) if outgoing_count > 0 else 0
        }
    
    def get_lead_conversations(self, lead_id: int, db: Session) -> List[Conversation]:
        """Get all conversations for a lead"""
        return db.query(Conversation).filter(Conversation.lead_id == lead_id).all()
    
    def search_conversations(
        self, 
        search_term: str, 
        platform_id: int = None,
        status: ConversationStatus = None,
        db: Session = None
    ) -> List[Conversation]:
        """Search conversations by message content"""
        query = db.query(Conversation).join(ConversationMessage).filter(
            ConversationMessage.message_content.contains(search_term)
        )
        
        if platform_id:
            query = query.filter(Conversation.platform_id == platform_id)
        
        if status:
            query = query.filter(Conversation.status == status)
        
        return query.distinct().all()

# Initialize the service
conversation_service = ConversationService()