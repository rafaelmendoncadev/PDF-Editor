"""
PDF Renderer — converts fitz.Page objects to PIL Images.
Stateless; can be called from any thread.
"""

from __future__ import annotations

import io

import fitz  # PyMuPDF
from PIL import Image


class PDFRenderer:
    """Renders a single PDF page to a PIL.Image at a given DPI."""

    DEFAULT_VIEWER_DPI: int = 150
    DEFAULT_THUMBNAIL_DPI: int = 72

    def render_page(self, page: fitz.Page, dpi: int = DEFAULT_VIEWER_DPI) -> Image.Image:
        """
        Render *page* at *dpi* dots per inch and return a PIL.Image (RGB).

        Args:
            page: A fitz.Page object loaded from a PDFDocument.
            dpi:  Output resolution in dots per inch.

        Returns:
            A PIL.Image in RGB mode.
        """
        zoom = dpi / 72.0  # fitz default is 72 DPI
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

        # Convert to PIL Image respecting pixmap stride.
        # pixmap.stride may differ from pixmap.width * pixmap.n due to
        # row-alignment padding.  Using the "raw" decoder with an explicit
        # stride avoids the scrambled-image artefact that occurs whenever
        # stride != width * 3.
        mode = "RGBA" if pixmap.alpha else "RGB"
        raw_mode = mode
        image = Image.frombytes(
            mode,
            (pixmap.width, pixmap.height),
            pixmap.samples,
            "raw",
            raw_mode,
            pixmap.stride,
            1,
        )
        if mode != "RGB":
            image = image.convert("RGB")
        return image

    def render_thumbnail(self, page: fitz.Page) -> Image.Image:
        """Convenience wrapper that renders a low-resolution thumbnail."""
        return self.render_page(page, dpi=self.DEFAULT_THUMBNAIL_DPI)

    def render_viewer(self, page: fitz.Page, zoom_factor: float = 1.0) -> Image.Image:
        """
        Render a page for the main viewer, applying an optional zoom factor
        on top of the default viewer DPI.

        Args:
            page:        A fitz.Page object.
            zoom_factor: Multiplier for the base DPI (1.0 = 150 DPI).

        Returns:
            A PIL.Image in RGB mode.
        """
        effective_dpi = int(self.DEFAULT_VIEWER_DPI * zoom_factor)
        effective_dpi = max(36, min(effective_dpi, 600))  # clamp to sane range
        return self.render_page(page, dpi=effective_dpi)
