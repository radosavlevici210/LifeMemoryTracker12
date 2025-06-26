"""
Gamification Engine for Enhanced User Engagement
"""
import json
import datetime
import logging
import math
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class AchievementType(Enum):
    STREAK = "streak"
    MILESTONE = "milestone"
    CONSISTENCY = "consistency"
    BREAKTHROUGH = "breakthrough"
    SOCIAL = "social"
    WELLNESS = "wellness"

class BadgeRarity(Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

@dataclass
class Achievement:
    id: str
    title: str
    description: str
    badge_icon: str
    rarity: BadgeRarity
    points: int
    unlock_condition: str
    achieved_date: Optional[datetime.datetime] = None

@dataclass
class UserStats:
    level: int
    total_points: int
    streak_days: int
    goals_completed: int
    habits_mastered: int
    wellness_score: float
    achievement_count: int

class GamificationEngine:
    def __init__(self):
        self.achievements = self._initialize_achievements()
        self.level_thresholds = [0, 100, 250, 500, 1000, 2000, 4000, 8000, 15000, 30000, 50000]
        self.daily_points = {}
        
    def _initialize_achievements(self) -> List[Achievement]:
        """Initialize all available achievements"""
        return [
            # Streak Achievements
            Achievement(
                id="first_week",
                title="First Week Warrior",
                description="Used the app for 7 consecutive days",
                badge_icon="🔥",
                rarity=BadgeRarity.COMMON,
                points=50,
                unlock_condition="streak_days >= 7"
            ),
            Achievement(
                id="month_master",
                title="Month Master",
                description="Maintained a 30-day streak",
                badge_icon="🏆",
                rarity=BadgeRarity.RARE,
                points=200,
                unlock_condition="streak_days >= 30"
            ),
            Achievement(
                id="century_champion",
                title="Century Champion",
                description="Achieved 100-day streak",
                badge_icon="👑",
                rarity=BadgeRarity.LEGENDARY,
                points=1000,
                unlock_condition="streak_days >= 100"
            ),
            
            # Goal Achievements
            Achievement(
                id="first_goal",
                title="Goal Getter",
                description="Completed your first goal",
                badge_icon="🎯",
                rarity=BadgeRarity.COMMON,
                points=25,
                unlock_condition="goals_completed >= 1"
            ),
            Achievement(
                id="goal_achiever",
                title="Goal Achiever",
                description="Completed 10 goals",
                badge_icon="⭐",
                rarity=BadgeRarity.RARE,
                points=150,
                unlock_condition="goals_completed >= 10"
            ),
            Achievement(
                id="goal_master",
                title="Goal Master",
                description="Completed 50 goals",
                badge_icon="🌟",
                rarity=BadgeRarity.EPIC,
                points=500,
                unlock_condition="goals_completed >= 50"
            ),
            
            # Habit Achievements
            Achievement(
                id="habit_starter",
                title="Habit Starter",
                description="Maintained a habit for 7 days",
                badge_icon="🌱",
                rarity=BadgeRarity.COMMON,
                points=30,
                unlock_condition="max_habit_streak >= 7"
            ),
            Achievement(
                id="habit_builder",
                title="Habit Builder",
                description="Maintained a habit for 30 days",
                badge_icon="🌿",
                rarity=BadgeRarity.RARE,
                points=100,
                unlock_condition="max_habit_streak >= 30"
            ),
            Achievement(
                id="habit_master",
                title="Habit Master",
                description="Mastered 5 different habits",
                badge_icon="🎨",
                rarity=BadgeRarity.EPIC,
                points=300,
                unlock_condition="habits_mastered >= 5"
            ),
            
            # Wellness Achievements
            Achievement(
                id="mood_tracker",
                title="Mood Tracker",
                description="Tracked mood for 14 consecutive days",
                badge_icon="😊",
                rarity=BadgeRarity.COMMON,
                points=40,
                unlock_condition="mood_tracking_streak >= 14"
            ),
            Achievement(
                id="wellness_warrior",
                title="Wellness Warrior",
                description="Maintained high wellness score for a month",
                badge_icon="💪",
                rarity=BadgeRarity.RARE,
                points=200,
                unlock_condition="wellness_score >= 8.0 for 30 days"
            ),
            
            # Consistency Achievements
            Achievement(
                id="consistent_performer",
                title="Consistent Performer",
                description="Completed daily activities for 21 days",
                badge_icon="📊",
                rarity=BadgeRarity.RARE,
                points=120,
                unlock_condition="daily_completion_streak >= 21"
            ),
            Achievement(
                id="perfectionist",
                title="Perfectionist",
                description="Achieved 100% completion rate for a week",
                badge_icon="💎",
                rarity=BadgeRarity.EPIC,
                points=250,
                unlock_condition="perfect_week"
            ),
            
            # Social Achievements
            Achievement(
                id="sharer",
                title="Sharer",
                description="Shared your first achievement",
                badge_icon="📤",
                rarity=BadgeRarity.COMMON,
                points=20,
                unlock_condition="shares_count >= 1"
            ),
            Achievement(
                id="inspiration",
                title="Inspiration",
                description="Your shared content received 10 likes",
                badge_icon="❤️",
                rarity=BadgeRarity.RARE,
                points=100,
                unlock_condition="total_likes >= 10"
            )
        ]
    
    def calculate_user_stats(self, memory: Dict) -> UserStats:
        """Calculate current user statistics"""
        # Extract data from memory
        goals = memory.get("goals", [])
        habits = memory.get("habits", [])
        mood_history = memory.get("mood_history", [])
        life_events = memory.get("life_events", [])
        achievements = memory.get("achievements", [])
        
        # Calculate basic stats
        goals_completed = sum(1 for goal in goals if goal.get("status") == "completed")
        habits_mastered = sum(1 for habit in habits if habit.get("current_streak", 0) >= 30)
        
        # Calculate streak days
        streak_days = self._calculate_streak_days(life_events)
        
        # Calculate wellness score
        wellness_score = self._calculate_wellness_score(mood_history, habits, goals)
        
        # Calculate total points
        total_points = self._calculate_total_points(memory)
        
        # Calculate level
        level = self._calculate_level(total_points)
        
        return UserStats(
            level=level,
            total_points=total_points,
            streak_days=streak_days,
            goals_completed=goals_completed,
            habits_mastered=habits_mastered,
            wellness_score=wellness_score,
            achievement_count=len(achievements)
        )
    
    def _calculate_streak_days(self, life_events: List[Dict]) -> int:
        """Calculate current streak of consecutive active days"""
        if not life_events:
            return 0
        
        # Get unique dates from life events
        valid_dates = [event.get("date") for event in life_events if event.get("date") is not None]
        dates = sorted(list(set(valid_dates))) if valid_dates else []
        
        if not dates:
            return 0
        
        # Calculate streak from most recent date backwards
        streak = 1
        current_date = datetime.datetime.fromisoformat(dates[-1])
        
        for i in range(len(dates) - 2, -1, -1):
            prev_date = datetime.datetime.fromisoformat(dates[i])
            if (current_date - prev_date).days == 1:
                streak += 1
                current_date = prev_date
            else:
                break
        
        return streak
    
    def _calculate_wellness_score(self, mood_history: List[Dict], habits: List[Dict], goals: List[Dict]) -> float:
        """Calculate overall wellness score (0-10)"""
        scores = []
        
        # Mood component
        if mood_history:
            recent_moods = [m.get("mood", 5) for m in mood_history[-7:]]
            mood_score = sum(recent_moods) / len(recent_moods)
            scores.append(mood_score)
        
        # Habit consistency component
        if habits:
            habit_scores = []
            for habit in habits:
                target_freq = habit.get("frequency", 7)
                current_streak = habit.get("current_streak", 0)
                consistency = min(current_streak / target_freq, 1.0) * 10
                habit_scores.append(consistency)
            scores.append(sum(habit_scores) / len(habit_scores))
        
        # Goal progress component
        if goals:
            active_goals = [g for g in goals if g.get("status") == "active"]
            if active_goals:
                progress_scores = [g.get("progress", 0) / 10 for g in active_goals]
                scores.append(sum(progress_scores) / len(progress_scores))
        
        return sum(scores) / len(scores) if scores else 5.0
    
    def _calculate_total_points(self, memory: Dict) -> int:
        """Calculate total points earned"""
        achievements = memory.get("achievements", [])
        
        # Points from achievements
        achievement_points = sum(self._get_achievement_points(ach.get("id", "")) for ach in achievements)
        
        # Daily activity points
        life_events = memory.get("life_events", [])
        daily_points = len(life_events) * 5  # 5 points per interaction
        
        # Goal completion points
        goals = memory.get("goals", [])
        goal_points = sum(25 for goal in goals if goal.get("status") == "completed")
        
        # Habit milestone points
        habits = memory.get("habits", [])
        habit_points = sum(min(habit.get("current_streak", 0), 30) for habit in habits)
        
        return achievement_points + daily_points + goal_points + habit_points
    
    def _get_achievement_points(self, achievement_id: str) -> int:
        """Get points for a specific achievement"""
        for achievement in self.achievements:
            if achievement.id == achievement_id:
                return achievement.points
        return 0
    
    def _calculate_level(self, total_points: int) -> int:
        """Calculate level based on total points"""
        for level, threshold in enumerate(self.level_thresholds):
            if total_points < threshold:
                return max(1, level)
        return len(self.level_thresholds)
    
    def check_new_achievements(self, memory: Dict) -> List[Achievement]:
        """Check for newly unlocked achievements"""
        current_achievements = {ach.get("id") for ach in memory.get("achievements", [])}
        new_achievements = []
        
        stats = self.calculate_user_stats(memory)
        
        for achievement in self.achievements:
            if achievement.id not in current_achievements:
                if self._check_achievement_condition(achievement, stats, memory):
                    achievement.achieved_date = datetime.datetime.now()
                    new_achievements.append(achievement)
        
        return new_achievements
    
    def _check_achievement_condition(self, achievement: Achievement, stats: UserStats, memory: Dict) -> bool:
        """Check if achievement condition is met"""
        condition = achievement.unlock_condition
        
        # Basic stat conditions
        if "streak_days >=" in condition:
            threshold = int(condition.split(">=")[1].strip())
            return stats.streak_days >= threshold
        
        if "goals_completed >=" in condition:
            threshold = int(condition.split(">=")[1].strip())
            return stats.goals_completed >= threshold
        
        if "habits_mastered >=" in condition:
            threshold = int(condition.split(">=")[1].strip())
            return stats.habits_mastered >= threshold
        
        # Custom conditions
        if condition == "max_habit_streak >= 7":
            habits = memory.get("habits", [])
            max_streak = max((h.get("current_streak", 0) for h in habits), default=0)
            return max_streak >= 7
        
        if condition == "max_habit_streak >= 30":
            habits = memory.get("habits", [])
            max_streak = max((h.get("current_streak", 0) for h in habits), default=0)
            return max_streak >= 30
        
        if condition == "mood_tracking_streak >= 14":
            mood_history = memory.get("mood_history", [])
            return len(mood_history) >= 14
        
        if condition == "wellness_score >= 8.0 for 30 days":
            return stats.wellness_score >= 8.0  # Simplified check
        
        if condition == "perfect_week":
            # Check if user completed all planned activities for a week
            goals = memory.get("goals", [])
            habits = memory.get("habits", [])
            return len(goals) > 0 and len(habits) > 0  # Simplified check
        
        return False
    
    def get_progress_to_next_level(self, total_points: int) -> Dict:
        """Get progress information for next level"""
        current_level = self._calculate_level(total_points)
        
        if current_level >= len(self.level_thresholds):
            return {
                "current_level": current_level,
                "next_level": current_level,
                "points_needed": 0,
                "progress_percentage": 100,
                "is_max_level": True
            }
        
        current_threshold = self.level_thresholds[current_level - 1] if current_level > 1 else 0
        next_threshold = self.level_thresholds[current_level]
        
        points_in_level = total_points - current_threshold
        points_needed_for_level = next_threshold - current_threshold
        progress_percentage = (points_in_level / points_needed_for_level) * 100
        
        return {
            "current_level": current_level,
            "next_level": current_level + 1,
            "points_needed": next_threshold - total_points,
            "progress_percentage": round(progress_percentage, 1),
            "is_max_level": False
        }
    
    def generate_daily_challenges(self, memory: Dict, stats: UserStats) -> List[Dict]:
        """Generate personalized daily challenges"""
        challenges = []
        
        # Streak maintenance challenge
        if stats.streak_days > 0:
            challenges.append({
                "id": "maintain_streak",
                "title": f"Maintain Your {stats.streak_days}-Day Streak",
                "description": "Keep your momentum going with any activity today",
                "points": 10 + min(stats.streak_days, 50),
                "difficulty": "easy",
                "category": "consistency"
            })
        
        # Goal progress challenge
        goals = memory.get("goals", [])
        active_goals = [g for g in goals if g.get("status") == "active"]
        if active_goals:
            challenges.append({
                "id": "goal_progress",
                "title": "Advance a Goal",
                "description": "Make meaningful progress on one of your active goals",
                "points": 25,
                "difficulty": "medium",
                "category": "goals"
            })
        
        # Habit challenge
        habits = memory.get("habits", [])
        if habits:
            challenges.append({
                "id": "habit_completion",
                "title": "Complete Your Habits",
                "description": "Complete all your scheduled habits for today",
                "points": 15 * len(habits),
                "difficulty": "medium",
                "category": "habits"
            })
        
        # Mood tracking challenge
        mood_history = memory.get("mood_history", [])
        today = datetime.date.today().isoformat()
        mood_tracked_today = any(m.get("date") == today for m in mood_history)
        
        if not mood_tracked_today:
            challenges.append({
                "id": "mood_tracking",
                "title": "Track Your Mood",
                "description": "Take a moment to check in with how you're feeling",
                "points": 10,
                "difficulty": "easy",
                "category": "wellness"
            })
        
        # Reflection challenge
        challenges.append({
            "id": "daily_reflection",
            "title": "Reflect on Your Day",
            "description": "Share one insight or lesson from today",
            "points": 15,
            "difficulty": "easy",
            "category": "growth"
        })
        
        return challenges[:4]  # Return top 4 challenges
    
    def get_leaderboard_data(self, memory: Dict) -> Dict:
        """Generate leaderboard and comparison data"""
        stats = self.calculate_user_stats(memory)
        
        # Simulated leaderboard positions (in real app, this would be from database)
        user_percentile = min(95, max(5, (stats.total_points / 1000) * 10))
        
        return {
            "user_rank": f"Top {100 - int(user_percentile)}%",
            "total_points": stats.total_points,
            "level": stats.level,
            "achievements_count": stats.achievement_count,
            "categories": {
                "Consistency": f"Top {100 - min(95, max(5, stats.streak_days))}%",
                "Goal Achievement": f"Top {100 - min(95, max(5, stats.goals_completed * 10))}%",
                "Wellness": f"Top {100 - min(95, max(5, int(stats.wellness_score * 10)))}%"
            },
            "badges": {
                "common": sum(1 for ach in self.achievements if ach.rarity == BadgeRarity.COMMON),
                "rare": sum(1 for ach in self.achievements if ach.rarity == BadgeRarity.RARE),
                "epic": sum(1 for ach in self.achievements if ach.rarity == BadgeRarity.EPIC),
                "legendary": sum(1 for ach in self.achievements if ach.rarity == BadgeRarity.LEGENDARY)
            }
        }
    
    def get_gamification_dashboard(self, memory: Dict) -> Dict:
        """Get complete gamification dashboard data"""
        stats = self.calculate_user_stats(memory)
        new_achievements = self.check_new_achievements(memory)
        level_progress = self.get_progress_to_next_level(stats.total_points)
        daily_challenges = self.generate_daily_challenges(memory, stats)
        leaderboard = self.get_leaderboard_data(memory)
        
        return {
            "user_stats": {
                "level": stats.level,
                "total_points": stats.total_points,
                "streak_days": stats.streak_days,
                "goals_completed": stats.goals_completed,
                "habits_mastered": stats.habits_mastered,
                "wellness_score": round(stats.wellness_score, 1),
                "achievement_count": stats.achievement_count
            },
            "level_progress": level_progress,
            "new_achievements": [
                {
                    "id": ach.id,
                    "title": ach.title,
                    "description": ach.description,
                    "badge_icon": ach.badge_icon,
                    "rarity": ach.rarity.value,
                    "points": ach.points
                }
                for ach in new_achievements
            ],
            "daily_challenges": daily_challenges,
            "leaderboard": leaderboard,
            "recent_achievements": memory.get("achievements", [])[-5:],
            "motivation_quote": self._get_motivation_quote(stats)
        }
    
    def _get_motivation_quote(self, stats: UserStats) -> str:
        """Get motivational quote based on user stats"""
        quotes = [
            "Every expert was once a beginner. Keep going!",
            "Progress, not perfection, is the goal.",
            "Your only limit is your mindset.",
            "Small steps lead to big changes.",
            "Consistency beats intensity every time.",
            "You're capable of amazing things.",
            "Growth begins at the end of your comfort zone.",
            "Success is the sum of small efforts repeated daily."
        ]
        
        # Select quote based on level
        quote_index = (stats.level - 1) % len(quotes)
        return quotes[quote_index]