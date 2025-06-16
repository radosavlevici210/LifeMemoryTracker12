
"""
Collaboration and Sharing Tools for AI Life Coach
"""
import json
import datetime
import hashlib
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

class ShareType(Enum):
    ACHIEVEMENT = "achievement"
    GOAL = "goal"
    MILESTONE = "milestone"
    PROGRESS_REPORT = "progress_report"
    INSIGHT = "insight"

class ShareVisibility(Enum):
    PRIVATE = "private"
    FRIENDS = "friends"
    PUBLIC = "public"

@dataclass
class SharedItem:
    id: str
    user_id: str
    share_type: ShareType
    title: str
    content: Dict
    visibility: ShareVisibility
    created_at: datetime.datetime
    views: int = 0
    likes: int = 0
    comments: List[Dict] = None

class CollaborationTools:
    def __init__(self):
        self.shared_items = []
        self.user_connections = {}  # user_id -> list of connected user_ids
        self.share_settings = {
            "auto_share_achievements": False,
            "auto_share_milestones": True,
            "default_visibility": ShareVisibility.FRIENDS,
            "allow_comments": True
        }
    
    def create_share(self, user_id: str, share_type: ShareType, title: str, 
                    content: Dict, visibility: ShareVisibility = None) -> str:
        """Create a new shared item"""
        try:
            if visibility is None:
                visibility = self.share_settings["default_visibility"]
            
            share_id = str(uuid.uuid4())
            
            shared_item = SharedItem(
                id=share_id,
                user_id=user_id,
                share_type=share_type,
                title=title,
                content=content,
                visibility=visibility,
                created_at=datetime.datetime.now(),
                comments=[]
            )
            
            self.shared_items.append(shared_item)
            
            logging.info(f"Created share: {share_id} ({share_type.value})")
            return share_id
            
        except Exception as e:
            logging.error(f"Error creating share: {str(e)}")
            return None
    
    def get_shared_items(self, user_id: str = None, share_type: ShareType = None, 
                        limit: int = 20) -> List[Dict]:
        """Get shared items with optional filtering"""
        try:
            filtered_items = self.shared_items
            
            # Filter by user
            if user_id:
                filtered_items = [item for item in filtered_items if item.user_id == user_id]
            
            # Filter by type
            if share_type:
                filtered_items = [item for item in filtered_items if item.share_type == share_type]
            
            # Sort by creation date (newest first)
            filtered_items.sort(key=lambda x: x.created_at, reverse=True)
            
            # Convert to dict format
            result = []
            for item in filtered_items[:limit]:
                result.append({
                    "id": item.id,
                    "user_id": item.user_id,
                    "type": item.share_type.value,
                    "title": item.title,
                    "content": item.content,
                    "visibility": item.visibility.value,
                    "created_at": item.created_at.isoformat(),
                    "views": item.views,
                    "likes": item.likes,
                    "comment_count": len(item.comments or [])
                })
            
            return result
            
        except Exception as e:
            logging.error(f"Error getting shared items: {str(e)}")
            return []
    
    def share_achievement(self, user_id: str, achievement: Dict, 
                         visibility: ShareVisibility = None) -> str:
        """Share an achievement"""
        title = f"🎉 Achievement Unlocked: {achievement.get('title', 'New Achievement')}"
        
        content = {
            "achievement_title": achievement.get("title", ""),
            "achievement_date": achievement.get("date", ""),
            "category": achievement.get("category", "general"),
            "description": f"Completed goal: {achievement.get('title', 'Unknown goal')}",
            "celebration_note": "Another step forward in my personal growth journey!"
        }
        
        return self.create_share(user_id, ShareType.ACHIEVEMENT, title, content, visibility)
    
    def share_milestone(self, user_id: str, milestone: Dict, 
                       visibility: ShareVisibility = None) -> str:
        """Share a milestone"""
        title = f"🎯 Milestone Reached: {milestone.get('title', 'New Milestone')}"
        
        content = {
            "milestone_title": milestone.get("title", ""),
            "milestone_date": milestone.get("date", ""),
            "category": milestone.get("category", "personal"),
            "importance": milestone.get("importance", "medium"),
            "description": milestone.get("description", ""),
            "reflection": milestone.get("reflection", "")
        }
        
        return self.create_share(user_id, ShareType.MILESTONE, title, content, visibility)
    
    def share_progress_report(self, user_id: str, report: Dict, 
                             visibility: ShareVisibility = None) -> str:
        """Share a progress report"""
        title = f"📊 My Progress Update - {datetime.date.today().strftime('%B %Y')}"
        
        # Summarize key metrics for sharing
        content = {
            "summary": {
                "goals_completed": report.get("summary", {}).get("goals_completed_this_month", 0),
                "active_goals": report.get("summary", {}).get("active_goals", 0),
                "habits_tracked": report.get("summary", {}).get("active_habits", 0),
                "mood_trend": report.get("mood_analysis", {}).get("dominant_emotion", "stable")
            },
            "highlights": self._extract_report_highlights(report),
            "period": report.get("period", "recent"),
            "generated_date": report.get("generated_date", datetime.date.today().isoformat())
        }
        
        return self.create_share(user_id, ShareType.PROGRESS_REPORT, title, content, visibility)
    
    def share_insight(self, user_id: str, insight: Dict, 
                     visibility: ShareVisibility = None) -> str:
        """Share a personal insight or reflection"""
        title = f"💡 Personal Insight: {insight.get('title', 'New Realization')}"
        
        content = {
            "insight_text": insight.get("text", ""),
            "category": insight.get("category", "general"),
            "tags": insight.get("tags", []),
            "date": insight.get("date", datetime.date.today().isoformat()),
            "mood_context": insight.get("mood", "neutral")
        }
        
        return self.create_share(user_id, ShareType.INSIGHT, title, content, visibility)
    
    def add_comment(self, share_id: str, user_id: str, comment_text: str) -> bool:
        """Add a comment to a shared item"""
        try:
            for item in self.shared_items:
                if item.id == share_id:
                    if not self.share_settings["allow_comments"]:
                        return False
                    
                    comment = {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "text": comment_text,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "likes": 0
                    }
                    
                    if item.comments is None:
                        item.comments = []
                    
                    item.comments.append(comment)
                    logging.info(f"Added comment to share {share_id}")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error adding comment: {str(e)}")
            return False
    
    def like_share(self, share_id: str, user_id: str) -> bool:
        """Like/unlike a shared item"""
        try:
            for item in self.shared_items:
                if item.id == share_id:
                    item.likes += 1
                    logging.info(f"User {user_id} liked share {share_id}")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error liking share: {str(e)}")
            return False
    
    def view_share(self, share_id: str) -> Dict:
        """View a shared item (increments view count)"""
        try:
            for item in self.shared_items:
                if item.id == share_id:
                    item.views += 1
                    
                    return {
                        "id": item.id,
                        "user_id": item.user_id,
                        "type": item.share_type.value,
                        "title": item.title,
                        "content": item.content,
                        "visibility": item.visibility.value,
                        "created_at": item.created_at.isoformat(),
                        "views": item.views,
                        "likes": item.likes,
                        "comments": item.comments or []
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Error viewing share: {str(e)}")
            return None
    
    def connect_users(self, user_id1: str, user_id2: str) -> bool:
        """Connect two users for sharing"""
        try:
            if user_id1 not in self.user_connections:
                self.user_connections[user_id1] = []
            if user_id2 not in self.user_connections:
                self.user_connections[user_id2] = []
            
            if user_id2 not in self.user_connections[user_id1]:
                self.user_connections[user_id1].append(user_id2)
            
            if user_id1 not in self.user_connections[user_id2]:
                self.user_connections[user_id2].append(user_id1)
            
            logging.info(f"Connected users {user_id1} and {user_id2}")
            return True
            
        except Exception as e:
            logging.error(f"Error connecting users: {str(e)}")
            return False
    
    def get_user_connections(self, user_id: str) -> List[str]:
        """Get list of connected users"""
        return self.user_connections.get(user_id, [])
    
    def get_feed(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get personalized feed of shared items"""
        try:
            # Get items from connected users and public items
            connections = self.get_user_connections(user_id)
            
            feed_items = []
            for item in self.shared_items:
                include_item = False
                
                # Include own items
                if item.user_id == user_id:
                    include_item = True
                # Include public items
                elif item.visibility == ShareVisibility.PUBLIC:
                    include_item = True
                # Include friends' items if connected
                elif (item.visibility == ShareVisibility.FRIENDS and 
                      item.user_id in connections):
                    include_item = True
                
                if include_item:
                    feed_items.append({
                        "id": item.id,
                        "user_id": item.user_id,
                        "type": item.share_type.value,
                        "title": item.title,
                        "content": item.content,
                        "created_at": item.created_at.isoformat(),
                        "views": item.views,
                        "likes": item.likes,
                        "comment_count": len(item.comments or [])
                    })
            
            # Sort by engagement score (likes + comments + recency)
            feed_items.sort(key=lambda x: self._calculate_engagement_score(x), reverse=True)
            
            return feed_items[:limit]
            
        except Exception as e:
            logging.error(f"Error generating feed: {str(e)}")
            return []
    
    def _calculate_engagement_score(self, item: Dict) -> float:
        """Calculate engagement score for feed ranking"""
        try:
            created_at = datetime.datetime.fromisoformat(item["created_at"])
            hours_old = (datetime.datetime.now() - created_at).total_seconds() / 3600
            
            # Recency factor (newer items get higher score)
            recency_score = max(0, 100 - hours_old / 24)  # Decays over days
            
            # Engagement factor
            engagement_score = item["likes"] * 3 + item["comment_count"] * 5
            
            return recency_score + engagement_score
            
        except:
            return 0
    
    def _extract_report_highlights(self, report: Dict) -> List[str]:
        """Extract key highlights from a progress report"""
        highlights = []
        
        try:
            # Goal highlights
            if report.get("summary", {}).get("goals_completed_this_month", 0) > 0:
                count = report["summary"]["goals_completed_this_month"]
                highlights.append(f"Completed {count} goal{'s' if count > 1 else ''} this month")
            
            # Mood highlights
            mood_analysis = report.get("mood_analysis", {})
            dominant_emotion = mood_analysis.get("dominant_emotion")
            if dominant_emotion and dominant_emotion not in ["neutral"]:
                highlights.append(f"Mood trend: {dominant_emotion}")
            
            # Habit highlights
            habit_performance = report.get("habit_performance", [])
            if habit_performance:
                best_habit = max(habit_performance, key=lambda h: h.get("current_streak", 0))
                if best_habit.get("current_streak", 0) > 7:
                    highlights.append(f"{best_habit['name']}: {best_habit['current_streak']}-day streak")
            
            # Achievements
            if report.get("summary", {}).get("achievements", 0) > 0:
                highlights.append(f"Earned new achievements")
            
        except Exception as e:
            logging.error(f"Error extracting highlights: {str(e)}")
        
        return highlights[:3]  # Top 3 highlights
    
    def update_share_settings(self, settings: Dict):
        """Update sharing settings"""
        self.share_settings.update(settings)
        logging.info("Share settings updated")
    
    def get_share_settings(self) -> Dict:
        """Get current sharing settings"""
        return self.share_settings.copy()
    
    def delete_share(self, share_id: str, user_id: str) -> bool:
        """Delete a shared item (only by owner)"""
        try:
            for i, item in enumerate(self.shared_items):
                if item.id == share_id and item.user_id == user_id:
                    del self.shared_items[i]
                    logging.info(f"Deleted share {share_id}")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error deleting share: {str(e)}")
            return False
    
    def get_trending_items(self, limit: int = 10) -> List[Dict]:
        """Get trending shared items based on recent engagement"""
        try:
            # Calculate trending score for last 7 days
            week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
            
            trending_items = []
            for item in self.shared_items:
                if item.created_at >= week_ago and item.visibility == ShareVisibility.PUBLIC:
                    # Trending score based on likes, comments, and views
                    trending_score = (item.likes * 3 + 
                                    len(item.comments or []) * 5 + 
                                    item.views * 0.5)
                    
                    if trending_score > 0:
                        trending_items.append({
                            "id": item.id,
                            "user_id": item.user_id,
                            "type": item.share_type.value,
                            "title": item.title,
                            "content": item.content,
                            "created_at": item.created_at.isoformat(),
                            "trending_score": trending_score,
                            "engagement": {
                                "likes": item.likes,
                                "comments": len(item.comments or []),
                                "views": item.views
                            }
                        })
            
            # Sort by trending score
            trending_items.sort(key=lambda x: x["trending_score"], reverse=True)
            
            return trending_items[:limit]
            
        except Exception as e:
            logging.error(f"Error getting trending items: {str(e)}")
            return []

# Global collaboration tools instance
collaboration_tools = CollaborationTools()
