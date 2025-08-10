from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from outreach_backend.app.database import get_db
from outreach_backend.app.schemas import (
    OutreachPlatform, OutreachPlatformCreate, OutreachPlatformUpdate,
    PlatformAuthRequest, PlatformAuthResponse
)
from outreach_backend.app.services.platform_service import platform_service
from outreach_backend.app.services.auth_service import auth_service
from outreach_backend.app.models import OutreachPlatform as OutreachPlatformModel

router = APIRouter()

@router.post("/platforms", response_model=OutreachPlatform)
async def create_platform(
    platform: OutreachPlatformCreate,
    db: Session = Depends(get_db)
):
    """Create a new email platform for a user with optional credentials"""
    if not platform.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )
    return platform_service.create_platform(platform, db)

@router.get("/user/{user_id}/platforms", response_model=List[OutreachPlatform])
async def get_platforms(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all email platforms for a user"""
    return platform_service.get_platforms(user_id, skip, limit, db)

@router.get("/user/{user_id}/platforms/{platform_id}", response_model=OutreachPlatform)
async def get_platform(
    user_id: str,
    platform_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific email platform by ID for a user"""
    platform = platform_service.get_platform(user_id, platform_id, db)
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found or not authorized for user"
        )
    return platform

@router.put("/user/{user_id}/platforms/{platform_id}", response_model=OutreachPlatform)
async def update_platform(
    user_id: str,
    platform_id: int,
    platform_update: OutreachPlatformUpdate,
    db: Session = Depends(get_db)
):
    """Update an email platform for a user"""
    platform = platform_service.update_platform(user_id, platform_id, platform_update, db)
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found or not authorized for user"
        )
    return platform

@router.delete("/user/{user_id}/platforms/{platform_id}")
async def delete_platform(
    user_id: str,
    platform_id: int,
    db: Session = Depends(get_db)
):
    """Delete an email platform for a user"""
    success = platform_service.delete_platform(user_id, platform_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found or not authorized for user"
        )
    return {"message": "Platform deleted successfully"}

@router.get("/user/{user_id}/connected")
async def get_user_connected_platforms(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all email platforms connected by a user"""
    return platform_service.get_user_connected_platforms(user_id, db)

@router.get("/user/{user_id}/available")
async def get_available_platforms(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all available email platforms and their connection status for a user"""
    return platform_service.get_available_platforms(user_id, db)

@router.post("/user/{user_id}/authenticate", response_model=PlatformAuthResponse)
async def authenticate_platform(
    user_id: str,
    auth_request: PlatformAuthRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user with an email platform"""
    platform = platform_service.get_platform(user_id, auth_request.platform_id, db)
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found or not authorized for user"
        )
    
    if not auth_request.username or not auth_request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )
    
    result = await auth_service.authenticate_email(auth_request, db)
    
    if not result or not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Authentication failed") if result else "Authentication failed"
        )
    
    return PlatformAuthResponse(
        success=True,
        message="Authentication successful",
        credential_id=result.get("credential_id")
    )

@router.delete("/user/{user_id}/platform/{platform_id}/disconnect")
async def disconnect_platform(
    user_id: str,
    platform_id: int,
    db: Session = Depends(get_db)
):
    """Disconnect a user from an email platform by removing credentials"""
    success = platform_service.disconnect_platform(user_id, platform_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform connection not found or not authorized for user"
        )
    return {"message": "Platform disconnected successfully"}

@router.post("/user/{user_id}/initialize-defaults")
async def initialize_default_platforms(
    user_id: str,
    platform_data: OutreachPlatformCreate,
    db: Session = Depends(get_db)
):
    """Initialize default email platform for a user"""
    platforms = platform_service.initialize_default_platforms(platform_data, db)
    return {
        "message": f"Initialized {len(platforms)} default platforms",
        "platforms": platforms
    }