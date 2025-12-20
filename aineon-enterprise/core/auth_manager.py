"""
AINEON Authentication & Authorization Manager
Multi-user SaaS authentication system with RBAC
"""

import os
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import jwt
import bcrypt
from functools import wraps

class User:
    """User model for AINEON SaaS"""
    def __init__(self, id: str, email: str, first_name: str, last_name: str,
                 organization_id: str, organization_name: str, role: str,
                 status: str = 'ACTIVE', email_verified: bool = False):
        self.id = id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.organization_id = organization_id
        self.organization_name = organization_name
        self.role = role
        self.status = status
        self.email_verified = email_verified
        self.created_at = datetime.utcnow()
        self.last_login = None

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'organizationId': self.organization_id,
            'organizationName': self.organization_name,
            'role': self.role,
            'status': self.status,
            'emailVerified': self.email_verified,
            'createdAt': self.created_at.isoformat(),
            'lastLogin': self.last_login.isoformat() if self.last_login else None,
        }


class AuthManager:
    """Authentication and authorization manager"""
    
    ROLES = {
        'SUPER_ADMIN': 5,
        'ADMIN': 4,
        'TRADER': 3,
        'AUDITOR': 2,
        'VIEWER': 1,
    }

    PERMISSIONS = {
        'SUPER_ADMIN': ['*'],  # All permissions
        'ADMIN': [
            'user:read', 'user:write', 'user:approve',
            'organization:read', 'organization:write',
            'dashboard:full', 'audit:read', 'settings:write'
        ],
        'TRADER': [
            'dashboard:analytics', 'dashboard:risk',
            'trade:execute', 'trade:read',
            'profit:read', 'report:read'
        ],
        'AUDITOR': [
            'dashboard:compliance', 'audit:read',
            'report:read', 'export:read'
        ],
        'VIEWER': [
            'dashboard:view', 'report:view_limited'
        ],
    }

    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'aineon-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.token_expiry = 900  # 15 minutes
        self.refresh_token_expiry = 604800  # 7 days
        self.users: Dict[str, User] = {}  # In-memory storage (use DB in production)
        self.passwords: Dict[str, str] = {}  # Hashed passwords
        self.pending_approvals: List[Dict] = []
        self._init_admin()

    def _init_admin(self):
        """Initialize default admin user"""
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@aineon.io')
        admin_password = os.getenv('ADMIN_PASSWORD', 'aineon-default-admin')
        
        admin_id = str(uuid.uuid4())
        admin = User(
            id=admin_id,
            email=admin_email,
            first_name='System',
            last_name='Admin',
            organization_id='aineon-system',
            organization_name='AINEON',
            role='SUPER_ADMIN',
            status='ACTIVE',
            email_verified=True
        )
        self.users[admin_id] = admin
        self.passwords[admin_email] = self._hash_password(admin_password)

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def _generate_token(self, user_id: str, expires_in: int) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def register(self, email: str, password: str, first_name: str, last_name: str,
                 organization_name: str, country: str, use_case: str,
                 subscription_tier: str) -> Dict:
        """Register new user"""
        if email in [u.email for u in self.users.values()]:
            return {'error': 'Email already registered', 'code': 'EMAIL_EXISTS'}

        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            organization_id=organization_name.lower().replace(' ', '-'),
            organization_name=organization_name,
            role='TRADER',  # Default role
            status='PENDING_APPROVAL',  # Requires admin approval
            email_verified=False
        )

        self.users[user_id] = user
        self.passwords[email] = self._hash_password(password)
        self.pending_approvals.append({
            'user_id': user_id,
            'email': email,
            'organization': organization_name,
            'tier': subscription_tier,
            'applied_at': datetime.utcnow().isoformat(),
            'country': country,
            'use_case': use_case,
        })

        return {
            'user_id': user_id,
            'status': 'PENDING_VERIFICATION',
            'message': 'Check email for verification link'
        }

    def login(self, email: str, password: str) -> Dict:
        """User login"""
        # Find user by email
        user = None
        for u in self.users.values():
            if u.email == email:
                user = u
                break

        if not user:
            return {'error': 'Invalid credentials', 'code': 'INVALID_CREDENTIALS'}

        if user.status != 'ACTIVE':
            return {'error': f'Account {user.status.lower()}', 'code': 'ACCOUNT_INACTIVE'}

        if email not in self.passwords or not self._verify_password(password, self.passwords[email]):
            return {'error': 'Invalid credentials', 'code': 'INVALID_CREDENTIALS'}

        # Generate tokens
        access_token = self._generate_token(user.id, self.token_expiry)
        refresh_token = self._generate_token(user.id, self.refresh_token_expiry)

        user.last_login = datetime.utcnow()

        return {
            'user': user.to_dict(),
            'accessToken': access_token,
            'refreshToken': refresh_token,
        }

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)

    def approve_user(self, user_id: str) -> bool:
        """Admin approval of user"""
        user = self.get_user(user_id)
        if user:
            user.status = 'ACTIVE'
            user.email_verified = True
            # Remove from pending
            self.pending_approvals = [p for p in self.pending_approvals if p['user_id'] != user_id]
            return True
        return False

    def reject_user(self, user_id: str) -> bool:
        """Admin rejection of user"""
        if user_id in self.users:
            del self.users[user_id]
            self.pending_approvals = [p for p in self.pending_approvals if p['user_id'] != user_id]
            return True
        return False

    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending user approvals"""
        result = []
        for pending in self.pending_approvals:
            user = self.get_user(pending['user_id'])
            if user:
                result.append({
                    'id': user.id,
                    'email': user.email,
                    'firstName': user.first_name,
                    'lastName': user.last_name,
                    'organizationName': pending['organization'],
                    'country': pending['country'],
                    'subscriptionTier': pending['tier'],
                    'useCase': pending['use_case'],
                    'appliedAt': pending['applied_at'],
                    'emailVerified': user.email_verified,
                })
        return result

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has permission"""
        user = self.get_user(user_id)
        if not user:
            return False

        permissions = self.PERMISSIONS.get(user.role, [])
        if '*' in permissions:
            return True

        return permission in permissions

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.get_user(user_id)
        if not user:
            return False

        if user.email not in self.passwords:
            return False

        if not self._verify_password(old_password, self.passwords[user.email]):
            return False

        self.passwords[user.email] = self._hash_password(new_password)
        return True


# Global auth manager instance
auth_manager = AuthManager()
