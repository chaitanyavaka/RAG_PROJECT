import os
import groq
from dotenv import load_dotenv
from .base import BaseAgent
from ..mcp.protocol import MCPMessage, MessageType

load_dotenv()

class LLMResponseAgent(BaseAgent):
    def __init__(self):
        super().__init__("LLMResponseAgent")
        self.client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

    async def process_message(self, message: MCPMessage):
        if message.type == MessageType.TASK_REQUEST:
            task = message.payload.get("task")
            if task == "generate_response":
                await self.generate_response(message)

    async def generate_response(self, message: MCPMessage):
        query = message.payload.get("query")
        context = message.payload.get("context", "")
        
        system_prompt = (
            "You are a helpful RAG Chatbot. Use the provided context to answer the user's question. "
            "If the answer is not in the context, say so. "
            "Cite the sources if available in the context."
        )
        
        user_prompt = f"Context:\n{context}\n\nQuestion: {query}"
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile", # Using a good model available on Groq
                temperature=0.1,
            )
            
            answer = chat_completion.choices[0].message.content
            
            await self.send_message(
                receiver=message.sender,
                type=MessageType.TASK_RESULT,
                payload={
                    "answer": answer,
                    "query": query
                },
                trace_id=message.trace_id
            )
        except Exception as e:
            await self.send_message(
                receiver=message.sender,
                type=MessageType.ERROR,
                payload={"error": str(e)},
                trace_id=message.trace_id
            )
