"""
Page Panel — left sidebar showing thumbnail previews of each PDF page.

Clicking a thumbnail fires on_page_selected(index).
The panel is rebuilt fully when the page list changes (reorder/delete).
"""

from __future__ import annotations

from typing import Callable, List, Optional

import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage


class PagePanel(ctk.CTkScrollableFrame):
    """
    Scrollable sidebar of page thumbnails.

    Each thumbnail is a CTkButton; clicking it selects that page.
    The currently selected thumbnail is highlighted.
    """

    THUMBNAIL_WIDTH: int = 120
    THUMBNAIL_HEIGHT: int = 160

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, width=150, corner_radius=0, label_text="Pages", **kwargs)
        self._on_page_selected: Optional[Callable[[int], None]] = None
        self._selected_index: int = 0
        self._buttons: List[ctk.CTkButton] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_on_page_selected(self, callback: Callable[[int], None]) -> None:
        """Register the callback fired when the user clicks a thumbnail."""
        self._on_page_selected = callback

    def load_thumbnails(self, thumbnails: List[Image.Image]) -> None:
        """
        Rebuild the panel from a fresh list of PIL thumbnail images.

        Args:
            thumbnails: One PIL.Image per page, already rendered at thumbnail DPI.
        """
        self._clear()
        for idx, img in enumerate(thumbnails):
            self._add_thumbnail(idx, img)
        # Select first page by default
        if self._buttons:
            self._highlight(0)

    def select_page(self, index: int) -> None:
        """Programmatically highlight the thumbnail at *index*."""
        if 0 <= index < len(self._buttons):
            self._highlight(index)

    def clear(self) -> None:
        """Remove all thumbnails."""
        self._clear()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _clear(self) -> None:
        for btn in self._buttons:
            btn.destroy()
        self._buttons = []

    def _add_thumbnail(self, index: int, img: Image.Image) -> None:
        """Create and pack a single thumbnail button for page *index*."""
        # Scale image to fit thumbnail size, preserving aspect ratio
        img.thumbnail((self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT), Image.LANCZOS)
        ctk_img = CTkImage(
            light_image=img,
            dark_image=img,
            size=(img.width, img.height),
        )

        btn = ctk.CTkButton(
            self,
            image=ctk_img,
            text=f"  {index + 1}",
            compound="top",
            width=self.THUMBNAIL_WIDTH + 10,
            height=self.THUMBNAIL_HEIGHT + 24,
            corner_radius=6,
            fg_color="transparent",
            hover_color=("gray75", "gray30"),
            command=lambda i=index: self._on_click(i),
        )
        btn.pack(pady=4, padx=6)
        self._buttons.append(btn)

    def _on_click(self, index: int) -> None:
        self._highlight(index)
        if self._on_page_selected:
            self._on_page_selected(index)

    def _highlight(self, index: int) -> None:
        """Apply selection colour to the button at *index*; reset others."""
        for i, btn in enumerate(self._buttons):
            if i == index:
                btn.configure(fg_color=("gray70", "gray25"))
            else:
                btn.configure(fg_color="transparent")
        self._selected_index = index
