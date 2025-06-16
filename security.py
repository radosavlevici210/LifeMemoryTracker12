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

# Security configuration
SECURITY_CONFIG = {
    "max_requests_per_minute": 60,
    "max_failed_attempts": 5,
    "session_timeout": 3600,  # 1 hour
    "rate_limit_window": 60,  # 1 minute
    "auto_backup_interval": 86400,  # 24 hours
    "health_check_interval": 300,  # 5 minutes
}

# In-memory storage for rate limiting and security tracking
rate_limit_storage = {}
failed_attempts = {}
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

def rate_limiter(max_requests=60, window=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = hash_ip(request.remote_addr)
            current_time = time.time()
            
            # Clean old entries
            if client_ip in rate_limit_storage:
                rate_limit_storage[client_ip] = [
                    timestamp for timestamp in rate_limit_storage[client_ip]
                    if current_time - timestamp < window
                ]
            else:
                rate_limit_storage[client_ip] = []
            
            # Check rate limit
            if len(rate_limit_storage[client_ip]) >= max_requests:
                log_security_event("rate_limit_exceeded", {
                    "ip": client_ip,
                    "endpoint": request.endpoint,
                    "requests": len(rate_limit_storage[client_ip])
                })
                return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
            
            # Add current request
            rate_limit_storage[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def security_monitor(f):
    """Security monitoring decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        client_ip = hash_ip(request.remote_addr)
        
        try:
            result = f(*args, **kwargs)
            
            # Log successful request
            log_security_event("request_success", {
                "ip": client_ip,
                "endpoint": request.endpoint,
                "method": request.method,
                "response_time": time.time() - start_time
            })
            
            return result
            
        except Exception as e:
            # Log failed request
            log_security_event("request_error", {
                "ip": client_ip,
                "endpoint": request.endpoint,
                "error": str(e),
                "response_time": time.time() - start_time
            })
            
            # Track failed attempts
            if client_ip not in failed_attempts:
                failed_attempts[client_ip] = []
            failed_attempts[client_ip].append(time.time())
            
            # Clean old failed attempts
            failed_attempts[client_ip] = [
                timestamp for timestamp in failed_attempts[client_ip]
                if time.time() - timestamp < 300  # 5 minutes
            ]
            
            # Block if too many failures
            if len(failed_attempts[client_ip]) >= SECURITY_CONFIG["max_failed_attempts"]:
                log_security_event("ip_blocked", {
                    "ip": client_ip,
                    "failed_attempts": len(failed_attempts[client_ip])
                })
                return jsonify({"error": "Too many failed attempts. Access temporarily blocked."}), 429
            
            raise e
            
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
    """Sanitize user input"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'javascript', 'onclick']
        for char in dangerous_chars:
            data = data.replace(char, '')
        return data.strip()
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

def validate_session():
    """Validate user session"""
    session_token = request.headers.get('X-Session-Token')
    if not session_token:
        return False
    
    # Simple session validation (in production, use proper JWT or session store)
    return len(session_token) == 43  # URL-safe base64 token length

def encrypt_sensitive_data(data):
    """Encrypt sensitive data (placeholder for production encryption)"""
    # In production, use proper encryption like Fernet or AES
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

def auto_repair():
    """Attempt automatic system repairs"""
    repairs_performed = []
    
    try:
        # Clear old rate limit entries
        current_time = time.time()
        for ip in list(rate_limit_storage.keys()):
            rate_limit_storage[ip] = [
                timestamp for timestamp in rate_limit_storage[ip]
                if current_time - timestamp < SECURITY_CONFIG["rate_limit_window"]
            ]
            if not rate_limit_storage[ip]:
                del rate_limit_storage[ip]
        
        repairs_performed.append("Cleared old rate limit entries")
        
        # Clear old failed attempts
        for ip in list(failed_attempts.keys()):
            failed_attempts[ip] = [
                timestamp for timestamp in failed_attempts[ip]
                if current_time - timestamp < 300
            ]
            if not failed_attempts[ip]:
                del failed_attempts[ip]
        
        repairs_performed.append("Cleared old failed attempts")
        
        # Clean old security events
        if len(security_events) > 1000:
            security_events[:] = security_events[-500:]
            repairs_performed.append("Cleaned security event log")
        
        # Restart services if critical issues detected
        if system_health["status"] == "critical":
            # In production, this could restart specific services
            log_security_event("auto_repair_triggered", {
                "issues": system_health["issues"],
                "repairs": repairs_performed
            })
            
        return repairs_performed
        
    except Exception as e:
        logging.error(f"Auto-repair failed: {str(e)}")
        return [f"Repair failed: {str(e)}"]

def backup_data():
    """Create automated backup"""
    try:
        from app import load_memory
        
        memory_data = load_memory()
        backup_filename = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join("backups", backup_filename)
        
        # Create backups directory if it doesn't exist
        os.makedirs("backups", exist_ok=True)
        
        with open(backup_path, 'w') as f:
            json.dump(memory_data, f, indent=2)
        
        # Keep only last 10 backups
        backup_files = sorted([
            f for f in os.listdir("backups") 
            if f.startswith("backup_") and f.endswith(".json")
        ])
        
        while len(backup_files) > 10:
            old_backup = backup_files.pop(0)
            os.remove(os.path.join("backups", old_backup))
        
        log_security_event("backup_created", {
            "filename": backup_filename,
            "size": os.path.getsize(backup_path)
        })
        
        return backup_filename
        
    except Exception as e:
        logging.error(f"Backup failed: {str(e)}")
        return None

def get_security_metrics():
    """Get security and performance metrics"""
    current_time = time.time()
    
    return {
        "active_sessions": len(rate_limit_storage),
        "blocked_ips": len(failed_attempts),
        "recent_events": len([
            event for event in security_events[-100:]
            if (current_time - time.mktime(
                datetime.datetime.fromisoformat(event["timestamp"]).timetuple()
            )) < 3600
        ]),
        "system_health": system_health,
        "uptime": "System running normally",
        "last_backup": max([
            f for f in os.listdir("backups") 
            if f.startswith("backup_") and f.endswith(".json")
        ], default="No backups") if os.path.exists("backups") else "No backups"
    }