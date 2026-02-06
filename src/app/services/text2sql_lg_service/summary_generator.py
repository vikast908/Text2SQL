"""Summary generator for query results."""

import json
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

from src.utils.logging import get_logger
from .llm_client import LLMClient
from .exceptions import LLMClientException
from .models import Text2SQLState

logger = get_logger(__name__)


class SummaryGenerator:
    """Generator for data summaries using LLM."""
    
    SYSTEM_PROMPT = """
    You are a data analyst expert. Your task is to analyze query results and generate a concise,
    insightful summary in exactly 4-5 lines.
    
    Rules:
    - Write exactly 4 lines (not more, not less)
    - Focus on key insights, trends, and important findings
    - Use clear, business-friendly language
    - Highlight the most significant data points
    - If there are comparisons (e.g., historical vs current), emphasize the differences
    - Be specific with numbers when relevant
    - Do not include markdown formatting or bullet points
    - Write in paragraph form, with each line being a complete sentence
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize summary generator.
        
        Args:
            llm_client: LLM client instance (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()
        logger.debug("Summary generator initialized")
    
    def _prepare_data_for_llm(self, data: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Prepare data for LLM analysis.
        
        Args:
            data: List of dictionaries representing query results
            
        Returns:
            Tuple of (sample_data, numeric_summary)
        """
        if not data:
            return {}, {}
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Limit to first 10 rows to avoid token limits
        sample_data = df.head(10).to_dict('records')
        
        # Get summary statistics for numeric columns
        numeric_summary = {}
        for col in df.select_dtypes(include=['number']).columns:
            numeric_summary[col] = {
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'mean': float(df[col].mean()),
                'sum': float(df[col].sum()),
            }
        
        return sample_data, numeric_summary
    
    def generate_summary(self, state: Text2SQLState) -> Dict[str, Any]:
        """
        Generate a concise 4-5 line summary of the given data using LLM.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with 'summary' key
            
        Raises:
            LLMClientException: If summary generation fails
        """
        try:
            data = state.get("data", [])
            
            if not data:
                return {"summary": "No data available to summarize."}
            
            # Convert to DataFrame if it's a list of dictionaries
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                return {"summary": "Invalid data format. Expected list of dictionaries or DataFrame."}
            
            if df.empty:
                return {"summary": "The query returned no results."}
            
            # Get basic statistics about the data
            num_rows = len(df)
            num_cols = len(df.columns)
            column_names = list(df.columns)
            
            # Prepare data for LLM
            sample_data, numeric_summary = self._prepare_data_for_llm(data)
            
            user_prompt = f"""
            Analyze the following query results and generate a 4-5 line summary:
            
            Data Overview:
            - Number of rows: {num_rows}
            - Number of columns: {num_cols}
            - Column names: {', '.join(column_names)}
            
            Sample data (first {min(10, num_rows)} rows):
            {json.dumps(sample_data, indent=2, default=str)}
            
            Numeric column statistics:
            {json.dumps(numeric_summary, indent=2) if numeric_summary else "No numeric columns"}
            
            Generate a concise 4-5 line summary that highlights the key insights from this data.
            """
            
            logger.debug(f"Generating summary for {num_rows} rows of data")
            
            summary = self.llm_client.generate_completion(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model="gpt-4o-mini",
                temperature=0.3,  # Moderate temperature for balanced creativity and consistency
            )
            
            # Ensure it's approximately 4-5 lines
            lines = [line.strip() for line in summary.split('\n') if line.strip()]
            if len(lines) < 4:
                # If too few lines, try splitting by sentences
                sentences = [s.strip() for s in summary.split('.') if s.strip()]
                if len(sentences) >= 4:
                    summary = '. '.join(sentences[:5]) + '.' if len(sentences) > 5 else '. '.join(sentences) + '.'
            elif len(lines) > 5:
                # If too many lines, take first 5
                summary = '\n'.join(lines[:5])
            
            logger.debug("Summary generated successfully")
            
            return {"summary": summary}
        
        except LLMClientException:
            raise
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Fallback to basic summary
            data = state.get("data", [])
            if isinstance(data, list):
                num_rows = len(data)
                num_cols = len(data[0].keys()) if data else 0
                column_names = list(data[0].keys()) if data else []
            else:
                num_rows = 0
                num_cols = 0
                column_names = []
            
            fallback_summary = (
                f"Query returned {num_rows} rows with {num_cols} columns: "
                f"{', '.join(column_names)}."
            )
            return {"summary": fallback_summary}

