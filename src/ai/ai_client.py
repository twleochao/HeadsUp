import abc
import openai
from typing import Any, Dict, List


class AIClient(abc.ABC):
    @abc.abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Send a chat-completion style request.

        :param messages: List of {"role": "...", "content": "..."} dicts.
        :param max_tokens: maximum tokens to generate.
        :param temperature: sampling temperature.
        :returns: the model’s reply text.
        """
        raise NotImplementedError


class OpenAIAPIClient(AIClient):
    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        openai.api_key = api_key
        self.model = model

    def generate(
        self,
        messages: List[Dict[str, Any]],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        return response.choices[0].message.content
