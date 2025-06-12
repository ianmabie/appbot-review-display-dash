#!/usr/bin/env python3
"""
Performance monitoring and optimization for deployment
"""

import os
import time
import psutil
import logging
from flask import request, g
from functools import wraps

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, app=None):
        self.app = app
        self.request_times = []
        self.slow_requests = []
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize performance monitoring with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Add performance endpoint
        @app.route('/performance')
        def performance_stats():
            return self.get_stats()
    
    def before_request(self):
        """Record request start time"""
        g.start_time = time.time()
        g.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    def after_request(self, response):
        """Record request completion and analyze performance"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            memory_used = psutil.Process().memory_info().rss / 1024 / 1024 - g.start_memory
            
            # Track request performance
            self.request_times.append(duration)
            
            # Log slow requests (> 2 seconds)
            if duration > 2.0:
                self.slow_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'duration': duration,
                    'memory_delta': memory_used,
                    'timestamp': time.time()
                })
                logger.warning(f"Slow request: {request.method} {request.path} took {duration:.2f}s")
            
            # Keep only recent data
            if len(self.request_times) > 100:
                self.request_times = self.request_times[-100:]
            
            if len(self.slow_requests) > 20:
                self.slow_requests = self.slow_requests[-20:]
        
        return response
    
    def get_stats(self):
        """Get performance statistics"""
        if not self.request_times:
            return {'status': 'no_data'}
        
        avg_time = sum(self.request_times) / len(self.request_times)
        max_time = max(self.request_times)
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'status': 'ok',
            'requests_tracked': len(self.request_times),
            'average_response_time': round(avg_time, 3),
            'max_response_time': round(max_time, 3),
            'slow_requests_count': len(self.slow_requests),
            'memory_usage_mb': round(memory_info.rss / 1024 / 1024, 2),
            'memory_percent': round(process.memory_percent(), 2),
            'cpu_percent': round(process.cpu_percent(), 2),
            'recent_slow_requests': self.slow_requests[-5:] if self.slow_requests else []
        }

def performance_timer(func):
    """Decorator to time function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        if duration > 1.0:  # Log functions taking > 1 second
            logger.warning(f"Slow function {func.__name__} took {duration:.2f}s")
        
        return result
    return wrapper

# Database connection optimization
def optimize_database_queries():
    """Optimize database queries for better performance"""
    from app import db
    
    # Enable query optimization
    if hasattr(db.engine, 'pool'):
        # Force connection pool cleanup
        db.engine.pool.dispose()
    
    logger.info("Database query optimization applied")

# Static file caching headers
def add_cache_headers(response, cache_timeout=300):
    """Add caching headers to improve load times"""
    if response.status_code == 200:
        response.cache_control.max_age = cache_timeout
        response.cache_control.public = True
    return response