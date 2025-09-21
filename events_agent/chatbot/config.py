import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

load_dotenv(override=True)

@dataclass
class Config:    
    openai_api_key: str
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None

    def __post_init__(self):
        if self.model is None:
            self.model = "gpt-4o-mini"
        if self.max_tokens is None:
            self.max_tokens = 1000
        if self.temperature is None:
            self.temperature = 0.7
        if self.system_prompt is None:
            self.system_prompt = "You are a helpful assistant for DSCubed."

    
    @classmethod
    def from_env(cls) -> "Config":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API Key is not present.")
        
        max_tokens = os.getenv("MAX_TOKENS")
        temperature = os.getenv("TEMPERATURE")
        
        return cls(
            openai_api_key=api_key,
            max_tokens=int(max_tokens) if max_tokens else None,
            temperature=float(temperature) if temperature else None,
            system_prompt=os.getenv("SYSTEM_PROMPT"),
        )
