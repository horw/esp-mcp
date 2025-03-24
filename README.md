Currently, this MCP supports simple project builds with logging, and automatic issue fixing based on logs for esp-idf build command.

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