
"""
Performance optimization utilities for AI Life Coach
"""
import time
import functools
import gzip
import json
from typing import Any, Dict, Optional
from flask import request, g, current_app

class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        self.cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0, 'size': 0}
        self.max_cache_size = 100
    
    def cache_with_ttl(self, ttl: int = 300):
        """Decorator for caching function results with TTL"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # Check cache
                if cache_key in self.cache:
                    cached_data, expiry = self.cache[cache_key]
                    if time.time() < expiry:
                        self.cache_stats['hits'] += 1
                        return cached_data
                    else:
                        del self.cache[cache_key]
                        self.cache_stats['size'] -= 1
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result if there's space
                if self.cache_stats['size'] < self.max_cache_size:
                    self.cache[cache_key] = (result, time.time() + ttl)
                    self.cache_stats['size'] += 1
                
                self.cache_stats['misses'] += 1
                return result
            return wrapper
        return decorator
    
    def compress_response(self, data: Any) -> bytes:
        """Compress JSON response data"""
        if isinstance(data, dict):
            json_str = json.dumps(data, separators=(',', ':'))
        else:
            json_str = str(data)
        
        return gzip.compress(json_str.encode('utf-8'))
    
    def cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if current_time >= expiry
        ]
        
        for key in expired_keys:
            del self.cache[key]
            self.cache_stats['size'] -= 1
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hit_rate': round(hit_rate, 2),
            'cache_size': self.cache_stats['size'],
            'total_requests': total_requests
        }

# Global performance optimizer
perf_optimizer = PerformanceOptimizer()

def optimize_memory_loading(func):
    """Decorator to optimize memory loading operations"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        
        # Log slow operations
        execution_time = time.time() - start_time
        if execution_time > 1.0:  # Log operations taking more than 1 second
            current_app.logger.warning(f"Slow operation: {func.__name__} took {execution_time:.2f}s")
        
        return result
    return wrapper

def compress_memory_data(memory_data: Dict) -> Dict:
    """Compress memory data for storage efficiency"""
    # Keep only recent items to reduce memory usage
    optimized_data = {}
    
    for key, value in memory_data.items():
        if isinstance(value, list):
            # Keep only last 100 items for most lists
            if key in ['life_events', 'mood_history']:
                optimized_data[key] = value[-100:]
            elif key in ['goals', 'habits', 'achievements']:
                optimized_data[key] = value[-50:]
            else:
                optimized_data[key] = value[-25:]
        else:
            optimized_data[key] = value
    
    return optimized_data

def setup_performance_monitoring(app):
    """Setup performance monitoring for Flask app"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        # Add performance headers
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        # Add caching headers for static content
        if request.endpoint and 'static' in request.endpoint:
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        
        return response
    
    @app.route('/performance')
    def performance_stats():
        return perf_optimizer.get_performance_stats()
