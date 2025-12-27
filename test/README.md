# ESP-MCP Test Suite

This directory contains integration tests for the ESP-MCP tools.

## Setup

1. **Copy the configuration template:**
   ```bash
   cp test/config.example.py test/config.py
   ```

2. **Edit `test/config.py`** with your local paths:
   ```python
   IDF_PATH = "/path/to/your/esp-idf"
   PROJECT_PATH = "/path/to/esp-idf/examples/get-started/hello_world"
   TARGET_CHIP = "esp32c3"  # or esp32, esp32s3, etc.
   SERIAL_PORT = None  # or "/dev/ttyUSB0" for Linux, "/dev/cu.usbserial-*" for macOS
   ```

3. **Ensure ESP-IDF is installed** at the specified path.

4. **Ensure the test project exists** at the specified path.

## Running Tests

### Method 1: Direct Function Testing

Run tests by directly importing and calling the functions:

```bash
python test/test_mcp_tools.py
```

Or with environment variables:
```bash
IDF_PATH=/path/to/esp-idf \
TEST_PROJECT_PATH=/path/to/project \
TEST_TARGET_CHIP=esp32c3 \
python test/test_mcp_tools.py
```

### Method 2: Agent MCP Testing (Recommended)

Test the MCP tools through a real MCP agent connection. This verifies that the tools work correctly in the actual MCP environment.

#### Prerequisites

1. **Configure MCP Server** in your agent/client (e.g., Cursor, Claude Desktop, etc.)

   Example configuration for Cursor:
   ```json
   {
       "mcpServers": {
           "esp-mcp": {
               "command": "uv",
               "args": [
                   "--directory",
                   "/path/to/esp-mcp",
                   "run",
                   "main.py"
               ],
               "env": {
                   "IDF_PATH": "/path/to/esp-idf"
               }
           }
       }
   }
   ```

2. **Restart your agent/client** to load the MCP server configuration

3. **Verify MCP connection** - The agent should be able to see the ESP-MCP tools

#### Testing via Agent

Once the MCP server is configured and connected, you can test the tools through the agent:

**Example test prompts:**

1. **Test install:**
   ```
   Use the run_esp_idf_install tool with idf_path="/path/to/esp-idf"
   ```

2. **Test set target:**
   ```
   Use setup_project_esp_target with:
   - project_path="/path/to/project"
   - target="esp32c3"
   - idf_path="/path/to/esp-idf"
   ```

3. **Test build:**
   ```
   Use build_esp_project with:
   - project_path="/path/to/project"
   - idf_path="/path/to/esp-idf"
   ```

4. **Test pytest:**
   ```
   Use run_pytest with:
   - project_path="/path/to/project"
   - test_path="pytest_hello_world.py"
   - pytest_args="--target=esp32c3 -v"
   - idf_path="/path/to/esp-idf"
   ```

5. **Full workflow test:**
   ```
   Test the complete ESP-IDF workflow:
   1. Run run_esp_idf_install with idf_path="/path/to/esp-idf"
   2. Run setup_project_esp_target for esp32c3
   3. Run build_esp_project
   4. Run run_pytest with --target=esp32c3
   ```

#### Verification Checklist

- [ ] MCP server starts without errors
- [ ] All tools are visible to the agent
- [ ] Tools accept `idf_path` parameter correctly
- [ ] Tools return expected output format
- [ ] Error handling works correctly
- [ ] Tools work with both `idf_path` parameter and `IDF_PATH` env var

#### Troubleshooting Agent Connection

If the agent cannot connect to the MCP server:

1. **Check server startup:**
   ```bash
   python /path/to/esp-mcp/main.py
   ```
   Should start without errors (will wait for stdio input)

2. **Check configuration:**
   - Verify paths are absolute
   - Check Python executable path
   - Ensure dependencies are installed

3. **Check logs:**
   - Look for import errors
   - Check for missing dependencies
   - Verify ESP-IDF path is correct

4. **See TROUBLESHOOTING.md** for detailed troubleshooting guide

## Test Flow

The test suite runs tests in the following sequence:

1. **run_esp_idf_install** - Verifies ESP-IDF installation and toolchain setup
2. **setup_project_esp_target** - Sets the target chip for the project
3. **build_esp_project** - Builds the ESP-IDF project
4. **run_pytest** - Runs pytest tests on the built firmware

## Configuration

### Environment Variables

All configuration values can be overridden using environment variables:

- `IDF_PATH` - ESP-IDF installation path
- `TEST_PROJECT_PATH` - Path to test project
- `TEST_TARGET_CHIP` - Target chip (esp32c3, esp32, esp32s3, etc.)
- `TEST_SERIAL_PORT` - Serial port for hardware tests (optional)

### config.py

The `config.py` file contains machine-specific settings and is git-ignored.
Do not commit this file. Use `config.example.py` as a template.

## Test Requirements

- Python 3.11+
- ESP-IDF installed and configured
- Test project (e.g., hello_world example)
- Hardware device (for pytest tests) - optional, can use host tests

## Troubleshooting

### Import Error: config.py not found
- Copy `config.example.py` to `config.py` and configure it

### ESP-IDF not found
- Check that `IDF_PATH` is set correctly
- Verify ESP-IDF is installed at the specified path

### Project not found
- Check that `PROJECT_PATH` points to a valid ESP-IDF project
- Ensure the project has a `CMakeLists.txt` file

### Serial port issues
- For Linux: `/dev/ttyUSB0`, `/dev/ttyACM0`
- For macOS: `/dev/cu.usbserial-*`, `/dev/cu.SLAB_USBtoUART`
- For Windows: `COM1`, `COM2`, etc.
- Leave `SERIAL_PORT` as `None` to auto-detect



