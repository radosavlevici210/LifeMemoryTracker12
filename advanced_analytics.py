# ============================================
# Project: LifeMemoryTracker12
# Author: Ervin Remus Radosavlevici
# Copyright: © 2025 Ervin Remus Radosavlevici
# All rights reserved. Protected under digital trace monitoring.
# Unauthorized usage will trigger automated reports.
# ============================================

import datetime
import socket
import platform
import getpass

def log_access():
    log_info = {
        "timestamp": datetime.datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "user": getpass.getuser()
    }
    with open("access_log.txt", "a") as f:
        f.write(str(log_info) + "\n")

log_access()

"""
Advanced Analytics and Reporting System for AI Life Coach
"""
import json
import datetime
import numpy as np
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import logging

@dataclass
class AnalyticsMetric:
    name: str
    value: float
    trend: str  # "up", "down", "stable"
    change_percent: float
    timeframe: str

class AdvancedAnalytics:
    def __init__(self):
        self.analytics_history = []
    
    def generate_comprehensive_report(self, memory: Dict) -> Dict:
        """Generate comprehensive analytics report"""
        try:
            report = {
                "generated_at": datetime.datetime.now().isoformat(),
                "overview": self._generate_overview(memory),
                "engagement_metrics": self._analyze_engagement(memory),
                "wellbeing_analytics": self._analyze_wellbeing(memory),
                "productivity_metrics": self._analyze_productivity(memory),
                "habit_analytics": self._analyze_habits(memory),
                "goal_performance": self._analyze_goals(memory),
                "behavioral_patterns": self._analyze_patterns(memory),
                "predictive_insights": self._generate_predictions(memory),
                "recommendations": self._generate_recommendations(memory)
            }
            
            # Store analytics history
            self.analytics_history.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "metrics": report
            })
            
            # Keep only last 30 reports
            self.analytics_history = self.analytics_history[-30:]
            
            return report
            
        except Exception as e:
            logging.error(f"Analytics generation failed: {str(e)}")
            return {"error": str(e)}
    
    def _generate_overview(self, memory: Dict) -> Dict:
        """Generate overview metrics"""
        now = datetime.datetime.now()
        
        return {
            "total_conversations": len(memory.get("life_events", [])),
            "active_goals": len([g for g in memory.get("goals", []) if g.get("status") == "active"]),
            "completed_goals": len([g for g in memory.get("goals", []) if g.get("status") == "completed"]),
            "active_habits": len([h for h in memory.get("habits", []) if h.get("status") == "active"]),
            "total_achievements": len(memory.get("achievements", [])),
            "mood_entries": len(memory.get("mood_history", [])),
            "reflections": len(memory.get("reflections", [])),
            "milestones": len(memory.get("milestones", [])),
            "user_since": self._calculate_user_since(memory),
            "streak_days": self._calculate_usage_streak(memory)
        }
    
    def _analyze_engagement(self, memory: Dict) -> Dict:
        """Analyze user engagement patterns"""
        life_events = memory.get("life_events", [])
        
        if not life_events:
            return {"daily_average": 0, "weekly_pattern": {}, "engagement_trend": "stable"}
        
        # Calculate daily engagement
        daily_counts = defaultdict(int)
        for event in life_events[-30:]:  # Last 30 days
            try:
                date = datetime.datetime.fromisoformat(event.get("timestamp", event.get("date"))).date()
                daily_counts[date] += 1
            except:
                continue
        
        # Weekly pattern analysis
        weekly_pattern = defaultdict(int)
        for event in life_events[-100:]:  # Last 100 events
            try:
                dt = datetime.datetime.fromisoformat(event.get("timestamp", event.get("date")))
                day_name = dt.strftime("%A")
                weekly_pattern[day_name] += 1
            except:
                continue
        
        return {
            "daily_average": statistics.mean(daily_counts.values()) if daily_counts else 0,
            "weekly_pattern": dict(weekly_pattern),
            "engagement_trend": self._calculate_trend(list(daily_counts.values())),
            "most_active_day": max(weekly_pattern.keys(), key=weekly_pattern.get) if weekly_pattern else "None",
            "session_frequency": len(daily_counts) / 30 if daily_counts else 0
        }
    
    def _analyze_wellbeing(self, memory: Dict) -> Dict:
        """Analyze wellbeing and mood patterns"""
        mood_history = memory.get("mood_history", [])
        
        if not mood_history:
            return {"average_mood": 5.0, "mood_stability": "unknown", "emotional_trend": "stable"}
        
        # Mood analysis
        recent_moods = mood_history[-30:]  # Last 30 entries
        intensities = [m.get("intensity", 5) for m in recent_moods]
        emotions = [m.get("emotion", "neutral") for m in recent_moods]
        
        # Emotional distribution
        emotion_counts = defaultdict(int)
        for emotion in emotions:
            emotion_counts[emotion] += 1
        
        # Mood stability (lower variance = more stable)
        mood_variance = statistics.variance(intensities) if len(intensities) > 1 else 0
        stability_score = max(0, 10 - mood_variance)
        
        return {
            "average_mood": statistics.mean(intensities),
            "mood_stability": stability_score,
            "emotional_distribution": dict(emotion_counts),
            "dominant_emotion": max(emotion_counts.keys(), key=emotion_counts.get) if emotion_counts else "neutral",
            "emotional_trend": self._calculate_trend(intensities),
            "mood_range": max(intensities) - min(intensities) if intensities else 0,
            "positive_mood_ratio": len([i for i in intensities if i >= 7]) / len(intensities) if intensities else 0
        }
    
    def _analyze_productivity(self, memory: Dict) -> Dict:
        """Analyze productivity metrics"""
        goals = memory.get("goals", [])
        achievements = memory.get("achievements", [])
        action_items = memory.get("action_items", [])
        
        # Goal completion rate
        total_goals = len(goals)
        completed_goals = len([g for g in goals if g.get("status") == "completed"])
        completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
        
        # Monthly achievements
        now = datetime.datetime.now()
        month_ago = now - datetime.timedelta(days=30)
        recent_achievements = [
            a for a in achievements
            if datetime.datetime.fromisoformat(a.get("date", now.isoformat())) >= month_ago
        ]
        
        # Action item completion
        completed_actions = len([a for a in action_items if a.get("status") == "completed"])
        total_actions = len(action_items)
        action_completion_rate = (completed_actions / total_actions * 100) if total_actions > 0 else 0
        
        return {
            "goal_completion_rate": completion_rate,
            "monthly_achievements": len(recent_achievements),
            "action_completion_rate": action_completion_rate,
            "productivity_score": (completion_rate + action_completion_rate) / 2,
            "average_goal_progress": self._calculate_average_goal_progress(goals),
            "goal_categories": self._analyze_goal_categories(goals)
        }
    
    def _analyze_habits(self, memory: Dict) -> Dict:
        """Analyze habit tracking performance"""
        habits = memory.get("habits", [])
        
        if not habits:
            return {"average_streak": 0, "habit_consistency": 0, "best_habit": "None"}
        
        active_habits = [h for h in habits if h.get("status") == "active"]
        
        # Calculate metrics
        streaks = [h.get("current_streak", 0) for h in active_habits]
        longest_streaks = [h.get("longest_streak", 0) for h in habits]
        
        # Habit consistency (based on check-ins vs days since creation)
        consistency_scores = []
        for habit in active_habits:
            created_date = datetime.datetime.fromisoformat(habit.get("created_date", datetime.datetime.now().isoformat()))
            days_since_created = (datetime.datetime.now() - created_date).days
            check_ins = len(habit.get("check_ins", []))
            
            if days_since_created > 0:
                consistency = min(100, (check_ins / days_since_created) * 100)
                consistency_scores.append(consistency)
        
        return {
            "total_habits": len(habits),
            "active_habits": len(active_habits),
            "average_streak": statistics.mean(streaks) if streaks else 0,
            "best_current_streak": max(streaks) if streaks else 0,
            "best_all_time_streak": max(longest_streaks) if longest_streaks else 0,
            "habit_consistency": statistics.mean(consistency_scores) if consistency_scores else 0,
            "most_consistent_habit": self._find_most_consistent_habit(active_habits),
            "habit_categories": self._analyze_habit_categories(habits)
        }
    
    def _analyze_goals(self, memory: Dict) -> Dict:
        """Detailed goal analysis"""
        goals = memory.get("goals", [])
        
        if not goals:
            return {"total": 0, "completion_time": 0, "success_factors": []}
        
        # Completion time analysis
        completed_goals = [g for g in goals if g.get("status") == "completed"]
        completion_times = []
        
        for goal in completed_goals:
            if goal.get("created_date") and goal.get("completed_date"):
                created = datetime.datetime.fromisoformat(goal["created_date"])
                completed = datetime.datetime.fromisoformat(goal["completed_date"])
                days_to_complete = (completed - created).days
                completion_times.append(days_to_complete)
        
        # Category analysis
        categories = defaultdict(int)
        for goal in goals:
            category = goal.get("category", "general")
            categories[category] += 1
        
        return {
            "total_goals": len(goals),
            "completed_goals": len(completed_goals),
            "active_goals": len([g for g in goals if g.get("status") == "active"]),
            "average_completion_time": statistics.mean(completion_times) if completion_times else 0,
            "fastest_completion": min(completion_times) if completion_times else 0,
            "goal_categories": dict(categories),
            "success_rate_by_category": self._calculate_success_by_category(goals),
            "goal_difficulty_analysis": self._analyze_goal_difficulty(goals)
        }
    
    def _analyze_patterns(self, memory: Dict) -> Dict:
        """Analyze behavioral patterns"""
        life_events = memory.get("life_events", [])
        mood_history = memory.get("mood_history", [])
        
        patterns = {
            "conversation_timing": self._analyze_conversation_timing(life_events),
            "mood_triggers": self._analyze_mood_triggers(mood_history, life_events),
            "activity_clusters": self._find_activity_clusters(life_events),
            "seasonal_patterns": self._analyze_seasonal_patterns(life_events, mood_history),
            "stress_indicators": self._identify_stress_patterns(mood_history, life_events)
        }
        
        return patterns
    
    def _generate_predictions(self, memory: Dict) -> Dict:
        """Generate predictive insights"""
        # Simple prediction algorithms based on historical data
        
        mood_history = memory.get("mood_history", [])
        goals = memory.get("goals", [])
        habits = memory.get("habits", [])
        
        predictions = {
            "goal_completion_likelihood": self._predict_goal_completion(goals),
            "mood_forecast": self._predict_mood_trend(mood_history),
            "habit_sustainability": self._predict_habit_sustainability(habits),
            "engagement_forecast": self._predict_engagement(memory.get("life_events", [])),
            "achievement_timeline": self._predict_next_achievement(memory)
        }
        
        return predictions
    
    def _generate_recommendations(self, memory: Dict) -> List[Dict]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Goal-based recommendations
        active_goals = [g for g in memory.get("goals", []) if g.get("status") == "active"]
        if len(active_goals) > 5:
            recommendations.append({
                "type": "goal_management",
                "priority": "medium",
                "title": "Focus Your Goals",
                "description": "You have many active goals. Consider focusing on 3-5 priority goals for better success.",
                "action": "Review and prioritize your goals"
            })
        
        # Habit recommendations
        habits = memory.get("habits", [])
        habit_consistency = self._analyze_habits(memory).get("habit_consistency", 0)
        if habit_consistency < 50:
            recommendations.append({
                "type": "habit_improvement",
                "priority": "high",
                "title": "Improve Habit Consistency",
                "description": "Your habit consistency is below average. Try starting with smaller, easier habits.",
                "action": "Simplify your habits or reduce frequency"
            })
        
        # Mood recommendations
        mood_data = self._analyze_wellbeing(memory)
        if mood_data.get("average_mood", 5) < 4:
            recommendations.append({
                "type": "wellbeing",
                "priority": "high",
                "title": "Focus on Wellbeing",
                "description": "Your recent mood scores suggest you might benefit from wellbeing-focused activities.",
                "action": "Consider stress reduction techniques, exercise, or seeking support"
            })
        
        # Engagement recommendations
        engagement = self._analyze_engagement(memory)
        if engagement.get("daily_average", 0) < 1:
            recommendations.append({
                "type": "engagement",
                "priority": "medium",
                "title": "Increase Engagement",
                "description": "Regular check-ins can help you stay on track with your goals.",
                "action": "Try to engage with your life coach daily, even briefly"
            })
        
        return recommendations
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"
        
        # Simple linear trend
        x = list(range(len(values)))
        slope = np.polyfit(x, values, 1)[0] if len(values) > 1 else 0
        
        if slope > 0.1:
            return "up"
        elif slope < -0.1:
            return "down"
        else:
            return "stable"
    
    def _calculate_user_since(self, memory: Dict) -> str:
        """Calculate how long user has been using the system"""
        life_events = memory.get("life_events", [])
        if not life_events:
            return "Today"
        
        try:
            first_event = life_events[0]
            first_date = datetime.datetime.fromisoformat(first_event.get("timestamp", first_event.get("date")))
            days_since = (datetime.datetime.now() - first_date).days
            
            if days_since < 7:
                return f"{days_since} days"
            elif days_since < 30:
                return f"{days_since // 7} weeks"
            else:
                return f"{days_since // 30} months"
        except:
            return "Unknown"
    
    def _calculate_usage_streak(self, memory: Dict) -> int:
        """Calculate current usage streak"""
        life_events = memory.get("life_events", [])
        if not life_events:
            return 0
        
        # Count consecutive days with activity
        daily_activity = set()
        for event in life_events:
            try:
                date = datetime.datetime.fromisoformat(event.get("timestamp", event.get("date"))).date()
                daily_activity.add(date)
            except:
                continue
        
        if not daily_activity:
            return 0
        
        sorted_dates = sorted(daily_activity, reverse=True)
        streak = 0
        current_date = datetime.date.today()
        
        for date in sorted_dates:
            if (current_date - date).days == streak:
                streak += 1
            else:
                break
        
        return streak
    
    # Additional helper methods for complex analytics
    def _find_most_consistent_habit(self, habits: List[Dict]) -> str:
        """Find the most consistently performed habit"""
        if not habits:
            return "None"
        
        best_habit = max(habits, key=lambda h: h.get("current_streak", 0))
        return best_habit.get("name", "Unknown")
    
    def _analyze_habit_categories(self, habits: List[Dict]) -> Dict:
        """Analyze habit distribution by category"""
        categories = defaultdict(int)
        for habit in habits:
            category = habit.get("category", "general")
            categories[category] += 1
        return dict(categories)
    
    def _calculate_average_goal_progress(self, goals: List[Dict]) -> float:
        """Calculate average progress across all goals"""
        if not goals:
            return 0
        
        active_goals = [g for g in goals if g.get("status") == "active"]
        if not active_goals:
            return 100  # All goals completed
        
        progress_values = [g.get("progress", 0) for g in active_goals]
        return statistics.mean(progress_values) if progress_values else 0
    
    def _analyze_goal_categories(self, goals: List[Dict]) -> Dict:
        """Analyze goal distribution and success by category"""
        categories = defaultdict(lambda: {"total": 0, "completed": 0})
        
        for goal in goals:
            category = goal.get("category", "general")
            categories[category]["total"] += 1
            if goal.get("status") == "completed":
                categories[category]["completed"] += 1
        
        # Calculate success rates
        result = {}
        for category, data in categories.items():
            success_rate = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0
            result[category] = {
                "total": data["total"],
                "completed": data["completed"],
                "success_rate": success_rate
            }
        
        return result
    
    def _calculate_success_by_category(self, goals: List[Dict]) -> Dict:
        """Calculate success rate by goal category"""
        return self._analyze_goal_categories(goals)
    
    def _analyze_goal_difficulty(self, goals: List[Dict]) -> Dict:
        """Analyze goal difficulty patterns"""
        # Simple heuristic based on completion time and progress
        easy_goals = medium_goals = hard_goals = 0
        
        for goal in goals:
            if goal.get("status") == "completed":
                # Assume goals completed quickly are easier
                if goal.get("progress", 0) == 100:
                    easy_goals += 1
            elif goal.get("progress", 0) < 20:
                hard_goals += 1
            else:
                medium_goals += 1
        
        return {
            "easy": easy_goals,
            "medium": medium_goals,
            "hard": hard_goals
        }
    
    # Pattern analysis methods
    def _analyze_conversation_timing(self, life_events: List[Dict]) -> Dict:
        """Analyze when user typically engages"""
        hour_counts = defaultdict(int)
        
        for event in life_events[-100:]:  # Last 100 events
            try:
                dt = datetime.datetime.fromisoformat(event.get("timestamp", event.get("date")))
                hour_counts[dt.hour] += 1
            except:
                continue
        
        peak_hour = max(hour_counts.keys(), key=hour_counts.get) if hour_counts else 12
        
        return {
            "hourly_distribution": dict(hour_counts),
            "peak_hour": peak_hour,
            "peak_time_period": self._categorize_time_period(peak_hour)
        }
    
    def _categorize_time_period(self, hour: int) -> str:
        """Categorize hour into time period"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    def _analyze_mood_triggers(self, mood_history: List[Dict], life_events: List[Dict]) -> Dict:
        """Identify potential mood triggers"""
        # Simple correlation analysis between events and mood changes
        triggers = defaultdict(list)
        
        for mood in mood_history[-50:]:  # Last 50 mood entries
            mood_date = datetime.datetime.fromisoformat(mood.get("timestamp"))
            
            # Look for events around the same time
            for event in life_events:
                try:
                    event_date = datetime.datetime.fromisoformat(event.get("timestamp", event.get("date")))
                    time_diff = abs((mood_date - event_date).total_seconds() / 3600)  # Hours
                    
                    if time_diff <= 6:  # Within 6 hours
                        emotion = mood.get("emotion", "neutral")
                        intensity = mood.get("intensity", 5)
                        event_text = event.get("entry", "")[:50]  # First 50 chars
                        
                        triggers[emotion].append({
                            "event": event_text,
                            "intensity": intensity,
                            "time_diff": time_diff
                        })
                except:
                    continue
        
        return dict(triggers)
    
    def _find_activity_clusters(self, life_events: List[Dict]) -> Dict:
        """Find clusters of similar activities"""
        # Simple keyword-based clustering
        clusters = defaultdict(int)
        
        for event in life_events[-100:]:  # Last 100 events
            entry = event.get("entry", "").lower()
            
            # Categorize based on keywords
            if any(word in entry for word in ["work", "job", "career", "meeting", "project"]):
                clusters["work"] += 1
            elif any(word in entry for word in ["exercise", "gym", "run", "workout", "fitness"]):
                clusters["fitness"] += 1
            elif any(word in entry for word in ["family", "friend", "social", "party", "dinner"]):
                clusters["social"] += 1
            elif any(word in entry for word in ["stress", "anxiety", "worried", "overwhelmed"]):
                clusters["stress"] += 1
            elif any(word in entry for word in ["happy", "excited", "celebration", "achievement"]):
                clusters["positive"] += 1
            else:
                clusters["other"] += 1
        
        return dict(clusters)
    
    def _analyze_seasonal_patterns(self, life_events: List[Dict], mood_history: List[Dict]) -> Dict:
        """Analyze seasonal and monthly patterns"""
        monthly_activity = defaultdict(int)
        monthly_mood = defaultdict(list)
        
        for event in life_events:
            try:
                dt = datetime.datetime.fromisoformat(event.get("timestamp", event.get("date")))
                month_name = dt.strftime("%B")
                monthly_activity[month_name] += 1
            except:
                continue
        
        for mood in mood_history:
            try:
                dt = datetime.datetime.fromisoformat(mood.get("timestamp"))
                month_name = dt.strftime("%B")
                monthly_mood[month_name].append(mood.get("intensity", 5))
            except:
                continue
        
        # Calculate average mood by month
        avg_monthly_mood = {}
        for month, intensities in monthly_mood.items():
            avg_monthly_mood[month] = statistics.mean(intensities) if intensities else 5
        
        return {
            "monthly_activity": dict(monthly_activity),
            "monthly_mood": avg_monthly_mood,
            "most_active_month": max(monthly_activity.keys(), key=monthly_activity.get) if monthly_activity else "Unknown",
            "best_mood_month": max(avg_monthly_mood.keys(), key=avg_monthly_mood.get) if avg_monthly_mood else "Unknown"
        }
    
    def _identify_stress_patterns(self, mood_history: List[Dict], life_events: List[Dict]) -> Dict:
        """Identify stress patterns and indicators"""
        stress_indicators = []
        stress_count = 0
        
        for mood in mood_history[-30:]:  # Last 30 mood entries
            emotion = mood.get("emotion", "neutral").lower()
            intensity = mood.get("intensity", 5)
            
            if emotion in ["anxious", "stressed", "overwhelmed", "frustrated", "angry"]:
                stress_count += 1
                stress_indicators.append({
                    "date": mood.get("timestamp"),
                    "emotion": emotion,
                    "intensity": intensity
                })
        
        stress_ratio = stress_count / len(mood_history[-30:]) if mood_history else 0
        
        return {
            "stress_frequency": stress_count,
            "stress_ratio": stress_ratio,
            "stress_level": "high" if stress_ratio > 0.3 else "medium" if stress_ratio > 0.1 else "low",
            "recent_stress_events": stress_indicators[-5:],  # Last 5 stress events
            "stress_trend": self._calculate_stress_trend(mood_history)
        }
    
    def _calculate_stress_trend(self, mood_history: List[Dict]) -> str:
        """Calculate if stress is increasing or decreasing"""
        if len(mood_history) < 10:
            return "insufficient_data"
        
        recent_stress = []
        older_stress = []
        
        for mood in mood_history[-20:]:  # Last 20 entries
            emotion = mood.get("emotion", "neutral").lower()
            if emotion in ["anxious", "stressed", "overwhelmed", "frustrated", "angry"]:
                recent_stress.append(1)
            else:
                recent_stress.append(0)
        
        # Compare first half vs second half
        first_half = recent_stress[:10]
        second_half = recent_stress[10:]
        
        first_stress_rate = sum(first_half) / len(first_half)
        second_stress_rate = sum(second_half) / len(second_half)
        
        if second_stress_rate > first_stress_rate * 1.2:
            return "increasing"
        elif second_stress_rate < first_stress_rate * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    # Prediction methods
    def _predict_goal_completion(self, goals: List[Dict]) -> Dict:
        """Predict likelihood of goal completion"""
        active_goals = [g for g in goals if g.get("status") == "active"]
        
        if not active_goals:
            return {"overall_likelihood": 100, "individual_predictions": []}
        
        predictions = []
        total_likelihood = 0
        
        for goal in active_goals:
            progress = goal.get("progress", 0)
            created_date = datetime.datetime.fromisoformat(goal.get("created_date", datetime.datetime.now().isoformat()))
            days_active = (datetime.datetime.now() - created_date).days
            
            # Simple prediction based on progress rate
            if days_active > 0:
                progress_rate = progress / days_active
                if progress_rate > 1:  # More than 1% per day
                    likelihood = min(95, 70 + progress * 0.3)
                elif progress_rate > 0.5:
                    likelihood = min(80, 50 + progress * 0.4)
                else:
                    likelihood = max(20, progress * 0.5)
            else:
                likelihood = 50  # New goal, neutral prediction
            
            predictions.append({
                "goal": goal.get("text", "Unknown"),
                "current_progress": progress,
                "likelihood": likelihood,
                "estimated_days_to_completion": self._estimate_completion_days(progress, progress_rate if days_active > 0 else 1)
            })
            
            total_likelihood += likelihood
        
        return {
            "overall_likelihood": total_likelihood / len(active_goals) if active_goals else 0,
            "individual_predictions": predictions
        }
    
    def _estimate_completion_days(self, current_progress: float, progress_rate: float) -> int:
        """Estimate days to goal completion"""
        if progress_rate <= 0:
            return 999  # Very long time
        
        remaining_progress = 100 - current_progress
        estimated_days = remaining_progress / progress_rate
        
        return max(1, int(estimated_days))
    
    def _predict_mood_trend(self, mood_history: List[Dict]) -> Dict:
        """Predict mood trend for next week"""
        if len(mood_history) < 7:
            return {"trend": "stable", "confidence": "low", "predicted_mood": 5.0}
        
        recent_moods = [m.get("intensity", 5) for m in mood_history[-14:]]  # Last 2 weeks
        
        # Simple linear trend
        trend_direction = self._calculate_trend(recent_moods)
        current_avg = statistics.mean(recent_moods[-7:])  # Last week average
        
        if trend_direction == "up":
            predicted_mood = min(10, current_avg + 0.5)
        elif trend_direction == "down":
            predicted_mood = max(1, current_avg - 0.5)
        else:
            predicted_mood = current_avg
        
        confidence = "high" if len(mood_history) > 20 else "medium" if len(mood_history) > 10 else "low"
        
        return {
            "trend": trend_direction,
            "predicted_mood": predicted_mood,
            "confidence": confidence,
            "recommendation": self._get_mood_recommendation(trend_direction, predicted_mood)
        }
    
    def _get_mood_recommendation(self, trend: str, predicted_mood: float) -> str:
        """Get recommendation based on mood prediction"""
        if trend == "down" or predicted_mood < 4:
            return "Consider stress reduction activities and self-care practices"
        elif trend == "up" and predicted_mood > 7:
            return "Great trend! Maintain your current positive practices"
        else:
            return "Focus on maintaining emotional balance and consistency"
    
    def _predict_habit_sustainability(self, habits: List[Dict]) -> Dict:
        """Predict which habits are most likely to be sustained"""
        if not habits:
            return {"sustainable_habits": [], "at_risk_habits": []}
        
        sustainable = []
        at_risk = []
        
        for habit in habits:
            if habit.get("status") != "active":
                continue
            
            current_streak = habit.get("current_streak", 0)
            total_completions = habit.get("total_completions", 0)
            check_ins = habit.get("check_ins", [])
            
            created_date = datetime.datetime.fromisoformat(habit.get("created_date", datetime.datetime.now().isoformat()))
            days_active = (datetime.datetime.now() - created_date).days
            
            if days_active > 0:
                consistency = len(check_ins) / days_active
                
                # Predict sustainability based on streak and consistency
                if current_streak >= 21 and consistency > 0.7:  # 21-day rule with high consistency
                    sustainability_score = min(95, 70 + current_streak * 0.5)
                    sustainable.append({
                        "habit": habit.get("name", "Unknown"),
                        "sustainability_score": sustainability_score,
                        "current_streak": current_streak
                    })
                elif current_streak < 7 or consistency < 0.3:
                    risk_score = max(5, 50 - current_streak * 2)
                    at_risk.append({
                        "habit": habit.get("name", "Unknown"),
                        "risk_score": risk_score,
                        "current_streak": current_streak,
                        "consistency": consistency
                    })
        
        return {
            "sustainable_habits": sustainable,
            "at_risk_habits": at_risk,
            "overall_habit_health": "good" if len(sustainable) > len(at_risk) else "needs_attention"
        }
    
    def _predict_engagement(self, life_events: List[Dict]) -> Dict:
        """Predict future engagement patterns"""
        if len(life_events) < 14:
            return {"trend": "stable", "predicted_weekly_sessions": 7}
        
        # Analyze recent engagement pattern
        recent_events = life_events[-30:]  # Last 30 events
        daily_counts = defaultdict(int)
        
        for event in recent_events:
            try:
                date = datetime.datetime.fromisoformat(event.get("timestamp", event.get("date"))).date()
                daily_counts[date] += 1
            except:
                continue
        
        # Calculate weekly average
        weekly_sessions = len(daily_counts) * 7 / 30 if daily_counts else 0
        
        # Predict based on trend
        engagement_trend = self._calculate_trend(list(daily_counts.values()))
        
        if engagement_trend == "up":
            predicted_sessions = min(14, weekly_sessions * 1.2)
        elif engagement_trend == "down":
            predicted_sessions = max(1, weekly_sessions * 0.8)
        else:
            predicted_sessions = weekly_sessions
        
        return {
            "current_weekly_sessions": weekly_sessions,
            "predicted_weekly_sessions": predicted_sessions,
            "trend": engagement_trend,
            "engagement_health": "high" if predicted_sessions > 5 else "medium" if predicted_sessions > 2 else "low"
        }
    
    def _predict_next_achievement(self, memory: Dict) -> Dict:
        """Predict when user might achieve next milestone"""
        goals = memory.get("goals", [])
        habits = memory.get("habits", [])
        
        # Find goals closest to completion
        active_goals = [g for g in goals if g.get("status") == "active"]
        closest_goals = sorted(active_goals, key=lambda g: g.get("progress", 0), reverse=True)
        
        # Find habits close to milestones
        habit_milestones = []
        for habit in habits:
            if habit.get("status") == "active":
                current_streak = habit.get("current_streak", 0)
                next_milestone = ((current_streak // 7) + 1) * 7  # Next weekly milestone
                days_to_milestone = next_milestone - current_streak
                
                if days_to_milestone <= 7:
                    habit_milestones.append({
                        "type": "habit_milestone",
                        "name": habit.get("name", "Unknown"),
                        "days_estimated": days_to_milestone,
                        "milestone": f"{next_milestone}-day streak"
                    })
        
        predictions = []
        
        # Add goal predictions
        for goal in closest_goals[:3]:  # Top 3 closest goals
            progress = goal.get("progress", 0)
            if progress > 50:  # Only predict for goals with significant progress
                created_date = datetime.datetime.fromisoformat(goal.get("created_date", datetime.datetime.now().isoformat()))
                days_active = (datetime.datetime.now() - created_date).days
                
                if days_active > 0:
                    progress_rate = progress / days_active
                    remaining_days = (100 - progress) / progress_rate if progress_rate > 0 else 999
                    
                    predictions.append({
                        "type": "goal_completion",
                        "name": goal.get("text", "Unknown"),
                        "days_estimated": max(1, int(remaining_days)),
                        "confidence": "high" if progress > 80 else "medium"
                    })
        
        # Add habit milestone predictions
        predictions.extend(habit_milestones)
        
        # Sort by estimated days
        predictions.sort(key=lambda p: p.get("days_estimated", 999))
        
        return {
            "next_achievements": predictions[:5],  # Top 5 predictions
            "estimated_next_achievement": predictions[0] if predictions else None
        }

# Global analytics instance
advanced_analytics = AdvancedAnalytics()
