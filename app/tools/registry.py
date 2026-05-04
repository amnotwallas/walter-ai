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
