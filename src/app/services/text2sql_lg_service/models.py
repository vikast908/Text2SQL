"""Data models for Text2SQL service."""

from typing import TypedDict, Literal, List, Dict, Any, Optional


class Text2SQLState(TypedDict, total=False):
    """State model for Text2SQL workflow."""

    metadata: str
    input_text: str
    generated_sql_query: str
    cleaned_query: str
    is_valid_sql: bool
    is_unanswerable: bool
    unanswerable_reason: str
    data: List[Dict[str, Any]]
    summary: str
    chart: str
    followup_que: List[str]
    max_iterations: int
    retry_count: int
    error: Optional[str]
    error_details: Optional[Dict[str, Any]]


class Text2SQLRequest:
    """Request model for Text2SQL service."""
    
    def __init__(
        self,
        input_text: str,
        max_iterations: int = 3,
        metadata_path: Optional[str] = None,
    ):
        self.input_text = input_text
        self.max_iterations = max_iterations
        self.metadata_path = metadata_path
    
    def to_state(self) -> Text2SQLState:
        """Convert request to workflow state."""
        return {
            "input_text": self.input_text,
            "max_iterations": self.max_iterations,
            "retry_count": 0,
        }


class Text2SQLResponse:
    """Response model for Text2SQL service."""
    
    def __init__(
        self,
        sql_query: str,
        data: List[Dict[str, Any]],
        summary: str,
        followup_questions: List[str],
        chart: Optional[str] = None,
        metadata: Optional[str] = None,
    ):
        self.sql_query = sql_query
        self.data = data
        self.summary = summary
        self.followup_questions = followup_questions
        self.chart = chart
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "sql_query": self.sql_query,
            "data": self.data,
            "summary": self.summary,
            "followup_questions": self.followup_questions,
            "chart": self.chart,
            "metadata": self.metadata,
        }

