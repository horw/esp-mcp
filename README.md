### Goal
The goal of this MCP is to:
- Consolidate ESP-IDF and related project commands in one place.
- Simplify getting started using only LLM communication.

### How to contribute to the project

Simply find a command that is missing from this MCP and create a PR for it!

If you want someone to help you with this implementation, just open an issue.


### Notice
This is just a proof of concept of MCP. As I see it, much can be done to make it more useful with embedded devices, home assistants, or documentation. If you have any ideas, we can discuss them in the issues.


### Install  

First, clone this MCP repository:  

```bash
git clone git@github.com:horw/esp-mcp.git
```  

Then, configure it in your chatbot. 


```json
{
    "mcpServers": {
        "esp-run": {
            "command": "/home/horw/.pyenv/shims/uv",
            "args": [
                "--directory",
                "/home/horw/PycharmProjects/esp-mcp", <- your cloned path
                "run",
                "main.py"
            ],
            "env": {
                "IDF_PATH": "~/esp-idf" <- your ESP-IDF path
            }
        }
    }
}
```  
![Result](./result.gif)
