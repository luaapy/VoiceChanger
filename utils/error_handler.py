import logging
import functools
import time
import threading
import traceback
from typing import Callable, Any
import sys
import os
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("VoiceChanger")

def safe_thread_run(error_event: threading.Event = None, auto_recovery: bool = True) -> Callable:
    """
    Decorator to wrap thread functions with try-catch blocks.
    Handles logging and optional error event signaling.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.critical(f"Thread crashed: {func.__name__} - {str(e)}")
                logger.debug(traceback.format_exc())
                
                if error_event:
                    error_event.set()
                
                if auto_recovery and config.AUTO_RECOVERY:
                    logger.info(f"Attempting auto-recovery for {func.__name__}...")
                    # In a real scenario, we might want to trigger a restart callback here
                    # For now, we rely on the main monitoring thread to notice the crash if needed
                    # or the thread might loop internally. 
                    # If this decorator wraps the entire run method, the thread dies.
                    pass 
                return None
        return wrapper
    return decorator

class ErrorTracker:
    """Tracks errors to prevent log flooding and manage recovery"""
    def __init__(self):
        self.error_counts = {}
        self.last_error_time = {}
        self._lock = threading.Lock()
    
    def log_error(self, source: str, message: str, level=logging.ERROR):
        with self._lock:
            now = time.time()
            # Reset count if last error was long ago (>1 min)
            if now - self.last_error_time.get(source, 0) > 60:
                self.error_counts[source] = 0
            
            self.error_counts[source] = self.error_counts.get(source, 0) + 1
            self.last_error_time[source] = now
            
            # Only log if under threshold or every 10th error
            if self.error_counts[source] <= 3 or self.error_counts[source] % 10 == 0:
                logger.log(level, f"[{source}] {message} (Count: {self.error_counts[source]})")
