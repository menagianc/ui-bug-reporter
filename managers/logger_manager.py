import logging
import os
import sys
from datetime import datetime


class LoggerManager:
    """
    A flexible logging manager class that can be used throughout the application.
    It allows for enabling/disabling logging and supports different log levels.
    """
    
    # Log levels
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        # Singleton pattern
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_dir="logs", log_level=logging.INFO, enabled=True):
        # Initialize only once
        if self._initialized:
            return
            
        self._initialized = True
        self.enabled = enabled
        self.log_level = log_level
        self.log_dir = log_dir
        self.logger = None
        
        if enabled:
            self._setup_logger()
    
    def _setup_logger(self):
        """Set up the logger with the appropriate configuration"""
        # Create logger
        self.logger = logging.getLogger("bug_validator")
        self.logger.setLevel(self.log_level)
        
        # Create log directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # File handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"bug_validator_{timestamp}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.log_level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.info(f"Logging initialized at {log_file}")
    
    def enable(self):
        """Enable logging"""
        if not self.enabled:
            self.enabled = True
            self._setup_logger()
    
    def disable(self):
        """Disable logging"""
        self.enabled = False
        if self.logger:
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            self.logger = None
    
    def set_level(self, level):
        """Set the logging level"""
        self.log_level = level
        if self.logger:
            self.logger.setLevel(level)
            for handler in self.logger.handlers:
                handler.setLevel(level)
    
    def debug(self, message):
        """Log a debug message"""
        if self.enabled and self.logger:
            self.logger.debug(message)
    
    def info(self, message):
        """Log an info message"""
        if self.enabled and self.logger:
            self.logger.info(message)
    
    def warning(self, message):
        """Log a warning message"""
        if self.enabled and self.logger:
            self.logger.warning(message)
    
    def error(self, message):
        """Log an error message"""
        if self.enabled and self.logger:
            self.logger.error(message)
    
    def critical(self, message):
        """Log a critical message"""
        if self.enabled and self.logger:
            self.logger.critical(message) 