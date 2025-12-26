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

def get_esp_idf_dir(idf_path: str = None) -> str:
    """Get the ESP-IDF directory path

    Args:
        idf_path: Optional path to ESP-IDF directory. If None or empty, uses IDF_PATH environment variable.

    Returns:
        str: Path to the ESP-IDF directory

    Raises:
        ValueError: If idf_path is not provided and IDF_PATH environment variable is not set
    """
    if idf_path:
        return idf_path
    if "IDF_PATH" in os.environ:
        return os.environ["IDF_PATH"]
    raise ValueError("IDF_PATH must be provided either as parameter or environment variable")

def get_export_script(idf_path: str = None) -> str:
    """Get the path to the ESP-IDF export script

    Args:
        idf_path: Optional path to ESP-IDF directory. If None or empty, uses IDF_PATH environment variable.

    Returns:
        str: Path to the export script
    """
    return os.path.join(get_esp_idf_dir(idf_path), "export.sh")

def check_esp_idf_installed(idf_path: str = None) -> bool:
    """Check if ESP-IDF is installed

    Args:
        idf_path: Optional path to ESP-IDF directory. If None or empty, uses IDF_PATH environment variable.

    Returns:
        bool: True if ESP-IDF is installed, False otherwise
    """
    try:
        return os.path.exists(get_esp_idf_dir(idf_path))
    except ValueError:
        return False

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
