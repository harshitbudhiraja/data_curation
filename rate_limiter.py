"""Thread-safe global rate limiter for parallel API calls."""
import time
import threading
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class GlobalRateLimiter:
    """Thread-safe rate limiter for parallel workers."""
    
    def __init__(self, requests_per_minute=10, min_interval=6.0):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            min_interval: Minimum seconds between ANY requests (prevents bursts)
        """
        self.requests_per_minute = requests_per_minute
        self.min_interval = min_interval
        self.request_times = []
        self.lock = threading.Lock()
        self.last_request = 0
    
    def acquire(self):
        """Wait until it's safe to make a request (thread-safe)."""
        with self.lock:
            now = time.time()
            
            # Enforce minimum interval between ANY requests (prevents bursts)
            time_since_last = now - self.last_request
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                logger.info(f"⏱️  Rate limit: waiting {wait_time:.1f}s between requests")
                time.sleep(wait_time)
                now = time.time()
            
            # Clean old requests (older than 1 minute)
            cutoff = datetime.now() - timedelta(minutes=1)
            self.request_times = [
                t for t in self.request_times 
                if t > cutoff
            ]
            
            # Check per-minute limit
            if len(self.request_times) >= self.requests_per_minute:
                oldest = self.request_times[0]
                wait_seconds = 60 - (datetime.now() - oldest).total_seconds() + 1
                if wait_seconds > 0:
                    logger.warning(f"⏱️  Per-minute limit reached: waiting {wait_seconds:.1f}s")
                    time.sleep(wait_seconds)
            
            # Record this request
            self.request_times.append(datetime.now())
            self.last_request = time.time()


# Global instance shared across all workers
_global_limiter = GlobalRateLimiter(requests_per_minute=10, min_interval=6.0)


def get_rate_limiter():
    """Get the global rate limiter instance."""
    return _global_limiter
