"""
PDF Document model.
Wraps a fitz.Document and manages the in-memory state:
   - page order (for reordering)
   - text overlays to be applied on export
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import fitz  # PyMuPDF


@dataclass
class TextOverlay:
    """A text annotation to be rendered on top of a PDF page."""
    page_index: int
    x: float
    y: float
    text: str
    font_size: float = 12.0
    color: tuple = (0.0, 0.0, 0.0)  # RGB floats in [0, 1]
    font_name: str = "helv"


class PDFDocument:
    """
    Manages an open PDF file.
    All mutations are in-memory; call save() / PDFExporter to persist.
    """

    def __init__(self) -> None:
        self._doc: Optional[fitz.Document] = None
        self._path: Optional[str] = None
        self._overlays: List[TextOverlay] = []
        # Page order as list of original page indices (supports reordering)
        self._page_order: List[int] = []

    # ------------------------------------------------------------------
    # Open / close
    # ------------------------------------------------------------------

    def open(self, path: str) -> None:
        """Open a PDF file from *path*."""
        if self._doc is not None:
            self.close()
        self._doc = fitz.open(path)
        self._path = path
        self._page_order = list(range(self._doc.page_count))
        self._overlays = []

    def close(self) -> None:
        """Close the underlying fitz document."""
        if self._doc is not None:
            self._doc.close()
            self._doc = None
        self._path = None
        self._page_order = []
        self._overlays = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return self._doc is not None

    @property
    def path(self) -> Optional[str]:
        return self._path

    @property
    def page_count(self) -> int:
        return len(self._page_order)

    @property
    def overlays(self) -> List[TextOverlay]:
        return list(self._overlays)

    # ------------------------------------------------------------------
    # Page access
    # ------------------------------------------------------------------

    def get_page(self, display_index: int) -> fitz.Page:
        """
        Return the fitz.Page corresponding to *display_index* in the
        current (possibly reordered) page list.
        """
        if not self.is_open:
            raise RuntimeError("No PDF document is open.")
        original_index = self._page_order[display_index]
        return self._doc.load_page(original_index)

    # ------------------------------------------------------------------
    # Page manipulation
    # ------------------------------------------------------------------

    def move_page(self, from_index: int, to_index: int) -> None:
        """Move the page at *from_index* to *to_index* in display order."""
        if from_index == to_index:
            return
        page = self._page_order.pop(from_index)
        # Adjust overlays that reference moved pages
        self._page_order.insert(to_index, page)

    def delete_page(self, display_index: int) -> None:
        """Remove the page at *display_index* from the document."""
        if self.page_count <= 1:
            raise ValueError("Cannot delete the only remaining page.")
        removed_original = self._page_order.pop(display_index)
        # Remove overlays that target the deleted page
        self._overlays = [
            ov for ov in self._overlays if ov.page_index != display_index
        ]
        # Shift overlay page indices for pages after the deleted one
        for ov in self._overlays:
            if ov.page_index > display_index:
                ov.page_index -= 1

    # ------------------------------------------------------------------
    # Text overlays
    # ------------------------------------------------------------------

    def add_text_overlay(
        self,
        page_index: int,
        x: float,
        y: float,
        text: str,
        font_size: float = 12.0,
        color: tuple = (0.0, 0.0, 0.0),
        font_name: str = "helv",
    ) -> TextOverlay:
        """Add a text overlay to *page_index* at position (*x*, *y*)."""
        overlay = TextOverlay(
            page_index=page_index,
            x=x,
            y=y,
            text=text,
            font_size=font_size,
            color=color,
            font_name=font_name,
        )
        self._overlays.append(overlay)
        return overlay

    def remove_overlay(self, overlay: TextOverlay) -> None:
        """Remove a specific overlay from the list."""
        self._overlays.remove(overlay)

    def get_overlays_for_page(self, display_index: int) -> List[TextOverlay]:
        """Return all overlays whose page_index matches *display_index*."""
        return [ov for ov in self._overlays if ov.page_index == display_index]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def get_page_order(self) -> List[int]:
        """Return a copy of the internal original-index order list."""
        return list(self._page_order)
