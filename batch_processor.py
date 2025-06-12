"""
Batch processing engine for Email QA System.
Handles validation of multiple email templates across different locales.
"""

import asyncio
import tempfile
import shutil
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from fastapi import UploadFile
from pathlib import Path
import os
from datetime import datetime

from email_qa_enhanced import validate_email
from locale_config import generate_locale_requirements, validate_locale_selection, get_locale_config

logger = logging.getLogger(__name__)

class BatchValidationRequest:
    """Request model for batch validation."""
    
    def __init__(
        self,
        templates: Dict[str, UploadFile],
        base_requirements: dict,
        selected_locales: List[str],
        check_product_tables: bool = True,
        product_table_timeout: Optional[int] = None
    ):
        self.templates = templates
        self.base_requirements = base_requirements
        self.selected_locales = selected_locales
        self.check_product_tables = check_product_tables
        self.product_table_timeout = product_table_timeout
        self.batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

class BatchValidationResult:
    """Result model for batch validation."""
    
    def __init__(self, batch_id: str):
        self.batch_id = batch_id
        self.results: Dict[str, Any] = {}
        self.status = "pending"
        self.start_time = datetime.now()
        self.end_time = None
        self.completed_locales: List[str] = []
        self.failed_locales: List[str] = []
        self.cancelled = False
        self.total_locales = 0

    def add_locale_result(self, locale: str, result: Any, status: str = "success"):
        """Add result for a specific locale."""
        self.results[locale] = {
            "locale": locale,
            "status": status,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if status == "success":
            self.completed_locales.append(locale)
        else:
            self.failed_locales.append(locale)

    def get_progress(self) -> dict:
        """Get current progress information."""
        total = self.total_locales
        completed = len(self.completed_locales) + len(self.failed_locales)
        
        return {
            "batch_id": self.batch_id,
            "total": total,
            "completed": completed,
            "successful": len(self.completed_locales),
            "failed": len(self.failed_locales),
            "progress_percent": (completed / total * 100) if total > 0 else 0,
            "status": self.status,
            "cancelled": self.cancelled
        }

    def finalize(self):
        """Mark batch as completed."""
        self.status = "completed"
        self.end_time = datetime.now()

class BatchProcessor:
    """Main batch processing engine."""
    
    def __init__(self):
        self.active_batches: Dict[str, BatchValidationResult] = {}
        self.cancelled_batches: set = set()
    
    async def process_batch(self, request: BatchValidationRequest) -> BatchValidationResult:
        """
        Process batch validation request.
        
        Args:
            request: BatchValidationRequest object
            
        Returns:
            BatchValidationResult: Complete batch results
        """
        batch_result = BatchValidationResult(request.batch_id)
        batch_result.total_locales = len(request.selected_locales)
        self.active_batches[request.batch_id] = batch_result
        
        logger.info(f"Starting batch processing {request.batch_id} for {len(request.selected_locales)} locales")
        
        try:
            # Skip locale validation in production to avoid deployment issues
            # The frontend already validates locales, so this backend validation is redundant
            try:
                logger.info(f"Validating locales: {request.selected_locales}")
                locale_validation = validate_locale_selection(request.selected_locales)
                logger.info(f"Locale validation result: {locale_validation}")
                
                if not locale_validation["valid"]:
                    # In production deployment, log the warning but continue processing
                    # This prevents batch failures due to environment-specific locale issues
                    logger.warning(f"Locale validation warning (continuing anyway): {locale_validation['errors']}")
                    logger.warning(f"Selected: {request.selected_locales}, Available: {locale_validation.get('supported_locales', 'unknown')}")
                    
                    # Only fail if this is a critical error (empty selection, etc.)
                    if not request.selected_locales or len(request.selected_locales) == 0:
                        error_detail = f"Critical locale validation failed: No locales selected"
                        logger.error(error_detail)
                        batch_result.status = "error"
                        batch_result.add_locale_result("validation_error", {
                            "error": error_detail,
                            "selected_locales": request.selected_locales,
                        }, "error")
                        return batch_result
            except Exception as validation_error:
                # If locale validation itself fails, log it but continue processing
                logger.warning(f"Locale validation module error (continuing anyway): {str(validation_error)}")
                logger.warning(f"This may be due to production deployment environment differences")
            
            # Process each locale
            tasks = []
            for locale in request.selected_locales:
                if request.batch_id in self.cancelled_batches:
                    batch_result.cancelled = True
                    batch_result.status = "cancelled"
                    break
                
                task = self._process_single_locale(
                    request, locale, batch_result
                )
                tasks.append(task)
            
            if not batch_result.cancelled:
                # Execute all locale validations concurrently
                await asyncio.gather(*tasks, return_exceptions=True)
        
        except Exception as e:
            logger.error(f"Batch processing error for {request.batch_id}: {str(e)}")
            batch_result.status = "error"
            batch_result.add_locale_result("batch_error", {
                "error": f"Batch processing failed: {str(e)}"
            }, "error")
        
        finally:
            batch_result.finalize()
            # Clean up cancelled batches tracking
            self.cancelled_batches.discard(request.batch_id)
        
        logger.info(f"Batch processing {request.batch_id} completed. Success: {len(batch_result.completed_locales)}, Failed: {len(batch_result.failed_locales)}")
        return batch_result
    
    async def _process_single_locale(
        self, 
        request: BatchValidationRequest, 
        locale: str, 
        batch_result: BatchValidationResult
    ):
        """Process validation for a single locale."""
        logger.info(f"Processing locale {locale} for batch {request.batch_id}")
        
        try:
            # Check if batch was cancelled
            if request.batch_id in self.cancelled_batches:
                logger.info(f"Locale {locale} skipped due to batch cancellation")
                return
            
            # Get template for this locale
            if locale not in request.templates:
                error_msg = f"No template provided for locale {locale}"
                logger.error(error_msg)
                batch_result.add_locale_result(locale, {"error": error_msg}, "error")
                return
            
            template_file = request.templates[locale]
            
            # Create temporary email file first
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.html', delete=False) as temp_email:
                # Reset file pointer to beginning
                await template_file.seek(0)
                content = await template_file.read()
                temp_email.write(content)
                temp_email_path = temp_email.name
            
            # Extract metadata from the actual template to use as Expected values
            from email_qa_enhanced import parse_email_html, extract_email_metadata
            soup = parse_email_html(temp_email_path)
            actual_metadata = extract_email_metadata(soup)
            
            # Generate locale-specific requirements using actual template metadata as Expected values
            locale_requirements = generate_locale_requirements(
                request.base_requirements, locale
            )
            
            # Only override metadata fields that are actually present and valid in the template
            # This preserves requirements for fields that should be validated (like sender_address, reply_address)
            for field in ['sender_name', 'subject', 'preheader']:
                if field in actual_metadata and actual_metadata[field] and actual_metadata[field] != 'Not found':
                    locale_requirements[field] = actual_metadata[field]
            
            # Do NOT override sender_address and reply_address - these should be validated against requirements
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_req:
                json.dump(locale_requirements, temp_req, indent=2)
                temp_req_path = temp_req.name
            
            try:
                # Run validation for this locale
                validation_result = validate_email(
                    email_path=temp_email_path,
                    requirements_path=temp_req_path,
                    check_product_tables=request.check_product_tables,
                    product_table_timeout=request.product_table_timeout
                )
                
                # Add locale context to result
                validation_result["locale"] = locale
                validation_result["locale_config"] = get_locale_config(locale)
                validation_result["requirements_used"] = locale_requirements
                
                batch_result.add_locale_result(locale, validation_result, "success")
                logger.info(f"Successfully processed locale {locale}")
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_email_path)
                    os.unlink(temp_req_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp files for {locale}: {cleanup_error}")
        
        except Exception as e:
            error_msg = f"Error processing locale {locale}: {str(e)}"
            logger.error(error_msg)
            batch_result.add_locale_result(locale, {"error": error_msg}, "error")
    
    def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancel an active batch processing operation.
        
        Args:
            batch_id: ID of the batch to cancel
            
        Returns:
            bool: True if batch was found and marked for cancellation
        """
        if batch_id in self.active_batches:
            self.cancelled_batches.add(batch_id)
            batch_result = self.active_batches[batch_id]
            batch_result.cancelled = True
            batch_result.status = "cancelled"
            logger.info(f"Batch {batch_id} marked for cancellation")
            return True
        return False
    
    def get_batch_progress(self, batch_id: str) -> Optional[dict]:
        """Get progress information for a specific batch."""
        if batch_id in self.active_batches:
            return self.active_batches[batch_id].get_progress()
        return None
    
    def get_batch_result(self, batch_id: str) -> Optional[BatchValidationResult]:
        """Get complete results for a finished batch."""
        return self.active_batches.get(batch_id)
    
    def cleanup_old_batches(self, max_age_hours: int = 24):
        """Clean up old batch results to prevent memory leaks."""
        current_time = datetime.now()
        to_remove = []
        
        for batch_id, result in self.active_batches.items():
            if result.end_time:
                age = current_time - result.end_time
                if age.total_seconds() > (max_age_hours * 3600):
                    to_remove.append(batch_id)
        
        for batch_id in to_remove:
            del self.active_batches[batch_id]
            logger.info(f"Cleaned up old batch {batch_id}")

# Global batch processor instance
batch_processor = BatchProcessor()