"""
AI Personality Engine for Dynamic Life Coach Adaptation
"""
import json
import datetime
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class PersonalityType(Enum):
    MOTIVATIONAL = "motivational"
    ANALYTICAL = "analytical"
    EMPATHETIC = "empathetic"
    PRACTICAL = "practical"
    CREATIVE = "creative"
    STRATEGIC = "strategic"

class CommunicationStyle(Enum):
    DIRECT = "direct"
    SUPPORTIVE = "supportive"
    CHALLENGING = "challenging"
    GENTLE = "gentle"
    ENERGETIC = "energetic"
    THOUGHTFUL = "thoughtful"

@dataclass
class PersonalityProfile:
    type: PersonalityType
    communication_style: CommunicationStyle
    energy_level: float  # 0.0 to 1.0
    formality: float     # 0.0 to 1.0
    humor_level: float   # 0.0 to 1.0
    directness: float    # 0.0 to 1.0

class AIPersonalityEngine:
    def __init__(self):
        self.user_preferences = {}
        self.interaction_history = []
        self.current_personality = self._get_default_personality()
        
    def _get_default_personality(self) -> PersonalityProfile:
        return PersonalityProfile(
            type=PersonalityType.EMPATHETIC,
            communication_style=CommunicationStyle.SUPPORTIVE,
            energy_level=0.7,
            formality=0.4,
            humor_level=0.3,
            directness=0.6
        )
    
    def analyze_user_preferences(self, memory: Dict) -> PersonalityProfile:
        """Analyze user interaction patterns to adapt personality"""
        life_events = memory.get("life_events", [])
        mood_history = memory.get("mood_history", [])
        
        # Analyze communication patterns
        recent_interactions = life_events[-20:] if life_events else []
        
        # Determine preferred energy level
        energy_indicators = []
        for event in recent_interactions:
            text = event.get("event", "").lower()
            if any(word in text for word in ["excited", "energetic", "motivated", "pumped"]):
                energy_indicators.append(0.8)
            elif any(word in text for word in ["tired", "exhausted", "overwhelmed", "stressed"]):
                energy_indicators.append(0.3)
            else:
                energy_indicators.append(0.6)
        
        avg_energy = sum(energy_indicators) / len(energy_indicators) if energy_indicators else 0.6
        
        # Determine communication style based on response patterns
        communication_style = CommunicationStyle.SUPPORTIVE
        if len(recent_interactions) > 10:
            goal_focused = sum(1 for event in recent_interactions 
                             if any(word in event.get("event", "").lower() 
                                   for word in ["goal", "achieve", "plan", "strategy"]))
            if goal_focused > len(recent_interactions) * 0.4:
                communication_style = CommunicationStyle.CHALLENGING
        
        # Determine personality type based on user focus areas
        goals = memory.get("goals", [])
        habits = memory.get("habits", [])
        
        if len(goals) > len(habits):
            personality_type = PersonalityType.STRATEGIC
        elif any("creative" in str(goal).lower() for goal in goals):
            personality_type = PersonalityType.CREATIVE
        elif len(mood_history) > 10:
            personality_type = PersonalityType.EMPATHETIC
        else:
            personality_type = PersonalityType.MOTIVATIONAL
        
        return PersonalityProfile(
            type=personality_type,
            communication_style=communication_style,
            energy_level=min(max(avg_energy, 0.1), 1.0),
            formality=0.4,  # Keep moderate formality
            humor_level=0.3 + (avg_energy * 0.2),  # More humor when energy is higher
            directness=0.5 + (0.3 if communication_style == CommunicationStyle.CHALLENGING else 0.0)
        )
    
    def generate_system_prompt(self, personality: PersonalityProfile, context: Dict) -> str:
        """Generate dynamic system prompt based on personality"""
        base_prompt = "You are an AI Life Coach. "
        
        # Personality-specific instructions
        if personality.type == PersonalityType.MOTIVATIONAL:
            base_prompt += "You inspire and energize users to take action. "
        elif personality.type == PersonalityType.ANALYTICAL:
            base_prompt += "You provide data-driven insights and logical frameworks. "
        elif personality.type == PersonalityType.EMPATHETIC:
            base_prompt += "You understand emotions deeply and provide compassionate support. "
        elif personality.type == PersonalityType.PRACTICAL:
            base_prompt += "You focus on actionable, real-world solutions. "
        elif personality.type == PersonalityType.CREATIVE:
            base_prompt += "You encourage innovative thinking and creative problem-solving. "
        elif personality.type == PersonalityType.STRATEGIC:
            base_prompt += "You help create long-term plans and systematic approaches. "
        
        # Communication style
        if personality.communication_style == CommunicationStyle.DIRECT:
            base_prompt += "Be straightforward and concise. "
        elif personality.communication_style == CommunicationStyle.SUPPORTIVE:
            base_prompt += "Be encouraging and nurturing. "
        elif personality.communication_style == CommunicationStyle.CHALLENGING:
            base_prompt += "Push the user to grow and exceed their limits. "
        elif personality.communication_style == CommunicationStyle.GENTLE:
            base_prompt += "Be patient and understanding. "
        elif personality.communication_style == CommunicationStyle.ENERGETIC:
            base_prompt += "Be enthusiastic and dynamic. "
        elif personality.communication_style == CommunicationStyle.THOUGHTFUL:
            base_prompt += "Be reflective and contemplative. "
        
        # Energy and tone adjustments
        if personality.energy_level > 0.7:
            base_prompt += "Use an upbeat, energetic tone. "
        elif personality.energy_level < 0.4:
            base_prompt += "Use a calm, soothing tone. "
        
        if personality.humor_level > 0.5:
            base_prompt += "Include appropriate humor when helpful. "
        
        if personality.directness > 0.7:
            base_prompt += "Be direct and honest, even if it challenges the user. "
        
        # Context-aware additions
        goals = context.get("goals", [])
        mood_history = context.get("mood_history", [])
        
        if goals:
            base_prompt += f"The user has {len(goals)} active goals. "
        
        if mood_history:
            recent_mood = mood_history[-1] if mood_history else {}
            mood_value = recent_mood.get("mood", 5)
            if mood_value < 4:
                base_prompt += "The user's recent mood indicates they may need extra support. "
            elif mood_value > 7:
                base_prompt += "The user's recent mood is positive - build on this energy. "
        
        base_prompt += "Provide supportive, actionable guidance. Be empathetic and helpful."
        
        return base_prompt
    
    def adapt_personality(self, memory: Dict) -> PersonalityProfile:
        """Adapt personality based on user data"""
        new_personality = self.analyze_user_preferences(memory)
        
        # Gradual adaptation to avoid jarring changes
        if hasattr(self, 'current_personality'):
            # Blend new personality with current one (70% new, 30% current)
            blended_personality = PersonalityProfile(
                type=new_personality.type,
                communication_style=new_personality.communication_style,
                energy_level=0.7 * new_personality.energy_level + 0.3 * self.current_personality.energy_level,
                formality=0.7 * new_personality.formality + 0.3 * self.current_personality.formality,
                humor_level=0.7 * new_personality.humor_level + 0.3 * self.current_personality.humor_level,
                directness=0.7 * new_personality.directness + 0.3 * self.current_personality.directness
            )
            self.current_personality = blended_personality
        else:
            self.current_personality = new_personality
            
        return self.current_personality
    
    def get_personality_summary(self) -> Dict:
        """Get current personality configuration summary"""
        return {
            "type": self.current_personality.type.value,
            "communication_style": self.current_personality.communication_style.value,
            "energy_level": round(self.current_personality.energy_level, 2),
            "formality": round(self.current_personality.formality, 2),
            "humor_level": round(self.current_personality.humor_level, 2),
            "directness": round(self.current_personality.directness, 2),
            "last_updated": datetime.datetime.now().isoformat()
        }
    
    def save_personality_profile(self, filename: str = "personality_profile.json"):
        """Save current personality profile"""
        try:
            profile_data = self.get_personality_summary()
            with open(filename, 'w') as f:
                json.dump(profile_data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save personality profile: {e}")
    
    def load_personality_profile(self, filename: str = "personality_profile.json"):
        """Load saved personality profile"""
        try:
            with open(filename, 'r') as f:
                profile_data = json.load(f)
            
            self.current_personality = PersonalityProfile(
                type=PersonalityType(profile_data["type"]),
                communication_style=CommunicationStyle(profile_data["communication_style"]),
                energy_level=profile_data["energy_level"],
                formality=profile_data["formality"],
                humor_level=profile_data["humor_level"],
                directness=profile_data["directness"]
            )
        except (FileNotFoundError, KeyError, ValueError) as e:
            logging.info(f"Using default personality profile: {e}")
            self.current_personality = self._get_default_personality()