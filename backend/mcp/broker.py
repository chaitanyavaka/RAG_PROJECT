import asyncio
from typing import Dict, Callable, Awaitable
from .protocol import MCPMessage

class MessageBroker:
    def __init__(self):
        self.subscribers: Dict[str, Callable[[MCPMessage], Awaitable[None]]] = {}
        self.message_log: list[MCPMessage] = []

    def register(self, agent_id: str, callback: Callable[[MCPMessage], Awaitable[None]]):
        """Registers an agent to receive messages."""
        self.subscribers[agent_id] = callback
        print(f"[Broker] Registered agent: {agent_id}")

    async def send(self, message: MCPMessage):
        """Routes a message to the receiver."""
        self.message_log.append(message)
        
        # Log for visual tracing aid
        print(f"[MCP] {message.sender} -> {message.receiver} [{message.type}]: {str(message.payload)[:100]}...")

        if message.receiver in self.subscribers:
            try:
                await self.subscribers[message.receiver](message)
            except Exception as e:
                print(f"[Broker] Error delivering message to {message.receiver}: {e}")
                # Ideally send an ERROR message back to sender
        else:
            print(f"[Broker] Warning: Receiver '{message.receiver}' not found.")

# Global broker instance for simplicity in this demo
broker = MessageBroker()
