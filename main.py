import logging

from mcp.server.fastmcp import FastMCP
import os
from esp_utils import run_command_async, get_export_script

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

if __name__ == '__main__':
    mcp.run(transport='stdio')