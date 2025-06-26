"""
Voice Interaction and Speech Recognition System
"""
import json
import datetime
import logging
from typing import Dict, List, Optional
import asyncio
from dataclasses import dataclass

@dataclass
class VoiceCommand:
    command: str
    confidence: float
    timestamp: datetime.datetime
    action: Optional[str] = None
    parameters: Optional[Dict] = None

class VoiceInteractionEngine:
    def __init__(self):
        self.voice_commands = []
        self.voice_enabled = False
        self.supported_commands = {
            "set goal": self._handle_set_goal,
            "track mood": self._handle_track_mood,
            "add habit": self._handle_add_habit,
            "get progress": self._handle_get_progress,
            "show insights": self._handle_show_insights,
            "daily summary": self._handle_daily_summary,
            "voice settings": self._handle_voice_settings
        }
    
    def _handle_set_goal(self, parameters: Dict) -> Dict:
        """Handle voice goal setting"""
        goal_text = parameters.get("text", "")
        return {
            "action": "set_goal",
            "goal": goal_text,
            "voice_response": f"I've added the goal: {goal_text}. What priority level should this have?"
        }
    
    def _handle_track_mood(self, parameters: Dict) -> Dict:
        """Handle voice mood tracking"""
        mood_value = parameters.get("mood", 5)
        return {
            "action": "track_mood",
            "mood": mood_value,
            "voice_response": f"Mood recorded as {mood_value} out of 10. Would you like to add any notes about how you're feeling?"
        }
    
    def _handle_add_habit(self, parameters: Dict) -> Dict:
        """Handle voice habit addition"""
        habit_text = parameters.get("text", "")
        return {
            "action": "add_habit",
            "habit": habit_text,
            "voice_response": f"Added habit: {habit_text}. How often would you like to do this?"
        }
    
    def _handle_get_progress(self, parameters: Dict) -> Dict:
        """Handle voice progress requests"""
        return {
            "action": "get_progress",
            "voice_response": "Let me get your latest progress summary. One moment please."
        }
    
    def _handle_show_insights(self, parameters: Dict) -> Dict:
        """Handle voice insights requests"""
        return {
            "action": "show_insights",
            "voice_response": "Here are your personalized insights based on your recent activity."
        }
    
    def _handle_daily_summary(self, parameters: Dict) -> Dict:
        """Handle daily summary requests"""
        return {
            "action": "daily_summary",
            "voice_response": "Generating your daily summary with goals, mood, and achievements."
        }
    
    def _handle_voice_settings(self, parameters: Dict) -> Dict:
        """Handle voice settings configuration"""
        return {
            "action": "voice_settings",
            "voice_response": "Voice settings menu. You can enable or disable voice responses, change language, or adjust speech speed."
        }
    
    def process_voice_command(self, command_text: str, confidence: float = 0.8) -> Dict:
        """Process voice command and return action"""
        command_text = command_text.lower().strip()
        
        # Find matching command
        for cmd_pattern, handler in self.supported_commands.items():
            if cmd_pattern in command_text:
                # Extract parameters from command
                parameters = self._extract_parameters(command_text, cmd_pattern)
                result = handler(parameters)
                
                # Log the command
                voice_command = VoiceCommand(
                    command=command_text,
                    confidence=confidence,
                    timestamp=datetime.datetime.now(),
                    action=result.get("action"),
                    parameters=parameters
                )
                self.voice_commands.append(voice_command)
                
                return result
        
        # Default response for unrecognized commands
        return {
            "action": "unknown",
            "voice_response": "I didn't understand that command. Try saying 'set goal', 'track mood', or 'show insights'."
        }
    
    def _extract_parameters(self, command_text: str, pattern: str) -> Dict:
        """Extract parameters from voice command"""
        # Remove the pattern from the command to get parameters
        remaining_text = command_text.replace(pattern, "").strip()
        
        parameters = {"text": remaining_text}
        
        # Extract mood numbers
        if "mood" in pattern:
            import re
            mood_match = re.search(r'\b(\d+)\b', remaining_text)
            if mood_match:
                parameters["mood"] = str(mood_match.group(1))
        
        return parameters
    
    def get_voice_commands_history(self, limit: int = 20) -> List[Dict]:
        """Get recent voice commands"""
        recent_commands = self.voice_commands[-limit:] if self.voice_commands else []
        return [
            {
                "command": cmd.command,
                "confidence": cmd.confidence,
                "timestamp": cmd.timestamp.isoformat(),
                "action": cmd.action
            }
            for cmd in recent_commands
        ]
    
    def enable_voice_interaction(self) -> Dict:
        """Enable voice interaction"""
        self.voice_enabled = True
        return {
            "status": "enabled",
            "message": "Voice interaction is now enabled. You can speak commands like 'set goal' or 'track mood'."
        }
    
    def disable_voice_interaction(self) -> Dict:
        """Disable voice interaction"""
        self.voice_enabled = False
        return {
            "status": "disabled",
            "message": "Voice interaction disabled."
        }
    
    def get_voice_settings(self) -> Dict:
        """Get current voice settings"""
        return {
            "enabled": self.voice_enabled,
            "supported_commands": list(self.supported_commands.keys()),
            "total_commands_processed": len(self.voice_commands),
            "language": "en-US",
            "speech_rate": 1.0,
            "voice_type": "neural"
        }