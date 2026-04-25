import json
from app.providers.llm_provider import LLMProvider
from app.tools.cv_tools import TOOLS_SCHEMA, AVAILABLE_TOOLS
from app.core.prompts import SYSTEM_PROMPT
from app.core.logger import get_logger

logger = get_logger(__name__)

class AgentService:
    def __init__(self):
        self.llm = LLMProvider()

    def _call_tool(self, tool_call):
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        function_to_call = AVAILABLE_TOOLS[function_name]
        
        logger.info(f"Executing Tool: {function_name} | Args: {function_args}")
        
        if function_args:
            return function_to_call(**function_args)
        return function_to_call()

    def get_streaming_response(self, user_query: str, history: list = []):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history, {"role": "user", "content": user_query}]
        
        logger.info(f"New Query: {user_query}")
        
        # 1. El Maestro decide
        response = self.llm.client.chat.completions.create(
            model=self.llm.model,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # 2. Si hay herramientas, las ejecutamos en silencio (para el usuario)
        if tool_calls:
            messages.append(response_message)
            for tool_call in tool_calls:
                function_response = self._call_tool(tool_call)
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": function_response,
                })
            
            # Streaming de la respuesta final con los datos ya cargados
            logger.info("Generating final response based on tool data...")
            stream = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=messages,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
        else:
            # Respuesta directa
            logger.info("Direct response initiated")
            stream = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=messages,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
