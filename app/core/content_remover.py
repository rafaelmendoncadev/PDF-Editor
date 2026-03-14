"""
Content Remover — handles deletion of content from selected PDF regions.

Detects text and images within a selection and removes them while
preserving document structure and maintaining undo capability.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple, Optional, Any
import fitz  # PyMuPDF
from dataclasses import dataclass, asdict

from app.core.selection_manager import SelectionRegion

logger = logging.getLogger(__name__)


@dataclass
class ContentInfo:
    """Information about content in a region"""
    text_blocks: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    graphics: List[Dict[str, Any]]
    
    @property
    def has_content(self) -> bool:
        """Check if region has any content"""
        return bool(self.text_blocks or self.images or self.graphics)
    
    @property
    def content_summary(self) -> str:
        """Human-readable summary of content"""
        parts = []
        if self.text_blocks:
            parts.append(f"{len(self.text_blocks)} text block(s)")
        if self.images:
            parts.append(f"{len(self.images)} image(s)")
        if self.graphics:
            parts.append(f"{len(self.graphics)} graphic(s)")
        
        if not parts:
            return "No content"
        return ", ".join(parts)


class ContentRemover:
    """
    Analyzes and removes content from PDF regions.
    
    Provides methods to:
    - Detect all content in a region (text, images, graphics)
    - Remove detected content
    - Validate if content can be safely removed
    - Create snapshots for undo functionality
    """
    
    def __init__(self) -> None:
        """Initialize content remover"""
        self._removal_tolerance = 2.0  # Points tolerance for region boundaries
    
    # ------------------------------------------------------------------
    # Content Detection
    # ------------------------------------------------------------------
    
    def detect_content_in_region(
        self,
        page: fitz.Page,
        region: SelectionRegion
    ) -> ContentInfo:
        """
        Detect all content within the selected region.
        
        Args:
            page: The PDF page
            region: The selection region
        
        Returns:
            ContentInfo with lists of detected content
        """
        region_rect = region.to_rect()
        
        text_blocks = self._detect_text_blocks(page, region_rect)
        images = self._detect_images(page, region_rect)
        graphics = self._detect_graphics(page, region_rect)
        
        return ContentInfo(
            text_blocks=text_blocks,
            images=images,
            graphics=graphics
        )
    
    def _detect_text_blocks(
        self,
        page: fitz.Page,
        region: fitz.Rect
    ) -> List[Dict[str, Any]]:
        """
        Detect text blocks within the region.
        
        Args:
            page: The PDF page
            region: Region to search
        
        Returns:
            List of text block information
        """
        text_blocks = []
        
        try:
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:  # Not text block
                    continue
                
                block_rect = fitz.Rect(block.get("bbox", [0, 0, 0, 0]))
                
                # Check if block overlaps with region
                if block_rect.intersects(region):
                    text_blocks.append({
                        "bbox": list(block_rect),
                        "text": self._extract_block_text(block),
                        "block_index": block.get("number", -1)
                    })
        except Exception as e:
            logger.error(f"Error detecting text blocks: {e}")

        return text_blocks
    
    def _detect_images(
        self,
        page: fitz.Page,
        region: fitz.Rect
    ) -> List[Dict[str, Any]]:
        """
        Detect images within the region.
        
        Args:
            page: The PDF page
            region: Region to search
        
        Returns:
            List of image information
        """
        images = []
        
        try:
            image_list = page.get_images()
            
            for img_index, img_ref in enumerate(image_list):
                # Get image bounding boxes
                rects = page.get_image_rects(img_ref)
                
                for img_rect in rects:
                    rect = fitz.Rect(img_rect)
                    
                    # Check if image overlaps with region
                    if rect.intersects(region):
                        images.append({
                            "bbox": list(rect),
                            "xref": img_ref,
                            "index": img_index
                        })
        except Exception as e:
            logger.error(f"Error detecting images: {e}")

        return images
    
    def _detect_graphics(
        self,
        page: fitz.Page,
        region: fitz.Rect
    ) -> List[Dict[str, Any]]:
        """
        Detect graphical objects within the region.
        
        Args:
            page: The PDF page
            region: Region to search
        
        Returns:
            List of graphic information
        """
        graphics = []
        
        try:
            # Get all drawing commands
            paths = page.get_drawings()
            
            for path in paths:
                path_rect = fitz.Rect(path["rect"])

                # Check if graphic overlaps with region
                if path_rect.intersects(region):
                    graphics.append({
                        "bbox": list(path_rect),
                        "type": path.get("type"),
                        "color": path.get("color")
                    })
        except Exception as e:
            logger.error(f"Error detecting graphics: {e}")

        return graphics
    
    # ------------------------------------------------------------------
    # Content Removal
    # ------------------------------------------------------------------
    
    def remove_text_blocks(
        self,
        page: fitz.Page,
        text_blocks: List[Dict[str, Any]]
    ) -> bool:
        """
        Remove specified text blocks from the page.
        
        Args:
            page: The PDF page to modify
            text_blocks: List of text block info to remove
        
        Returns:
            True if removal successful, False otherwise
        """
        try:
            for block_info in text_blocks:
                bbox = fitz.Rect(block_info["bbox"])
                
                # Use Redaction mark to remove text
                # This is more reliable than direct deletion
                annot = page.add_redact_annot(bbox)
                page.apply_redactions()
            
            return True
        except Exception as e:
            logger.error(f"Error removing text blocks: {e}")
            return False
    
    def remove_images(
        self,
        page: fitz.Page,
        images: List[Dict[str, Any]]
    ) -> bool:
        """
        Remove specified images from the page.
        
        Args:
            page: The PDF page to modify
            images: List of image info to remove
        
        Returns:
            True if removal successful, False otherwise
        """
        try:
            for img_info in images:
                bbox = fitz.Rect(img_info["bbox"])
                
                # Use redaction to remove image
                annot = page.add_redact_annot(bbox)
                page.apply_redactions()
            
            return True
        except Exception as e:
            logger.error(f"Error removing images: {e}")
            return False
    
    def remove_graphics(
        self,
        page: fitz.Page,
        graphics: List[Dict[str, Any]]
    ) -> bool:
        """
        Remove specified graphics from the page.
        
        Args:
            page: The PDF page to modify
            graphics: List of graphic info to remove
        
        Returns:
            True if removal successful, False otherwise
        """
        try:
            for graphic_info in graphics:
                bbox = fitz.Rect(graphic_info["bbox"])
                
                # Use redaction to remove graphic
                annot = page.add_redact_annot(bbox)
                page.apply_redactions()
            
            return True
        except Exception as e:
            logger.error(f"Error removing graphics: {e}")
            return False
    
    def clear_region(
        self,
        page: fitz.Page,
        region: SelectionRegion
    ) -> bool:
        """
        Clear all content from a region.
        
        This is more efficient than removing individual items.
        
        Args:
            page: The PDF page to modify
            region: The region to clear
        
        Returns:
            True if successful, False otherwise
        """
        try:
            bbox = region.to_rect()
            
            # Add redaction annotation and apply it
            annot = page.add_redact_annot(bbox)
            page.apply_redactions()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing region: {e}")
            return False
    
    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    
    def validate_removal(
        self,
        page: fitz.Page,
        region: SelectionRegion
    ) -> Tuple[bool, List[str]]:
        """
        Validate that content in region can be safely removed.
        
        Args:
            page: The PDF page
            region: The selection region
        
        Returns:
            Tuple of (is_valid, warning_list)
        """
        warnings = []
        
        try:
            content = self.detect_content_in_region(page, region)
            
            if not content.has_content:
                warnings.append("Selected region has no content to remove")
            
            # Check for important content types
            if content.images:
                warnings.append(f"Region contains {len(content.images)} image(s) that will be removed")
            
            if content.text_blocks and len(content.text_blocks) > 5:
                warnings.append(f"Region contains {len(content.text_blocks)} text blocks - large deletion")
            
            # Check if region touches page boundaries
            page_rect = page.rect
            region_rect = region.to_rect()
            
            if (region_rect.x0 < page_rect.x0 + self._removal_tolerance or
                region_rect.y0 < page_rect.y0 + self._removal_tolerance or
                region_rect.x1 > page_rect.x1 - self._removal_tolerance or
                region_rect.y1 > page_rect.y1 - self._removal_tolerance):
                warnings.append("Selection touches page edge - may affect layout")
            
            return True, warnings
        except Exception as e:
            warnings.append(f"Validation error: {str(e)}")
            return False, warnings
    
    # ------------------------------------------------------------------
    # Snapshots for Undo
    # ------------------------------------------------------------------
    
    def create_snapshot(
        self,
        page: fitz.Page,
        region: SelectionRegion
    ) -> bytes:
        """
        Create a snapshot of the page for undo functionality.
        
        Args:
            page: The PDF page
            region: The region being modified
        
        Returns:
            Serialized page snapshot
        """
        try:
            # Get the parent document
            doc = page.parent
            
            # Save current state to bytes
            snapshot = doc.write()
            return snapshot
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            return b""
    
    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    
    def _extract_block_text(self, block: Dict[str, Any]) -> str:
        """Extract text from a text block"""
        try:
            text_parts = []
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text_parts.append(span.get("text", ""))
            return "".join(text_parts)
        except Exception:
            return ""
    
    def set_tolerance(self, tolerance: float) -> None:
        """
        Set the tolerance for region boundary detection.
        
        Args:
            tolerance: Tolerance in points
        """
        self._removal_tolerance = tolerance
