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
    return os.path.join(idf_dir, "esp-idf")

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
