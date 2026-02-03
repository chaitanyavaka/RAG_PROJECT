# import chromadb # Moved to lazy init
# from chromadb.utils import embedding_functions # Moved to lazy init
from .base import BaseAgent
from ..mcp.protocol import MCPMessage, MessageType
import uuid

class RetrievalAgent(BaseAgent):
    def __init__(self):
        super().__init__("RetrievalAgent")
        self.client = None
        self.ef = None
        self.collection = None

    def _lazy_init(self):
        if self.client is None:
            print("[RetrievalAgent] Lazy initializing ChromaDB and Embeddings...")
            import chromadb
            from chromadb.utils import embedding_functions
            
            self.client = chromadb.PersistentClient(path="./chroma_db")
            # Use a simple default embedding function (all-MiniLM-L6-v2 is standard)
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            self.collection = self.client.get_or_create_collection(name="rag_docs", embedding_function=self.ef)
            print("[RetrievalAgent] Initialization complete.")

    async def process_message(self, message: MCPMessage):
        # Ensure initialized
        self._lazy_init()
        
        if message.type == MessageType.TASK_REQUEST:
            task = message.payload.get("task")
            if task == "embed_chunks":
                await self.embed_chunks(message)
            elif task == "retrieve_context":
                await self.retrieve_context(message)

    async def embed_chunks(self, message: MCPMessage):
        chunks = message.payload.get("chunks", [])
        metadata = message.payload.get("metadata", {})
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [metadata for _ in chunks]
        
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        # Ack (no need to reply to IngestionAgent usually, but good for tracing)
        # print(f"[RetrievalAgent] Indexed {len(chunks)} chunks.")

    async def retrieve_context(self, message: MCPMessage):
        query = message.payload.get("query")
        n_results = message.payload.get("n_results", 3)
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Flatten results
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        
        context_str = "\n".join([f"Source: {m.get('source', 'unknown')}\nContent: {d}" for d, m in zip(documents, metadatas)])
        
        await self.send_message(
            receiver=message.sender, # Likely LLMResponseAgent or Coordinator
            type=MessageType.CONTEXT_RESPONSE,
            payload={
                "context": context_str,
                "original_query": query
            },
            trace_id=message.trace_id
        )
