"""
RAG-Anything Integration Module for LightRAG API

This module provides integration between LightRAG and RAG-Anything framework
for multimodal document processing (images, tables, equations in PDFs).
"""
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from lightrag.utils import logger
from lightrag.lightrag import LightRAG
from raganything import RAGAnything
from raganything.config import RAGAnythingConfig

# type: ignore  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002ZURkd1dnPT06OTAwOTQ1NGY=

class RAGAnythingProcessor:
    """
    Processor for multimodal document parsing using RAG-Anything framework
    """

    def __init__(
        self,
        rag: LightRAG,
        parser: str = "docling",
        parse_method: str = "auto",
        parser_output_dir: str = None,
        enable_multimodal: bool = True,
        vision_model_func: Any = None,
    ):
        """
        Initialize RAG-Anything processor

        Args:
            rag: LightRAG instance
            parser: Parser to use ("mineru" or "docling")
            parse_method: Parse method ("auto", "ocr", "txt")
            parser_output_dir: Output directory for parser results
            enable_multimodal: Whether to enable multimodal processing
            vision_model_func: Vision model function for image processing
        """
        self.rag = rag
        self.parser = parser
        self.parse_method = parse_method
        self.parser_output_dir = parser_output_dir or "./parser_output"
        self.enable_multimodal = enable_multimodal
        self.vision_model_func = vision_model_func

        # Lazy import RAG-Anything to avoid import errors if not installed
        self._raganything = None

    def _ensure_raganything_initialized(self):
        """Ensure RAG-Anything is initialized"""
        if self._raganything is not None:
            return

        try:

            # Create RAG-Anything configuration
            config = RAGAnythingConfig(
                parser=self.parser,
                parse_method=self.parse_method,
                parser_output_dir=self.parser_output_dir,
                enable_image_processing=self.enable_multimodal,
                enable_table_processing=self.enable_multimodal,
                enable_equation_processing=self.enable_multimodal,
                display_content_stats=False,  # Disable stats for API usage
            )

            # Initialize RAG-Anything with existing LightRAG instance
            self._raganything = RAGAnything(
                lightrag=self.rag,
                config=config,
                vision_model_func=self.vision_model_func,
            )

            logger.info(
                f"RAG-Anything initialized with parser={self.parser}, "
                f"method={self.parse_method}, multimodal={self.enable_multimodal}"
            )
# fmt: off  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002ZURkd1dnPT06OTAwOTQ1NGY=

        except ImportError as e:
            logger.error(
                f"Failed to import RAG-Anything: {e}. "
                "Please install raganything package."
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize RAG-Anything: {e}")
            raise

    async def parse_and_process_document(
        self,
        file_path: Path,
        track_id: str = None,
        pipeline_status: Optional[Dict] = None,
        pipeline_status_lock: Optional[Any] = None,
        **kwargs,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Parse and process document with multimodal support

        Args:
            file_path: Path to the document file
            track_id: Tracking ID for pipeline status
            pipeline_status: Pipeline status dict
            pipeline_status_lock: Lock for pipeline status updates
            **kwargs: Additional parser parameters

        Returns:
            Tuple of (success: bool, track_id: str, doc_id: Optional[str])
        """
        try:
            # Ensure RAG-Anything is initialized
            self._ensure_raganything_initialized()

            # Update pipeline status
            if pipeline_status_lock and pipeline_status:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = (
                        f"Parsing document with RAG-Anything ({self.parser})..."
                    )
                    pipeline_status["history_messages"].append(
                        pipeline_status["latest_message"]
                    )

            # Parse document to get content_list and doc_id
            content_list, doc_id = await self._raganything.parse_document(
                file_path=str(file_path),
                output_dir=self.parser_output_dir,
                parse_method=self.parse_method,
                display_stats=False,
                **kwargs,
            )

            logger.info(
                f"Document parsed successfully: {file_path.name}, "
                f"doc_id={doc_id}, blocks={len(content_list)}"
            )

            # Update pipeline status
            if pipeline_status_lock and pipeline_status:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = (
                        f"Parsed {len(content_list)} content blocks"
                    )
                    pipeline_status["history_messages"].append(
                        pipeline_status["latest_message"]
                    )

            # Insert content into LightRAG with multimodal processing
            # Note: RAG-Anything's insert_content_list does NOT support track_id,
            # pipeline_status, or pipeline_status_lock parameters
            await self._raganything.insert_content_list(
                content_list=content_list,
                doc_id=doc_id,
                file_path=str(file_path),
            )
# fmt: off  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002ZURkd1dnPT06OTAwOTQ1NGY=

            logger.info(
                f"Document processing complete: {file_path.name}, doc_id={doc_id}"
            )

            return True, track_id, doc_id

        except Exception as e:
            logger.error(f"Error processing document with RAG-Anything: {e}")
            logger.debug("Exception details:", exc_info=True)

            # Update pipeline status with error
            if pipeline_status_lock and pipeline_status:
                async with pipeline_status_lock:
                    error_msg = f"RAG-Anything processing error: {str(e)}"
                    pipeline_status["latest_message"] = error_msg
                    pipeline_status["history_messages"].append(error_msg)

            return False, track_id, None

    def should_use_raganything(self, file_path: Path) -> bool:
        """
        Determine if RAG-Anything should be used for this file

        Args:
            file_path: Path to the file

        Returns:
            True if RAG-Anything should be used, False otherwise
        """
        if not self.enable_multimodal:
            return False

        ext = file_path.suffix.lower()

        # Use RAG-Anything for file types that benefit from multimodal processing
        multimodal_extensions = {
            ".pdf",  # PDFs with images, tables, equations
            ".docx",  # Word documents with images
            ".pptx",  # PowerPoint with images
            ".xlsx",  # Excel with charts
            ".jpg",
            ".jpeg",
            ".png",  # Images
            ".bmp",
            ".tiff",
            ".tif",
            ".gif",
            ".webp",
        }

        return ext in multimodal_extensions

    async def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats

        Returns:
            List of supported file extensions
        """
        return [
            ".pdf",
            ".docx",
            ".pptx",
            ".xlsx",
            ".doc",
            ".ppt",
            ".xls",
            ".html",
            ".htm",
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".tiff",
            ".tif",
            ".gif",
            ".webp",
            ".txt",
            ".md",
        ]
# pragma: no cover  My80OmFIVnBZMlhtblk3a3ZiUG1yS002ZURkd1dnPT06OTAwOTQ1NGY=


def create_raganything_processor(
    rag: LightRAG,
    enable_multimodal: bool = True,
    parser: str = "mineru",
    parse_method: str = "auto",
    parser_output_dir: str = None,
    vision_model_func: Any = None,
) -> Optional[RAGAnythingProcessor]:
    """
    Factory function to create RAG-Anything processor

    Args:
        rag: LightRAG instance
        enable_multimodal: Whether to enable multimodal processing
        parser: Parser to use ("mineru" or "docling")
        parse_method: Parse method ("auto", "ocr", "txt")
        parser_output_dir: Output directory for parser results
        vision_model_func: Vision model function for image processing

    Returns:
        RAGAnythingProcessor instance or None if disabled
    """
    if not enable_multimodal:
        logger.info("Multimodal processing is disabled")
        return None

    try:
        processor = RAGAnythingProcessor(
            rag=rag,
            parser=parser,
            parse_method=parse_method,
            parser_output_dir=parser_output_dir,
            enable_multimodal=enable_multimodal,
            vision_model_func=vision_model_func,
        )
        logger.info("RAG-Anything processor created successfully")
        return processor
    except Exception as e:
        logger.error(f"Failed to create RAG-Anything processor: {e}")
        logger.warning("Falling back to standard document processing")
        return None

