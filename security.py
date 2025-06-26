"""
Security and monitoring module for AI Life Coach application
"""
import os
import json
import time
import hashlib
import datetime
import logging
from functools import wraps
from flask import request, jsonify, g
import secrets
import jwt

# In-memory storage for basic tracking
security_events = []
system_health = {
    "last_check": None,
    "status": "healthy",
    "issues": [],
    "metrics": {}
}

def generate_session_token():
    """Generate secure session token"""
    return secrets.token_urlsafe(32)

def hash_ip(ip_address):
    """Hash IP address for privacy"""
    return hashlib.sha256(ip_address.encode()).hexdigest()[:16]

def simple_logger(f):
    """Simple request logger"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def log_security_event(event_type, details):
    """Log security events"""
    event = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": event_type,
        "details": details
    }
    
    security_events.append(event)
    
    # Keep only last 1000 events
    if len(security_events) > 1000:
        security_events.pop(0)
    
    # Log critical events
    if event_type in ["rate_limit_exceeded", "ip_blocked", "security_breach"]:
        logging.warning(f"Security event: {event_type} - {details}")

def sanitize_input(data):
    """Basic input cleaning"""
    if isinstance(data, str):
        return data.strip()
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

def system_health_check():
    """Perform system health check"""
    global system_health
    
    current_time = datetime.datetime.now()
    issues = []
    metrics = {}
    
    try:
        # Check memory usage
        import psutil
        memory_usage = psutil.virtual_memory().percent
        metrics["memory_usage"] = memory_usage
        
        if memory_usage > 90:
            issues.append(f"High memory usage: {memory_usage}%")
        
        # Check disk space
        disk_usage = psutil.disk_usage('/').percent
        metrics["disk_usage"] = disk_usage
        
        if disk_usage > 90:
            issues.append(f"Low disk space: {disk_usage}% used")
        
        # Check API response time (simulate)
        start_time = time.time()
        # Simulate health check
        time.sleep(0.001)
        api_response_time = (time.time() - start_time) * 1000
        metrics["api_response_time"] = api_response_time
        
        if api_response_time > 1000:  # 1 second
            issues.append(f"Slow API response: {api_response_time}ms")
        
        # Check recent errors
        recent_errors = [
            event for event in security_events[-50:]
            if event["type"] == "request_error" and
            (current_time - datetime.datetime.fromisoformat(event["timestamp"])).seconds < 300
        ]
        
        metrics["recent_errors"] = len(recent_errors)
        
        if len(recent_errors) > 10:
            issues.append(f"High error rate: {len(recent_errors)} errors in 5 minutes")
        
    except ImportError:
        # psutil not available, use basic checks
        metrics["system_check"] = "basic"
    
    except Exception as e:
        issues.append(f"Health check error: {str(e)}")
    
    system_health.update({
        "last_check": current_time.isoformat(),
        "status": "healthy" if not issues else "warning" if len(issues) < 3 else "critical",
        "issues": issues,
        "metrics": metrics
    })
    
    return system_health

def simple_cleanup():
    """Basic cleanup function"""
    try:
        # Clean old security events
        if len(security_events) > 1000:
            security_events[:] = security_events[-500:]
        return ["Cleaned event log"]
    except Exception as e:
        logging.error(f"Cleanup failed: {str(e)}")
        return [f"Cleanup failed: {str(e)}"]

def get_basic_metrics():
    """Get basic system metrics"""
    return {
        "system_health": system_health,
        "uptime": "System running normally",
        "recent_events": len(security_events[-100:]) if security_events else 0
    }

def get_security_metrics():
    """Get security metrics for admin dashboard"""
    return {
        "total_events": len(security_events),
        "recent_events": security_events[-10:] if security_events else [],
        "system_status": system_health.get("status", "unknown"),
        "last_check": system_health.get("last_check", "never"),
        "active_issues": len(system_health.get("issues", [])),
        "metrics": system_health.get("metrics", {})
    }
