from typing import List
from tools.tool import BaseTool, Params

class Calculator(BaseTool):    
    @property
    def name(self) -> str:
        return "Calculator"
    
    @property
    def description(self) -> str:
        return "Simple calculator"
    
    @property
    def parameters(self) -> List[Params]:
        return [
            Params(
                name="expression",
                type="string",
                description="expression for Calculator to solve"
            )
        ]
    
    def execute(self, expression: str) -> str:
        try:
            allowed_chars = set('0123456789+-*/.() ')
            for c in expression:
                if c not in allowed_chars:
                    return "Invalid character in expression"
            
            result = eval(expression)
            return f"{expression} = {result}"
            
        except ZeroDivisionError:
            return "ZeroDivisionError, do not divide by 0"
        except Exception as e:
            return f"Error: {str(e)}" 
