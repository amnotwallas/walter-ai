import groq
from app.core.config import get_settings

class LLMProvider:
    """
    Provider class for LLM interactions using Groq SDK.
    Handles client initialization and completion requests.
    """
    def __init__(self):
        settings = get_settings()
        self.client = groq.Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.MODEL_NAME

    def completion(self, messages: list, stream: bool = False):
        """
        Generates a completion based on provided messages.
        
        Args:
            messages (list): List of message dictionaries (role/content).
            stream (bool): Whether to stream the response.
            
        Returns:
            The completion response or stream.
        """
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.5,
            stream=stream
        )
