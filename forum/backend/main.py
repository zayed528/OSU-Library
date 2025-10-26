"""
FastAPI backend for the community forum.
Provides REST API endpoints for questions and replies.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime
from decimal import Decimal

import forum_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OSU Library Community Forum API",
    description="API for managing forum questions and replies",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response validation
class QuestionCreate(BaseModel):
    """Request model for creating a question."""
    title: str
    content: str
    author: str


class ReplyCreate(BaseModel):
    """Request model for creating a reply."""
    content: str
    author: str


class Reply(BaseModel):
    """Reply model."""
    replyId: str
    content: str
    author: str
    createdAt: int


class Question(BaseModel):
    """Question model."""
    postId: str
    postType: str
    title: str
    content: str
    author: str
    createdAt: int
    replyCount: int
    replies: List[Reply] = []


def convert_decimals(obj):
    """Convert Decimal objects to int/float for JSON serialization."""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "message": "OSU Library Community Forum API",
        "version": "1.0.0",
        "endpoints": {
            "questions": "/api/questions",
            "question_detail": "/api/questions/{post_id}",
            "create_question": "POST /api/questions",
            "add_reply": "POST /api/questions/{post_id}/replies",
            "search": "/api/questions/search?q={search_term}"
        }
    }


@app.get("/api/questions", response_model=List[Question])
async def get_questions(limit: int = 50):
    """
    Get all questions, ordered by creation date (newest first).
    
    Args:
        limit: Maximum number of questions to return (default 50)
    """
    try:
        questions = forum_store.list_questions(limit=limit)
        # Convert Decimal objects to int
        questions = convert_decimals(questions)
        return questions
    except Exception as e:
        logger.error(f"Error fetching questions: {e}")
        raise HTTPException(status_code=500, detail="Error fetching questions")


@app.get("/api/questions/{post_id}", response_model=Question)
async def get_question(post_id: str):
    """
    Get a specific question by ID.
    
    Args:
        post_id: Question post ID
    """
    try:
        question = forum_store.get_question(post_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        question = convert_decimals(question)
        return question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching question {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching question")


@app.post("/api/questions", response_model=Question, status_code=201)
async def create_question(question: QuestionCreate):
    """
    Create a new question.
    
    Args:
        question: Question data (title, content, author)
    """
    try:
        new_question = forum_store.create_question(
            title=question.title,
            content=question.content,
            author=question.author
        )
        new_question = convert_decimals(new_question)
        return new_question
    except Exception as e:
        logger.error(f"Error creating question: {e}")
        raise HTTPException(status_code=500, detail="Error creating question")


@app.post("/api/questions/{post_id}/replies", response_model=Question)
async def add_reply(post_id: str, reply: ReplyCreate):
    """
    Add a reply to a question.
    
    Args:
        post_id: Question post ID
        reply: Reply data (content, author)
    """
    try:
        updated_question = forum_store.add_reply(
            post_id=post_id,
            content=reply.content,
            author=reply.author
        )
        updated_question = convert_decimals(updated_question)
        return updated_question
    except Exception as e:
        logger.error(f"Error adding reply: {e}")
        raise HTTPException(status_code=500, detail="Error adding reply")


@app.get("/api/questions/search/", response_model=List[Question])
async def search_questions(q: str):
    """
    Search questions by title or content.
    
    Args:
        q: Search query term
    """
    if not q or len(q.strip()) == 0:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    try:
        results = forum_store.search_questions(q)
        results = convert_decimals(results)
        return results
    except Exception as e:
        logger.error(f"Error searching questions: {e}")
        raise HTTPException(status_code=500, detail="Error searching questions")


@app.delete("/api/questions/{post_id}")
async def delete_question(post_id: str):
    """
    Delete a question.
    
    Args:
        post_id: Question post ID
    """
    try:
        forum_store.delete_question(post_id)
        return {"message": "Question deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting question: {e}")
        raise HTTPException(status_code=500, detail="Error deleting question")


#  Library Tables API 
@app.get("/api/library/tables")
async def get_all_library_tables():
    """Get all library tables from DynamoDB"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app'))
        from store_dynamo import get_all_tables
        
        tables = get_all_tables()
        return {"tables": convert_decimals(tables), "count": len(tables)}
    except Exception as e:
        logger.error(f"Error getting all tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/library/tables/floor/{floor_id}")
async def get_library_tables_by_floor(floor_id: str):
    """Get all tables for a specific floor"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app'))
        from store_dynamo import get_floor_tables
        
        tables = get_floor_tables(floor_id)
        return {"floorId": floor_id, "tables": convert_decimals(tables), "count": len(tables)}
    except Exception as e:
        logger.error(f"Error getting floor tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/library/tables/{table_id}")
async def get_library_table(table_id: str):
    """Get a specific library table by ID"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app'))
        from store_dynamo import get_table
        
        table = get_table(table_id)
        if not table:
            raise HTTPException(status_code=404, detail=f"Table {table_id} not found")
        return convert_decimals(table)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting table: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
