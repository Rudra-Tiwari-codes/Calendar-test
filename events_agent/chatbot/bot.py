import json
from openai import OpenAI
from rich.console import Console
from .config import Config
from tools.registry import ToolRegistry
from util.formats import format_message, format_error, format_tool_call, format_welcome, format_tool_result
import asyncio

console = Console()

async def async_input(prompt: str = "") -> str:
    return await asyncio.to_thread(input, prompt)


class Chatbot:    
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key)
        self.tool_registry = ToolRegistry()
        self.messages = []
        
        self.messages.append({
            "role": "system",
            "content": config.system_prompt
        })

    
    def register_tool(self, tool) -> None:
        self.tool_registry.register(tool)

    
    def auto_discover_tools(self) -> None:
        self.tool_registry.auto_discover_tools()

    
    async def execute_tools(self, tool_calls) -> None:
        tasks = []

        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            format_tool_call(name, args)

            task = asyncio.to_thread(self.tool_registry.execute_tool, name, **args)
            tasks.append((tool_call, task))

        results = await asyncio.gather(*(task for _, task in tasks))

        for (tool_call, _), result in zip(tasks, results):
            format_tool_result(tool_call.function.name, result)

            self.messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }]
            })

            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
    

    async def user_prompt(self, message: str) -> str:
        self.messages.append({
            "role": "user",
            "content": message
        })
        
        try:
            tools = self.tool_registry.get_openai_tools()
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.config.model,
                messages=self.messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )
            
            message = response.choices[0].message
            
            if message.tool_calls:
                await self.execute_tools(message.tool_calls)

                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.config.model,
                    messages=self.messages,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    tools=tools if tools else None,
                    tool_choice="auto" if tools else None
                )
                message = response.choices[0].message
            
            self.messages.append({
                "role": "assistant",
                "content": message.content
            })
            
            return message.content
        
            
        except Exception as e:
            error_msg = f"OpenAI Error: {str(e)}"
            format_error(error_msg)
            return error_msg
    
    
    async def run(self) -> None:
        format_welcome()
        console.print("[cyan]🔍 Discovering tools...[/cyan]")
        self.auto_discover_tools()

        try:
            while True:
                prompt = await async_input("\nUser: ")
                format_message("user", prompt)

                response = await self.user_prompt(prompt)
                format_message("assistant", response)

        except KeyboardInterrupt:
            print("Exiting Chatbot")
        except Exception as e:
            format_error(f"Error: {str(e)}")
