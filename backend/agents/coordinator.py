import asyncio
import uuid
from .base import BaseAgent
from .ingestion import IngestionAgent
from .retrieval import RetrievalAgent
from .response import LLMResponseAgent
from ..mcp.protocol import MCPMessage, MessageType

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CoordinatorAgent")
        self.pending_requests = {} # trace_id -> future
        
        # Initialize other agents
        self.ingestion_agent = IngestionAgent()
        self.retrieval_agent = RetrievalAgent()
        self.llm_agent = LLMResponseAgent()

    async def process_message(self, message: MCPMessage):
        # Handle responses from valid agents
        if message.trace_id in self.pending_requests:
            # If we were waiting for this response, set the result
            # But the flow is multi-step, so we need to know WHICH step we are at.
            # Simplified flow:
            # 1. Coordinator blocks on Retrieval
            # 2. Coordinator blocks on LLM
            
            # Since we can't easily block in a simple message handler without proper state machine,
            # we will assume the Pending Request is an asyncio.Future that the API endpoint is awaiting.
            # However, since the response comes asynchronously, we need to route it.
            
            # For simplicity in this async API:
            # The API endpoint will subscribe to a specific Trace ID?
            # Or we simplify and don't use the Broker for the Coordinator -> API return (that's internal).
            
            # Let's use a Future store
            future = self.pending_requests.get(message.trace_id)
            if future and not future.done():
                future.set_result(message)

    async def handle_user_query(self, query: str):
        trace_id = str(uuid.uuid4())
        
        # Step 1: Retrieve
        req_msg = MCPMessage(
            sender=self.agent_id,
            receiver="RetrievalAgent",
            type=MessageType.TASK_REQUEST,
            payload={"task": "retrieve_context", "query": query, "n_results": 3},
            trace_id=trace_id
        )
        
        # Setup future for Step 1
        retrieval_future = asyncio.get_running_loop().create_future()
        self.pending_requests[trace_id] = retrieval_future
        
        await self.send_message(req_msg.receiver, req_msg.type, req_msg.payload, req_msg.trace_id)
        
        # Wait for Retrieval Result
        try:
            retrieval_result = await asyncio.wait_for(retrieval_future, timeout=10.0)
        except asyncio.TimeoutError:
            return {"error": "Retrieval timed out"}
            
        if retrieval_result.type == MessageType.ERROR:
            return {"error": retrieval_result.payload.get("error")}
            
        context = retrieval_result.payload.get("context")
        
        # Step 2: LLM
        # Reset future for Step 2
        llm_future = asyncio.get_running_loop().create_future()
        self.pending_requests[trace_id] = llm_future
        
        await self.send_message(
            receiver="LLMResponseAgent",
            type=MessageType.TASK_REQUEST,
            payload={"task": "generate_response", "query": query, "context": context},
            trace_id=trace_id
        )
        
        try:
            llm_result = await asyncio.wait_for(llm_future, timeout=30.0)
        except asyncio.TimeoutError:
            return {"error": "LLM response timed out"}

        # Cleanup
        del self.pending_requests[trace_id]
        
        return {
            "answer": llm_result.payload.get("answer"),
            "context": context,
            "trace_id": trace_id
        }

    async def handle_file_upload(self, file_path: str, file_name: str):
        trace_id = str(uuid.uuid4())
        
        ingest_future = asyncio.get_running_loop().create_future()
        self.pending_requests[trace_id] = ingest_future
        
        await self.send_message(
            receiver="IngestionAgent",
            type=MessageType.TASK_REQUEST,
            payload={"task": "ingest_file", "file_path": file_path, "file_name": file_name},
            trace_id=trace_id
        )
        
        try:
            result = await asyncio.wait_for(ingest_future, timeout=60.0)
            return result.payload
        except asyncio.TimeoutError:
            return {"error": "Ingestion timed out"}
        finally:
             if trace_id in self.pending_requests:
                del self.pending_requests[trace_id]

# Singleton coordinator
coordinator = CoordinatorAgent()
