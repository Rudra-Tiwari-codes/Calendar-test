from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel


class Params(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    enum: List[str] = None


class BaseTool(ABC):    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[Params]:
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass
    
    def get_tools(self) -> Dict[str, Any]:
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        } 
    