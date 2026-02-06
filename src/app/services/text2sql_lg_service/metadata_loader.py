"""Metadata loader for database schema information."""

import os
from pathlib import Path
from typing import Optional

from src.utils.logging import get_logger
from .exceptions import MetadataLoadException

logger = get_logger(__name__)


class MetadataLoader:
    """Loader for database metadata files."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize metadata loader.
        
        Args:
            base_path: Base path for metadata files (defaults to src/notebook/metadata)
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Default to src/notebook/metadata relative to this file
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent.parent
            self.base_path = project_root / "src" / "notebook" / "metadata"
        
        logger.debug(f"Metadata loader initialized with base path: {self.base_path}")
    
    def load_metadata(self, filename: str = "causal_inference_metadata.txt") -> str:
        """
        Load metadata from file.
        
        Args:
            filename: Name of the metadata file
            
        Returns:
            Metadata content as string
            
        Raises:
            MetadataLoadException: If file cannot be loaded
        """
        try:
            metadata_path = self.base_path / filename
            
            if not metadata_path.exists():
                raise MetadataLoadException(
                    f"Metadata file not found: {metadata_path}",
                    file_path=str(metadata_path),
                )
            
            if not metadata_path.is_file():
                raise MetadataLoadException(
                    f"Metadata path is not a file: {metadata_path}",
                    file_path=str(metadata_path),
                )
            
            logger.debug(f"Loading metadata from: {metadata_path}")
            
            with open(metadata_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.strip():
                raise MetadataLoadException(
                    f"Metadata file is empty: {metadata_path}",
                    file_path=str(metadata_path),
                )
            
            logger.debug(f"Successfully loaded metadata ({len(content)} characters)")
            return content
        
        except PermissionError as e:
            logger.error(f"Permission denied reading metadata file: {e}")
            raise MetadataLoadException(
                f"Permission denied reading metadata file: {str(e)}",
                file_path=str(metadata_path),
                details={"error_type": "permission_error"},
            ) from e
        
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode metadata file: {e}")
            raise MetadataLoadException(
                f"Failed to decode metadata file (not UTF-8): {str(e)}",
                file_path=str(metadata_path),
                details={"error_type": "encoding_error"},
            ) from e
        
        except Exception as e:
            logger.error(f"Unexpected error loading metadata: {e}")
            raise MetadataLoadException(
                f"Unexpected error loading metadata: {str(e)}",
                file_path=str(metadata_path) if 'metadata_path' in locals() else None,
                details={"error_type": type(e).__name__},
            ) from e
    
    def set_base_path(self, base_path: str) -> None:
        """
        Set a new base path for metadata files.
        
        Args:
            base_path: New base path
        """
        self.base_path = Path(base_path)
        logger.debug(f"Metadata base path updated to: {self.base_path}")

