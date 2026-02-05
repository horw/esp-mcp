"""
Utility functions for ESP-IDF tools
"""
import os
import logging
from typing import Tuple
from config import get_config

logger = logging.getLogger(__name__)

# Get global configuration
cfg = get_config()


def run_command_async(command: str) -> Tuple[int, str, str]:
    """Run a command and capture output

    Args:
        command: The command to run

    Returns:
        Tuple[int, str, str]: Return code, stdout, stderr
    """
    import subprocess
    
    try:
        # Use subprocess.run for synchronous execution
        # Use UTF-8 encoding with error handling for cross-platform compatibility
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding=cfg.DEFAULT_ENCODING,
            errors=cfg.ENCODING_ERRORS,
            timeout=cfg.DEFAULT_COMMAND_TIMEOUT
        )
        
        logger.debug(f"Command executed: {command}")
        logger.debug(f"Return code: {result.returncode}")
        logger.debug(f"Stdout: {result.stdout[:cfg.LOG_DEBUG_LENGTH]}...")
        logger.debug(f"Stderr: {result.stderr[:cfg.LOG_DEBUG_LENGTH]}...")
        
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timeout: {e}")
        return 1, "", f"Command timeout after {cfg.DEFAULT_COMMAND_TIMEOUT} seconds: {str(e)}"
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return 1, "", f"Error executing command: {str(e)}"

def get_esp_idf_dir(idf_path: str = None) -> str:
    """Get the ESP-IDF directory path

    Args:
        idf_path: Optional path to ESP-IDF directory. If None or empty, uses IDF_PATH environment variable.

    Returns:
        str: Path to the ESP-IDF directory

    Raises:
        ValueError: If idf_path is not provided and IDF_PATH environment variable is not set
    """
    if idf_path and idf_path.strip():
        # Normalize the path
        normalized_path = os.path.abspath(os.path.expanduser(idf_path.strip()))
        logger.info(f"Using provided ESP-IDF path: {normalized_path}")
        return normalized_path
    
    if "IDF_PATH" in os.environ and os.environ["IDF_PATH"].strip():
        normalized_path = os.path.abspath(os.path.expanduser(os.environ["IDF_PATH"].strip()))
        logger.info(f"Using ESP-IDF path from environment variable: {normalized_path}")
        return normalized_path
    
    error_msg = "IDF_PATH must be provided either as parameter or environment variable. Please set the IDF_PATH environment variable to point to your ESP-IDF installation directory."
    logger.error(error_msg)
    raise ValueError(error_msg)

def convert_to_bash_path(windows_path: str) -> str:
    """Convert Windows path to Git Bash-compatible path
    
    Args:
        windows_path: Windows path (e.g., 'E:\\path\\to\\file' or 'E:/path/to/file')
    
    Returns:
        str: Git Bash-compatible path (e.g., '/e/path/to/file')
    """
    # Normalize to forward slashes first
    normalized = windows_path.replace('\\', '/')
    
    # Check if it's an absolute Windows path with drive letter
    if len(normalized) >= 2 and normalized[1] == ':':
        # E:/path -> /e/path
        return '/' + normalized[0].lower() + normalized[2:]
    
    return normalized


def get_export_script(idf_path: str = None) -> str:
    """Get path to ESP-IDF export script

    Args:
        idf_path: Optional path to ESP-IDF directory. If None or empty, uses IDF_PATH environment variable.

    Returns:
        str: Path to export script
    
    Raises:
        FileNotFoundError: If export.sh script is not found
    """
    esp_idf_dir = get_esp_idf_dir(idf_path)
    export_script = os.path.join(esp_idf_dir, "export.sh")
    
    if not os.path.exists(export_script):
        error_msg = f"ESP-IDF export script not found at: {export_script}. Please verify your ESP-IDF installation."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Convert Windows path to bash-compatible path for Git Bash
    if os.name == 'nt':
        export_script_bash = convert_to_bash_path(export_script)
        logger.debug(f"Using export script (converted for bash): {export_script_bash}")
        return export_script_bash
    
    logger.debug(f"Using export script: {export_script}")
    return export_script

def check_esp_idf_installed(idf_path: str = None) -> bool:
    """Check if ESP-IDF is installed

    Args:
        idf_path: Optional path to ESP-IDF directory. If None or empty, uses IDF_PATH environment variable.

    Returns:
        bool: True if ESP-IDF is installed, False otherwise
    """
    try:
        esp_idf_dir = get_esp_idf_dir(idf_path)
        is_installed = os.path.exists(esp_idf_dir)
        logger.info(f"ESP-IDF installed check: {is_installed} at {esp_idf_dir}")
        return is_installed
    except ValueError as e:
        logger.warning(f"ESP-IDF installation check failed: {e}")
        return False

def list_serial_ports() -> Tuple[int, str, str]:
    """List available serial ports for ESP devices

    Returns:
        Tuple[int, str, str]: Return code, stdout with port list, stderr
    """
    import subprocess
    
    try:
        # Try to list COM ports on Windows using mode command
        if os.name == 'nt':  # Windows
            # Use fully-qualified path to prevent command hijacking
            # Check if mode.com exists in System32 first
            system_root = cfg.get_system_root()
            mode_com_path = os.path.join(system_root, cfg.MODE_COM_PATH)
            
            # Use fully-qualified path if it exists, otherwise fall back to "mode"
            if os.path.exists(mode_com_path):
                command = [mode_com_path]
                logger.debug(f"Using fully-qualified mode.com path: {mode_com_path}")
            else:
                command = ["mode"]
                logger.debug("Using fallback 'mode' command")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding=cfg.DEFAULT_ENCODING,
                errors=cfg.ENCODING_ERRORS,
                timeout=cfg.SERIAL_PORT_TIMEOUT
            )
            if result.returncode == 0:
                # Parse COM ports from mode output
                lines = result.stdout.split('\n')
                com_ports = []
                for line in lines:
                    if 'COM' in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith('COM'):
                                com_ports.append(part)
                if com_ports:
                    port_list = '\n'.join(com_ports)
                    logger.debug(f"Found COM ports: {com_ports}")
                    return 0, f"Available serial ports:\n{port_list}", ""
        
        # Try pyserial if available
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            if ports:
                port_list = '\n'.join([f"{port.device} - {port.description}" for port in ports])
                logger.debug(f"Found serial ports via pyserial: {len(ports)}")
                return 0, f"Available serial ports:\n{port_list}", ""
        except ImportError:
            pass
        
        # Fallback: try common port patterns
        logger.warning("Using fallback port list")
        port_info = "Common ESP device ports to try:\n" + "\n".join(cfg.COMMON_SERIAL_PORTS)
        return 0, port_info, "Note: Could not auto-detect ports, showing common ports"
        
    except Exception as e:
        # Fallback: try common port patterns
        logger.warning(f"Failed to list serial ports: {e}")
        port_info = "Common ESP device ports to try:\n" + "\n".join(cfg.COMMON_SERIAL_PORTS)
        return 0, port_info, f"Note: Could not auto-detect ports. Error: {str(e)}"
