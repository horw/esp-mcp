"""
Configuration module for ESP MCP Server
Centralized configuration management to avoid hardcoded values
"""
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MCPConfig:
    """Configuration class for ESP MCP Server"""
    
    # MCP Server Information
    PROTOCOL_VERSION = "2024-11-05"
    SERVER_VERSION = "1.0.0"
    SERVER_NAME = "esp-mcp"
    
    # Command Execution Settings
    DEFAULT_COMMAND_TIMEOUT = 300  # seconds (5 minutes)
    SERIAL_PORT_TIMEOUT = 10  # seconds
    GDB_TIMEOUT = 600  # seconds (10 minutes for GDB)
    
    # Serial Port Settings
    DEFAULT_FLASH_BAUD = 460800
    DEFAULT_MONITOR_BAUD = 115200
    
    # Common Serial Ports (fallback list)
    COMMON_SERIAL_PORTS = [
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6",
        "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1",
        "/dev/cu.usbserial-*", "/dev/cu.SLAB_USBtoUART"
    ]
    
    # Windows Fallback Paths
    DEFAULT_SYSTEM_ROOT = r"C:\Windows"
    MODE_COM_PATH = os.path.join("System32", "mode.com")
    
    # Result Limits (for analysis tools)
    MAX_ERRORS = 20
    MAX_WARNINGS = 20
    MAX_SYMBOLS = 50
    MAX_ADDED_CONFIGS = 50
    MAX_REMOVED_CONFIGS = 50
    MAX_MODIFIED_CONFIGS = 100
    MAX_LOG_ENTRIES = 200
    MAX_CRASHES = 10
    MAX_ERRORS_LOG = 20
    
    # Display Settings
    LOG_DEBUG_LENGTH = 200  # Characters to show in debug logs
    TIME_FORMAT_MINUTES = "{minutes}m {seconds}s"
    TIME_FORMAT_SECONDS = "{seconds}s"
    
    # Encoding Settings
    DEFAULT_ENCODING = 'utf-8'
    ENCODING_ERRORS = 'replace'
    
    # File Operation Limits
    DEFAULT_READ_LINES = 100
    
    @classmethod
    def load_from_env(cls) -> 'MCPConfig':
        """Load configuration from environment variables
        
        Environment variables:
        - ESP_MCP_TIMEOUT: Default command timeout in seconds
        - ESP_MCP_SERIAL_TIMEOUT: Serial port timeout in seconds
        - ESP_MCP_FLASH_BAUD: Default flash baud rate
        - ESP_MCP_MONITOR_BAUD: Default monitor baud rate
        - ESP_MCP_MAX_ERRORS: Maximum errors to return in analysis
        - ESP_MCP_MAX_WARNINGS: Maximum warnings to return in analysis
        
        Returns:
            MCPConfig: Configuration instance with environment overrides
        """
        config = cls()
        
        # Load timeout settings
        if 'ESP_MCP_TIMEOUT' in os.environ:
            try:
                value = int(os.environ['ESP_MCP_TIMEOUT'])
                if value > 0:
                    config.DEFAULT_COMMAND_TIMEOUT = value
                    logger.debug(f"Loaded timeout from env: {config.DEFAULT_COMMAND_TIMEOUT}s")
                else:
                    logger.warning("Invalid ESP_MCP_TIMEOUT value (must be > 0), using default")
            except ValueError:
                logger.warning("Invalid ESP_MCP_TIMEOUT value, using default")
        
        if 'ESP_MCP_SERIAL_TIMEOUT' in os.environ:
            try:
                value = int(os.environ['ESP_MCP_SERIAL_TIMEOUT'])
                if value > 0:
                    config.SERIAL_PORT_TIMEOUT = value
                    logger.debug(f"Loaded serial timeout from env: {config.SERIAL_PORT_TIMEOUT}s")
                else:
                    logger.warning("Invalid ESP_MCP_SERIAL_TIMEOUT value (must be > 0), using default")
            except ValueError:
                logger.warning("Invalid ESP_MCP_SERIAL_TIMEOUT value, using default")
        
        # Load baud rate settings
        if 'ESP_MCP_FLASH_BAUD' in os.environ:
            try:
                value = int(os.environ['ESP_MCP_FLASH_BAUD'])
                if value > 0:
                    config.DEFAULT_FLASH_BAUD = value
                    logger.debug(f"Loaded flash baud from env: {config.DEFAULT_FLASH_BAUD}")
                else:
                    logger.warning("Invalid ESP_MCP_FLASH_BAUD value (must be > 0), using default")
            except ValueError:
                logger.warning("Invalid ESP_MCP_FLASH_BAUD value, using default")
        
        if 'ESP_MCP_MONITOR_BAUD' in os.environ:
            try:
                value = int(os.environ['ESP_MCP_MONITOR_BAUD'])
                if value > 0:
                    config.DEFAULT_MONITOR_BAUD = value
                    logger.debug(f"Loaded monitor baud from env: {config.DEFAULT_MONITOR_BAUD}")
                else:
                    logger.warning("Invalid ESP_MCP_MONITOR_BAUD value (must be > 0), using default")
            except ValueError:
                logger.warning("Invalid ESP_MCP_MONITOR_BAUD value, using default")
        
        # Load limit settings
        if 'ESP_MCP_MAX_ERRORS' in os.environ:
            try:
                value = int(os.environ['ESP_MCP_MAX_ERRORS'])
                if value > 0:
                    config.MAX_ERRORS = value
                    logger.debug(f"Loaded max errors from env: {config.MAX_ERRORS}")
                else:
                    logger.warning("Invalid ESP_MCP_MAX_ERRORS value (must be > 0), using default")
            except ValueError:
                logger.warning("Invalid ESP_MCP_MAX_ERRORS value, using default")
        
        if 'ESP_MCP_MAX_WARNINGS' in os.environ:
            try:
                value = int(os.environ['ESP_MCP_MAX_WARNINGS'])
                if value > 0:
                    config.MAX_WARNINGS = value
                    logger.debug(f"Loaded max warnings from env: {config.MAX_WARNINGS}")
                else:
                    logger.warning("Invalid ESP_MCP_MAX_WARNINGS value (must be > 0), using default")
            except ValueError:
                logger.warning("Invalid ESP_MCP_MAX_WARNINGS value, using default")
        
        return config
    
    @classmethod
    def get_system_root(cls) -> str:
        """Get Windows SystemRoot path
        
        Returns:
            str: SystemRoot path from environment or default
        """
        return os.environ.get("SystemRoot", cls.DEFAULT_SYSTEM_ROOT)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return {
            'server': {
                'name': self.SERVER_NAME,
                'version': self.SERVER_VERSION,
                'protocol_version': self.PROTOCOL_VERSION
            },
            'timeouts': {
                'command': self.DEFAULT_COMMAND_TIMEOUT,
                'serial_port': self.SERIAL_PORT_TIMEOUT,
                'gdb': self.GDB_TIMEOUT
            },
            'serial': {
                'flash_baud': self.DEFAULT_FLASH_BAUD,
                'monitor_baud': self.DEFAULT_MONITOR_BAUD,
                'common_ports': self.COMMON_SERIAL_PORTS
            },
            'limits': {
                'max_errors': self.MAX_ERRORS,
                'max_warnings': self.MAX_WARNINGS,
                'max_symbols': self.MAX_SYMBOLS,
                'max_added_configs': self.MAX_ADDED_CONFIGS,
                'max_removed_configs': self.MAX_REMOVED_CONFIGS,
                'max_modified_configs': self.MAX_MODIFIED_CONFIGS,
                'max_log_entries': self.MAX_LOG_ENTRIES,
                'max_crashes': self.MAX_CRASHES,
                'max_errors_log': self.MAX_ERRORS_LOG
            },
            'display': {
                'log_debug_length': self.LOG_DEBUG_LENGTH,
                'time_format_minutes': self.TIME_FORMAT_MINUTES,
                'time_format_seconds': self.TIME_FORMAT_SECONDS
            },
            'encoding': {
                'default': self.DEFAULT_ENCODING,
                'errors': self.ENCODING_ERRORS
            }
        }


# Global configuration instance
config = MCPConfig.load_from_env()


def get_config() -> MCPConfig:
    """Get the global configuration instance
    
    Returns:
        MCPConfig: Global configuration instance
    """
    return config