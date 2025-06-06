import logging

from mcp.server.fastmcp import FastMCP
import os
from esp_utils import run_command_async, get_export_script, list_serial_ports

mcp = FastMCP("esp-mcp")

command_history = []

@mcp.tool()
async def build_esp_related_project(project_path: str) -> (str, str):
    """Build an esp project.

    Args:
        project_path: Path to the ESP-IDF project

    Returns:
        str: Build logs
    """
    os.chdir(project_path)
    export_script = get_export_script()
    returncode, stdout, stderr = await run_command_async(f"bash -c 'source {export_script} && idf.py build'")
    open('mcp-process.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"build result {stdout} {stderr}")
    return stdout, stderr


@mcp.tool()
async def setup_project_esp_target(project_path: str, target: str) -> (str, str):
    """
    Sets up the target for an ESP-IDF project before building.

    Args:
        project_path (str): Path to the ESP-IDF project.
        target (str): Lowercase target name, such as 'esp32' or 'esp32c3'.

    Returns:
        Tuple[str, str]: A tuple containing the standard output and standard error.
    """
    os.chdir(project_path)
    export_script = get_export_script()
    returncode, stdout, stderr = await run_command_async(f"bash -c 'source {export_script} && idf.py set-target {target}'")
    open('mcp-set-target.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"build result {stdout} {stderr}")
    return stdout, stderr


@mcp.tool()
async def create_esp_project(project_path: str, project_name: str) -> (str, str):
    """
    Creates a new ESP-IDF project for an ESP chip.

    Args:
        project_path (str): Path where the new ESP-IDF project will be created. 
                            Must be located directly under the current working directory.
        project_name (str): Name of the ESP-IDF project to create.

    Returns:
        Tuple[str, str]: A tuple containing the standard output and standard error messages.
    """
    os.makedirs(project_path, exist_ok=True)
    os.chdir(project_path)
    export_script = get_export_script()
    returncode, stdout, stderr = await run_command_async(f"bash -c 'source {export_script} && idf.py create-project --path {project_path} {project_name}'")
    open('mcp-project-root-path.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"build result {stdout} {stderr}")
    return stdout, stderr


@mcp.tool()
async def flash_esp_project(project_path: str, port: str = None) -> (str, str):
    """Flash built firmware to a connected ESP device.

    Args:
        project_path: Path to the ESP-IDF project
        port: Serial port for the ESP device (optional, auto-detect if not provided)

    Returns:
        tuple: (stdout, stderr) - Flash logs and any error messages
    """
    os.chdir(project_path)
    export_script = get_export_script()
    
    # Build the flash command
    if port:
        flash_cmd = f"bash -c 'source {export_script} && idf.py -p {port} flash'"
    else:
        flash_cmd = f"bash -c 'source {export_script} && idf.py flash'"
    
    returncode, stdout, stderr = await run_command_async(flash_cmd)
    
    # Log the flash operation
    flash_log = f"Flash operation - Return code: {returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
    open('mcp-flash.log', 'w+').write(flash_log)
    logging.warning(f"flash result - return code: {returncode}, stdout: {stdout}, stderr: {stderr}")
    
    return stdout, stderr

@mcp.tool()
async def list_esp_serial_ports() -> (str, str):
    """List available serial ports for ESP devices.

    Returns:
        tuple: (stdout, stderr) - Available serial ports and any error messages
    """
    returncode, stdout, stderr = await list_serial_ports()
    
    # Log the port listing operation
    port_log = f"Port listing - Return code: {returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
    open('mcp-ports.log', 'w+').write(port_log)
    logging.warning(f"port listing result - return code: {returncode}, stdout: {stdout}, stderr: {stderr}")
    
    return stdout, stderr

if __name__ == '__main__':
    mcp.run(transport='stdio')
