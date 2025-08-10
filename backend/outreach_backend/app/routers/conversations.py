from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from outreach_backend.app.database import get_db, get_lead_parser_db
from outreach_backend.app.schemas import (
    Conversation, ConversationCreate, ConversationUpdate,
    ConversationMessage, ConversationMessageCreate,
    ConversationStatus
)
from outreach_backend.app.services.conversation_service import conversation_service
from outreach_backend.app.services.webhook_service import webhook_service
from outreach_backend.app.models import Conversation as ConversationModel

router = APIRouter()

# Conversation endpoints
@router.post("/", response_model=Conversation)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    return conversation_service.create_conversation(conversation, db)

@router.get("/", response_model=List[Conversation])
async def get_conversations(
    skip: int = 0,
    limit: int = 100,
    lead_id: Optional[int] = None,
    platform_id: Optional[int] = None,
    status: Optional[ConversationStatus] = None,
    db: Session = Depends(get_db)
):
    """Get conversations with optional filtering"""
    return conversation_service.get_conversations(
        skip=skip,
        limit=limit,
        lead_id=lead_id,
        platform_id=platform_id,
        status=status,
        db=db
    )

@router.get("/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific conversation"""
    conversation = conversation_service.get_conversation(conversation_id, db)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation

@router.put("/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db)
):
    """Update a conversation"""
    conversation = conversation_service.update_conversation(conversation_id, conversation_update, db)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    conversation = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted successfully"}

@router.get("/{conversation_id}/messages", response_model=List[ConversationMessage])
async def get_conversation_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get messages for a conversation"""
    # Verify conversation exists
    conversation = conversation_service.get_conversation(conversation_id, db)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation_service.get_conversation_messages(conversation_id, skip, limit, db)

@router.post("/{conversation_id}/messages", response_model=ConversationMessage)
async def add_message_to_conversation(
    conversation_id: int,
    message: ConversationMessageCreate,
    db: Session = Depends(get_db)
):
    """Add a message to a conversation"""
    # Verify conversation exists
    conversation = conversation_service.get_conversation(conversation_id, db)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation_service.add_message_to_conversation(conversation_id, message, db)

@router.post("/{conversation_id}/close")
async def close_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Close a conversation"""
    conversation = conversation_service.close_conversation(conversation_id, db)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return {"message": "Conversation closed successfully"}

@router.post("/{conversation_id}/reopen")
async def reopen_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Reopen a conversation"""
    conversation = conversation_service.reopen_conversation(conversation_id, db)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return {"message": "Conversation reopened successfully"}

@router.get("/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Get a summary of a conversation"""
    summary = conversation_service.get_conversation_summary(conversation_id, db)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return summary

@router.get("/lead/{lead_id}")
async def get_lead_conversations(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Get all conversations for a lead"""
    conversations = conversation_service.get_lead_conversations(lead_id, db)
    return {
        "lead_id": lead_id,
        "conversations": conversations,
        "count": len(conversations)
    }

@router.get("/search/")
async def search_conversations(
    search_term: str = Query(..., description="Search term to look for in message content"),
    platform_id: Optional[int] = None,
    status: Optional[ConversationStatus] = None,
    db: Session = Depends(get_db)
):
    """Search conversations by message content"""
    conversations = conversation_service.search_conversations(
        search_term=search_term,
        platform_id=platform_id,
        status=status,
        db=db
    )
    return {
        "search_term": search_term,
        "conversations": conversations,
        "count": len(conversations)
    }

# Webhook endpoints
@router.post("/webhooks/facebook")
async def facebook_webhook(
    request: Request,
    db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Handle Facebook webhook for incoming messages"""
    payload = await request.json()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    result = await webhook_service.handle_facebook_webhook(payload, signature, db, lead_parser_db)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/webhooks/facebook")
async def verify_facebook_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """Verify Facebook webhook subscription"""
    if hub_mode == "subscribe":
        challenge = webhook_service.verify_facebook_webhook(hub_verify_token, hub_challenge)
        if challenge:
            return int(challenge)
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid verification token"
    )

@router.post("/webhooks/instagram")
async def instagram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Handle Instagram webhook for incoming messages"""
    payload = await request.json()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    result = await webhook_service.handle_instagram_webhook(payload, signature, db, lead_parser_db)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/webhooks/instagram")
async def verify_instagram_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """Verify Instagram webhook subscription"""
    if hub_mode == "subscribe":
        challenge = webhook_service.verify_instagram_webhook(hub_verify_token, hub_challenge)
        if challenge:
            return int(challenge)
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid verification token"
    )

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Handle WhatsApp webhook for incoming messages"""
    payload = await request.json()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    result = await webhook_service.handle_whatsapp_webhook(payload, signature, db, lead_parser_db)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/webhooks/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """Verify WhatsApp webhook subscription"""
    if hub_mode == "subscribe":
        challenge = webhook_service.verify_whatsapp_webhook(hub_verify_token, hub_challenge)
        if challenge:
            return int(challenge)
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid verification token"
    )

@router.post("/webhooks/email")
async def email_webhook(
    request: Request,
    db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Handle email webhook for incoming messages"""
    payload = await request.json()
    signature = request.headers.get("X-Signature", "")
    
    result = await webhook_service.handle_email_webhook(payload, signature, db, lead_parser_db)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

