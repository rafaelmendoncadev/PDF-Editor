"""
Selection Manager — manages PDF area selections and coordinate transformations.

This module handles:
- Different selection modes (rectangular, freehand, bounding box)
- Coordinate transformations between canvas and PDF coordinates
- Selection state tracking
- Region storage and validation
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, List

import fitz  # PyMuPDF


class SelectionMode(Enum):
    """Available selection modes."""
    RECTANGULAR = "rectangular"
    FREEHAND = "freehand"
    BOUNDING_BOX = "bounding_box"


@dataclass
class SelectionRegion:
    """
    Represents a selected region on a PDF page.
    
    Coordinates are in PDF space (72 DPI by default in fitz).
    """
    x0: float
    y0: float
    x1: float
    y1: float
    page_index: int
    mode: SelectionMode = SelectionMode.RECTANGULAR
    points: Optional[List[Tuple[float, float]]] = None  # For freehand
    
    @property
    def width(self) -> float:
        """Width of the region in PDF units."""
        return abs(self.x1 - self.x0)
    
    @property
    def height(self) -> float:
        """Height of the region in PDF units."""
        return abs(self.y1 - self.y0)
    
    @property
    def area(self) -> float:
        """Area of the region in PDF units."""
        return self.width * self.height
    
    def normalize(self) -> SelectionRegion:
        """Return a new region with coordinates normalized (x0 < x1, y0 < y1)."""
        x_min = min(self.x0, self.x1)
        x_max = max(self.x0, self.x1)
        y_min = min(self.y0, self.y1)
        y_max = max(self.y0, self.y1)
        return SelectionRegion(
            x0=x_min, y0=y_min,
            x1=x_max, y1=y_max,
            page_index=self.page_index,
            mode=self.mode,
            points=self.points
        )
    
    def to_rect(self) -> fitz.Rect:
        """Convert to a fitz.Rect for PDF operations."""
        region = self.normalize()
        return fitz.Rect(region.x0, region.y0, region.x1, region.y1)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within the region."""
        region = self.normalize()
        return (region.x0 <= x <= region.x1 and 
                region.y0 <= y <= region.y1)
    
    def expand(self, margin: float) -> SelectionRegion:
        """Expand the region by a given margin in PDF units."""
        return SelectionRegion(
            x0=self.x0 - margin,
            y0=self.y0 - margin,
            x1=self.x1 + margin,
            y1=self.y1 + margin,
            page_index=self.page_index,
            mode=self.mode,
            points=self.points
        )


class SelectionManager:
    """
    Manages area selections on PDF pages.
    
    Handles coordinate transformations and selection state.
    """
    
    def __init__(self) -> None:
        self._current_selection: Optional[SelectionRegion] = None
        self._selection_history: List[SelectionRegion] = []
    
    # ------------------------------------------------------------------
    # Selection Management
    # ------------------------------------------------------------------
    
    def set_selection(self, region: SelectionRegion) -> None:
        """Set the current selection and add it to history."""
        if self._current_selection is not None:
            self._selection_history.append(self._current_selection)
        self._current_selection = region
    
    def get_current_selection(self) -> Optional[SelectionRegion]:
        """Get the current selection, or None if no selection."""
        return self._current_selection
    
    def clear_selection(self) -> None:
        """Clear the current selection."""
        if self._current_selection is not None:
            self._selection_history.append(self._current_selection)
        self._current_selection = None
    
    def has_selection(self) -> bool:
        """Check if there is an active selection."""
        return self._current_selection is not None
    
    # ------------------------------------------------------------------
    # Coordinate Transformations
    # ------------------------------------------------------------------
    
    @staticmethod
    def canvas_to_pdf(
        canvas_x: float,
        canvas_y: float,
        canvas_width: int,
        canvas_height: int,
        pdf_page_width: float,
        pdf_page_height: float,
        zoom: float = 1.0,
    ) -> Tuple[float, float]:
        """
        Convert canvas coordinates to PDF coordinates.
        
        Args:
            canvas_x, canvas_y: Position on the canvas widget
            canvas_width, canvas_height: Canvas dimensions
            pdf_page_width, pdf_page_height: PDF page dimensions (in points/72 DPI)
            zoom: Current zoom level (1.0 = 100%)
        
        Returns:
            (pdf_x, pdf_y) coordinates in PDF space
        """
        # Account for zoom
        effective_canvas_width = canvas_width * zoom
        effective_canvas_height = canvas_height * zoom
        
        # Calculate scale factors
        scale_x = pdf_page_width / effective_canvas_width
        scale_y = pdf_page_height / effective_canvas_height
        
        # Transform
        pdf_x = canvas_x * scale_x
        pdf_y = canvas_y * scale_y
        
        return (pdf_x, pdf_y)
    
    @staticmethod
    def pdf_to_canvas(
        pdf_x: float,
        pdf_y: float,
        canvas_width: int,
        canvas_height: int,
        pdf_page_width: float,
        pdf_page_height: float,
        zoom: float = 1.0,
    ) -> Tuple[int, int]:
        """
        Convert PDF coordinates to canvas coordinates.
        
        Args:
            pdf_x, pdf_y: Position in PDF space
            canvas_width, canvas_height: Canvas dimensions
            pdf_page_width, pdf_page_height: PDF page dimensions
            zoom: Current zoom level
        
        Returns:
            (canvas_x, canvas_y) as integers
        """
        # Account for zoom
        effective_canvas_width = canvas_width * zoom
        effective_canvas_height = canvas_height * zoom
        
        # Calculate scale factors
        scale_x = effective_canvas_width / pdf_page_width
        scale_y = effective_canvas_height / pdf_page_height
        
        # Transform
        canvas_x = int(pdf_x * scale_x)
        canvas_y = int(pdf_y * scale_y)
        
        return (canvas_x, canvas_y)
    
    # ------------------------------------------------------------------
    # Region Validation
    # ------------------------------------------------------------------
    
    @staticmethod
    def validate_region(region: SelectionRegion, page: fitz.Page) -> bool:
        """
        Validate that a region fits within the page bounds.
        
        Args:
            region: The region to validate
            page: The PDF page
        
        Returns:
            True if the region is valid
        """
        page_rect = page.rect
        normalized = region.normalize()
        
        # Check if region is within page bounds
        return (
            normalized.x0 >= page_rect.x0 and
            normalized.y0 >= page_rect.y0 and
            normalized.x1 <= page_rect.x1 and
            normalized.y1 <= page_rect.y1 and
            normalized.width > 0 and
            normalized.height > 0
        )
    
    # ------------------------------------------------------------------
    # Region History
    # ------------------------------------------------------------------
    
    def undo(self) -> bool:
        """Undo the last selection."""
        if not self._selection_history:
            return False
        self._current_selection = self._selection_history.pop()
        return True
    
    def clear_history(self) -> None:
        """Clear the selection history."""
        self._selection_history.clear()
