"""
Test configuration template.

Copy this file to config.py and fill in your local paths.
config.py is git-ignored and should not be committed.
"""
import os

# ESP-IDF installation path
# Can be overridden by IDF_PATH environment variable
IDF_PATH = os.getenv("IDF_PATH", "/path/to/your/esp-idf")

# Test project path (ESP-IDF example project)
PROJECT_PATH = os.getenv("TEST_PROJECT_PATH", "/path/to/esp-idf/examples/get-started/hello_world")

# Test file name
PYTEST_FILE = "pytest_hello_world.py"

# Target chip for testing
TARGET_CHIP = os.getenv("TEST_TARGET_CHIP", "esp32c3")

# Serial port (optional, will auto-detect if not specified)
SERIAL_PORT = os.getenv("TEST_SERIAL_PORT", None)

# SDKCONFIG defaults files for testing (optional, will trigger full rebuild)
# Multiple files can be specified separated by semicolons
# Example: "sdkconfig.defaults;sdkconfig.ci.release"
SDKCONFIG_DEFAULTS = os.getenv("TEST_SDKCONFIG_DEFAULTS", None)

