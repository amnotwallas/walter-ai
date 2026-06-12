import json
from typing import Dict, List, Callable, Any
from app.core.logger import get_logger

logger = get_logger(__name__)

class ToolRegistry:
    """
    Registry for managing LLM tools and their schemas.
    Provides a central point for tool lookup and execution.
    """
    _instance = None
    _tools: Dict[str, Callable] = {}
    _schemas: List[Dict[str, Any]] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
        return cls._instance

    def register_tool(self, schema: Dict[str, Any], func: Callable):
        """Registers a tool with its schema and implementation."""
        name = schema["function"]["name"]
        self._tools[name] = func
        self._schemas.append(schema)
        logger.info(f"Registered tool: {name}")

    def tool(self, description: str, param_descriptions: Dict[str, str] = None, enums: Dict[str, List[Any]] = None):
        """
        Decorator to register a function as a tool for the LLM.
        Automatically infers types, names, and requirements from the function signature.
        """
        import inspect
        param_descriptions = param_descriptions or {}
        enums = enums or {}

        def decorator(func: Callable):
            sig = inspect.signature(func)
            properties = {}
            required = []
            
            type_mapping = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object"
            }
            
            for param_name, param in sig.parameters.items():
                if param.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
                    continue
                
                annotation = param.annotation
                json_type = type_mapping.get(annotation, "string")
                
                prop_schema = {
                    "type": json_type,
                    "description": param_descriptions.get(param_name, f"The {param_name} parameter.")
                }
                
                if param_name in enums:
                    prop_schema["enum"] = enums[param_name]
                
                properties[param_name] = prop_schema
                
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            schema = {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                    }
                }
            }
            
            if required:
                schema["function"]["parameters"]["required"] = required
                
            self.register_tool(schema, func)
            return func
        return decorator

    @property
    def tools(self) -> Dict[str, Callable]:
        return self._tools

    @property
    def schemas(self) -> List[Dict[str, Any]]:
        return self._schemas

    async def execute(self, name: str, **kwargs) -> str:
        """Executes a registered tool by name."""
        if name not in self._tools:
            logger.error(f"Tool not found: {name}")
            return f"Error: Tool '{name}' not found."
        
        try:
            func = self._tools[name]
            logger.info(f"Executing tool: {name} with args: {kwargs}")
            return await func(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}")
            return f"Error executing tool '{name}': {str(e)}"

tool_registry = ToolRegistry()
