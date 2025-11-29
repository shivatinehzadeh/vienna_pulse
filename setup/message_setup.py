from abc import ABC, abstractmethod

class BaseMessageProvider(ABC):
    @abstractmethod
    async def send_message(self, to: str, message: str) -> dict:
        pass