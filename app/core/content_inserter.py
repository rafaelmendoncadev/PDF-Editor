"""
Content Inserter — handles insertion of text into selected PDF regions.

Provides text insertion with layout calculation, wrapping, and formatting.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple, Optional, Any
import fitz  # PyMuPDF
from dataclasses import dataclass

from app.core.selection_manager import SelectionRegion

logger = logging.getLogger(__name__)


@dataclass
class TextLayout:
    """Information about text layout in region"""
    text: str
    fits: bool
    lines: List[str]
    overflow_text: str
    line_height: float
    char_width: float
    total_height: float
    warnings: List[str]


class ContentInserter:
    """
    Handles text insertion into PDF regions.
    
    Provides methods to:
    - Calculate text layout for a region
    - Insert text with formatting
    - Preview insertion
    - Validate text fits in region
    """
    
    # Default font settings
    DEFAULT_FONT = "helv"
    DEFAULT_FONT_SIZE = 12
    DEFAULT_FONT_COLOR = (0, 0, 0)  # Black
    
    def __init__(self) -> None:
        """Initialize content inserter"""
        self._line_spacing = 1.2  # Line height multiplier
    
    # ------------------------------------------------------------------
    # Text Layout Calculation
    # ------------------------------------------------------------------
    
    def calculate_text_layout(
        self,
        text: str,
        region: SelectionRegion,
        font_size: int = DEFAULT_FONT_SIZE,
        font_name: str = DEFAULT_FONT
    ) -> TextLayout:
        """
        Calculate how text fits in the region.
        
        Args:
            text: The text to insert
            region: The selection region
            font_size: Font size in points
            font_name: Font name (e.g., 'helv', 'times-roman')
        
        Returns:
            TextLayout with wrapping and fit information
        """
        warnings = []
        region_width = region.width - 4  # 2pt margin on each side
        region_height = region.height - 4
        
        if region_width <= 0 or region_height <= 0:
            return TextLayout(
                text=text,
                fits=False,
                lines=[],
                overflow_text=text,
                line_height=font_size * self._line_spacing,
                char_width=font_size * 0.5,
                total_height=0,
                warnings=["Region too small for text"]
            )
        
        # Calculate character dimensions
        char_width = font_size * 0.5  # Approximate
        line_height = font_size * self._line_spacing
        
        # Wrap text
        lines = self._wrap_text(text, region_width, char_width)
        
        # Check if fits vertically
        total_height = len(lines) * line_height
        fits = total_height <= region_height
        
        if not fits:
            warnings.append(f"Text overflows region height ({total_height:.0f} > {region_height:.0f})")
            # Calculate how much text fits
            max_lines = max(1, int(region_height / line_height))
            overflow_start = sum(len(line) for line in lines[:max_lines])
            overflow_text = text[overflow_start:]
            lines = lines[:max_lines]
        else:
            overflow_text = ""
        
        if len(lines) > 10:
            warnings.append(f"Large text block ({len(lines)} lines) may affect layout")
        
        return TextLayout(
            text=text,
            fits=fits,
            lines=lines,
            overflow_text=overflow_text,
            line_height=line_height,
            char_width=char_width,
            total_height=total_height,
            warnings=warnings
        )
    
    def _wrap_text(
        self,
        text: str,
        max_width: float,
        char_width: float
    ) -> List[str]:
        """
        Wrap text to fit within width.
        
        Args:
            text: Text to wrap
            max_width: Maximum line width in points
            char_width: Average character width
        
        Returns:
            List of wrapped lines
        """
        if not text or max_width <= 0:
            return []
        
        chars_per_line = max(1, int(max_width / char_width))
        lines = []
        
        for paragraph in text.split('\n'):
            if not paragraph:
                lines.append('')
                continue
            
            # Split long lines
            current_line = ''
            for word in paragraph.split(' '):
                if not current_line:
                    current_line = word
                elif len(current_line) + len(word) + 1 <= chars_per_line:
                    current_line += ' ' + word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
        
        return lines
    
    # ------------------------------------------------------------------
    # Text Insertion
    # ------------------------------------------------------------------
    
    def insert_text(
        self,
        page: fitz.Page,
        region: SelectionRegion,
        text: str,
        font_size: int = DEFAULT_FONT_SIZE,
        font_name: str = DEFAULT_FONT,
        color: Tuple[float, float, float] = DEFAULT_FONT_COLOR,
        align: int = fitz.TEXT_ALIGN_LEFT
    ) -> bool:
        """
        Insert text into the region.
        
        Args:
            page: The PDF page
            region: The insertion region
            text: The text to insert
            font_size: Font size in points
            font_name: Font name
            color: RGB color tuple (0-1 range)
            align: Text alignment (TEXT_ALIGN_LEFT, etc.)
        
        Returns:
            True if insertion successful
        """
        try:
            # Get region bounds
            rect = region.to_rect()
            
            # Prepare text with margins
            margin = 2
            text_rect = rect.normalize()
            text_rect.x0 += margin
            text_rect.y0 += margin
            text_rect.x1 -= margin
            text_rect.y1 -= margin
            
            # Insert text
            page.insert_textbox(
                text_rect,
                text,
                fontsize=font_size,
                fontname=font_name,
                color=color,
                align=align,
                overflow=fitz.TEXT_PRESERVE
            )
            
            return True
        except Exception as e:
            logger.error(f"Error inserting text: {e}")
            return False
    
    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    
    def validate_insertion(
        self,
        region: SelectionRegion,
        text: str,
        font_size: int = DEFAULT_FONT_SIZE
    ) -> Tuple[bool, List[str]]:
        """
        Validate that text can be inserted in region.
        
        Args:
            region: The insertion region
            text: The text to insert
            font_size: Font size
        
        Returns:
            Tuple of (is_valid, warnings_list)
        """
        warnings = []
        
        if not text:
            warnings.append("Text is empty")
            return False, warnings
        
        if region.width < font_size:
            warnings.append("Region too narrow for text")
            return False, warnings
        
        if region.height < font_size * 1.2:
            warnings.append("Region too short for text")
            return False, warnings
        
        # Check for very long text
        if len(text) > 1000:
            warnings.append("Text is very long (>1000 chars), may overflow")
        
        # Check region size reasonableness
        region_area = region.width * region.height
        if region_area < (font_size * 20) ** 2:
            warnings.append("Region is very small for text insertion")
        
        return True, warnings
    
    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------
    
    def preview_insertion(
        self,
        text: str,
        region: SelectionRegion,
        font_size: int = DEFAULT_FONT_SIZE,
        font_name: str = DEFAULT_FONT
    ) -> Optional[fitz.Pixmap]:
        """
        Generate a preview of text insertion.
        
        Args:
            text: The text to insert
            region: The insertion region
            font_size: Font size
            font_name: Font name
        
        Returns:
            Pixmap preview image, or None if generation failed
        """
        try:
            # Create temporary page
            doc = fitz.open()
            page = doc.new_page(width=region.width, height=region.height)
            
            # Insert text
            rect = fitz.Rect(0, 0, region.width, region.height)
            page.insert_textbox(
                rect,
                text,
                fontsize=font_size,
                fontname=font_name,
                color=(0, 0, 0)
            )
            
            # Render to pixmap
            pix = page.get_pixmap(alpha=False, dpi=150)
            doc.close()
            
            return pix
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return None
    
    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    
    def set_line_spacing(self, spacing: float) -> None:
        """
        Set line spacing multiplier.
        
        Args:
            spacing: Line height multiplier (e.g., 1.2 for 20% extra space)
        """
        self._line_spacing = max(1.0, spacing)
    
    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    
    @staticmethod
    def get_available_fonts() -> List[str]:
        """Get list of available PDF fonts"""
        return [
            "helv",           # Helvetica
            "times-roman",    # Times
            "courier",        # Courier
            "symbol",         # Symbol
            "zapf-dingbats"   # Dingbats
        ]
