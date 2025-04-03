Currently, this MCP supports simple project builds with logging, and automatic issue fixing based on logs for esp-idf build command.

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
