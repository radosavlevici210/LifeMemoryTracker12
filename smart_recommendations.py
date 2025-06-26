"""
Smart Recommendations Engine with Machine Learning Insights
"""
import json
import datetime
import logging
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class RecommendationType(Enum):
    GOAL_OPTIMIZATION = "goal_optimization"
    HABIT_FORMATION = "habit_formation"
    MOOD_IMPROVEMENT = "mood_improvement"
    PRODUCTIVITY_BOOST = "productivity_boost"
    WELLNESS_ENHANCEMENT = "wellness_enhancement"
    TIME_MANAGEMENT = "time_management"
    STRESS_REDUCTION = "stress_reduction"

@dataclass
class Recommendation:
    type: RecommendationType
    title: str
    description: str
    action_steps: List[str]
    priority: int  # 1-10
    confidence: float  # 0.0-1.0
    expected_impact: str
    timeline: str
    personalization_factors: List[str]

class SmartRecommendationsEngine:
    def __init__(self):
        self.recommendation_history = []
        self.user_feedback = {}
        self.learning_weights = {
            "goal_completion_rate": 0.25,
            "mood_stability": 0.20,
            "habit_consistency": 0.20,
            "productivity_patterns": 0.15,
            "engagement_level": 0.10,
            "stress_indicators": 0.10
        }
    
    def generate_recommendations(self, memory: Dict) -> List[Recommendation]:
        """Generate personalized recommendations based on user data"""
        recommendations = []
        
        # Analyze user patterns
        analysis = self._analyze_user_patterns(memory)
        
        # Generate different types of recommendations
        recommendations.extend(self._generate_goal_recommendations(memory, analysis))
        recommendations.extend(self._generate_habit_recommendations(memory, analysis))
        recommendations.extend(self._generate_mood_recommendations(memory, analysis))
        recommendations.extend(self._generate_productivity_recommendations(memory, analysis))
        recommendations.extend(self._generate_wellness_recommendations(memory, analysis))
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda x: (x.priority * x.confidence), reverse=True)
        
        return recommendations[:8]  # Return top 8 recommendations
    
    def _analyze_user_patterns(self, memory: Dict) -> Dict:
        """Analyze user behavior patterns"""
        goals = memory.get("goals", [])
        habits = memory.get("habits", [])
        mood_history = memory.get("mood_history", [])
        life_events = memory.get("life_events", [])
        
        analysis = {
            "goal_completion_rate": self._calculate_goal_completion_rate(goals),
            "habit_consistency": self._calculate_habit_consistency(habits),
            "mood_trend": self._analyze_mood_trend(mood_history),
            "activity_patterns": self._analyze_activity_patterns(life_events),
            "stress_indicators": self._identify_stress_patterns(mood_history, life_events),
            "productivity_windows": self._identify_productivity_windows(life_events),
            "engagement_level": self._calculate_engagement_level(life_events)
        }
        
        return analysis
    
    def _calculate_goal_completion_rate(self, goals: List[Dict]) -> float:
        """Calculate goal completion rate"""
        if not goals:
            return 0.5
        
        completed = sum(1 for goal in goals if goal.get("status") == "completed")
        return completed / len(goals) if goals else 0.0
    
    def _calculate_habit_consistency(self, habits: List[Dict]) -> float:
        """Calculate habit consistency score"""
        if not habits:
            return 0.5
        
        total_consistency = 0
        for habit in habits:
            streak = habit.get("current_streak", 0)
            target_frequency = habit.get("frequency", 7)  # Default weekly
            consistency = min(streak / target_frequency, 1.0)
            total_consistency += consistency
        
        return total_consistency / len(habits)
    
    def _analyze_mood_trend(self, mood_history: List[Dict]) -> Dict:
        """Analyze mood trend and stability"""
        if len(mood_history) < 3:
            return {"trend": "stable", "average": 5.0, "stability": 0.5}
        
        recent_moods = [m.get("mood", 5) for m in mood_history[-14:]]  # Last 2 weeks
        average_mood = sum(recent_moods) / len(recent_moods)
        
        # Calculate trend
        if len(recent_moods) >= 5:
            first_half = recent_moods[:len(recent_moods)//2]
            second_half = recent_moods[len(recent_moods)//2:]
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            if second_avg > first_avg + 0.5:
                trend = "improving"
            elif second_avg < first_avg - 0.5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Calculate stability (inverse of variance)
        variance = sum((mood - average_mood) ** 2 for mood in recent_moods) / len(recent_moods)
        stability = max(0, 1 - (variance / 10))  # Normalize variance
        
        return {
            "trend": trend,
            "average": average_mood,
            "stability": stability
        }
    
    def _analyze_activity_patterns(self, life_events: List[Dict]) -> Dict:
        """Analyze user activity patterns"""
        if not life_events:
            return {"most_active_time": "morning", "activity_frequency": 0}
        
        # Analyze by time of day
        time_activity = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
        
        for event in life_events[-30:]:  # Last 30 events
            timestamp = event.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = dt.hour
                    
                    if 6 <= hour < 12:
                        time_activity["morning"] += 1
                    elif 12 <= hour < 18:
                        time_activity["afternoon"] += 1
                    elif 18 <= hour < 22:
                        time_activity["evening"] += 1
                    else:
                        time_activity["night"] += 1
                except:
                    continue
        
        most_active_time = max(time_activity.items(), key=lambda x: x[1])[0] if any(time_activity.values()) else "morning"
        unique_dates = [e.get("date") for e in life_events if e.get("date")]
        activity_frequency = len(life_events) / max(1, len(set(unique_dates)))
        
        return {
            "most_active_time": most_active_time,
            "activity_frequency": activity_frequency,
            "time_distribution": time_activity
        }
    
    def _identify_stress_patterns(self, mood_history: List[Dict], life_events: List[Dict]) -> Dict:
        """Identify stress patterns and triggers"""
        stress_indicators = []
        
        # Low mood periods
        for mood_entry in mood_history[-14:]:
            if mood_entry.get("mood", 5) < 4:
                stress_indicators.append("low_mood")
        
        # Overwhelming language in events
        stress_keywords = ["overwhelmed", "stressed", "anxious", "pressure", "deadline", "difficult"]
        for event in life_events[-20:]:
            event_text = event.get("event", "").lower()
            if any(keyword in event_text for keyword in stress_keywords):
                stress_indicators.append("stress_language")
        
        stress_level = min(len(stress_indicators) / 10, 1.0)  # Normalize to 0-1
        
        return {
            "stress_level": stress_level,
            "indicators": stress_indicators,
            "needs_attention": stress_level > 0.6
        }
    
    def _identify_productivity_windows(self, life_events: List[Dict]) -> Dict:
        """Identify when user is most productive"""
        productivity_keywords = ["completed", "finished", "achieved", "accomplished", "done"]
        
        time_productivity = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
        
        for event in life_events[-30:]:
            event_text = event.get("event", "").lower()
            if any(keyword in event_text for keyword in productivity_keywords):
                timestamp = event.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        hour = dt.hour
                        
                        if 6 <= hour < 12:
                            time_productivity["morning"] += 1
                        elif 12 <= hour < 18:
                            time_productivity["afternoon"] += 1
                        elif 18 <= hour < 22:
                            time_productivity["evening"] += 1
                        else:
                            time_productivity["night"] += 1
                    except:
                        continue
        
        peak_time = max(time_productivity.items(), key=lambda x: x[1])[0] if any(time_productivity.values()) else "morning"
        
        return {
            "peak_time": peak_time,
            "productivity_distribution": time_productivity
        }
    
    def _calculate_engagement_level(self, life_events: List[Dict]) -> float:
        """Calculate user engagement level"""
        if not life_events:
            return 0.5
        
        recent_events = life_events[-7:]  # Last week
        engagement_score = len(recent_events) / 7  # Events per day
        
        return min(engagement_score, 1.0)
    
    def _generate_goal_recommendations(self, memory: Dict, analysis: Dict) -> List[Recommendation]:
        """Generate goal-related recommendations"""
        recommendations = []
        goals = memory.get("goals", [])
        completion_rate = analysis["goal_completion_rate"]
        
        if completion_rate < 0.3:
            recommendations.append(Recommendation(
                type=RecommendationType.GOAL_OPTIMIZATION,
                title="Simplify Your Goals",
                description="Your goal completion rate suggests you might be taking on too much at once.",
                action_steps=[
                    "Review your current goals and identify the top 3 priorities",
                    "Break large goals into smaller, manageable milestones",
                    "Set weekly mini-goals to build momentum",
                    "Celebrate small wins to maintain motivation"
                ],
                priority=9,
                confidence=0.8,
                expected_impact="Increased completion rate by 40-60%",
                timeline="2-3 weeks",
                personalization_factors=["low_completion_rate", "goal_overload"]
            ))
        
        if len(goals) == 0:
            recommendations.append(Recommendation(
                type=RecommendationType.GOAL_OPTIMIZATION,
                title="Set Your First Goal",
                description="Start your growth journey by setting a meaningful, achievable goal.",
                action_steps=[
                    "Choose one area of life you want to improve",
                    "Set a specific, measurable goal for the next 30 days",
                    "Write down why this goal matters to you",
                    "Plan your first action step for tomorrow"
                ],
                priority=8,
                confidence=0.9,
                expected_impact="Foundation for personal growth",
                timeline="This week",
                personalization_factors=["no_goals", "new_user"]
            ))
        
        return recommendations
    
    def _generate_habit_recommendations(self, memory: Dict, analysis: Dict) -> List[Recommendation]:
        """Generate habit-related recommendations"""
        recommendations = []
        habits = memory.get("habits", [])
        consistency = analysis["habit_consistency"]
        
        if consistency < 0.4:
            recommendations.append(Recommendation(
                type=RecommendationType.HABIT_FORMATION,
                title="Start with Micro-Habits",
                description="Build consistency with tiny habits that are impossible to fail.",
                action_steps=[
                    "Choose one habit and reduce it to 2 minutes or less",
                    "Link the habit to something you already do daily",
                    "Track completion with a simple checkmark",
                    "Focus on consistency over performance for 21 days"
                ],
                priority=8,
                confidence=0.85,
                expected_impact="80% improvement in habit consistency",
                timeline="3-4 weeks",
                personalization_factors=["low_consistency", "habit_struggles"]
            ))
        
        if len(habits) > 5:
            recommendations.append(Recommendation(
                type=RecommendationType.HABIT_FORMATION,
                title="Reduce Habit Overload",
                description="Too many habits at once can lead to failure. Focus on fewer, more impactful ones.",
                action_steps=[
                    "Identify your 3 most important habits",
                    "Pause other habits temporarily",
                    "Master these 3 habits for 30 days",
                    "Gradually add new habits one at a time"
                ],
                priority=7,
                confidence=0.75,
                expected_impact="Better habit sustainability",
                timeline="1 month",
                personalization_factors=["habit_overload", "too_many_habits"]
            ))
        
        return recommendations
    
    def _generate_mood_recommendations(self, memory: Dict, analysis: Dict) -> List[Recommendation]:
        """Generate mood-related recommendations"""
        recommendations = []
        mood_data = analysis["mood_trend"]
        
        if mood_data["trend"] == "declining" or mood_data["average"] < 4:
            recommendations.append(Recommendation(
                type=RecommendationType.MOOD_IMPROVEMENT,
                title="Boost Your Daily Mood",
                description="Your mood trend suggests you could benefit from mood-boosting activities.",
                action_steps=[
                    "Start each day with 5 minutes of gratitude journaling",
                    "Take a 10-minute walk outside daily",
                    "Connect with a friend or loved one each day",
                    "Practice deep breathing when feeling low"
                ],
                priority=9,
                confidence=0.9,
                expected_impact="1-2 point mood improvement within 2 weeks",
                timeline="2-3 weeks",
                personalization_factors=["declining_mood", "low_average"]
            ))
        
        if mood_data["stability"] < 0.4:
            recommendations.append(Recommendation(
                type=RecommendationType.MOOD_IMPROVEMENT,
                title="Create Emotional Stability",
                description="Your mood fluctuates significantly. Building routines can help stabilize emotions.",
                action_steps=[
                    "Establish consistent sleep and wake times",
                    "Create a calming evening routine",
                    "Practice mindfulness or meditation for 10 minutes daily",
                    "Track mood triggers to identify patterns"
                ],
                priority=8,
                confidence=0.8,
                expected_impact="More stable emotional well-being",
                timeline="4-6 weeks",
                personalization_factors=["mood_instability", "emotional_volatility"]
            ))
        
        return recommendations
    
    def _generate_productivity_recommendations(self, memory: Dict, analysis: Dict) -> List[Recommendation]:
        """Generate productivity-related recommendations"""
        recommendations = []
        productivity_data = analysis["productivity_windows"]
        peak_time = productivity_data["peak_time"]
        
        recommendations.append(Recommendation(
            type=RecommendationType.PRODUCTIVITY_BOOST,
            title=f"Optimize Your {peak_time.title()} Productivity",
            description=f"Your data shows you're most productive in the {peak_time}. Let's maximize this window.",
            action_steps=[
                f"Schedule your most important tasks for the {peak_time}",
                "Protect this time from interruptions and meetings",
                "Prepare the night before to hit the ground running",
                "Track your energy levels to confirm optimal timing"
            ],
            priority=7,
            confidence=0.75,
            expected_impact="25-40% increase in productive output",
            timeline="2 weeks",
            personalization_factors=[f"{peak_time}_productivity", "time_optimization"]
        ))
        
        if analysis["engagement_level"] < 0.3:
            recommendations.append(Recommendation(
                type=RecommendationType.PRODUCTIVITY_BOOST,
                title="Increase Daily Engagement",
                description="Your activity level suggests you could benefit from more structured daily engagement.",
                action_steps=[
                    "Set 3 specific tasks to complete each day",
                    "Use time-blocking to structure your day",
                    "Take regular breaks to maintain energy",
                    "Review and adjust your approach weekly"
                ],
                priority=6,
                confidence=0.7,
                expected_impact="More structured and productive days",
                timeline="3-4 weeks",
                personalization_factors=["low_engagement", "structure_needed"]
            ))
        
        return recommendations
    
    def _generate_wellness_recommendations(self, memory: Dict, analysis: Dict) -> List[Recommendation]:
        """Generate wellness-related recommendations"""
        recommendations = []
        stress_data = analysis["stress_indicators"]
        
        if stress_data["needs_attention"]:
            recommendations.append(Recommendation(
                type=RecommendationType.STRESS_REDUCTION,
                title="Implement Stress Management",
                description="Your patterns indicate elevated stress levels that need attention.",
                action_steps=[
                    "Practice the 4-7-8 breathing technique when stressed",
                    "Schedule 15 minutes of relaxation daily",
                    "Identify and address your top 3 stress triggers",
                    "Consider talking to someone about your stress"
                ],
                priority=9,
                confidence=0.85,
                expected_impact="Significant stress reduction",
                timeline="2-4 weeks",
                personalization_factors=["high_stress", "stress_management"]
            ))
        
        # General wellness recommendation
        recommendations.append(Recommendation(
            type=RecommendationType.WELLNESS_ENHANCEMENT,
            title="Enhance Overall Wellness",
            description="Focus on foundational wellness practices for better life balance.",
            action_steps=[
                "Ensure 7-8 hours of quality sleep nightly",
                "Drink 8 glasses of water daily",
                "Include 30 minutes of physical activity in your routine",
                "Practice gratitude or mindfulness for 5 minutes daily"
            ],
            priority=6,
            confidence=0.8,
            expected_impact="Improved energy and well-being",
            timeline="Ongoing",
            personalization_factors=["wellness_foundation", "holistic_health"]
        ))
        
        return recommendations
    
    def get_recommendation_summary(self, memory: Dict) -> Dict:
        """Get a summary of recommendations with key insights"""
        recommendations = self.generate_recommendations(memory)
        analysis = self._analyze_user_patterns(memory)
        
        # Convert recommendations to dict format for JSON serialization
        recommendation_dicts = []
        focus_areas = set()
        
        for r in recommendations:
            if hasattr(r, 'type'):
                # Handle Recommendation objects
                rec_dict = {
                    "type": r.type.value,
                    "title": r.title,
                    "description": r.description,
                    "priority": r.priority,
                    "confidence": round(r.confidence * 100, 1),
                    "timeline": r.timeline,
                    "action_steps": r.action_steps
                }
                focus_areas.add(r.type.value)
            else:
                # Handle dict objects
                rec_dict = {
                    "type": r.get("type", "general"),
                    "title": r.get("title", ""),
                    "description": r.get("description", ""),
                    "priority": r.get("priority", 5),
                    "confidence": round(r.get("confidence", 0.5) * 100, 1),
                    "timeline": r.get("timeline", ""),
                    "action_steps": r.get("action_steps", [])
                }
                focus_areas.add(r.get("type", "general"))
            
            recommendation_dicts.append(rec_dict)
        
        return {
            "total_recommendations": len(recommendations),
            "top_priority": recommendation_dicts[0] if recommendation_dicts else None,
            "focus_areas": list(focus_areas),
            "user_analysis": {
                "goal_completion_rate": round(analysis["goal_completion_rate"] * 100, 1),
                "habit_consistency": round(analysis["habit_consistency"] * 100, 1),
                "mood_trend": analysis["mood_trend"]["trend"],
                "stress_level": analysis["stress_indicators"]["stress_level"],
                "engagement_level": round(analysis["engagement_level"] * 100, 1)
            },
            "recommendations": recommendation_dicts
        }