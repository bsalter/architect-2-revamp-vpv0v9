"""
Redis client implementation for the Interaction Management System.

This module provides a client interface for interacting with Redis cache,
handling connection management, data serialization, and basic Redis operations.
It supports both simple key-value operations and more complex data structures
like hashes and lists, with automatic serialization of Python objects.
"""

import redis  # version 4.5.4
import json  # standard library
import pickle  # standard library
from typing import Any, Dict, List, Optional, Union  # standard library
from contextlib import contextmanager  # standard library

from ..config import REDIS_CONFIG
from ..logging.structured_logger import get_logger
from ..utils.error_util import handle_error

# Initialize logger
logger = get_logger('redis_client')


def serialize_data(data: Any) -> bytes:
    """
    Serializes data to be stored in Redis based on its type.
    
    Args:
        data: Data of any type to be serialized
        
    Returns:
        Serialized data in bytes format suitable for Redis storage
    """
    if data is None:
        return None
    
    # Handle primitive types
    if isinstance(data, (str, int, float, bool)):
        return str(data).encode('utf-8')
    
    # Handle complex types
    try:
        if isinstance(data, (dict, list)):
            # Use JSON for dictionaries and lists for better interoperability
            return json.dumps(data).encode('utf-8')
        else:
            # Use pickle for more complex Python objects
            return pickle.dumps(data)
    except (TypeError, pickle.PickleError) as e:
        logger.error(f"Serialization error: {str(e)}")
        # Fall back to string representation if serialization fails
        return str(data).encode('utf-8')


def deserialize_data(data: bytes, data_type: str = 'str') -> Any:
    """
    Deserializes data retrieved from Redis back to its original type.
    
    Args:
        data: Serialized data from Redis
        data_type: Type hint for deserialization ('str', 'int', 'float',
                  'bool', 'json', 'pickle')
        
    Returns:
        Deserialized data in its original type
    """
    if data is None:
        return None
    
    try:
        # Decode bytes to string if we're dealing with text-based data
        if data_type in ('str', 'int', 'float', 'bool', 'json'):
            decoded = data.decode('utf-8')
        
        # Process according to expected type
        if data_type == 'str':
            return decoded
        elif data_type == 'int':
            return int(decoded)
        elif data_type == 'float':
            return float(decoded)
        elif data_type == 'bool':
            return decoded.lower() in ('true', 't', 'yes', 'y', '1')
        elif data_type == 'json':
            return json.loads(decoded)
        elif data_type == 'pickle':
            return pickle.loads(data)
        else:
            # Default to string if type is unknown
            return data.decode('utf-8') if isinstance(data, bytes) else data
    except Exception as e:
        logger.error(f"Deserialization error for type {data_type}: {str(e)}")
        # Return raw data if deserialization fails
        return data


class RedisClient:
    """
    Client for interacting with Redis cache, providing connection management
    and common Redis operations.
    
    This class encapsulates Redis functionality with proper error handling,
    connection management, and serialization/deserialization of data. It provides
    methods for common Redis operations like key-value storage, hashes, lists,
    and pub/sub messaging.
    """
    
    def __init__(self, host: str = None, port: int = None, db: int = 0,
                 password: str = None, socket_timeout: int = None,
                 socket_connect_timeout: int = None, retry_on_timeout: bool = True,
                 decode_responses: bool = False):
        """
        Initializes the Redis client with connection parameters from configuration.
        
        Args:
            host: Redis server hostname or IP (falls back to config if None)
            port: Redis server port (falls back to config if None)
            db: Redis database number (defaults to 0)
            password: Redis password (falls back to config if None)
            socket_timeout: Socket timeout in seconds (falls back to config if None)
            socket_connect_timeout: Connection timeout in seconds (falls back to config if None)
            retry_on_timeout: Whether to retry operations on timeout (defaults to True)
            decode_responses: Whether Redis should decode responses to strings (defaults to False)
        """
        self._redis_client = None
        self._connected = False
        
        # Store connection parameters, using provided values or falling back to config
        self._connection_params = {
            'host': host or REDIS_CONFIG.get('host'),
            'port': port or REDIS_CONFIG.get('port'),
            'db': db,
            'password': password or REDIS_CONFIG.get('password'),
            'socket_timeout': socket_timeout or REDIS_CONFIG.get('socket_timeout'),
            'socket_connect_timeout': socket_connect_timeout or REDIS_CONFIG.get('socket_connect_timeout'),
            'retry_on_timeout': retry_on_timeout,
            'decode_responses': decode_responses,
            'ssl': REDIS_CONFIG.get('ssl', False)
        }
        
        # Remove None values to use Redis defaults
        self._connection_params = {k: v for k, v in self._connection_params.items() if v is not None}
        
        logger.info(f"Initialized Redis client with host={self._connection_params.get('host')}, port={self._connection_params.get('port')}, db={db}")
    
    def connect(self) -> bool:
        """
        Establishes connection to Redis server.
        
        Returns:
            True if connection was successful, False otherwise
        """
        if self._connected and self._redis_client:
            return True
        
        try:
            # Create Redis connection with stored parameters
            self._redis_client = redis.Redis(**self._connection_params)
            
            # Ping Redis server to verify connection
            self._redis_client.ping()
            self._connected = True
            
            logger.info("Successfully connected to Redis server")
            return True
        except redis.RedisError as e:
            error_message = f"Failed to connect to Redis: {str(e)}"
            logger.error(error_message)
            self._connected = False
            self._redis_client = None
            return False
    
    def disconnect(self) -> bool:
        """
        Closes connection to Redis server.
        
        Returns:
            True if disconnect was successful, False otherwise
        """
        if not self._connected or not self._redis_client:
            return True
        
        try:
            # Close Redis connection
            self._redis_client.close()
            self._connected = False
            logger.info("Disconnected from Redis server")
            return True
        except redis.RedisError as e:
            error_message = f"Error while disconnecting from Redis: {str(e)}"
            logger.error(error_message)
            return False
    
    def get(self, key: str, data_type: str = 'str') -> Any:
        """
        Retrieves a value from the cache by key.
        
        Args:
            key: Redis key to retrieve
            data_type: Expected data type for deserialization
            
        Returns:
            The cached value or None if not found
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot get key, not connected to Redis")
            return None
        
        try:
            # Execute Redis GET command for the key
            result = self._redis_client.get(key)
            
            # Return None if key doesn't exist
            if result is None:
                return None
            
            # Deserialize the result
            return deserialize_data(result, data_type)
        except redis.RedisError as e:
            error_message = f"Error retrieving key '{key}' from Redis: {str(e)}"
            logger.error(error_message)
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Sets a value in the cache with optional expiration.
        
        Args:
            key: Redis key to set
            value: Value to store (will be serialized)
            ttl: Time-to-live in seconds (None for no expiration)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot set key, not connected to Redis")
            return False
        
        try:
            # Serialize the value
            serialized_value = serialize_data(value)
            
            # If ttl is provided, use SETEX command
            if ttl is not None:
                self._redis_client.setex(key, ttl, serialized_value)
            else:
                # Otherwise use SET command
                self._redis_client.set(key, serialized_value)
                
            return True
        except redis.RedisError as e:
            error_message = f"Error setting key '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return False
    
    def delete(self, key: str) -> bool:
        """
        Removes a key from the cache.
        
        Args:
            key: Redis key to delete
            
        Returns:
            True if successful (key existed and was deleted), False otherwise
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot delete key, not connected to Redis")
            return False
        
        try:
            # Execute Redis DEL command for the key
            result = self._redis_client.delete(key)
            
            # Redis DEL returns the number of keys that were deleted
            return result > 0
        except redis.RedisError as e:
            error_message = f"Error deleting key '{key}' from Redis: {str(e)}"
            logger.error(error_message)
            return False
    
    def exists(self, key: str) -> bool:
        """
        Checks if a key exists in the cache.
        
        Args:
            key: Redis key to check
            
        Returns:
            True if key exists, False otherwise
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot check key existence, not connected to Redis")
            return False
        
        try:
            # Execute Redis EXISTS command for the key
            result = self._redis_client.exists(key)
            
            # Redis EXISTS returns 1 if key exists, 0 otherwise
            return result > 0
        except redis.RedisError as e:
            error_message = f"Error checking existence of key '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Sets expiration time for a key.
        
        Args:
            key: Redis key to set expiration on
            ttl: Time-to-live in seconds
            
        Returns:
            True if successful (key existed and expiration was set), False otherwise
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot set expiration, not connected to Redis")
            return False
        
        try:
            # Execute Redis EXPIRE command for the key with ttl in seconds
            result = self._redis_client.expire(key, ttl)
            
            # Redis EXPIRE returns 1 if timeout was set, 0 otherwise
            return result > 0
        except redis.RedisError as e:
            error_message = f"Error setting expiration for key '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return False
    
    def ttl(self, key: str) -> int:
        """
        Gets the remaining time to live for a key.
        
        Args:
            key: Redis key to check
            
        Returns:
            Remaining TTL in seconds, -1 if key has no expiry, -2 if key doesn't exist
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot get TTL, not connected to Redis")
            return -2
        
        try:
            # Execute Redis TTL command for the key
            return self._redis_client.ttl(key)
        except redis.RedisError as e:
            error_message = f"Error getting TTL for key '{key}' from Redis: {str(e)}"
            logger.error(error_message)
            return -2
    
    def incr(self, key: str) -> int:
        """
        Increments the integer value of a key by 1.
        
        Args:
            key: Redis key to increment
            
        Returns:
            New value after increment
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot increment key, not connected to Redis")
            return 0
        
        try:
            # Execute Redis INCR command for the key
            return self._redis_client.incr(key)
        except redis.RedisError as e:
            error_message = f"Error incrementing key '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return 0
    
    def hset(self, key: str, field: str, value: Any) -> bool:
        """
        Sets field in the hash stored at key to value.
        
        Args:
            key: Redis hash key
            field: Hash field name
            value: Value to store (will be serialized)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot set hash field, not connected to Redis")
            return False
        
        try:
            # Serialize the value
            serialized_value = serialize_data(value)
            
            # Execute Redis HSET command
            self._redis_client.hset(key, field, serialized_value)
            return True
        except redis.RedisError as e:
            error_message = f"Error setting field '{field}' in hash '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return False
    
    def hget(self, key: str, field: str, data_type: str = 'str') -> Any:
        """
        Gets the value of a hash field stored at key.
        
        Args:
            key: Redis hash key
            field: Hash field name
            data_type: Expected data type for deserialization
            
        Returns:
            The value of the field or None if field or key doesn't exist
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot get hash field, not connected to Redis")
            return None
        
        try:
            # Execute Redis HGET command
            result = self._redis_client.hget(key, field)
            
            # Return None if field doesn't exist
            if result is None:
                return None
            
            # Deserialize the result
            return deserialize_data(result, data_type)
        except redis.RedisError as e:
            error_message = f"Error getting field '{field}' from hash '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return None
    
    def hgetall(self, key: str, data_type: str = 'str') -> Dict[str, Any]:
        """
        Gets all the fields and values in a hash.
        
        Args:
            key: Redis hash key
            data_type: Expected data type for deserialization of values
            
        Returns:
            Dictionary of field/value pairs, or empty dict if key doesn't exist
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot get hash, not connected to Redis")
            return {}
        
        try:
            # Execute Redis HGETALL command
            result = self._redis_client.hgetall(key)
            
            # Return empty dict if hash doesn't exist
            if not result:
                return {}
            
            # Deserialize each value in the result
            deserialized = {}
            for field, value in result.items():
                field_name = field.decode('utf-8') if isinstance(field, bytes) else field
                deserialized[field_name] = deserialize_data(value, data_type)
                
            return deserialized
        except redis.RedisError as e:
            error_message = f"Error getting all fields from hash '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return {}
    
    def lpush(self, key: str, values: List[Any]) -> int:
        """
        Prepends values to a list, creating it if it doesn't exist.
        
        Args:
            key: Redis list key
            values: List of values to push (will be serialized)
            
        Returns:
            Length of the list after the push operation
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot push to list, not connected to Redis")
            return 0
        
        try:
            # Serialize each value in the list
            serialized_values = [serialize_data(value) for value in values]
            
            # Execute Redis LPUSH command with the key and serialized values
            return self._redis_client.lpush(key, *serialized_values)
        except redis.RedisError as e:
            error_message = f"Error pushing values to list '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return 0
    
    def rpush(self, key: str, values: List[Any]) -> int:
        """
        Appends values to a list, creating it if it doesn't exist.
        
        Args:
            key: Redis list key
            values: List of values to push (will be serialized)
            
        Returns:
            Length of the list after the push operation
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot push to list, not connected to Redis")
            return 0
        
        try:
            # Serialize each value in the list
            serialized_values = [serialize_data(value) for value in values]
            
            # Execute Redis RPUSH command with the key and serialized values
            return self._redis_client.rpush(key, *serialized_values)
        except redis.RedisError as e:
            error_message = f"Error pushing values to list '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return 0
    
    def lpop(self, key: str, data_type: str = 'str') -> Any:
        """
        Removes and returns the first element of a list.
        
        Args:
            key: Redis list key
            data_type: Expected data type for deserialization
            
        Returns:
            First element of the list, or None if list is empty or doesn't exist
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot pop from list, not connected to Redis")
            return None
        
        try:
            # Execute Redis LPOP command
            result = self._redis_client.lpop(key)
            
            # Return None if list is empty or doesn't exist
            if result is None:
                return None
            
            # Deserialize the result
            return deserialize_data(result, data_type)
        except redis.RedisError as e:
            error_message = f"Error popping value from list '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return None
    
    def rpop(self, key: str, data_type: str = 'str') -> Any:
        """
        Removes and returns the last element of a list.
        
        Args:
            key: Redis list key
            data_type: Expected data type for deserialization
            
        Returns:
            Last element of the list, or None if list is empty or doesn't exist
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot pop from list, not connected to Redis")
            return None
        
        try:
            # Execute Redis RPOP command
            result = self._redis_client.rpop(key)
            
            # Return None if list is empty or doesn't exist
            if result is None:
                return None
            
            # Deserialize the result
            return deserialize_data(result, data_type)
        except redis.RedisError as e:
            error_message = f"Error popping value from list '{key}' in Redis: {str(e)}"
            logger.error(error_message)
            return None
    
    def publish(self, channel: str, message: Any) -> int:
        """
        Publishes a message to a channel.
        
        Args:
            channel: Redis channel name
            message: Message to publish (will be serialized)
            
        Returns:
            Number of clients that received the message
        """
        if not self._connected and not self.connect():
            logger.warning("Cannot publish message, not connected to Redis")
            return 0
        
        try:
            # Serialize the message
            serialized_message = serialize_data(message)
            
            # Execute Redis PUBLISH command with channel and serialized message
            return self._redis_client.publish(channel, serialized_message)
        except redis.RedisError as e:
            error_message = f"Error publishing message to channel '{channel}' in Redis: {str(e)}"
            logger.error(error_message)
            return 0
    
    def health_check(self) -> bool:
        """
        Performs a health check on the Redis connection.
        
        Returns:
            True if Redis is healthy, False otherwise
        """
        # If not connected, try to connect
        if not self._connected:
            if not self.connect():
                return False
        
        try:
            # Ping Redis server to verify connection is alive
            self._redis_client.ping()
            return True
        except redis.RedisError as e:
            error_message = f"Redis health check failed: {str(e)}"
            logger.error(error_message)
            self._connected = False
            return False