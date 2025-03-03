"""
Performance monitoring module for the Interaction Management System.

This module provides capabilities to track and measure application performance metrics
including API response times, database queries, function execution times, and other
performance indicators. It helps identify bottlenecks and enables performance optimization.
"""

import logging  # standard library
import time  # standard library
import functools  # standard library
import typing  # standard library
from enum import Enum  # standard library
import statistics  # standard library

from ..cache.cache_service import get_cache_service
from ./structured_logger import get_request_id
from ..utils.datetime_util import get_current_datetime

# Initialize logger
logger = logging.getLogger(__name__)

# Metric categories for standard performance measurement
METRIC_CATEGORIES = {
    'API': 'api',
    'DATABASE': 'db',
    'CACHE': 'cache',
    'AUTH': 'auth',
    'SEARCH': 'search',
    'INTERACTION': 'interaction'
}

# Cache TTL for metrics (24 hours)
METRIC_CACHE_TTL = 60 * 60 * 24

# Warning thresholds for different metric categories (in milliseconds)
METRIC_THRESHOLD_WARNING = {
    'API': 500,  # 500ms
    'DATABASE': 200,  # 200ms
    'CACHE': 50,   # 50ms
    'AUTH': 500,   # 500ms
    'SEARCH': 1000, # 1s
    'INTERACTION': 200  # 200ms
}

# Singleton instance
_performance_monitor_instance = None


class Timer:
    """
    Context manager for timing code blocks with automatic metric recording.
    
    Usage:
    ```
    with Timer('DATABASE', 'query_users') as timer:
        result = db.execute_query(...)
    ```
    """
    
    def __init__(self, category: str, name: str):
        """
        Initialize a timer with category and name.
        
        Args:
            category: Metric category from METRIC_CATEGORIES
            name: Descriptive name for the operation being timed
        """
        if category not in METRIC_CATEGORIES:
            raise ValueError(f"Invalid metric category: {category}. Must be one of: {', '.join(METRIC_CATEGORIES.keys())}")
        
        self.category = category
        self.name = name
        self.start_time = None
        self._monitor = get_performance_monitor()
    
    def __enter__(self) -> 'Timer':
        """
        Start the timer when entering context.
        
        Returns:
            Self reference for context manager
        """
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Stop the timer and record metric when exiting context.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
            
        Returns:
            None (context manager exit doesn't suppress exceptions)
        """
        elapsed_time = time.perf_counter() - self.start_time
        elapsed_ms = elapsed_time * 1000.0  # Convert to milliseconds
        
        # Record the metric
        self._monitor.record_metric(self.category, self.name, elapsed_ms)
        
        # Log warning if threshold exceeded
        if elapsed_ms > METRIC_THRESHOLD_WARNING.get(self.category, 1000):
            logger.warning(
                f"Performance threshold exceeded: {self.category}:{self.name} took {elapsed_ms:.2f}ms "
                f"(threshold: {METRIC_THRESHOLD_WARNING.get(self.category, 1000)}ms)"
            )
        
        # Don't suppress exceptions
        return None


class PerformanceMonitor:
    """
    Service for tracking and storing performance metrics across the application.
    
    This class implements a comprehensive performance monitoring system that tracks
    timing metrics for various operations, analyzes performance patterns, and 
    optionally stores metrics in cache for longer-term analysis.
    """
    
    def __init__(self):
        """
        Initialize the performance monitor.
        """
        # Initialize metrics dictionary
        # Structure: {category: {name: [values]}}
        self._metrics = {}
        
        # Try to get cache service for persistent metrics
        try:
            self._cache_service = get_cache_service()
            self._enabled = True
            logger.info("Performance monitor initialized with cache service")
        except Exception as e:
            self._cache_service = None
            self._enabled = True  # Still enabled but without persistence
            logger.warning(f"Performance monitor initialized without cache service: {str(e)}")
    
    def start_timer(self, category: str, name: str) -> float:
        """
        Start a performance timer with a specific name and category.
        
        Args:
            category: Metric category from METRIC_CATEGORIES
            name: Descriptive name for the operation being timed
            
        Returns:
            Start time in seconds (high precision)
        """
        if category not in METRIC_CATEGORIES:
            raise ValueError(f"Invalid metric category: {category}. Must be one of: {', '.join(METRIC_CATEGORIES.keys())}")
        
        start_time = time.perf_counter()
        return start_time
    
    def stop_timer(self, category: str, name: str, start_time: float) -> float:
        """
        Stop a performance timer and record the metric.
        
        Args:
            category: Metric category from METRIC_CATEGORIES
            name: Descriptive name for the operation being timed
            start_time: Start time returned from start_timer
            
        Returns:
            Elapsed time in milliseconds
        """
        if category not in METRIC_CATEGORIES:
            raise ValueError(f"Invalid metric category: {category}. Must be one of: {', '.join(METRIC_CATEGORIES.keys())}")
        
        elapsed_time = time.perf_counter() - start_time
        elapsed_ms = elapsed_time * 1000.0  # Convert to milliseconds
        
        # Record the metric
        self.record_metric(category, name, elapsed_ms)
        
        return elapsed_ms
    
    def record_metric(self, category: str, name: str, value: float) -> bool:
        """
        Record a performance metric.
        
        Args:
            category: Metric category from METRIC_CATEGORIES
            name: Descriptive name for the operation
            value: Metric value (usually time in milliseconds)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._enabled:
            return False
            
        if category not in METRIC_CATEGORIES:
            raise ValueError(f"Invalid metric category: {category}. Must be one of: {', '.join(METRIC_CATEGORIES.keys())}")
        
        # Create category dict if it doesn't exist
        if category not in self._metrics:
            self._metrics[category] = {}
        
        # Create name list if it doesn't exist
        if name not in self._metrics[category]:
            self._metrics[category][name] = []
        
        # Add value to metrics list
        self._metrics[category][name].append(value)
        
        # Try to cache the metric if cache service is available
        if self._cache_service:
            try:
                # Create cache key with category, name, and timestamp
                timestamp = get_current_datetime().isoformat()
                request_id = get_request_id()
                
                # Store the metric value with category, name, timestamp, and request_id
                metric_data = {
                    'category': category,
                    'name': name,
                    'value': value,
                    'timestamp': timestamp,
                    'request_id': request_id
                }
                
                # Use a key structure that allows for efficient querying
                cache_key = f"metrics:{category}:{name}:{timestamp}"
                self._cache_service.set(cache_key, metric_data, METRIC_CACHE_TTL)
            except Exception as e:
                logger.error(f"Failed to cache performance metric: {str(e)}")
        
        # Log warning if threshold exceeded
        if value > METRIC_THRESHOLD_WARNING.get(category, 1000):
            logger.warning(
                f"Performance threshold exceeded: {category}:{name} took {value:.2f}ms "
                f"(threshold: {METRIC_THRESHOLD_WARNING.get(category, 1000)}ms)"
            )
        
        return True
    
    def get_metrics(self, category: str = None) -> dict:
        """
        Get all recorded metrics or for a specific category.
        
        Args:
            category: Optional category to filter metrics
            
        Returns:
            Metrics data structure
        """
        if not self._enabled:
            return {}
            
        if category is None:
            # Return all metrics
            return self._metrics
        elif category in self._metrics:
            # Return metrics for the specified category
            return {category: self._metrics[category]}
        else:
            # Category not found
            return {}
    
    def get_metric_statistics(self, category: str, name: str) -> dict:
        """
        Get statistical summary of metrics for a category and name.
        
        Args:
            category: Metric category
            name: Metric name
            
        Returns:
            Statistical summary (min, max, avg, median, count)
        """
        if not self._enabled:
            return {}
            
        if category not in self._metrics:
            raise ValueError(f"No metrics found for category: {category}")
        
        if name not in self._metrics[category]:
            raise ValueError(f"No metrics found for name: {name} in category: {category}")
        
        values = self._metrics[category][name]
        
        if not values:
            return {
                'min': None,
                'max': None,
                'avg': None,
                'median': None,
                'count': 0
            }
        
        return {
            'min': min(values),
            'max': max(values),
            'avg': statistics.mean(values),
            'median': statistics.median(values),
            'count': len(values)
        }
    
    def reset_metrics(self, category: str = None) -> bool:
        """
        Reset all metrics or for a specific category.
        
        Args:
            category: Optional category to reset
            
        Returns:
            True if successful, False otherwise
        """
        if not self._enabled:
            return False
            
        if category is None:
            # Reset all metrics
            self._metrics = {}
            logger.info("All performance metrics reset")
        elif category in self._metrics:
            # Reset metrics for the specified category
            self._metrics[category] = {}
            logger.info(f"Performance metrics reset for category: {category}")
        else:
            # Category not found
            logger.warning(f"No metrics found for category: {category}")
            return False
        
        return True
    
    def create_timer(self, category: str, name: str) -> Timer:
        """
        Create a Timer context manager for a specific category and name.
        
        Args:
            category: Metric category from METRIC_CATEGORIES
            name: Descriptive name for the operation
            
        Returns:
            Timer context manager instance
        """
        return Timer(category, name)


def time_function(category: str, name: str = None) -> typing.Callable:
    """
    Decorator to measure the execution time of a function.
    
    Args:
        category: Metric category from METRIC_CATEGORIES
        name: Optional name for the metric (defaults to function name)
        
    Returns:
        Decorated function that records timing metrics
    """
    # Validate category
    if category not in METRIC_CATEGORIES:
        raise ValueError(f"Invalid metric category: {category}. Must be one of: {', '.join(METRIC_CATEGORIES.keys())}")
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name if name not provided
            metric_name = name if name is not None else func.__name__
            
            # Get performance monitor singleton
            monitor = get_performance_monitor()
            
            # Measure execution time
            start_time = time.perf_counter()
            try:
                # Execute the wrapped function
                result = func(*args, **kwargs)
                return result
            finally:
                # Calculate and record execution time
                elapsed_time = time.perf_counter() - start_time
                elapsed_ms = elapsed_time * 1000.0  # Convert to milliseconds
                
                # Record the metric
                monitor.record_metric(category, metric_name, elapsed_ms)
                
                # Log warning if threshold exceeded
                if elapsed_ms > METRIC_THRESHOLD_WARNING.get(category, 1000):
                    logger.warning(
                        f"Performance threshold exceeded: {category}:{metric_name} took {elapsed_ms:.2f}ms "
                        f"(threshold: {METRIC_THRESHOLD_WARNING.get(category, 1000)}ms)"
                    )
        
        return wrapper
    
    return decorator


def get_performance_monitor() -> PerformanceMonitor:
    """
    Singleton factory function to get or create the performance monitor instance.
    
    Returns:
        Singleton instance of PerformanceMonitor
    """
    global _performance_monitor_instance
    
    if _performance_monitor_instance is None:
        _performance_monitor_instance = PerformanceMonitor()
    
    return _performance_monitor_instance