"""
Production Monitoring and Metrics for AI Life Coach Application
"""
import time
import psutil
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from functools import wraps
from flask import request, g

class ProductionMetrics:
    """Production metrics collection and monitoring"""
    
    def __init__(self):
        self.metrics = {
            'requests': {'total': 0, 'errors': 0, 'success': 0},
            'response_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'ai_requests': {'total': 0, 'errors': 0, 'tokens_used': 0},
            'users': {'active_sessions': 0, 'total_interactions': 0},
            'system': {'uptime': time.time(), 'errors': []},
            'performance': {'slow_requests': 0, 'cache_hits': 0, 'cache_misses': 0}
        }
        self.start_time = time.time()
        
    def record_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record request metrics"""
        self.metrics['requests']['total'] += 1
        
        if status_code >= 400:
            self.metrics['requests']['errors'] += 1
        else:
            self.metrics['requests']['success'] += 1
            
        self.metrics['response_times'].append({
            'endpoint': endpoint,
            'method': method,
            'time': response_time,
            'timestamp': time.time()
        })
        
        # Keep only last 1000 response times
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]
            
        # Track slow requests (>2 seconds)
        if response_time > 2.0:
            self.metrics['performance']['slow_requests'] += 1
            
    def record_ai_request(self, tokens_used: int, success: bool):
        """Record AI API request metrics"""
        self.metrics['ai_requests']['total'] += 1
        self.metrics['ai_requests']['tokens_used'] += tokens_used
        
        if not success:
            self.metrics['ai_requests']['errors'] += 1
            
    def record_system_metrics(self):
        """Record system performance metrics"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].append({
                'percent': memory.percent,
                'used': memory.used,
                'available': memory.available,
                'timestamp': time.time()
            })
            
            # CPU usage
            cpu = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage'].append({
                'percent': cpu,
                'timestamp': time.time()
            })
            
            # Keep only last 100 system metrics
            for metric in ['memory_usage', 'cpu_usage']:
                if len(self.metrics[metric]) > 100:
                    self.metrics[metric] = self.metrics[metric][-100:]
                    
        except Exception as e:
            logging.error(f"Failed to record system metrics: {e}")
            
    def get_health_status(self) -> Dict:
        """Get comprehensive health status"""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # Calculate average response time
        recent_responses = [r for r in self.metrics['response_times'] 
                          if current_time - r['timestamp'] < 300]  # Last 5 minutes
        avg_response_time = sum(r['time'] for r in recent_responses) / len(recent_responses) if recent_responses else 0
        
        # Calculate error rate
        total_requests = self.metrics['requests']['total']
        error_rate = (self.metrics['requests']['errors'] / total_requests * 100) if total_requests > 0 else 0
        
        # Get system metrics
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        disk = psutil.disk_usage('/')
        
        return {
            'status': 'healthy' if error_rate < 5 and avg_response_time < 2.0 else 'degraded',
            'uptime': uptime,
            'metrics': {
                'total_requests': total_requests,
                'error_rate': round(error_rate, 2),
                'avg_response_time': round(avg_response_time, 3),
                'ai_requests': self.metrics['ai_requests']['total'],
                'ai_tokens_used': self.metrics['ai_requests']['tokens_used'],
                'system': {
                    'memory_percent': memory.percent,
                    'cpu_percent': cpu,
                    'disk_percent': disk.percent
                }
            },
            'timestamp': current_time
        }
        
    def export_metrics(self) -> Dict:
        """Export all metrics for analysis"""
        return {
            'metrics': self.metrics,
            'health': self.get_health_status(),
            'exported_at': time.time()
        }

# Global metrics instance
metrics = ProductionMetrics()

def monitor_request(f):
    """Decorator to monitor Flask requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        g.start_time = start_time
        
        try:
            result = f(*args, **kwargs)
            status_code = getattr(result, 'status_code', 200)
        except Exception as e:
            status_code = 500
            logging.error(f"Request error: {e}")
            raise
        finally:
            end_time = time.time()
            response_time = end_time - start_time
            
            metrics.record_request(
                endpoint=request.endpoint or request.path,
                method=request.method,
                status_code=status_code,
                response_time=response_time
            )
            
        return result
    return decorated_function

def monitor_ai_request(f):
    """Decorator to monitor AI API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            # Estimate tokens used (rough calculation)
            tokens_used = len(str(result)) // 4 if result else 0
            metrics.record_ai_request(tokens_used, True)
            return result
        except Exception as e:
            metrics.record_ai_request(0, False)
            raise
    return decorated_function

class ErrorTracker:
    """Track and analyze application errors"""
    
    def __init__(self):
        self.errors = []
        
    def log_error(self, error: Exception, context: Dict = None):
        """Log an error with context"""
        error_data = {
            'timestamp': time.time(),
            'type': type(error).__name__,
            'message': str(error),
            'context': context or {},
            'user_agent': request.headers.get('User-Agent') if request else None,
            'ip_address': request.remote_addr if request else None
        }
        
        self.errors.append(error_data)
        
        # Keep only last 500 errors
        if len(self.errors) > 500:
            self.errors = self.errors[-500:]
            
        # Log to file for persistence
        try:
            log_file = os.path.join('logs', 'errors.json')
            os.makedirs('logs', exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(error_data) + '\n')
        except Exception as e:
            logging.error(f"Failed to write error log: {e}")
            
    def get_error_summary(self, hours: int = 24) -> Dict:
        """Get error summary for the last N hours"""
        cutoff_time = time.time() - (hours * 3600)
        recent_errors = [e for e in self.errors if e['timestamp'] > cutoff_time]
        
        error_types = {}
        for error in recent_errors:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
        return {
            'total_errors': len(recent_errors),
            'error_types': error_types,
            'error_rate': len(recent_errors) / hours if hours > 0 else 0,
            'period_hours': hours
        }

# Global error tracker
error_tracker = ErrorTracker()

class PerformanceOptimizer:
    """Optimize application performance"""
    
    def __init__(self):
        self.cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        
    def cache_response(self, key: str, data: any, ttl: int = 300):
        """Cache response data with TTL"""
        expiry = time.time() + ttl
        self.cache[key] = {
            'data': data,
            'expiry': expiry
        }
        
    def get_cached_response(self, key: str) -> Optional[any]:
        """Get cached response if valid"""
        if key in self.cache:
            cached = self.cache[key]
            if time.time() < cached['expiry']:
                self.cache_stats['hits'] += 1
                metrics.metrics['performance']['cache_hits'] += 1
                return cached['data']
            else:
                del self.cache[key]
                
        self.cache_stats['misses'] += 1
        metrics.metrics['performance']['cache_misses'] += 1
        return None
        
    def cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [k for k, v in self.cache.items() 
                       if current_time >= v['expiry']]
        
        for key in expired_keys:
            del self.cache[key]
            
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hit_rate': round(hit_rate, 2),
            'total_requests': total,
            'cache_size': len(self.cache),
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses']
        }

# Global performance optimizer
performance_optimizer = PerformanceOptimizer()

def setup_production_monitoring(app):
    """Setup production monitoring for Flask app"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        
    @app.after_request
    def after_request(response):
        # Record metrics
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            metrics.record_request(
                endpoint=request.endpoint or request.path,
                method=request.method,
                status_code=response.status_code,
                response_time=response_time
            )
        return response
        
    @app.errorhandler(Exception)
    def handle_exception(e):
        error_tracker.log_error(e, {
            'endpoint': request.endpoint,
            'method': request.method,
            'url': request.url
        })
        return {'error': 'Internal server error'}, 500
        
    # Add monitoring endpoints
    @app.route('/metrics')
    def get_metrics():
        return metrics.export_metrics()
        
    @app.route('/health-detailed')
    def get_detailed_health():
        return {
            'health': metrics.get_health_status(),
            'errors': error_tracker.get_error_summary(),
            'cache': performance_optimizer.get_cache_stats()
        }
        
    return app