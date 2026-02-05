#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESP MCP Server - Synchronous implementation (like cheat-engine)"""

import json
import shlex
import time
import sys
import os
import io
import traceback
from typing import Any, Optional

from esp_utils import run_command_async, get_export_script, list_serial_ports, get_esp_idf_dir
from config import get_config

# Load configuration
cfg = get_config()

# Configure stdio for proper MCP communication
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', newline='\n')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configure logging to stderr for proper MCP communication
import logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)


# ============ Logger ============
class Logger:
    @staticmethod
    def log(msg: str, level: str = "INFO"):
        sys.stderr.write(f"[ESP-MCP-{level}] {msg}\n")
        sys.stderr.flush()
    
    @staticmethod
    def info(msg: str): Logger.log(msg, "INFO")
    
    @staticmethod
    def error(msg: str): Logger.log(msg, "ERROR")

log = Logger()


# ============ Tool Definitions ============
TOOLS = [
    {
        "name": "build_esp_project",
        "description": "Build an ESP-IDF project. Can Incremental Build. Similar to `idf.py build`.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to project."
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                },
                "sdkconfig_defaults": {
                    "type": "string",
                    "description": "Optional sdkconfig defaults files separated by semicolons."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "clean_esp_project",
        "description": "Clean build files from an ESP-IDF project. Similar to `idf.py fullclean`.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "full_clean": {
                    "type": "boolean",
                    "description": "Perform full clean (remove build directory). Default: false."
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "erase_flash_esp",
        "description": "Erase flash memory on ESP device. Similar to `idf.py erase-flash`.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "port": {
                    "type": "string",
                    "description": "Serial port for ESP device (optional, auto-detect if not provided)"
                },
                "baud": {
                    "type": "integer",
                    "description": "Baud rate for flashing (default: 460800)"
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "monitor_esp",
        "description": "Monitor serial output from ESP device. Similar to `idf.py monitor`.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "port": {
                    "type": "string",
                    "description": "Serial port for ESP device (optional, auto-detect if not provided)"
                },
                "baud": {
                    "type": "integer",
                    "description": "Baud rate for monitor (default: 115200)"
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "flash_and_monitor_esp",
        "description": "Flash firmware and immediately monitor serial output. Similar to `idf.py flash monitor`.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "port": {
                    "type": "string",
                    "description": "Serial port for ESP device (optional, auto-detect if not provided)"
                },
                "baud": {
                    "type": "integer",
                    "description": "Baud rate for flashing/monitoring"
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "menuconfig_esp",
        "description": "Run menuconfig to configure ESP-IDF project. Note: This requires terminal interaction.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "get_esp_idf_version",
        "description": "Get ESP-IDF version information.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": []
        }
    },
    {
        "name": "check_esp_idf_env",
        "description": "Check ESP-IDF environment status and configuration.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_project_config",
        "description": "Get project configuration information (sdkconfig).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "config_key": {
                    "type": "string",
                    "description": "Optional specific config key to retrieve (e.g., CONFIG_ESP32C3_DEFAULT_CPU_FREQ_MHZ)"
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "set_esp_partition",
        "description": "Set partition table for ESP-IDF project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "partition_table": {
                    "type": "string",
                    "description": "Partition table file path (e.g., 'partitions.csv' or 'partitions_singleapp.csv')"
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path", "partition_table"]
        }
    },
    {
        "name": "setup_project_esp_target",
        "description": "Sets up target for an ESP-IDF project before building.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "target": {
                    "type": "string",
                    "description": "Lowercase target name, such as 'esp32' or 'esp32c3'."
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path", "target"]
        }
    },
    {
        "name": "create_esp_project",
        "description": "Creates a new ESP-IDF project for an ESP chip.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path where new ESP-IDF project will be created."
                },
                "project_name": {
                    "type": "string",
                    "description": "Name of ESP-IDF project to create."
                }
            },
            "required": ["project_path", "project_name"]
        }
    },
    {
        "name": "flash_esp_project",
        "description": "Flash built firmware to a connected ESP device.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project"
                },
                "port": {
                    "type": "string",
                    "description": "Serial port for ESP device (optional, auto-detect if not provided)"
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "list_esp_serial_ports",
        "description": "List available serial ports for ESP devices.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "run_esp_idf_install",
        "description": "Run install.sh script in ESP-IDF directory to install ESP-IDF dependencies and toolchain.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": []
        }
    },
    {
        "name": "run_pytest",
        "description": "Run pytest tests in a project. Supports pytest-embedded for ESP-IDF/ESP32 testing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to project directory containing tests"
                },
                "test_path": {
                    "type": "string",
                    "description": "Path to test file or directory (default: '.', runs all tests)"
                },
                "pytest_args": {
                    "type": "string",
                    "description": "Additional pytest arguments"
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "get_project_info",
        "description": "Get detailed information about an ESP-IDF project including components, targets, and configuration.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "list_components",
        "description": "List all components in an ESP-IDF project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "gdb_attach",
        "description": "Attach GDB debugger to ESP device. Returns the command to run in an interactive terminal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "port": {
                    "type": "string",
                    "description": "Serial port for ESP device (optional, auto-detect if not provided)"
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "get_core_dump",
        "description": "Get core dump information from ESP device for debugging crashes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "port": {
                    "type": "string",
                    "description": "Serial port for ESP device (optional, auto-detect if not provided)"
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "get_heap_info",
        "description": "Get heap memory information from ESP device.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "port": {
                    "type": "string",
                    "description": "Serial port for ESP device (optional, auto-detect if not provided)"
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "get_task_stats",
        "description": "Get FreeRTOS task statistics from ESP device.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project."
                },
                "port": {
                    "type": "string",
                    "description": "Serial port for ESP device (optional, auto-detect if not provided)"
                },
                "idf_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF directory. Optional when IDF_PATH environment variable is set."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "read_file",
        "description": "Read contents of a file in the project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read."
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (optional, default: 100)"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write."
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file."
                }
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "list_files",
        "description": "List files and directories in a project path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to list files from."
                },
                "recursive": {
                    "type": "boolean",
                    "description": "List files recursively (default: false)"
                },
                "pattern": {
                    "type": "string",
                    "description": "Filter files by pattern (e.g., '*.c', '*.h')"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "parse_build_log",
        "description": "Parse and analyze build log with structured output for AI analysis. Extracts errors, warnings, and provides fix suggestions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "log_path": {
                    "type": "string",
                    "description": "Path to build log file (e.g., 'build_output.txt')"
                },
                "project_path": {
                    "type": "string",
                    "description": "Project path for context (optional)"
                }
            },
            "required": ["log_path"]
        }
    },
    {
        "name": "analyze_memory_map",
        "description": "Analyze memory usage from .map file. Returns structured JSON with memory regions, symbols, and usage statistics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "map_path": {
                    "type": "string",
                    "description": "Path to .map file (e.g., 'build/project_name.map')"
                }
            },
            "required": ["map_path"]
        }
    },
    {
        "name": "compare_sdkconfig",
        "description": "Compare two sdkconfig files and output structured differences with context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "config1_path": {
                    "type": "string",
                    "description": "Path to first sdkconfig file"
                },
                "config2_path": {
                    "type": "string",
                    "description": "Path to second sdkconfig file"
                }
            },
            "required": ["config1_path", "config2_path"]
        }
    },
    {
        "name": "analyze_dependencies",
        "description": "Analyze component dependencies from CMakeLists.txt files. Returns dependency graph and circular dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to ESP-IDF project"
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "format_device_log",
        "description": "Parse and format device serial logs with structured output. Extracts timestamps, log levels, and key events.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "log_path": {
                    "type": "string",
                    "description": "Path to device log file"
                },
                "filter_level": {
                    "type": "string",
                    "description": "Filter by log level: ERROR, WARNING, INFO, DEBUG, VERBOSE (optional)"
                }
            },
            "required": ["log_path"]
        }
    }
]

# ============ Tool Handlers ============
def handle_build_esp_project(args: dict) -> dict:
    """Handle build_esp_project"""
    project_path = args.get("project_path", "")
    idf_path = args.get("idf_path")
    sdkconfig_defaults = args.get("sdkconfig_defaults")
    
    start_time = time.time()
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        log.info(f"Building project at: {project_path}")
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error during setup: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}

    if sdkconfig_defaults and sdkconfig_defaults.strip():
        quoted_defaults = shlex.quote(sdkconfig_defaults)
        build_cmd = f"idf.py build -DSDKCONFIG_DEFAULTS={quoted_defaults}"
    else:
        build_cmd = "idf.py build"

    returncode, stdout, stderr = run_command_async(f'bash -c "source {shlex.quote(export_script_bash)} && {build_cmd}"')

    elapsed_time = time.time() - start_time
    elapsed_minutes = int(elapsed_time // 60)
    elapsed_seconds = elapsed_time % 60

    timing_info = f"\n\n[Build completed in {elapsed_minutes}m {elapsed_seconds:.2f}s ({elapsed_time:.2f} seconds)]\n"
    stdout_with_timing = stdout + timing_info

    try:
        with open('mcp-process.log', 'w+') as log_file:
            log_file.write(str((stdout, stderr)))
    except Exception as e:
        logger.warning(f"Failed to write log file: {e}")
    
    log.info(f"Build completed - elapsed: {elapsed_time:.2f}s, return code: {returncode}")
    return {"result": f"STDOUT:\n{stdout_with_timing}\nSTDERR:\n{stderr}"}


def handle_setup_project_esp_target(args: dict) -> dict:
    """Handle setup_project_esp_target"""
    project_path = args.get("project_path", "")
    target = args.get("target", "")
    idf_path = args.get("idf_path")
    
    log.info(f"Setting up target {target} for project at {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        processed_idf_path = idf_path if (idf_path and idf_path.strip()) else None
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(processed_idf_path)
        returncode, stdout, stderr = run_command_async(f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py set-target {shlex.quote(target)}'")
        
        try:
            with open('mcp-set-target.log', 'w+') as log_file:
                log_file.write(str((stdout, stderr)))
        except Exception as e:
            logger.warning(f"Failed to write log file: {e}")
        
        log.info(f"Target setup completed - return code: {returncode}")
        return {"result": f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_create_esp_project(args: dict) -> dict:
    """Handle create_esp_project"""
    project_path = args.get("project_path", "")
    project_name = args.get("project_name", "")
    
    log.info(f"Creating ESP project: {project_name} at {project_path}")
    
    try:
        os.makedirs(project_path, exist_ok=True)
        os.chdir(project_path)
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script()
        # Convert project path to bash-compatible path
        from esp_utils import convert_to_bash_path
        project_path_bash = convert_to_bash_path(project_path)
        returncode, stdout, stderr = run_command_async(f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py create-project --path {shlex.quote(project_path_bash)} {shlex.quote(project_name)}'")
        
        try:
            with open('mcp-project-root-path.log', 'w+') as log_file:
                log_file.write(str((stdout, stderr)))
        except Exception as e:
            logger.warning(f"Failed to write log file: {e}")
        
        log.info(f"Project creation completed - return code: {returncode}")
        return {"result": f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_flash_esp_project(args: dict) -> dict:
    """Handle flash_esp_project"""
    project_path = args.get("project_path", "")
    port = args.get("port")
    
    log.info(f"Flashing project at {project_path} to port: {port if port else 'auto-detect'}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script()

        if port:
            flash_cmd = f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py -p {shlex.quote(port)} flash'"
        else:
            flash_cmd = f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py flash'"

        returncode, stdout, stderr = run_command_async(flash_cmd)

        flash_log = f"Flash operation - Return code: {returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        try:
            with open('mcp-flash.log', 'w+') as log_file:
                log_file.write(flash_log)
        except Exception as e:
            logger.warning(f"Failed to write log file: {e}")
        
        log.info(f"Flash operation completed - return code: {returncode}")
        return {"result": f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_list_esp_serial_ports(args: dict) -> dict:
    """Handle list_esp_serial_ports"""
    log.info("Listing available serial ports")
    
    returncode, stdout, stderr = list_serial_ports()

    port_log = f"Port listing - Return code: {returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
    try:
        with open('mcp-ports.log', 'w+') as log_file:
            log_file.write(port_log)
    except Exception as e:
        logger.warning(f"Failed to write log file: {e}")
    
    log.info(f"Port listing completed - return code: {returncode}")
    return {"result": f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"}


def handle_run_esp_idf_install(args: dict) -> dict:
    """Handle run_esp_idf_install"""
    idf_path = args.get("idf_path")
    start_time = time.time()
    log.info(f"Starting ESP-IDF installation for idf_path: {idf_path}")

    try:
        esp_idf_dir = get_esp_idf_dir(idf_path if (idf_path and idf_path.strip()) else None)
    except ValueError as e:
        error_msg = str(e)
        log.error(f"Failed to get ESP-IDF directory: {error_msg}")
        return {"error": error_msg}

    install_script = os.path.join(esp_idf_dir, "install.sh")

    if not os.path.exists(install_script):
        error_msg = f"install.sh not found at {install_script}. Please verify that ESP-IDF path is correct."
        log.error(error_msg)
        return {"error": error_msg}

    original_dir = os.getcwd()
    try:
        os.chdir(esp_idf_dir)
        returncode, stdout, stderr = run_command_async(f"bash {install_script}")

        elapsed_time = time.time() - start_time
        elapsed_minutes = int(elapsed_time // 60)
        elapsed_seconds = elapsed_time % 60

        timing_info = f"\n\n[Installation completed in {elapsed_minutes}m {elapsed_seconds:.2f}s ({elapsed_time:.2f} seconds)]\n"
        stdout_with_timing = stdout + timing_info

        install_log = f"ESP-IDF installation - Elapsed time: {elapsed_time:.2f}s ({elapsed_minutes}m {elapsed_seconds:.2f}s)\nReturn code: {returncode}\nESP-IDF path: {esp_idf_dir}\nInstall script: {install_script}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        try:
            with open('mcp-install.log', 'w+') as log_file:
                log_file.write(install_log)
        except Exception as e:
            logger.warning(f"Failed to write log file: {e}")
        
        log.info(f"ESP-IDF installation completed - elapsed: {elapsed_time:.2f}s, return code: {returncode}")
        return {"result": f"STDOUT:\n{stdout_with_timing}\nSTDERR:\n{stderr}"}
    finally:
        os.chdir(original_dir)


def handle_run_pytest(args: dict) -> dict:
    """Handle run_pytest"""
    project_path = args.get("project_path", "")
    test_path = args.get("test_path", ".")
    pytest_args = args.get("pytest_args", "")
    idf_path = args.get("idf_path")
    
    log.info(f"Running pytest for project at {project_path}, test path: {test_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    original_dir = os.getcwd()
    try:
        os.chdir(project_path)

        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)

        pytest_cmd = f"pytest {shlex.quote(test_path)}"
        if pytest_args:
            pytest_cmd += f" {shlex.quote(pytest_args)}"
        full_cmd = f"bash -c 'source {shlex.quote(export_script_bash)} && {pytest_cmd}'"

        returncode, stdout, stderr = run_command_async(full_cmd)

        pytest_log = f"Pytest execution - Return code: {returncode}\nCommand: {full_cmd}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        try:
            with open('mcp-pytest.log', 'w+') as log_file:
                log_file.write(pytest_log)
        except Exception as e:
            logger.warning(f"Failed to write log file: {e}")
        
        log.info(f"Pytest completed - return code: {returncode}")
        return {"result": f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    finally:
        os.chdir(original_dir)


def handle_clean_esp_project(args: dict) -> dict:
    """Handle clean_esp_project"""
    project_path = args.get("project_path", "")
    full_clean = args.get("full_clean", False)
    idf_path = args.get("idf_path")
    
    log.info(f"Cleaning ESP project at {project_path} (full_clean={full_clean})")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
        
        clean_cmd = "idf.py fullclean" if full_clean else "idf.py clean"
        returncode, stdout, stderr = run_command_async(f"bash -c 'source {shlex.quote(export_script_bash)} && {clean_cmd}'")
        
        try:
            with open('mcp-clean.log', 'w+') as log_file:
                log_file.write(f"Clean operation - Return code: {returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
        except Exception as e:
            logger.warning(f"Failed to write log file: {e}")
        
        log.info(f"Clean completed - return code: {returncode}")
        return {"result": f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_erase_flash_esp(args: dict) -> dict:
    """Handle erase_flash_esp"""
    project_path = args.get("project_path", "")
    port = args.get("port")
    baud = args.get("baud", cfg.DEFAULT_FLASH_BAUD)
    idf_path = args.get("idf_path")
    
    log.info(f"Erasing flash on ESP device at {project_path} on port {port}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
        erase_cmd = f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py erase-flash"
        if port:
            erase_cmd += f" -p {shlex.quote(port)}"
        erase_cmd += f" --baud {baud}'"
        
        returncode, stdout, stderr = run_command_async(erase_cmd)
        
        try:
            with open('mcp-erase.log', 'w+') as log_file:
                log_file.write(f"Erase flash - Return code: {returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
        except Exception as e:
            logger.warning(f"Failed to write log file: {e}")
        
        log.info(f"Erase flash completed - return code: {returncode}")
        return {"result": f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_monitor_esp(args: dict) -> dict:
    """Handle monitor_esp"""
    project_path = args.get("project_path", "")
    port = args.get("port")
    baud = args.get("baud", cfg.DEFAULT_MONITOR_BAUD)
    idf_path = args.get("idf_path")
    
    log.info(f"Starting monitor for ESP device at {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
        
        # Monitor requires interaction, so we'll note this limitation
        monitor_cmd = f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py monitor"
        if port:
            monitor_cmd += f" -p {shlex.quote(port)}"
        monitor_cmd += f" --baud {baud}'"
        
        return {"result": "Monitor command requires interactive terminal. Please run manually:\n" + monitor_cmd}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_flash_and_monitor_esp(args: dict) -> dict:
    """Handle flash_and_monitor_esp"""
    project_path = args.get("project_path", "")
    port = args.get("port")
    baud = args.get("baud")
    idf_path = args.get("idf_path")
    
    log.info(f"Flashing and monitoring ESP device at {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
        
        # Flash and monitor requires interaction, so we'll note this limitation
        cmd = f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py flash monitor"
        if port:
            cmd += f" -p {shlex.quote(port)}"
        if baud:
            cmd += f" --baud {baud}'"
        
        return {"result": "Flash and monitor command requires interactive terminal. Please run manually:\n" + cmd}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_menuconfig_esp(args: dict) -> dict:
    """Handle menuconfig_esp"""
    project_path = args.get("project_path", "")
    idf_path = args.get("idf_path")
    
    log.info(f"Starting menuconfig for ESP project at {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
        
        # Menuconfig requires interactive terminal
        cmd = f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py menuconfig'"
        return {"result": "Menuconfig requires interactive terminal. Please run manually:\n" + cmd}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_get_esp_idf_version(args: dict) -> dict:
    """Handle get_esp_idf_version"""
    idf_path = args.get("idf_path")
    
    log.info(f"Getting ESP-IDF version for idf_path: {idf_path}")
    
    try:
        esp_idf_dir = get_esp_idf_dir(idf_path if (idf_path and idf_path.strip()) else None)
        version_file = os.path.join(esp_idf_dir, "version.txt")
        
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                version = f.read().strip()
            return {"result": f"ESP-IDF Version: {version}\nPath: {esp_idf_dir}"}
        else:
            # Try to get version from git
            original_dir = os.getcwd()
            try:
                os.chdir(esp_idf_dir)
                returncode, stdout, stderr = run_command_async("git describe --tags --always")
                if returncode == 0:
                    version = stdout.strip()
                    return {"result": f"ESP-IDF Version (git): {version}\nPath: {esp_idf_dir}"}
                else:
                    return {"result": f"ESP-IDF Path: {esp_idf_dir}\nNote: Could not determine version automatically"}
            finally:
                os.chdir(original_dir)
    except ValueError as e:
        error_msg = str(e)
        log.error(f"Failed to get ESP-IDF directory: {error_msg}")
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_check_esp_idf_env(args: dict) -> dict:
    """Handle check_esp_idf_env"""
    idf_path = args.get("idf_path")
    
    log.info("Checking ESP-IDF environment")
    
    try:
        from esp_utils import check_esp_idf_installed
        esp_idf_dir = get_esp_idf_dir(idf_path if (idf_path and idf_path.strip()) else None)
        is_installed = check_esp_idf_installed(esp_idf_dir)
        
        # Check for key files
        export_script = os.path.join(esp_idf_dir, "export.sh")
        install_script = os.path.join(esp_idf_dir, "install.sh")
        
        env_info = {
            "ESP-IDF Path": esp_idf_dir,
            "Installed": is_installed,
            "export.sh exists": os.path.exists(export_script),
            "install.sh exists": os.path.exists(install_script),
            "IDF_PATH env var": os.environ.get("IDF_PATH", "Not set")
        }
        
        # Format as text
        result_text = "\n".join([f"{k}: {v}" for k, v in env_info.items()])
        return {"result": result_text}
    except ValueError as e:
        error_msg = str(e)
        log.error(f"Failed to check ESP-IDF environment: {error_msg}")
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_get_project_config(args: dict) -> dict:
    """Handle get_project_config"""
    project_path = args.get("project_path", "")
    config_key = args.get("config_key")
    
    log.info(f"Getting project config from {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        sdkconfig_path = os.path.join(project_path, "sdkconfig")
        build_sdkconfig_path = os.path.join(project_path, "build", "config", "sdkconfig.h")
        
        # Check sdkconfig.h in build directory (more reliable)
        if os.path.exists(build_sdkconfig_path):
            config_file = build_sdkconfig_path
        elif os.path.exists(sdkconfig_path):
            config_file = sdkconfig_path
        else:
            return {"error": f"Neither sdkconfig nor build/config/sdkconfig.h found in {project_path}"}
        
        if config_key:
            # Search for specific key
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                for line in lines:
                    if config_key in line and '#define' in line:
                        return {"result": line.strip()}
            return {"error": f"Config key '{config_key}' not found"}
        else:
            # Return first N lines of config (configurable)
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:cfg.CONFIG_PREVIEW_LINES]
            return {"result": f"Project Configuration ({config_file}):\n" + "".join(lines)}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_set_esp_partition(args: dict) -> dict:
    """Handle set_esp_partition"""
    project_path = args.get("project_path", "")
    partition_table = args.get("partition_table", "")
    idf_path = args.get("idf_path")
    
    log.info(f"Setting partition table {partition_table} for project at {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    if not partition_table:
        error_msg = "Partition table file is required"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
        
        # Set partition table via menuconfig or directly
        # Using idf.py with partition table option
        cmd = f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py set-partition-table {shlex.quote(partition_table)}'"
        
        returncode, stdout, stderr = run_command_async(cmd)
        
        try:
            with open('mcp-partition.log', 'w+') as log_file:
                log_file.write(f"Partition table set - Return code: {returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
        except Exception as e:
            logger.warning(f"Failed to write log file: {e}")
        
        log.info(f"Partition table set completed - return code: {returncode}")
        return {"result": f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_get_project_info(args: dict) -> dict:
    """Handle get_project_info"""
    project_path = args.get("project_path", "")
    
    log.info(f"Getting project info from {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        info = {
            "Project Path": project_path,
            "CMakeLists.txt exists": os.path.exists(os.path.join(project_path, "CMakeLists.txt")),
            "sdkconfig exists": os.path.exists(os.path.join(project_path, "sdkconfig")),
            "main directory exists": os.path.exists(os.path.join(project_path, "main")),
            "components directory exists": os.path.exists(os.path.join(project_path, "components")),
        }
        
        # Try to get target from sdkconfig
        sdkconfig_path = os.path.join(project_path, "sdkconfig")
        if os.path.exists(sdkconfig_path):
            try:
                with open(sdkconfig_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if 'CONFIG_IDF_TARGET' in line and '=' in line:
                            target = line.split('=')[1].strip().strip('"')
                            info["Target"] = target
                            break
            except:
                pass
        
        # List components
        main_dir = os.path.join(project_path, "main")
        components_dir = os.path.join(project_path, "components")
        
        main_files = []
        if os.path.exists(main_dir):
            main_files = [f for f in os.listdir(main_dir) if f.endswith(('.c', '.cpp', '.h', '.hpp'))]
        
        components = []
        if os.path.exists(components_dir):
            components = [d for d in os.listdir(components_dir) if os.path.isdir(os.path.join(components_dir, d))]
        
        info["Main files"] = f"{len(main_files)} files"
        info["Components"] = components if components else "None"
        
        result_text = "\n".join([f"{k}: {v}" for k, v in info.items()])
        return {"result": result_text}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_list_components(args: dict) -> dict:
    """Handle list_components"""
    project_path = args.get("project_path", "")
    
    log.info(f"Listing components in {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        components_info = []
        
        # Check main component
        main_dir = os.path.join(project_path, "main")
        if os.path.exists(main_dir):
            main_files = [f for f in os.listdir(main_dir) if f.endswith(('.c', '.cpp', '.h', '.hpp'))]
            components_info.append(f"main ({len(main_files)} files)")
        
        # Check components directory
        components_dir = os.path.join(project_path, "components")
        if os.path.exists(components_dir):
            for comp_name in os.listdir(components_dir):
                comp_path = os.path.join(components_dir, comp_name)
                if os.path.isdir(comp_path):
                    comp_files = []
                    for root, dirs, files in os.walk(comp_path):
                        comp_files.extend([f for f in files if f.endswith(('.c', '.cpp', '.h', '.hpp'))])
                    components_info.append(f"{comp_name} ({len(comp_files)} files)")
        
        # Check managed components
        managed_dir = os.path.join(project_path, "managed_components")
        if os.path.exists(managed_dir):
            managed_comps = [d for d in os.listdir(managed_dir) if os.path.isdir(os.path.join(managed_dir, d))]
            if managed_comps:
                components_info.append(f"\nManaged Components: {len(managed_comps)}")
                for comp in managed_comps[:10]:  # Limit to first 10
                    components_info.append(f"  - {comp}")
        
        result = "Project Components:\n" + "\n".join(components_info)
        return {"result": result}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_gdb_attach(args: dict) -> dict:
    """Handle gdb_attach"""
    project_path = args.get("project_path", "")
    port = args.get("port")
    idf_path = args.get("idf_path")
    
    log.info(f"Preparing GDB attach for project at {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
        
        # Build GDB command
        gdb_cmd = f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py gdb"
        if port:
            gdb_cmd += f" -p {shlex.quote(port)}"
        gdb_cmd += "'"
        
        instructions = (
            "GDB Debugger Attach\n"
            "===================\n\n"
            "To attach GDB to your ESP device, run the following command in an interactive terminal:\n\n"
            f"{gdb_cmd}\n\n"
            "Alternatively, you can:\n"
            "1. Start OpenOCD in one terminal: idf.py openocd\n"
            "2. Start GDB in another terminal: idf.py gdb\n\n"
            "Note: GDB requires an interactive terminal for proper operation."
        )
        
        return {"result": instructions}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_get_core_dump(args: dict) -> dict:
    """Handle get_core_dump"""
    project_path = args.get("project_path", "")
    port = args.get("port")
    idf_path = args.get("idf_path")
    
    log.info(f"Getting core dump from ESP device at {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # get_export_script already returns bash-compatible path on Windows
        export_script_bash = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
        
        # Check if core dump is enabled
        sdkconfig_path = os.path.join(project_path, "sdkconfig")
        core_dump_enabled = False
        
        if os.path.exists(sdkconfig_path):
            try:
                with open(sdkconfig_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if 'CONFIG_ESP_COREDUMP_ENABLE' in line and '=y' in line:
                            core_dump_enabled = True
                            break
            except:
                pass
        
        if not core_dump_enabled:
            return {"result": "Core dump is not enabled in sdkconfig. To enable:\n1. Run: idf.py menuconfig\n2. Navigate to Component config -> Core to Core communication\n3. Enable 'Enable Core Dump'\n4. Save and rebuild the project"}
        
        # Get core dump (export_script_bash already converted)
        core_cmd = f"bash -c 'source {shlex.quote(export_script_bash)} && idf.py coredump-info"
        if port:
            core_cmd += f" -p {shlex.quote(port)}"
        core_cmd += "'"
        
        returncode, stdout, stderr = run_command_async(core_cmd)
        
        try:
            with open('mcp-coredump.log', 'w+') as log_file:
                log_file.write(f"Core dump info - Return code: {returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
        except Exception as e:
            logger.warning(f"Failed to write log file: {e}")
        
        log.info(f"Core dump info completed - return code: {returncode}")
        return {"result": f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_get_heap_info(args: dict) -> dict:
    """Handle get_heap_info"""
    project_path = args.get("project_path", "")
    port = args.get("port")
    idf_path = args.get("idf_path")
    
    log.info(f"Getting heap info from ESP device at {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # Note: get_export_script already returns bash-compatible path on Windows
        _ = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
        
        # Send heap info command via esp-idf monitor
        # Note: This is a simplified version - actual implementation requires proper terminal handling
        instructions = (
            "Heap Memory Information\n"
            "=======================\n\n"
            "To get heap information from your ESP device:\n\n"
            "1. Run monitor: idf.py monitor\n"
            "2. Type the following command in monitor:\n"
            "   'heap info' (or 'heap caps')\n\n"
            "Available heap commands:\n"
            "- heap info: Show heap summary\n"
            "- heap caps: Show heap capabilities\n"
            "- heap tasks: Show heap per task\n\n"
            "Note: Monitor requires interactive terminal."
        )
        
        return {"result": instructions}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_get_task_stats(args: dict) -> dict:
    """Handle get_task_stats"""
    project_path = args.get("project_path", "")
    port = args.get("port")
    idf_path = args.get("idf_path")
    
    log.info(f"Getting task stats from ESP device at {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        os.chdir(project_path)
        # Note: get_export_script already returns bash-compatible path on Windows
        _ = get_export_script(idf_path if (idf_path and idf_path.strip()) else None)
        
        instructions = (
            "FreeRTOS Task Statistics\n"
            "=========================\n\n"
            "To get task statistics from your ESP device:\n\n"
            "1. Run monitor: idf.py monitor\n"
            "2. Type the following command in monitor:\n"
            "   'task stats'\n\n"
            "Available task commands:\n"
            "- task stats: Show all task statistics\n"
            "- task list: Show task list\n"
            "- task watch <task_name>: Watch a specific task\n\n"
            "Note: Monitor requires interactive terminal."
        )
        
        return {"result": instructions}
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Failed to setup ESP-IDF environment: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_read_file(args: dict) -> dict:
    """Handle read_file"""
    file_path = args.get("file_path", "")
    max_lines = args.get("max_lines", cfg.DEFAULT_MAX_LINES)
    
    log.info(f"Reading file: {file_path}")
    
    if not file_path or not os.path.exists(file_path):
        error_msg = f"File does not exist: {file_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        # Limit lines
        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines]
            result = "".join(lines)
            result += f"\n\n... ({len(lines) - max_lines} more lines hidden, use max_lines parameter to read more)"
        else:
            result = "".join(lines)
        
        return {"result": f"File: {file_path}\nLines: {len(lines)}\n\n{result}"}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_write_file(args: dict) -> dict:
    """Handle write_file"""
    file_path = args.get("file_path", "")
    content = args.get("content", "")
    
    log.info(f"Writing file: {file_path}")
    
    if not file_path:
        error_msg = "File path is required"
        log.error(error_msg)
        return {"error": error_msg}
    
    if content is None:
        error_msg = "Content is required"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"result": f"Successfully wrote {len(content)} characters to {file_path}"}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_list_files(args: dict) -> dict:
    """Handle list_files"""
    path = args.get("path", ".")
    recursive = args.get("recursive", False)
    pattern = args.get("pattern", "")
    
    log.info(f"Listing files in: {path}")
    
    if not path or not os.path.exists(path):
        error_msg = f"Path does not exist: {path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        files_info = []
        
        if recursive:
            # Recursively list files
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if not pattern or file.endswith(pattern):
                        rel_path = os.path.relpath(file_path, path)
                        files_info.append(rel_path)
        else:
            # List only top-level files
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)
                
                if not pattern or item.endswith(pattern):
                    files_info.append(f"[{'DIR' if is_dir else 'FILE'}] {item}")
        
        result = f"Path: {path}\nRecursive: {recursive}\nPattern: {pattern if pattern else 'None'}\n\n"
        result += f"Found {len(files_info)} items:\n"
        result += "\n".join(sorted(files_info))
        
        return {"result": result}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


# ============ Structured Analysis Tool Handlers ============
def handle_parse_build_log(args: dict) -> dict:
    """Handle parse_build_log - Parse and analyze build log with structured output"""
    log_path = args.get("log_path", "")
    project_path = args.get("project_path", "")
    
    log.info(f"Parsing build log: {log_path}")
    
    if not log_path or not os.path.exists(log_path):
        error_msg = f"Build log file does not exist: {log_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        errors = []
        warnings = []
        info_messages = []
        
        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            # Detect errors
            if any(keyword in line_lower for keyword in ['error:', 'error ', 'failed', 'undefined reference', 'multiple definition']):
                errors.append({
                    "line": i,
                    "message": line.strip(),
                    "type": "error"
                })
            
            # Detect warnings
            elif any(keyword in line_lower for keyword in ['warning:', 'warning ', 'deprecated', 'unused']):
                warnings.append({
                    "line": i,
                    "message": line.strip(),
                    "type": "warning"
                })
            
            # Collect useful info
            elif any(keyword in line_lower for keyword in ['building', 'linking', 'generating', 'project build complete']):
                info_messages.append({
                    "line": i,
                    "message": line.strip(),
                    "type": "info"
                })
        
        # Generate structured JSON output
        result = {
            "log_path": log_path,
            "project_path": project_path if project_path else "not specified",
            "summary": {
                "total_lines": len(lines),
                "errors_count": len(errors),
                "warnings_count": len(warnings),
                "info_count": len(info_messages)
            },
            "errors": errors[:cfg.MAX_ERRORS],  # Limit to first N errors
            "warnings": warnings[:cfg.MAX_WARNINGS],  # Limit to first N warnings
            "info": info_messages[:cfg.MAX_INFO_MESSAGES],  # Limit to first N info messages
            "has_errors": len(errors) > 0,
            "has_warnings": len(warnings) > 0
        }
        
        # Add suggestions if there are errors
        if errors:
            error_types = set()
            for err in errors:
                msg = err["message"].lower()
                if 'undefined reference' in msg:
                    error_types.add("linking_error")
                elif 'multiple definition' in msg:
                    error_types.add("linking_error")
                elif 'syntax error' in msg:
                    error_types.add("syntax_error")
                elif 'no such file' in msg:
                    error_types.add("file_not_found")
            
            result["suggestions"] = []
            if "linking_error" in error_types:
                result["suggestions"].append("Check for missing source files in CMakeLists.txt")
                result["suggestions"].append("Ensure all required libraries are linked")
            if "syntax_error" in error_types:
                result["suggestions"].append("Review syntax errors in source files")
            if "file_not_found" in error_types:
                result["suggestions"].append("Verify all file paths are correct")
        
        return {"result": json.dumps(result, indent=2, ensure_ascii=False)}
    
    except Exception as e:
        error_msg = f"Unexpected error parsing build log: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_analyze_memory_map(args: dict) -> dict:
    """Handle analyze_memory_map - Analyze memory usage from .map file"""
    map_path = args.get("map_path", "")
    
    log.info(f"Analyzing memory map: {map_path}")
    
    if not map_path or not os.path.exists(map_path):
        error_msg = f"Memory map file does not exist: {map_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        with open(map_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        memory_regions = []
        symbols = []
        total_size = 0
        
        for line in lines:
            # Detect memory regions (format: .text 0x00000000 0x00010000)
            if line.startswith('.') and '0x' in line:
                parts = line.split()
                if len(parts) >= 3:
                    region_name = parts[0]
                    try:
                        addr = int(parts[1], 16)
                        size = int(parts[2], 16)
                        memory_regions.append({
                            "name": region_name,
                            "address": f"0x{addr:08X}",
                            "size": size,
                            "size_kb": size / 1024
                        })
                        total_size += size
                    except (ValueError, IndexError):
                        pass
            
            # Detect symbols (format: function_name 0x00000000 0x10)
            elif line.strip() and not line.startswith('.') and '0x' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        addr = int(parts[-2], 16) if len(parts) >= 2 else 0
                        size = int(parts[-1], 16) if len(parts) >= 3 else 0
                        symbol_name = ' '.join(parts[:-2]) if len(parts) > 3 else parts[0]
                        symbols.append({
                            "name": symbol_name,
                            "address": f"0x{addr:08X}",
                            "size": size
                        })
                    except (ValueError, IndexError):
                        pass
        
        # Sort symbols by size (largest first)
        symbols_sorted = sorted(symbols, key=lambda x: x["size"], reverse=True)[:cfg.MAX_SYMBOLS]
        
        # Calculate usage statistics
        result = {
            "map_path": map_path,
            "summary": {
                "total_regions": len(memory_regions),
                "total_symbols": len(symbols),
                "total_size": total_size,
                "total_size_kb": total_size / 1024
            },
            "memory_regions": memory_regions,
            "top_symbols": symbols_sorted,
            "analysis": {
                "largest_region": max(memory_regions, key=lambda x: x["size"]) if memory_regions else None,
                "smallest_region": min(memory_regions, key=lambda x: x["size"]) if memory_regions else None
            }
        }
        
        return {"result": json.dumps(result, indent=2, ensure_ascii=False)}
    
    except Exception as e:
        error_msg = f"Unexpected error analyzing memory map: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def handle_compare_sdkconfig(args: dict) -> dict:
    """Handle compare_sdkconfig - Compare two sdkconfig files"""
    config1_path = args.get("config1_path", "")
    config2_path = args.get("config2_path", "")
    
    log.info(f"Comparing sdkconfig files: {config1_path} vs {config2_path}")
    
    if not config1_path or not os.path.exists(config1_path):
        error_msg = f"First sdkconfig file does not exist: {config1_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    if not config2_path or not os.path.exists(config2_path):
        error_msg = f"Second sdkconfig file does not exist: {config2_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        # Parse config files
        def parse_config(path):
            config = {}
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"')
            return config
        
        config1 = parse_config(config1_path)
        config2 = parse_config(config2_path)
        
        # Find differences
        all_keys = set(config1.keys()) | set(config2.keys())
        
        added = []
        removed = []
        modified = []
        
        for key in sorted(all_keys):
            if key not in config1:
                added.append({
                    "key": key,
                    "value": config2[key],
                    "category": _categorize_config(key)
                })
            elif key not in config2:
                removed.append({
                    "key": key,
                    "value": config1[key],
                    "category": _categorize_config(key)
                })
            elif config1[key] != config2[key]:
                modified.append({
                    "key": key,
                    "old_value": config1[key],
                    "new_value": config2[key],
                    "category": _categorize_config(key),
                    "recommendation": _config_recommendation(key, config1[key], config2[key])
                })
        
        result = {
            "config1_path": config1_path,
            "config2_path": config2_path,
            "summary": {
                "total_keys": len(all_keys),
                "added_count": len(added),
                "removed_count": len(removed),
                "modified_count": len(modified)
            },
            "added": added[:cfg.MAX_CONFIG_DIFF_ITEMS],  # Limit to first N added
            "removed": removed[:cfg.MAX_CONFIG_DIFF_ITEMS],
            "modified": modified[:cfg.MAX_CONFIG_DIFF_MODIFIED]  # Limit to first N modified
        }
        
        return {"result": json.dumps(result, indent=2, ensure_ascii=False)}
    
    except Exception as e:
        error_msg = f"Unexpected error comparing sdkconfig files: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def _categorize_config(key: str) -> str:
    """Categorize sdkconfig key"""
    key_lower = key.lower()
    if 'wifi' in key_lower:
        return "WiFi"
    elif 'ble' in key_lower or 'bluetooth' in key_lower:
        return "Bluetooth"
    elif 'cpu' in key_lower or 'freq' in key_lower:
        return "Performance"
    elif 'heap' in key_lower or 'memory' in key_lower:
        return "Memory"
    elif 'log' in key_lower or 'debug' in key_lower:
        return "Debug"
    else:
        return "General"


def _config_recommendation(key: str, old_val: str, new_val: str) -> str:
    """Generate recommendation for config change"""
    if 'freq' in key.lower():
        if int(new_val) > int(old_val):
            return "Increasing CPU frequency improves performance but increases power consumption"
        else:
            return "Decreasing CPU frequency saves power but reduces performance"
    elif 'heap' in key.lower():
        return "Heap size change may affect available memory for tasks"
    elif 'log' in key.lower():
        if new_val == 'n':
            return "Disabling logs saves flash space but makes debugging harder"
        else:
            return "Enabling logs helps debugging but uses more flash space"
    return ""


def handle_analyze_dependencies(args: dict) -> dict:
    """Handle analyze_dependencies - Analyze component dependencies"""
    project_path = args.get("project_path", "")
    
    log.info(f"Analyzing dependencies for project: {project_path}")
    
    if not project_path or not os.path.exists(project_path):
        error_msg = f"Project path does not exist: {project_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        # Find all CMakeLists.txt files
        cmake_files = []
        for root, dirs, files in os.walk(project_path):
            if 'CMakeLists.txt' in files:
                cmake_files.append(os.path.join(root, 'CMakeLists.txt'))
        
        # Parse dependencies
        dependencies = {}  # component -> list of dependencies
        all_components = set()
        
        for cmake_file in cmake_files:
            component_dir = os.path.dirname(cmake_file)
            component_name = os.path.basename(component_dir)
            all_components.add(component_name)
            
            deps = []
            with open(cmake_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
                # Find REQUIRES lines
                import re
                requires_matches = re.findall(r'REQUIRES\s+([^\s\n]+)', content)
                deps.extend(requires_matches)
                
                # Find PRIV_REQUIRES lines
                priv_requires_matches = re.findall(r'PRIV_REQUIRES\s+([^\s\n]+)', content)
                deps.extend([f"{d} (private)" for d in priv_requires_matches])
            
            if deps:
                dependencies[component_name] = deps
        
        # Detect circular dependencies
        circular_deps = _detect_circular_deps(dependencies)
        
        # Calculate dependency depth
        max_depth = _calculate_max_depth(dependencies)
        
        # Build component info
        component_info = []
        for comp in sorted(all_components):
            comp_deps = dependencies.get(comp, [])
            component_info.append({
                "name": comp,
                "dependencies": comp_deps,
                "dependency_count": len(comp_deps),
                "is_leaf": len(comp_deps) == 0,
                "has_circular": comp in circular_deps
            })
        
        result = {
            "project_path": project_path,
            "summary": {
                "total_components": len(all_components),
                "components_with_deps": len(dependencies),
                "circular_dependencies": len(circular_deps),
                "max_dependency_depth": max_depth
            },
            "components": component_info,
            "circular_dependencies": circular_deps,
            "recommendations": []
        }
        
        # Add recommendations
        if circular_deps:
            result["recommendations"].append("Circular dependencies detected - this may cause build issues")
        if max_depth > 5:
            result["recommendations"].append(f"Deep dependency chain detected (depth {max_depth}) - consider refactoring")
        
        return {"result": json.dumps(result, indent=2, ensure_ascii=False)}
    
    except Exception as e:
        error_msg = f"Unexpected error analyzing dependencies: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


def _detect_circular_deps(deps: dict) -> list:
    """Detect circular dependencies using DFS"""
    visited = set()
    rec_stack = set()
    circular = []
    
    def dfs(node, path):
        if node in rec_stack:
            # Found cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            circular.append(cycle)
            return True
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        
        for dep in deps.get(node, []):
            # Remove (private) suffix for dependency tracking
            dep_clean = dep.replace(' (private)', '').strip()
            dfs(dep_clean, path + [node])
        
        rec_stack.remove(node)
        return False
    
    for node in deps:
        dfs(node, [])
    
    return circular


def _calculate_max_depth(deps: dict) -> int:
    """Calculate maximum dependency depth"""
    memo = {}
    
    def get_depth(node):
        if node in memo:
            return memo[node]
        
        node_deps = deps.get(node, [])
        if not node_deps:
            return 0
        
        max_child_depth = 0
        for dep in node_deps:
            dep_clean = dep.replace(' (private)', '').strip()
            child_depth = get_depth(dep_clean)
            max_child_depth = max(max_child_depth, child_depth)
        
        memo[node] = max_child_depth + 1
        return memo[node]
    
    max_depth = 0
    for node in deps:
        max_depth = max(max_depth, get_depth(node))
    
    return max_depth


def handle_format_device_log(args: dict) -> dict:
    """Handle format_device_log - Parse and format device logs"""
    log_path = args.get("log_path", "")
    filter_level = args.get("filter_level", "").upper()
    
    log.info(f"Formatting device log: {log_path}, filter: {filter_level}")
    
    if not log_path or not os.path.exists(log_path):
        error_msg = f"Device log file does not exist: {log_path}"
        log.error(error_msg)
        return {"error": error_msg}
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        # Parse log entries
        log_entries = []
        level_counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0, "VERBOSE": 0, "OTHER": 0}
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Detect log level
            level = "OTHER"
            for lvl in ["ERROR", "WARNING", "INFO", "DEBUG", "VERBOSE"]:
                if lvl in line_stripped:
                    level = lvl
                    break
            
            level_counts[level] += 1
            
            # Detect timestamp (ESP-IDF format: I (123) log_tag: message)
            timestamp = ""
            tag = ""
            message = line_stripped
            
            import re
            # Match ESP-IDF log format: I (123) tag: message
            match = re.match(r'([EIWDV]) \((\d+)\) ([^:]+): (.+)', line_stripped)
            if match:
                level_char = match.group(1)
                timestamp = match.group(2)
                tag = match.group(3)
                message = match.group(4)
                
                # Map level char to name
                level_map = {'E': 'ERROR', 'W': 'WARNING', 'I': 'INFO', 'D': 'DEBUG', 'V': 'VERBOSE'}
                level = level_map.get(level_char, level)
            
            # Detect crashes
            is_crash = any(keyword in line_stripped.lower() for keyword in
                         ['assert', 'abort', 'guru', 'panic', 'stack trace', 'backtrace'])
            
            # Detect errors
            is_error = level == "ERROR" or "error" in line_stripped.lower()
            
            entry = {
                "level": level,
                "timestamp": timestamp,
                "tag": tag,
                "message": message,
                "is_crash": is_crash,
                "is_error": is_error
            }
            
            # Apply filter
            if not filter_level or level == filter_level or filter_level == "":
                log_entries.append(entry)
        
        # Find crashes and errors
        crashes = [e for e in log_entries if e["is_crash"]]
        errors = [e for e in log_entries if e["is_error"]]
        
        # Generate recommendations
        recommendations = []
        if crashes:
            recommendations.append(f"Found {len(crashes)} crash(es) - review stack traces")
        if errors:
            recommendations.append(f"Found {len(errors)} error(s) - review error messages")
        if level_counts["ERROR"] > 10:
            recommendations.append("High error count detected - investigate error patterns")
        
        result = {
            "log_path": log_path,
            "summary": {
                "total_lines": len(lines),
                "total_entries": len(log_entries),
                "level_counts": level_counts,
                "crashes_count": len(crashes),
                "errors_count": len(errors)
            },
            "entries": log_entries[:cfg.MAX_LOG_ENTRIES],  # Limit to first N entries
            "crashes": crashes[:cfg.MAX_CRASHES],  # Limit to first N crashes
            "errors": errors[:cfg.MAX_LOG_ERRORS],  # Limit to first N errors
            "recommendations": recommendations
        }
        
        return {"result": json.dumps(result, indent=2, ensure_ascii=False)}
    
    except Exception as e:
        error_msg = f"Unexpected error formatting device log: {str(e)}"
        log.error(error_msg)
        return {"error": error_msg}


# ============ MCP Server ============
class ESPMCPServer:
    """Main MCP Server implementation (synchronous, like cheat-engine)"""
    
    def __init__(self):
        self.request_count = 0
    
    def execute_tool(self, name: str, args: dict) -> dict:
        """Execute a tool by name"""
        handlers = {
            "build_esp_project": handle_build_esp_project,
            "clean_esp_project": handle_clean_esp_project,
            "erase_flash_esp": handle_erase_flash_esp,
            "monitor_esp": handle_monitor_esp,
            "flash_and_monitor_esp": handle_flash_and_monitor_esp,
            "menuconfig_esp": handle_menuconfig_esp,
            "get_esp_idf_version": handle_get_esp_idf_version,
            "check_esp_idf_env": handle_check_esp_idf_env,
            "get_project_config": handle_get_project_config,
            "set_esp_partition": handle_set_esp_partition,
            "setup_project_esp_target": handle_setup_project_esp_target,
            "create_esp_project": handle_create_esp_project,
            "flash_esp_project": handle_flash_esp_project,
            "list_esp_serial_ports": handle_list_esp_serial_ports,
            "run_esp_idf_install": handle_run_esp_idf_install,
            "run_pytest": handle_run_pytest,
            "get_project_info": handle_get_project_info,
            "list_components": handle_list_components,
            "gdb_attach": handle_gdb_attach,
            "get_core_dump": handle_get_core_dump,
            "get_heap_info": handle_get_heap_info,
            "get_task_stats": handle_get_task_stats,
            "read_file": handle_read_file,
            "write_file": handle_write_file,
            "list_files": handle_list_files,
            "parse_build_log": handle_parse_build_log,
            "analyze_memory_map": handle_analyze_memory_map,
            "compare_sdkconfig": handle_compare_sdkconfig,
            "analyze_dependencies": handle_analyze_dependencies,
            "format_device_log": handle_format_device_log,
        }
        
        handler = handlers.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}"}
        
        try:
            result = handler(args)
            return result
        except Exception as e:
            log.error(f"Tool execution error: {traceback.format_exc()}")
            return {"error": str(e)}
    
    def handle_request(self, req: dict) -> Optional[dict]:
        """Handle incoming MCP request"""
        method = req.get("method", "")
        req_id = req.get("id")
        params = req.get("params", {})
        
        if method == "initialize":
            return self._handle_initialize(req_id)
        elif method == "notifications/initialized":
            return None
        elif method == "tools/list":
            return self._handle_tools_list(req_id)
        elif method == "tools/call":
            return self._handle_tools_call(req_id, params)
        else:
            return self._error_response(req_id, -32601, f"Method not found: {method}")
    
    def _handle_initialize(self, req_id) -> dict:
        """Handle initialize request"""
        # Dynamically get ESP-IDF path from environment variable
        idf_path = os.environ.get("IDF_PATH", "")
        if idf_path:
            # Normalize path for display
            normalized_path = os.path.abspath(idf_path).replace('\\', '/')
            path_info = f"\nESP-IDF path detected: {normalized_path}"
        else:
            path_info = "\nNote: ESP-IDF path not detected in environment. Please configure IDF_PATH in MCP settings."
        
        # Base instructions
        base_instructions = (
            "# ESP MCP Server\n\n"
            "Available tools:\n"
            "- build_esp_project: Build an ESP-IDF project\n"
            "- clean_esp_project: Clean build files from an ESP-IDF project\n"
            "- erase_flash_esp: Erase flash memory on ESP device\n"
            "- monitor_esp: Monitor serial output from ESP device\n"
            "- flash_and_monitor_esp: Flash firmware and immediately monitor serial output\n"
            "- menuconfig_esp: Run menuconfig to configure ESP-IDF project\n"
            "- get_esp_idf_version: Get ESP-IDF version information\n"
            "- check_esp_idf_env: Check ESP-IDF environment status and configuration\n"
            "- get_project_config: Get project configuration information (sdkconfig)\n"
            "- set_esp_partition: Set partition table for ESP-IDF project\n"
            "- setup_project_esp_target: Set up target for an ESP-IDF project\n"
            "- create_esp_project: Create a new ESP-IDF project\n"
            "- flash_esp_project: Flash built firmware to a connected ESP device\n"
            "- list_esp_serial_ports: List available serial ports for ESP devices\n"
            "- run_esp_idf_install: Run install.sh script in ESP-IDF directory\n"
            "- run_pytest: Run pytest tests in a project\n"
            "- get_project_info: Get detailed information about an ESP-IDF project\n"
            "- list_components: List all components in an ESP-IDF project\n"
            "- gdb_attach: Attach GDB debugger to ESP device\n"
            "- get_core_dump: Get core dump information from ESP device\n"
            "- get_heap_info: Get heap memory information from ESP device\n"
            "- get_task_stats: Get FreeRTOS task statistics from ESP device\n"
            "- read_file: Read contents of a file in the project\n"
            "- write_file: Write content to a file in the project\n"
            "- list_files: List files and directories in a project path\n"
            "- parse_build_log: Parse and analyze build log with structured output for AI analysis\n"
            "- analyze_memory_map: Analyze memory usage from .map file\n"
            "- compare_sdkconfig: Compare two sdkconfig files and output structured differences\n"
            "- analyze_dependencies: Analyze component dependencies from CMakeLists.txt files\n"
            "- format_device_log: Parse and format device serial logs with structured output\n"
        )
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": cfg.PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": cfg.SERVER_NAME, "version": cfg.SERVER_VERSION},
                "instructions": base_instructions + path_info
            }
        }
    
    def _handle_tools_list(self, req_id) -> dict:
        """Handle tools/list request"""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS}
        }
    
    def _handle_tools_call(self, req_id, params: dict) -> dict:
        """Handle tools/call request"""
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        
        result = self.execute_tool(tool_name, tool_args)
        
        is_error = "error" in result
        text = f"Error: {result['error']}" if is_error else json.dumps(result.get("result", result), ensure_ascii=False, indent=2)
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": text}],
                "isError": is_error
            }
        }
    
    def _error_response(self, req_id, code: int, message: str) -> dict:
        """Create error response"""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message}
        }
    
    def run(self):
        """Main server loop"""
        log.info("ESP MCP Server Started. Waiting for input...")
        log.info(f"Python version: {sys.version}")
        
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                
                self.request_count += 1
                
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    if response:
                        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                        sys.stdout.flush()
                except json.JSONDecodeError as e:
                    log.error(f"Failed to decode JSON: {e}")
                except Exception as e:
                    log.error(f"Critical Error (request #{self.request_count}): {traceback.format_exc()}")
                    
        except KeyboardInterrupt:
            log.info("Received interrupt signal")
        finally:
            log.info(f"Server Stopped (processed {self.request_count} requests)")


# ============ Entry Point ============
def main():
    server = ESPMCPServer()
    server.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("ESP MCP server stopped by user")
        sys.exit(0)
    except Exception as e:
        log.error(f"ESP MCP server error: {e}", exc_info=True)
        sys.exit(1)
