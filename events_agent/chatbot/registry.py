import importlib
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
from .tool import BaseTool

console = Console()

class ToolRegistry:    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        console.print(f"[green]✓[/green] Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found")
        return self._tools[name]
    
    def list_tools(self) -> List[str]:
        return list(self._tools.keys())
    
    def get_openai_tools(self) -> List[Dict[str, Any]]:
        return [tool.get_tools() for tool in self._tools.values()]
    
    def auto_discover_tools(self, tools_dir: str = "tools/calendar") -> None:
        tools_path = Path(tools_dir)
        if not tools_path.exists():
            console.print(f"[yellow]Warning:[/yellow] Tools directory '{tools_dir}' not found")
            return
        
        for py_file in tools_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            module_name = f"tools.calendar.{py_file.stem}"
            try:
                module = importlib.import_module(module_name)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseTool) and 
                        attr != BaseTool):
                        tool_instance = attr()
                        self.register(tool_instance)
                        
            except Exception as e:
                console.print(f"[red]Error loading tool from {py_file}: {e}[/red]")
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        tool = self.get_tool(name)
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            console.print(f"[red]Error executing tool '{name}': {e}[/red]")
            return f"Error: {str(e)}" 
