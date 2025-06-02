### Goal
The goal of this MCP is to:
- Consolidate ESP-IDF and related project commands in one place.
- Simplify getting started using only LLM communication.

### How to contribute to the project

Simply find a command that is missing from this MCP and create a PR for it!

If you want someone to help you with this implementation, just open an issue.


### Notice
This project is currently a **Proof of Concept (PoC)** for an MCP server tailored for ESP-IDF workflows. 

**Current Capabilities:**
*   Supports basic ESP-IDF project build commands.
*   Flash built firmware to connected ESP devices with optional port specification.
*   Includes experimental support for automatic issue fixing based on build logs.

**Vision & Future Work:**
The long-term vision is to expand this MCP into a comprehensive toolkit for interacting with embedded devices, potentially integrating with home assistant platforms, and streamlining documentation access for ESP-IDF and related technologies. 

We envision features such as:
*   Broader ESP-IDF command support (e.g., `monitor`, `menuconfig` interaction if feasible).
*   Device management and information retrieval.
*   Integration with other embedded development tools and platforms.

Your ideas and contributions are welcome! Please feel free to discuss them by opening an issue.


### Install  

First, clone this MCP repository:  

```bash
git clone git@github.com:horw/esp-mcp.git
```  

Then, configure it in your chatbot. 

The JSON snippet below is an example of how you might configure this `esp-mcp` server within a chatbot or an agent system that supports the Model Context Protocol (MCP). The exact configuration steps and format may vary depending on the specific chatbot system you are using. Refer to your chatbot's documentation for details on how to integrate MCP servers.

```json
{
    "mcpServers": {
        "esp-run": { // "esp-run" is an arbitrary name you can assign to this server configuration.
            "command": "<path_to_uv_or_python_executable>",
            "args": [
                "--directory",
                "<path_to_cloned_esp-mcp_repository>", // e.g., /path/to/your/cloned/esp-mcp
                "run",
                "main.py" // If using python directly, this might be just "main.py" and `command` would be your python interpreter
            ],
            "env": {
                "IDF_PATH": "<path_to_your_esp-idf_directory>" // e.g., ~/esp/esp-idf or C:\\Espressif\\frameworks\\esp-idf
            }
        }
    }
}
```

A few notes on the configuration:

*   **`command`**: This should be the full path to your `uv` executable if you are using it, or your Python interpreter (e.g., `/usr/bin/python3` or `C:\\Python39\\python.exe`) if you plan to run `main.py` directly.
*   **`args`**:
    *   The first argument to `--directory` should be the absolute path to where you cloned the `esp-mcp` repository.
    *   If you're using `uv`, the arguments `run main.py` are appropriate. If you're using Python directly, you might only need `main.py` in the `args` list, and ensure your `command` points to the Python executable.
*   **`IDF_PATH`**: This environment variable must point to the root directory of your ESP-IDF installation. ESP-IDF is Espressif's official IoT Development Framework. If you haven't installed it, please refer to the [official ESP-IDF documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/index.html) for installation instructions.

### Usage

Once the `esp-mcp` server is configured and running, your LLM or chatbot can interact with it using the tools defined in this MCP. For example, you could ask your chatbot to:

*   "Build the project located at `/path/to/my/esp-project` using the `esp-mcp`."
*   "Clean the build files for the ESP32 project in the `examples/hello_world` directory."
*   "Flash the firmware to my connected ESP32 device for the project in `my_app`."

The MCP server will then execute the corresponding ESP-IDF commands (like `idf.py build`, `idf.py fullclean`, `idf.py flash`) based on the tools implemented in `main.py`.

The `result.gif` below shows an example interaction:

![Result](./result.gif)
