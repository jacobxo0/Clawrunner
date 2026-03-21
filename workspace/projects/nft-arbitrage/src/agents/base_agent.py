"""
Abstract base class for all agents in the system.
"""

from abc import ABC, abstractmethod


class BaseAgent(ABC):

    @abstractmethod
    async def evaluate(self, *args, **kwargs):
        """Evaluate input and return a structured result."""
        ...
