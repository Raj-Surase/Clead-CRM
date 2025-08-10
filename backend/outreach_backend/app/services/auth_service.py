from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from outreach_backend.app.models import UserPlatformCredential, OutreachPlatform
from outreach_backend.app.schemas import PlatformAuthRequest, UserPlatformCredentialCreate, UserPlatformCredentialUpdate
from config.settings import settings

class AuthenticationService:
    def __init__(self):
        self.cipher_suite = Fernet(settings.encryption_key.encode())
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token for secure storage"""
        return self.cipher_suite.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token for use"""
        return self.cipher_suite.decrypt(encrypted_token.encode()).decode()
    
    async def authenticate_email(self, platform_auth: PlatformAuthRequest, db: Session) -> Dict[str, Any]:
        """Authenticate user with email SMTP credentials"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            # Test SMTP connection
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.starttls()
            server.login(platform_auth.username, platform_auth.password)
            server.quit()
            
            # Store credentials in database
            platform = db.query(OutreachPlatform).filter(
                OutreachPlatform.id == platform_auth.platform_id,
                OutreachPlatform.user_id == platform_auth.user_id
            ).first()
            if not platform:
                return {"success": False, "error": "Email platform not found or not authorized for user"}
            
            # Check if credentials already exist
            existing_cred = db.query(UserPlatformCredential).filter(
                UserPlatformCredential.user_id == platform_auth.user_id,
                UserPlatformCredential.platform_id == platform_auth.platform_id
            ).first()
            
            encrypted_password = platform_auth.password
            
            if existing_cred:
                # Update existing credentials
                existing_cred.username = platform_auth.username
                existing_cred.password = encrypted_password
                db.commit()
                credential_id = existing_cred.id
            else:
                # Create new credentials
                new_cred = UserPlatformCredential(
                    user_id=platform_auth.user_id,
                    platform_id=platform_auth.platform_id,
                    username=platform_auth.username,
                    password=encrypted_password
                )
                db.add(new_cred)
                db.commit()
                db.refresh(new_cred)
                credential_id = new_cred.id
            
            return {
                "success": True,
                "credential_id": credential_id,
                "username": platform_auth.username
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_credentials(self, user_id: str, platform_id: int, db: Session) -> Optional[UserPlatformCredential]:
        """Get user credentials for a specific platform"""
        return db.query(UserPlatformCredential).filter(
            UserPlatformCredential.user_id == user_id,
            UserPlatformCredential.platform_id == platform_id
        ).first()

auth_service = AuthenticationService()