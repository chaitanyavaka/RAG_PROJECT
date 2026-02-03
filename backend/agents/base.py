from abc import ABC, abstractmethod
from ..mcp.protocol import MCPMessage, MessageType
from ..mcp.broker import broker

class BaseAgent(ABC):
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        broker.register(self.agent_id, self.receive_message)

    @abstractmethod
    async def process_message(self, message: MCPMessage):
        """Logic to handle incoming messages."""
        pass

    async def receive_message(self, message: MCPMessage):
        """Callback for the broker."""
        await self.process_message(message)

    async def send_message(self, receiver: str, type: MessageType, payload: dict, trace_id: str = None):
        """Helper to send messages via broker."""
        msg = MCPMessage(
            sender=self.agent_id,
            receiver=receiver,
            type=type,
            payload=payload,
            trace_id=trace_id
        )
        await broker.send(msg)
