"""Followup question generator."""

from typing import Dict, Any, Optional, List
from src.utils.logging import get_logger
from .llm_client import LLMClient
from .exceptions import LLMClientException
from .models import Text2SQLState

logger = get_logger(__name__)


class FollowupQuestionGenerator:
    """Generator for followup questions based on database metadata."""
    
    SYSTEM_PROMPT = """
    You are an expert at analyzing database schemas and generating relevant business questions.
    Based on the provided database metadata, generate natural language questions that users might ask
    to analyze their business data.
    
    Rules:
    - Generate questions that are relevant to the tables, columns, and relationships described in the metadata
    - Questions should be business-focused and actionable
    - Questions should be clear and specific
    - Each question should be on a separate line
    - Do not include numbering, bullets, or markdown formatting
    - Output only the questions, one per line
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize followup question generator.
        
        Args:
            llm_client: LLM client instance (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()
        logger.debug("Followup question generator initialized")
    
    def generate_followup_questions(
        self,
        state: Text2SQLState,
        count: int = 3,
    ) -> Dict[str, Any]:
        """
        Generate suggested questions based on the database metadata.
        
        Args:
            state: Current workflow state
            count: Number of suggested questions to generate (default: 3)
            
        Returns:
            Dictionary with 'followup_que' key containing list of questions
            
        Raises:
            LLMClientException: If question generation fails
        """
        try:
            metadata = state.get("metadata", "")
            
            if not metadata:
                logger.warning("No metadata available for generating followup questions")
                return {"followup_que": []}
            
            user_prompt = f"""
            Database schema metadata: {metadata}
            
            Generate exactly {count} relevant business questions that can be answered using this database.
            Output only the questions, one per line, without any numbering or formatting.
            """
            
            logger.debug(f"Generating {count} followup questions")
            
            questions_text = self.llm_client.generate_completion(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model="gpt-4o-mini",
                temperature=0.7,  # Higher temperature for more creative questions
            )
            
            # Extract questions from response
            questions_text = questions_text.strip()
            
            # Split by newlines and clean up
            questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
            
            # Remove any numbering or bullets if present
            questions = [q.lstrip('0123456789.-) ').strip() for q in questions]
            
            # Return the requested number of questions
            questions = questions[:count]
            
            logger.debug(f"Generated {len(questions)} followup questions")
            
            return {"followup_que": questions}
        
        except LLMClientException:
            raise
        except Exception as e:
            logger.error(f"Error generating suggested questions: {e}")
            raise LLMClientException(
                f"Failed to generate followup questions: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e

