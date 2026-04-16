import openai
import textwrap
from sqlalchemy import delete
from sqlalchemy.future import select
from app.models.knowledge_chunk import KnowledgeChunk
from app.core.config import settings

async def ingest_text(db, business_id, text: str, source: str):
    # Delete old chunks for this source
    await db.execute(delete(KnowledgeChunk).where(
        KnowledgeChunk.business_id == business_id,
        KnowledgeChunk.source == source
    ))
    
    # Chunk into ~400-word pieces with 50-word overlap
    words = text.split()
    chunks = [' '.join(words[i:i+400]) for i in range(0, len(words), 350)]
    
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    for chunk in chunks:
        if not chunk.strip(): continue
        resp = await client.embeddings.create(input=chunk, model='text-embedding-ada-002')
        embedding = resp.data[0].embedding
        db.add(KnowledgeChunk(business_id=business_id, source=source, content=chunk, embedding=embedding))
        
    await db.commit()

async def search_knowledge(db, business_id, query: str, top_k=5) -> str:
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    resp = await client.embeddings.create(input=query, model='text-embedding-ada-002')
    qvec = resp.data[0].embedding
    
    results = await db.execute(
        select(KnowledgeChunk.content)
        .where(KnowledgeChunk.business_id == business_id)
        .order_by(KnowledgeChunk.embedding.cosine_distance(qvec))
        .limit(top_k)
    )
    chunks = results.scalars().all()
    return '\n\n'.join(chunks) if chunks else ''
