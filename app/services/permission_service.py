"""
User Permission Service
Manages user data access with permission controls
"""
from typing import Dict, Optional, List
import logging
from datetime import datetime
from app.database import db_client
from app.database.KYCdatabase import MongoDB
import asyncio

logger = logging.getLogger(__name__)


class PermissionService:
    """Handles user data access with permission management"""
    
    def __init__(self):
        self.kyc_db = MongoDB()
    
    async def check_user_permission(
        self,
        user_id: str,
        permission_type: str
    ) -> bool:
        """
        Check if user has granted permission for data access
        
        Args:
            user_id: User ID
            permission_type: Type of permission (kyc, wallet, posts, profile)
        
        Returns:
            True if permission granted
        """
        try:
            if not db_client or not db_client.is_connected():
                return False
            
            # Get user permissions from database
            permissions = await asyncio.to_thread(
                db_client.db['user_permissions'].find_one,
                {"user_id": user_id}
            )
            
            if not permissions:
                # Default: no permissions granted
                return False
            
            return permissions.get(permission_type, False)
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    async def grant_permission(
        self,
        user_id: str,
        permission_type: str
    ) -> bool:
        """Grant permission for user data access"""
        try:
            if not db_client or not db_client.is_connected():
                return False
            
            result = await asyncio.to_thread(
                db_client.db['user_permissions'].update_one,
                {"user_id": user_id},
                {
                    "$set": {
                        permission_type: True,
                        f"{permission_type}_granted_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.info(f"Permission {permission_type} granted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error granting permission: {e}")
            return False
    
    async def revoke_permission(
        self,
        user_id: str,
        permission_type: str
    ) -> bool:
        """Revoke permission for user data access"""
        try:
            if not db_client or not db_client.is_connected():
                return False
            
            result = await asyncio.to_thread(
                db_client.db['user_permissions'].update_one,
                {"user_id": user_id},
                {
                    "$set": {
                        permission_type: False,
                        f"{permission_type}_revoked_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Permission {permission_type} revoked for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking permission: {e}")
            return False
    
    async def get_user_context(self, user_id: str) -> Dict:
        """
        Get user context data based on granted permissions
        
        Returns:
            Dictionary with user data (only permitted fields)
        """
        context = {}
        
        try:
            # Check KYC permission and get data
            if await self.check_user_permission(user_id, "kyc"):
                kyc_data = await self._get_kyc_data(user_id)
                context.update(kyc_data)
            
            # Check wallet permission and get data
            if await self.check_user_permission(user_id, "wallet"):
                wallet_data = await self._get_wallet_data(user_id)
                context.update(wallet_data)
            
            # Check posts permission and get data
            if await self.check_user_permission(user_id, "posts"):
                posts_data = await self._get_posts_data(user_id)
                context.update(posts_data)
            
            # Check profile permission and get data
            if await self.check_user_permission(user_id, "profile"):
                profile_data = await self._get_profile_data(user_id)
                context.update(profile_data)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {}
    
    async def _get_kyc_data(self, user_id: str) -> Dict:
        """Get KYC data for user"""
        try:
            kyc_result = await asyncio.to_thread(
                self.kyc_db.get_verification_result,
                user_id
            )
            
            if not kyc_result:
                return {"kyc_status": "not_started"}
            
            review_result = kyc_result.get("reviewResult", {})
            review_answer = review_result.get("reviewAnswer", "unknown")
            
            data = {
                "kyc_status": review_answer.lower(),
                "applicant_id": kyc_result.get("applicantId"),
            }
            
            # Add rejection reason if rejected
            if review_answer.lower() == "red":
                rejection_labels = review_result.get("rejectLabels", [])
                if rejection_labels:
                    data["kyc_rejection_reason"] = ", ".join(rejection_labels)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting KYC data: {e}")
            return {}
    
    async def _get_wallet_data(self, user_id: str) -> Dict:
        """Get wallet data for user"""
        try:
            # This would integrate with your actual wallet system
            # For now, returning placeholder structure
            wallet = await asyncio.to_thread(
                db_client.db['wallets'].find_one,
                {"user_id": user_id}
            ) if db_client else None
            
            if wallet:
                return {
                    "wallet_balance": wallet.get("balance", 0.0),
                    "pending_transactions": wallet.get("pending_count", 0)
                }
            
            return {"wallet_balance": 0.0}
            
        except Exception as e:
            logger.error(f"Error getting wallet data: {e}")
            return {}
    
    async def _get_posts_data(self, user_id: str) -> Dict:
        """Get posts data for user"""
        try:
            # This would integrate with your actual posts system
            if not db_client or not db_client.is_connected():
                return {}
            
            posts_count = await asyncio.to_thread(
                db_client.db['posts'].count_documents,
                {"user_id": user_id}
            )
            
            # Get recent post status
            recent_post = await asyncio.to_thread(
                db_client.db['posts'].find_one,
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            
            data = {"total_posts": posts_count}
            
            if recent_post:
                data["last_post_status"] = recent_post.get("status", "unknown")
                if recent_post.get("status") == "rejected":
                    data["last_post_rejection_reason"] = recent_post.get("rejection_reason", "")
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting posts data: {e}")
            return {}
    
    async def _get_profile_data(self, user_id: str) -> Dict:
        """Get profile data for user"""
        try:
            if not db_client or not db_client.is_connected():
                return {}
            
            profile = await asyncio.to_thread(
                db_client.db['profiles'].find_one,
                {"user_id": user_id}
            )
            
            if profile:
                return {
                    "username": profile.get("username", ""),
                    "account_created": profile.get("created_at", ""),
                    "last_activity": profile.get("last_activity", "")
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting profile data: {e}")
            return {}
    
    async def get_all_permissions(self, user_id: str) -> Dict:
        """Get all permission settings for a user"""
        try:
            if not db_client or not db_client.is_connected():
                return {}
            
            permissions = await asyncio.to_thread(
                db_client.db['user_permissions'].find_one,
                {"user_id": user_id}
            )
            
            if not permissions:
                return {
                    "kyc": False,
                    "wallet": False,
                    "posts": False,
                    "profile": False
                }
            
            return {
                "kyc": permissions.get("kyc", False),
                "wallet": permissions.get("wallet", False),
                "posts": permissions.get("posts", False),
                "profile": permissions.get("profile", False)
            }
            
        except Exception as e:
            logger.error(f"Error getting permissions: {e}")
            return {}


# Singleton instance
permission_service = PermissionService()
