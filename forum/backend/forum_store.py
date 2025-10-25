"""
DynamoDB store for forum posts and replies.
Handles CRUD operations for the community forum.
"""

import os
import boto3
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
TABLE_NAME = 'ForumPosts'

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)


def now() -> int:
    """Return current Unix timestamp in milliseconds."""
    return int(datetime.now().timestamp() * 1000)


def decimal_to_int(obj):
    """Convert Decimal objects to int for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError


def create_question(title: str, content: str, author: str) -> Dict:
    """
    Create a new question post.
    
    Args:
        title: Question title
        content: Question description/content
        author: Author name
        
    Returns:
        Created question object
    """
    post_id = str(uuid.uuid4())
    timestamp = now()
    
    question = {
        'postId': post_id,
        'postType': 'question',
        'title': title,
        'content': content,
        'author': author,
        'createdAt': timestamp,
        'replyCount': 0,
        'replies': []
    }
    
    try:
        table.put_item(Item=question)
        logger.info(f"Created question: {post_id}")
        return question
    except Exception as e:
        logger.error(f"Error creating question: {e}")
        raise


def get_question(post_id: str) -> Optional[Dict]:
    """
    Get a question by ID.
    
    Args:
        post_id: Question post ID
        
    Returns:
        Question object or None if not found
    """
    try:
        response = table.get_item(Key={'postId': post_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting question {post_id}: {e}")
        raise


def list_questions(limit: int = 50) -> List[Dict]:
    """
    List all questions, ordered by creation date (newest first).
    
    Args:
        limit: Maximum number of questions to return
        
    Returns:
        List of question objects
    """
    try:
        response = table.query(
            IndexName='postType-createdAt-index',
            KeyConditionExpression='postType = :type',
            ExpressionAttributeValues={':type': 'question'},
            ScanIndexForward=False,  # Descending order (newest first)
            Limit=limit
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error listing questions: {e}")
        raise


def add_reply(post_id: str, content: str, author: str) -> Dict:
    """
    Add a reply to a question.
    
    Args:
        post_id: Question post ID
        content: Reply content
        author: Reply author name
        
    Returns:
        Updated question object
    """
    timestamp = now()
    reply_id = str(uuid.uuid4())
    
    reply = {
        'replyId': reply_id,
        'content': content,
        'author': author,
        'createdAt': timestamp
    }
    
    try:
        # Update the question with the new reply
        response = table.update_item(
            Key={'postId': post_id},
            UpdateExpression='SET replies = list_append(if_not_exists(replies, :empty_list), :reply), replyCount = replyCount + :inc',
            ExpressionAttributeValues={
                ':reply': [reply],
                ':inc': 1,
                ':empty_list': []
            },
            ReturnValues='ALL_NEW'
        )
        logger.info(f"Added reply to question: {post_id}")
        return response['Attributes']
    except Exception as e:
        logger.error(f"Error adding reply to {post_id}: {e}")
        raise


def search_questions(search_term: str) -> List[Dict]:
    """
    Search questions by title or content.
    Note: This is a simple scan-based search. For production, consider using
    Amazon OpenSearch or CloudSearch for better performance.
    
    Args:
        search_term: Term to search for
        
    Returns:
        List of matching question objects
    """
    try:
        response = table.scan(
            FilterExpression='contains(title, :term) OR contains(content, :term)',
            ExpressionAttributeValues={':term': search_term}
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error searching questions: {e}")
        raise


def delete_question(post_id: str) -> bool:
    """
    Delete a question.
    
    Args:
        post_id: Question post ID
        
    Returns:
        True if deleted successfully
    """
    try:
        table.delete_item(Key={'postId': post_id})
        logger.info(f"Deleted question: {post_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting question {post_id}: {e}")
        raise
