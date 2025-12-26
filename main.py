import logging
import shlex
import time
from typing import Tuple

from mcp.server.fastmcp import FastMCP
import os
from esp_utils import run_command_async, get_export_script, list_serial_ports, get_esp_idf_dir

mcp = FastMCP("esp-mcp")

@mcp.tool()
async def build_esp_project(project_path: str, idf_path: str = None, sdkconfig_defaults: str = None) -> Tuple[str, str]:
    """Build an ESP-IDF project. Can Incremental Build. Similar to `idf.py build`.

    Args:
        project_path: Path to the project.
        idf_path: Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set.
                  - If None or empty: uses IDF_PATH environment variable
                  - If provided: uses the specified path, allowing different projects to use different ESP-IDF versions.
        sdkconfig_defaults: Optional sdkconfig defaults files. Multiple files can be specified separated by semicolons.
                           Example: "sdkconfig.defaults;sdkconfig.ci.release"
                           - If provided: uses the specified sdkconfig defaults files. This will cause reconfigure and full rebuild.
                           - If None: uses default incremental build behavior.
                           Note: Only use this parameter when you need to modify config. For incremental builds, omit this parameter.

    Returns:
        tuple: (stdout, stderr) - Build logs and error messages. Time information is included in stdout.
    """
    start_time = time.time()
    os.chdir(project_path)
    export_script = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)

    # Build command with optional sdkconfig_defaults
    if sdkconfig_defaults and sdkconfig_defaults.strip():
        # Use shlex.quote to properly escape the value for shell
        quoted_defaults = shlex.quote(sdkconfig_defaults)
        build_cmd = f"idf.py build -DSDKCONFIG_DEFAULTS={quoted_defaults}"
    else:
        build_cmd = "idf.py build"

    # Use double quotes for the outer command to allow single quotes in build_cmd
    returncode, stdout, stderr = await run_command_async(f'bash -c "source {export_script} && {build_cmd}"')

    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    elapsed_minutes = int(elapsed_time // 60)
    elapsed_seconds = elapsed_time % 60

    # Add timing information to stdout
    timing_info = f"\n\n[Build completed in {elapsed_minutes}m {elapsed_seconds:.2f}s ({elapsed_time:.2f} seconds)]\n"
    stdout_with_timing = stdout + timing_info

    open('mcp-process.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"build result - elapsed: {elapsed_time:.2f}s, return code: {returncode}, stdout: {stdout[:200]}..., stderr: {stderr[:200]}...")
    return stdout_with_timing, stderr


@mcp.tool()
async def setup_project_esp_target(project_path: str, target: str, idf_path: str = None) -> Tuple[str, str]:
    """
    Sets up the target for an ESP-IDF project before building.

    Args:
        project_path (str): Path to the ESP-IDF project.
        target (str): Lowercase target name, such as 'esp32' or 'esp32c3'.
        idf_path: Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set.
                  - If None or empty: uses IDF_PATH environment variable
                  - If provided: uses the specified path, allowing different projects to use different ESP-IDF versions.

    Returns:
        Tuple[str, str]: A tuple containing the standard output and standard error.
    """
    logging.warning(f"setup_project_esp_target called with idf_path={idf_path}, project_path={project_path}, target={target}")
    os.chdir(project_path)
    # Process idf_path parameter
    processed_idf_path = idf_path if (idf_path and idf_path.strip()) else None
    logging.warning(f"processed_idf_path={processed_idf_path}")
    export_script = get_export_script(processed_idf_path)
    returncode, stdout, stderr = await run_command_async(f"bash -c 'source {export_script} && idf.py set-target {target}'")
    open('mcp-set-target.log', 'w+').write(str((stdout, stderr)))
    logging.warning(f"build result {stdout} {stderr}")
    return stdout, stderr


@mcp.tool()
async def create_esp_project(project_path: str, project_name: str) -> Tuple[str, str]:
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
async def flash_esp_project(project_path: str, port: str = None) -> Tuple[str, str]:
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
async def list_esp_serial_ports() -> Tuple[str, str]:
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
async def run_esp_idf_install(idf_path: str = None) -> Tuple[str, str]:
    """Run the install.sh script in the ESP-IDF directory to install ESP-IDF dependencies and toolchain.

    Args:
        idf_path: Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set.
                  - If None or empty: uses IDF_PATH environment variable
                  - If provided: uses the specified path, allowing different projects to use different ESP-IDF versions.

    Returns:
        tuple: (stdout, stderr) - Installation logs and any error messages
    """
    start_time = time.time()

    # Get ESP-IDF directory path
    try:
        esp_idf_dir = get_esp_idf_dir(idf_path if (idf_path and idf_path.strip()) else None)
    except ValueError as e:
        error_msg = str(e)
        logging.error(f"Failed to get ESP-IDF directory: {error_msg}")
        return "", error_msg

    # Build path to install.sh
    install_script = os.path.join(esp_idf_dir, "install.sh")

    # Check if install.sh exists
    if not os.path.exists(install_script):
        error_msg = f"install.sh not found at {install_script}. Please verify the ESP-IDF path is correct."
        logging.error(error_msg)
        return "", error_msg

    # Change to ESP-IDF directory and execute install.sh
    original_dir = os.getcwd()
    try:
        os.chdir(esp_idf_dir)
        returncode, stdout, stderr = await run_command_async(f"bash {install_script}")

        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        elapsed_minutes = int(elapsed_time // 60)
        elapsed_seconds = elapsed_time % 60

        # Add timing information to stdout
        timing_info = f"\n\n[Installation completed in {elapsed_minutes}m {elapsed_seconds:.2f}s ({elapsed_time:.2f} seconds)]\n"
        stdout_with_timing = stdout + timing_info

        # Log the installation operation
        install_log = f"ESP-IDF installation - Elapsed time: {elapsed_time:.2f}s ({elapsed_minutes}m {elapsed_seconds:.2f}s)\nReturn code: {returncode}\nESP-IDF path: {esp_idf_dir}\nInstall script: {install_script}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        open('mcp-install.log', 'w+').write(install_log)
        logging.warning(f"install.sh result - elapsed: {elapsed_time:.2f}s, return code: {returncode}, stdout: {stdout[:200]}..., stderr: {stderr[:200]}...")

        return stdout_with_timing, stderr
    finally:
        os.chdir(original_dir)

@mcp.tool()
async def run_pytest(project_path: str, test_path: str = ".", pytest_args: str = "", idf_path: str = None) -> Tuple[str, str]:
    """Run pytest tests in a project. Supports pytest-embedded for ESP-IDF/ESP32 testing.

    This tool uses pytest-embedded (https://espressif-docs.readthedocs-hosted.com/projects/pytest-embedded/en/latest/),
    which is a pytest plugin framework for embedded testing. For ESP-IDF projects, it provides support for running tests
    on ESP32, ESP32-C3, ESP32-S3, and other ESP targets.

    Args:
        project_path: Path to the project directory containing tests
        test_path: Path to test file or directory (default: ".", runs all tests)
        pytest_args: Additional pytest arguments. Common options:
                     - -v: Verbose output
                     - -k EXPRESSION: Run tests matching the expression
                     - -m MARKER: Run tests with specific marker
                     - --target TARGET: Specify ESP target (esp32, esp32c3, esp32s3, esp32c6, esp32h2)
                     - --sdkconfig PATH: Specify sdkconfig config name
        idf_path: Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set.
                  - If None or empty: uses IDF_PATH environment variable
                  - If provided: uses the specified path, allowing different projects to use different ESP-IDF versions.

    Returns:
        tuple: (stdout, stderr) - Test results and any error messages
    """
    original_dir = os.getcwd()
    try:
        os.chdir(project_path)

        # Get ESP-IDF export script
        export_script = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)

        # Build pytest command with environment setup
        pytest_cmd = f"pytest {test_path}"
        if pytest_args:
            pytest_cmd += f" {pytest_args}"

        full_cmd = f"bash -c 'source {export_script} && {pytest_cmd}'"

        returncode, stdout, stderr = await run_command_async(full_cmd)

        # Log the pytest operation
        pytest_log = f"Pytest execution - Return code: {returncode}\nCommand: {full_cmd}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        open('mcp-pytest.log', 'w+').write(pytest_log)
        logging.warning(f"pytest result - return code: {returncode}, stdout: {stdout}, stderr: {stderr}")

        return stdout, stderr
    finally:
        os.chdir(original_dir)

if __name__ == '__main__':
    mcp.run(transport='stdio')
