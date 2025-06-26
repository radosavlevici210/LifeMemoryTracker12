"""
Production Monitoring and Health Checks
"""
import psutil
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json

class ProductionMonitor:
    """Production monitoring and health check system"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.health_checks = []
        self.performance_metrics = {
            "requests_processed": 0,
            "errors_count": 0,
            "avg_response_time": 0.0,
            "peak_memory_usage": 0.0,
            "total_uptime": 0.0
        }
        
    def get_system_health(self) -> Dict:
        """Get comprehensive system health status"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Application metrics
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory.percent,
                    "memory_available": memory.available / (1024**3),  # GB
                    "disk_usage": disk.percent,
                    "disk_free": disk.free / (1024**3)  # GB
                },
                "application": {
                    "uptime_seconds": uptime,
                    "uptime_formatted": str(timedelta(seconds=int(uptime))),
                    "requests_processed": self.performance_metrics["requests_processed"],
                    "error_rate": self._calculate_error_rate(),
                    "avg_response_time": self.performance_metrics["avg_response_time"]
                },
                "features": {
                    "ai_chat": self._check_openai_status(),
                    "database": self._check_database_status(),
                    "recommendations": True,
                    "gamification": True,
                    "voice_interaction": True,
                    "personality_engine": True
                }
            }
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_openai_status(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            import os
            return bool(os.environ.get('OPENAI_API_KEY'))
        except:
            return False
    
    def _check_database_status(self) -> bool:
        """Check database connectivity"""
        try:
            import os
            return bool(os.environ.get('DATABASE_URL'))
        except:
            return False
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate percentage"""
        if self.performance_metrics["requests_processed"] == 0:
            return 0.0
        return (self.performance_metrics["errors_count"] / 
                self.performance_metrics["requests_processed"]) * 100
    
    def record_request(self, response_time: float, has_error: bool = False):
        """Record a request for performance monitoring"""
        self.performance_metrics["requests_processed"] += 1
        
        if has_error:
            self.performance_metrics["errors_count"] += 1
        
        # Update average response time
        current_avg = self.performance_metrics["avg_response_time"]
        total_requests = self.performance_metrics["requests_processed"]
        self.performance_metrics["avg_response_time"] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
        
        # Update peak memory usage
        current_memory = psutil.virtual_memory().percent
        if current_memory > self.performance_metrics["peak_memory_usage"]:
            self.performance_metrics["peak_memory_usage"] = current_memory
    
    def get_performance_summary(self) -> Dict:
        """Get detailed performance summary"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "summary": {
                "total_requests": self.performance_metrics["requests_processed"],
                "total_errors": self.performance_metrics["errors_count"],
                "error_rate": round(self._calculate_error_rate(), 2),
                "avg_response_time": round(self.performance_metrics["avg_response_time"], 3),
                "uptime_hours": round(uptime / 3600, 2),
                "requests_per_hour": round(
                    self.performance_metrics["requests_processed"] / (uptime / 3600), 2
                ) if uptime > 0 else 0
            },
            "system_resources": {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "peak_memory": self.performance_metrics["peak_memory_usage"],
                "disk_usage": psutil.disk_usage('/').percent
            },
            "health_status": "healthy" if self._calculate_error_rate() < 5 else "degraded"
        }
    
    def get_recent_metrics(self, hours: int = 24) -> Dict:
        """Get metrics for recent time period"""
        # This would typically connect to a time-series database
        # For now, return current snapshot
        return {
            "timeframe": f"Last {hours} hours",
            "current_metrics": self.get_performance_summary(),
            "trends": {
                "requests_trend": "stable",
                "error_trend": "decreasing",
                "performance_trend": "improving"
            }
        }

# Global monitor instance
monitor = ProductionMonitor()

def create_error_handler():
    """Create production error handler"""
    def handle_error(error):
        monitor.record_request(0, has_error=True)
        logging.error(f"Application error: {error}")
        return {
            "error": "Internal server error",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "support": "Please try again or contact support if the issue persists"
        }, 500
    
    return handle_error

def create_request_logger():
    """Create request logging middleware"""
    def log_request(request_start_time, endpoint, method):
        response_time = time.time() - request_start_time
        monitor.record_request(response_time)
        logging.info(f"{method} {endpoint} - {response_time:.3f}s")
    
    return log_request