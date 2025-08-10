from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from cryptography.fernet import Fernet
import smtplib
from email.mime.text import MIMEText
import redis
import json
from config.settings import settings

from outreach_backend.app.models import OutreachPlatform, UserPlatformCredential
from outreach_backend.app.schemas import OutreachPlatformCreate, OutreachPlatformUpdate, UserPlatformCredentialCreate

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class PlatformService:
    def __init__(self):
        self.cipher_suite = Fernet(settings.encryption_key.encode())
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token for secure storage"""
        return self.cipher_suite.encrypt(token.encode()).decode()
    
    def create_platform(self, platform_data: OutreachPlatformCreate, db: Session) -> OutreachPlatform:
        """Create a new email platform with optional credentials"""
        db_platform = OutreachPlatform(
            name=platform_data.name,
            description=platform_data.description,
            user_id=platform_data.user_id
        )
        db.add(db_platform)
        db.commit()
        db.refresh(db_platform)
        
        if hasattr(platform_data, 'username') and platform_data.username and hasattr(platform_data, 'password') and platform_data.password:
            try:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
                server.starttls()
                server.login(platform_data.username, platform_data.password)
                server.quit()
                
                encrypted_password = platform_data.password
                
                new_cred = UserPlatformCredential(
                    user_id=platform_data.user_id,
                    platform_id=db_platform.id,
                    username=platform_data.username,
                    password=encrypted_password
                )
                db.add(new_cred)
                db.commit()
                db.refresh(new_cred)
                
                # Cache platform
                redis_client.setex(
                    f"platform:{platform_data.user_id}:{db_platform.id}",
                    settings.REDIS_CACHE_TTL,
                    json.dumps({k: v for k, v in db_platform.__dict__.items() if not k.startswith('_')}, default=str)
                )
                
            except Exception as e:
                db.delete(db_platform)
                db.commit()
                raise Exception(f"Authentication failed: {str(e)}")
        
        return db_platform
    
    def get_platform(self, user_id: str, platform_id: int, db: Session) -> Optional[OutreachPlatform]:
        """Get an email platform by ID for a user"""
        cache_key = f"platform:{user_id}:{platform_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return OutreachPlatform(**json.loads(cached_data))
            
        platform = db.query(OutreachPlatform).filter(
            OutreachPlatform.id == platform_id,
            OutreachPlatform.user_id == user_id
        ).first()
        
        if platform:
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps({k: v for k, v in platform.__dict__.items() if not k.startswith('_')}, default=str)
            )
        
        return platform
    
    def get_platform_by_name(self, user_id: str, name: str, db: Session) -> Optional[OutreachPlatform]:
        """Get an email platform by name for a user"""
        cache_key = f"platform_by_name:{user_id}:{name}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return OutreachPlatform(**json.loads(cached_data))
            
        platform = db.query(OutreachPlatform).filter(
            OutreachPlatform.name == name,
            OutreachPlatform.user_id == user_id
        ).first()
        
        if platform:
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps({k: v for k, v in platform.__dict__.items() if not k.startswith('_')}, default=str)
            )
        
        return platform
    
    def get_platforms(self, user_id: str, skip: int = 0, limit: int = 100, db: Session = None) -> List[OutreachPlatform]:
        """Get all email platforms with pagination for a user"""
        cache_key = f"platforms:{user_id}:{skip}:{limit}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            platforms_data = json.loads(cached_data)
            return [OutreachPlatform(**{k: v for k, v in platform.items() if not k.startswith('_')}) for platform in platforms_data]
            
        platforms = db.query(OutreachPlatform).filter(OutreachPlatform.user_id == user_id).offset(skip).limit(limit).all()
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(
                [{k: v for k, v in platform.__dict__.items() if not k.startswith('_')} for platform in platforms],
                default=str
            )

        )
        
        return platforms
    
    def update_platform(self, user_id: str, platform_id: int, platform_data: OutreachPlatformUpdate, db: Session) -> Optional[OutreachPlatform]:
        """Update an email platform and its credentials"""
        db_platform = db.query(OutreachPlatform).filter(
            OutreachPlatform.id == platform_id,
            OutreachPlatform.user_id == user_id
        ).first()
        if not db_platform:
            return None
        
        update_data = platform_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field not in ['username', 'password']:
                setattr(db_platform, field, value)
        
        if hasattr(platform_data, 'username') and platform_data.username and hasattr(platform_data, 'password') and platform_data.password:
            try:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
                server.starttls()
                server.login(platform_data.username, platform_data.password)
                server.quit()
                
                existing_cred = db.query(UserPlatformCredential).filter(
                    UserPlatformCredential.user_id == user_id,
                    UserPlatformCredential.platform_id == platform_id
                ).first()
                
                encrypted_password = self.encrypt_token(platform_data.password)
                
                if existing_cred:
                    existing_cred.username = platform_data.username
                    existing_cred.password = encrypted_password
                else:
                    new_cred = UserPlatformCredential(
                        user_id=user_id,
                        platform_id=platform_id,
                        username=platform_data.username,
                        password=encrypted_password
                    )
                    db.add(new_cred)
                
                db.commit()
            except Exception as e:
                db.rollback()
                raise Exception(f"Authentication failed: {str(e)}")
        
        db.commit()
        db.refresh(db_platform)
        
        # Update cache
        cache_key = f"platform:{user_id}:{platform_id}"
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(db_platform.__dict__, default=str)
        )
        redis_client.delete(f"platforms:{user_id}")
        redis_client.delete(f"platform_by_name:{user_id}:{db_platform.name}")
        redis_client.delete(f"connected_platforms:{user_id}")
        redis_client.delete(f"available_platforms:{user_id}")
        
        return db_platform
    
    def delete_platform(self, user_id: str, platform_id: int, db: Session) -> bool:
        """Delete an email platform"""
        db_platform = db.query(OutreachPlatform).filter(
            OutreachPlatform.id == platform_id,
            OutreachPlatform.user_id == user_id
        ).first()
        if not db_platform:
            return False
        
        db.delete(db_platform)
        db.commit()
        
        # Invalidate cache
        redis_client.delete(f"platform:{user_id}:{platform_id}")
        redis_client.delete(f"platforms:{user_id}")
        redis_client.delete(f"platform_by_name:{user_id}:{db_platform.name}")
        redis_client.delete(f"connected_platforms:{user_id}")
        redis_client.delete(f"available_platforms:{user_id}")
        
        return True
    
    def disconnect_platform(self, user_id: str, platform_id: int, db: Session) -> bool:
        """Disconnect a user from a platform by removing credentials"""
        credential = db.query(UserPlatformCredential).filter(
            UserPlatformCredential.user_id == user_id,
            UserPlatformCredential.platform_id == platform_id
        ).first()
        if not credential:
            return False
        
        db.delete(credential)
        db.commit()
        
        # Invalidate cache
        redis_client.delete(f"connected_platforms:{user_id}")
        redis_client.delete(f"available_platforms:{user_id}")
        
        return True
    
    def get_user_connected_platforms(self, user_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get all email platforms that a user has connected"""
        cache_key = f"connected_platforms:{user_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        query = db.query(OutreachPlatform, UserPlatformCredential).join(
            UserPlatformCredential,
            OutreachPlatform.id == UserPlatformCredential.platform_id
        ).filter(UserPlatformCredential.user_id == user_id)
        
        results = []
        for platform, credential in query.all():
            results.append({
                "platform": platform.__dict__,
                "credential": credential.__dict__,
                "is_connected": True,
                "username": credential.username,
                "connected_at": credential.created_at
            })
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(results, default=str)
        )
        
        return results
    
    def get_available_platforms(self, user_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get all available email platforms and their connection status for a user"""
        cache_key = f"available_platforms:{user_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        all_platforms = db.query(OutreachPlatform).filter(OutreachPlatform.user_id == user_id).all()
        connected_platforms = db.query(UserPlatformCredential.platform_id).filter(
            UserPlatformCredential.user_id == user_id
        ).all()
        
        connected_platform_ids = [p[0] for p in connected_platforms]
        
        results = []
        for platform in all_platforms:
            is_connected = platform.id in connected_platform_ids
            credential = None
            
            if is_connected:
                credential = db.query(UserPlatformCredential).filter(
                    and_(
                        UserPlatformCredential.user_id == user_id,
                        UserPlatformCredential.platform_id == platform.id
                    )
                ).first()
            
            results.append({
                "platform": platform.__dict__,
                "is_connected": is_connected,
                "credential": credential.__dict__ if credential else None,
                "username": credential.username if credential else None,
                "connected_at": credential.created_at if credential else None
            })
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(results, default=str)
        )
        
        return results
    
    def initialize_default_platforms(self, platform_data: OutreachPlatformCreate, db: Session) -> List[OutreachPlatform]:
        """Initialize default email platform"""
        cache_key = f"platforms:{platform_data.user_id}"
        
        default_platforms = [
            {
                "name": "Email",
                "description": "Email outreach via SMTP",
                "user_id": platform_data.user_id,
                "username": getattr(platform_data, 'username', None),
                "password": getattr(platform_data, 'password', None)
            }
        ]
        
        created_platforms = []
        for platform_info in default_platforms:
            existing = self.get_platform_by_name(platform_data.user_id, platform_info["name"], db)
            if not existing:
                platform_create = OutreachPlatformCreate(**platform_info)
                platform = self.create_platform(platform_create, db)
                created_platforms.append(platform)
            else:
                created_platforms.append(existing)
        
        # Invalidate platforms cache
        redis_client.delete(cache_key)
        
        return created_platforms

platform_service = PlatformService()