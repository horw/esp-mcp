"""
Utility functions for ESP-IDF tools
"""
import os
import asyncio
from typing import Tuple


async def run_command_async(command: str) -> Tuple[int, str, str]:
    """Run a command asynchronously and capture output
    
    Args:
        command: The command to run
        
    Returns:
        Tuple[int, str, str]: Return code, stdout, stderr
    """
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()
    except Exception as e:
        return 1, "", f"Error executing command: {str(e)}"

def get_esp_idf_dir() -> str:
    """Get the ESP-IDF directory path
    
    Returns:
        str: Path to the ESP-IDF directory
    """
    idf_dir = os.environ["IDF_PATH"]
    return idf_dir

def get_export_script() -> str:
    """Get the path to the ESP-IDF export script
    
    Returns:
        str: Path to the export script
    """
    return os.path.join(get_esp_idf_dir(), "export.sh")

def check_esp_idf_installed() -> bool:
    """Check if ESP-IDF is installed
    
    Returns:
        bool: True if ESP-IDF is installed, False otherwise
    """
    return os.path.exists(get_esp_idf_dir())

async def list_serial_ports() -> Tuple[int, str, str]:
    """List available serial ports for ESP devices
    
    Returns:
        Tuple[int, str, str]: Return code, stdout with port list, stderr
    """
    try:
        # Try to use idf.py to list ports (if available)
        process = await asyncio.create_subprocess_shell(
            "python -m serial.tools.list_ports",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()
    except Exception as e:
        # Fallback: try common port patterns
        common_ports = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1", 
                       "/dev/cu.usbserial-*", "/dev/cu.SLAB_USBtoUART", "COM1", "COM2", "COM3"]
        port_info = "Common ESP device ports to try:\n" + "\n".join(common_ports)
        return 0, port_info, f"Note: Could not auto-detect ports. Error: {str(e)}"
