from setup.message_setup import BaseMessageProvider

class MockMessageProvider(BaseMessageProvider):
    async def send_message(self, to: str, message: str) -> dict:
        return {
            "status": "success",
            "provider": "mock",
            "to": to,
            "message": message,
            "description": "Message NOT actually sent. This is a mock provider."
        }