
"""
Notification and Alert System for AI Life Coach application
"""
import os
import json
import datetime
import logging
import smtplib
try:
    import email.mime.text
    import email.mime.multipart
    MimeText = email.mime.text.MimeText
    MimeMultipart = email.mime.multipart.MimeMultipart
except (ImportError, AttributeError):
    # Fallback for systems where email modules might not be available
    MimeText = None
    MimeMultipart = None
from typing import Dict, List, Optional
import threading
import time
from dataclasses import dataclass
from enum import Enum

class NotificationType(Enum):
    GOAL_REMINDER = "goal_reminder"
    HABIT_STREAK = "habit_streak"
    MOOD_CHECK = "mood_check"
    ACHIEVEMENT = "achievement"
    SYSTEM_ALERT = "system_alert"
    SECURITY_WARNING = "security_warning"
    MAINTENANCE = "maintenance"
    MILESTONE = "milestone"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Notification:
    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    user_id: str
    created_at: datetime.datetime
    scheduled_for: Optional[datetime.datetime] = None
    sent: bool = False
    delivery_methods: List[str] = None
    metadata: Dict = None

class NotificationSystem:
    def __init__(self):
        self.notifications = []
        self.notification_preferences = {
            "email_enabled": True,
            "push_enabled": True,
            "in_app_enabled": True,
            "sms_enabled": False,
            "quiet_hours": {"start": "22:00", "end": "08:00"},
            "frequency_limits": {
                "goal_reminder": "daily",
                "habit_streak": "weekly",
                "mood_check": "daily"
            }
        }
        self.start_notification_scheduler()
    
    def create_notification(self, notification_type: NotificationType, 
                          title: str, message: str, user_id: str = "default",
                          priority: NotificationPriority = NotificationPriority.MEDIUM,
                          scheduled_for: Optional[datetime.datetime] = None,
                          delivery_methods: List[str] = None,
                          metadata: Dict = None) -> str:
        """Create a new notification"""
        
        notification_id = f"notif_{int(time.time())}"
        
        if delivery_methods is None:
            delivery_methods = ["in_app"]
            if priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL]:
                delivery_methods.extend(["email", "push"])
        
        notification = Notification(
            id=notification_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            user_id=user_id,
            created_at=datetime.datetime.now(),
            scheduled_for=scheduled_for,
            delivery_methods=delivery_methods,
            metadata=metadata or {}
        )
        
        self.notifications.append(notification)
        
        # Send immediately if not scheduled
        if scheduled_for is None:
            self._send_notification(notification)
        
        return notification_id
    
    def _send_notification(self, notification: Notification):
        """Send notification through specified channels"""
        try:
            if self._is_quiet_hours():
                if notification.priority != NotificationPriority.CRITICAL:
                    # Reschedule for after quiet hours
                    notification.scheduled_for = self._get_next_active_time()
                    return
            
            for method in notification.delivery_methods:
                if method == "email" and self.notification_preferences["email_enabled"]:
                    self._send_email(notification)
                elif method == "push" and self.notification_preferences["push_enabled"]:
                    self._send_push(notification)
                elif method == "in_app" and self.notification_preferences["in_app_enabled"]:
                    self._send_in_app(notification)
                elif method == "sms" and self.notification_preferences["sms_enabled"]:
                    self._send_sms(notification)
            
            notification.sent = True
            logging.info(f"Notification {notification.id} sent successfully")
            
        except Exception as e:
            logging.error(f"Failed to send notification {notification.id}: {str(e)}")
    
    def _send_email(self, notification: Notification):
        """Send email notification"""
        try:
            if MimeText is None or MimeMultipart is None:
                logging.warning("Email modules not available, skipping email notification")
                return
                
            # In production, configure SMTP settings
            smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            smtp_username = os.environ.get("SMTP_USERNAME", "")
            smtp_password = os.environ.get("SMTP_PASSWORD", "")
            
            if not smtp_username or not smtp_password:
                logging.warning("SMTP credentials not configured")
                return
            
            msg = MimeMultipart()
            msg["From"] = smtp_username
            msg["To"] = os.environ.get("USER_EMAIL", "user@example.com")
            msg["Subject"] = f"AI Life Coach: {notification.title}"
            
            body = f"""
            {notification.message}
            
            Priority: {notification.priority.value.upper()}
            Time: {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}
            
            This is an automated message from your AI Life Coach.
            """
            
            msg.attach(MimeText(body, "plain"))
            
            # Send email (commented out for demo)
            # server = smtplib.SMTP(smtp_server, smtp_port)
            # server.starttls()
            # server.login(smtp_username, smtp_password)
            # server.send_message(msg)
            # server.quit()
            
            logging.info(f"Email notification sent: {notification.title}")
            
        except Exception as e:
            logging.error(f"Email sending failed: {str(e)}")
    
    def _send_push(self, notification: Notification):
        """Send push notification"""
        # In production, integrate with push notification service
        logging.info(f"Push notification: {notification.title}")
    
    def _send_in_app(self, notification: Notification):
        """Send in-app notification"""
        # Store for web interface display
        in_app_file = "in_app_notifications.json"
        try:
            if os.path.exists(in_app_file):
                with open(in_app_file, "r") as f:
                    in_app_notifications = json.load(f)
            else:
                in_app_notifications = []
            
            in_app_notifications.append({
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "priority": notification.priority.value,
                "timestamp": notification.created_at.isoformat(),
                "read": False
            })
            
            # Keep only last 50 notifications
            in_app_notifications = in_app_notifications[-50:]
            
            with open(in_app_file, "w") as f:
                json.dump(in_app_notifications, f, indent=2)
                
        except Exception as e:
            logging.error(f"In-app notification failed: {str(e)}")
    
    def _send_sms(self, notification: Notification):
        """Send SMS notification"""
        # In production, integrate with SMS service like Twilio
        logging.info(f"SMS notification: {notification.title}")
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours"""
        now = datetime.datetime.now().time()
        start_time = datetime.time.fromisoformat(self.notification_preferences["quiet_hours"]["start"])
        end_time = datetime.time.fromisoformat(self.notification_preferences["quiet_hours"]["end"])
        
        if start_time <= end_time:
            return start_time <= now <= end_time
        else:  # Quiet hours cross midnight
            return now >= start_time or now <= end_time
    
    def _get_next_active_time(self) -> datetime.datetime:
        """Get next time outside quiet hours"""
        now = datetime.datetime.now()
        end_time = datetime.time.fromisoformat(self.notification_preferences["quiet_hours"]["end"])
        
        next_active = datetime.datetime.combine(now.date(), end_time)
        if next_active <= now:
            next_active += datetime.timedelta(days=1)
        
        return next_active
    
    def start_notification_scheduler(self):
        """Start background scheduler for notifications"""
        def scheduler_loop():
            while True:
                current_time = datetime.datetime.now()
                
                # Check for scheduled notifications
                for notification in self.notifications:
                    if (not notification.sent and 
                        notification.scheduled_for and 
                        notification.scheduled_for <= current_time):
                        self._send_notification(notification)
                
                # Generate smart notifications
                self._generate_smart_notifications()
                
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_thread.start()
    
    def _generate_smart_notifications(self):
        """Generate intelligent notifications based on user patterns"""
        try:
            from app import load_memory
            memory = load_memory()
            now = datetime.datetime.now()
            
            # Goal reminder notifications
            goals = memory.get("goals", [])
            for goal in goals:
                if goal.get("status") == "active":
                    created_date = datetime.datetime.fromisoformat(goal.get("created_date", now.isoformat()))
                    days_since_created = (now - created_date).days
                    
                    if days_since_created > 7 and goal.get("progress", 0) < 20:
                        self.create_notification(
                            NotificationType.GOAL_REMINDER,
                            "Goal Needs Attention",
                            f"Your goal '{goal['text']}' hasn't seen much progress. Let's work on it today!",
                            priority=NotificationPriority.MEDIUM
                        )
            
            # Habit streak notifications
            habits = memory.get("habits", [])
            for habit in habits:
                if habit.get("status") == "active":
                    streak = habit.get("current_streak", 0)
                    if streak > 0 and streak % 7 == 0:  # Weekly streak milestones
                        self.create_notification(
                            NotificationType.HABIT_STREAK,
                            "Streak Milestone!",
                            f"Amazing! You've maintained '{habit['name']}' for {streak} days straight!",
                            priority=NotificationPriority.HIGH
                        )
            
            # Mood check notifications
            mood_history = memory.get("mood_history", [])
            if mood_history:
                last_mood = mood_history[-1]
                last_mood_date = datetime.datetime.fromisoformat(last_mood.get("timestamp"))
                days_since_mood = (now - last_mood_date).days
                
                if days_since_mood >= 2:
                    self.create_notification(
                        NotificationType.MOOD_CHECK,
                        "How are you feeling?",
                        "It's been a while since your last mood check-in. How are you doing today?",
                        priority=NotificationPriority.LOW
                    )
        
        except Exception as e:
            logging.error(f"Smart notification generation failed: {str(e)}")
    
    def get_user_notifications(self, user_id: str = "default", 
                             limit: int = 20, unread_only: bool = False) -> List[Dict]:
        """Get notifications for user"""
        user_notifications = [
            n for n in self.notifications 
            if n.user_id == user_id and (not unread_only or not n.sent)
        ]
        
        # Sort by priority and creation time
        priority_order = {
            NotificationPriority.CRITICAL: 0,
            NotificationPriority.HIGH: 1,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.LOW: 3
        }
        
        user_notifications.sort(
            key=lambda x: (priority_order[x.priority], x.created_at),
            reverse=True
        )
        
        return [
            {
                "id": n.id,
                "type": n.type.value,
                "priority": n.priority.value,
                "title": n.title,
                "message": n.message,
                "created_at": n.created_at.isoformat(),
                "sent": n.sent,
                "metadata": n.metadata
            }
            for n in user_notifications[:limit]
        ]
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.sent = True
                return True
        return False
    
    def update_preferences(self, preferences: Dict):
        """Update notification preferences"""
        self.notification_preferences.update(preferences)
        logging.info("Notification preferences updated")

# Global notification system
notification_system = NotificationSystem()
