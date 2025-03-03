"""
Gunicorn WSGI server configuration for the Interaction Management System.

This file configures Gunicorn for production deployment, including settings for
worker processes, logging, timeouts, and server binding. Settings can be overridden
using environment variables to facilitate containerized deployments.
"""

import os
import multiprocessing
from .logging.structured_logger import StructuredLogger

# Initialize structured logger
logger = StructuredLogger('gunicorn.conf')

# Server socket binding configuration (default: 0.0.0.0:8000)
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')

# Worker processes - using the formula (2 x $num_cores) + 1 for optimal performance
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# Worker type - gevent provides better performance for I/O bound applications
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'gevent')

# Maximum number of simultaneous clients per worker when using async workers
worker_connections = int(os.getenv('GUNICORN_WORKER_CONNECTIONS', '1000'))

# Request timeout in seconds
timeout = int(os.getenv('GUNICORN_TIMEOUT', '30'))

# Seconds to keep idle client connections alive
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', '2'))

# Logging configuration
# '-' sends logs to stdout/stderr, ideal for container environments
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# Process name
proc_name = os.getenv('GUNICORN_PROC_NAME', 'interaction-management-api')

# Worker lifecycle management to prevent memory leaks
# Maximum requests a worker will process before restarting
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '1000'))
# Jitter added to max_requests to prevent all workers from restarting simultaneously
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '100'))

def on_starting(server):
    """
    Handler called when Gunicorn is starting up
    
    Args:
        server: Gunicorn server instance
    """
    logger.info("Starting Gunicorn server", {
        "workers": workers,
        "bind": bind,
        "worker_class": worker_class,
        "proc_name": proc_name,
        "loglevel": loglevel
    })

def post_fork(server, worker):
    """
    Handler called after a worker has been forked
    
    Args:
        server: Gunicorn server instance
        worker: Worker instance that was forked
    """
    logger.info("Worker spawned", {
        "pid": worker.pid,
        "worker_id": worker.id,
        "server_pid": server.pid
    })

def on_exit(server, worker):
    """
    Handler called when a worker is exiting
    
    Args:
        server: Gunicorn server instance
        worker: Worker instance that is exiting
    """
    logger.info("Worker exiting", {
        "pid": worker.pid,
        "worker_id": worker.id,
        "server_pid": server.pid
    })

def worker_int(worker):
    """
    Handler for SIGINT signal to workers
    
    Args:
        worker: Worker instance that received the signal
    """
    logger.info("Worker received interrupt signal", {
        "pid": worker.pid,
        "worker_id": worker.id
    })

def worker_abort(worker):
    """
    Handler for worker abort events
    
    Args:
        worker: Worker instance that was aborted
    """
    logger.error("Worker aborted", {
        "pid": worker.pid,
        "worker_id": worker.id,
        "reason": "Worker exceeded timeout or memory limit"
    })