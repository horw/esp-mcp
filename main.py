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


@mcp.tool()
async def clean_esp_project(project_path: str, full_clean: bool = False) -> (str, str):
    """Clean build artifacts from an ESP-IDF project.

    Args:
        project_path: Path to the ESP-IDF project
        full_clean: If True, performs fullclean (removes build dir entirely).
                   If False, performs regular clean.

    Returns:
        tuple: (stdout, stderr) - Clean operation logs
    """
    os.chdir(project_path)
    export_script = get_export_script()
    
    clean_cmd = "fullclean" if full_clean else "clean"
    returncode, stdout, stderr = await run_command_async(
        f"bash -c 'source {export_script} && idf.py {clean_cmd}'"
    )
    
    open('mcp-clean.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"clean result {stdout} {stderr}")
    return stdout, stderr


@mcp.tool()
async def get_esp_project_size(project_path: str) -> (str, str):
    """Analyze the size of a built ESP-IDF project firmware.

    Args:
        project_path: Path to the ESP-IDF project (must be built first)

    Returns:
        tuple: (stdout, stderr) - Size analysis output showing RAM/Flash usage
    """
    os.chdir(project_path)
    export_script = get_export_script()
    
    returncode, stdout, stderr = await run_command_async(
        f"bash -c 'source {export_script} && idf.py size'"
    )
    
    open('mcp-size.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"size result {stdout} {stderr}")
    return stdout, stderr


@mcp.tool()
async def get_esp_component_size(project_path: str) -> (str, str):
    """Get detailed per-component size breakdown of an ESP-IDF project.

    Args:
        project_path: Path to the ESP-IDF project (must be built first)

    Returns:
        tuple: (stdout, stderr) - Detailed component size breakdown
    """
    os.chdir(project_path)
    export_script = get_export_script()
    
    returncode, stdout, stderr = await run_command_async(
        f"bash -c 'source {export_script} && idf.py size-components'"
    )
    
    open('mcp-size-components.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"size-components result {stdout} {stderr}")
    return stdout, stderr


@mcp.tool()
async def erase_esp_flash(project_path: str, port: str = None) -> (str, str):
    """Erase the entire flash memory of a connected ESP device.

    WARNING: This will erase all data on the device including firmware,
    NVS storage, and any other flash contents.

    Args:
        project_path: Path to any ESP-IDF project (used for idf.py context)
        port: Serial port for the ESP device (optional, auto-detect if not provided)

    Returns:
        tuple: (stdout, stderr) - Erase operation logs
    """
    os.chdir(project_path)
    export_script = get_export_script()
    
    if port:
        erase_cmd = f"bash -c 'source {export_script} && idf.py -p {port} erase-flash'"
    else:
        erase_cmd = f"bash -c 'source {export_script} && idf.py erase-flash'"
    
    returncode, stdout, stderr = await run_command_async(erase_cmd)
    
    open('mcp-erase.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"erase-flash result {stdout} {stderr}")
    return stdout, stderr


@mcp.tool()
async def monitor_esp_device(project_path: str, port: str = None, timeout_seconds: int = 30) -> (str, str):
    """Monitor serial output from a connected ESP device.

    Note: This captures output for a limited time since MCP tools can't run indefinitely.
    For interactive monitoring, use idf.py monitor directly in a terminal.

    Args:
        project_path: Path to the ESP-IDF project
        port: Serial port for the ESP device (optional, auto-detect if not provided)
        timeout_seconds: How long to capture output (default: 30 seconds, max: 120)

    Returns:
        tuple: (stdout, stderr) - Captured serial output
    """
    os.chdir(project_path)
    export_script = get_export_script()
    
    # Cap timeout to prevent runaway processes
    timeout_seconds = min(timeout_seconds, 120)
    
    if port:
        monitor_cmd = f"bash -c 'source {export_script} && timeout {timeout_seconds} idf.py -p {port} monitor || true'"
    else:
        monitor_cmd = f"bash -c 'source {export_script} && timeout {timeout_seconds} idf.py monitor || true'"
    
    returncode, stdout, stderr = await run_command_async(monitor_cmd)
    
    open('mcp-monitor.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"monitor result (captured {timeout_seconds}s) {stdout} {stderr}")
    return stdout, stderr


@mcp.tool()
async def get_esp_app_info(project_path: str) -> (str, str):
    """Get information about the built ESP-IDF application.

    Args:
        project_path: Path to the ESP-IDF project (must be built first)

    Returns:
        tuple: (stdout, stderr) - App information including version, IDF version, etc.
    """
    os.chdir(project_path)
    export_script = get_export_script()
    
    # Get project description from build
    returncode, stdout, stderr = await run_command_async(
        f"bash -c 'source {export_script} && idf.py reconfigure 2>/dev/null; cat build/project_description.json 2>/dev/null || echo \"Project not built yet\"'"
    )
    
    open('mcp-app-info.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"app-info result {stdout} {stderr}")
    return stdout, stderr


if __name__ == '__main__':
    mcp.run(transport='stdio')
