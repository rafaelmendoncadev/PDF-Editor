"""
PDF Exporter — applies in-memory changes to a new fitz.Document and saves it.

Steps performed during export:
  1. Create a new blank fitz.Document.
  2. Insert pages in the current display order (handles reordering/deletions).
  3. Draw text overlays on each page.
  4. Save to the requested output path.
"""

from __future__ import annotations

import fitz  # PyMuPDF

from app.core.pdf_document import PDFDocument, TextOverlay


class PDFExporter:
    """Serialises a PDFDocument (with overlays) to a PDF file on disk."""

    def export(self, document: PDFDocument, output_path: str) -> None:
        """
        Export *document* to *output_path*.

        A new fitz.Document is assembled so the original file is never
        modified in place.

        Args:
            document:    An open PDFDocument instance.
            output_path: Absolute or relative path for the output PDF file.

        Raises:
            RuntimeError: If *document* has no open PDF.
        """
        if not document.is_open:
            raise RuntimeError("Cannot export: no PDF document is open.")

        # Build the new document with pages in display order
        new_doc = fitz.open()
        page_order = document.get_page_order()

        # Access the underlying source document via the public page API
        # We need to copy pages in order; grab the source doc from page 0
        source_doc = document.get_page(0).parent  # fitz.Document reference

        for display_idx, original_idx in enumerate(page_order):
            # Insert from source document maintaining original page geometry
            new_doc.insert_pdf(source_doc, from_page=original_idx, to_page=original_idx)

        # Apply text overlays
        for overlay in document.overlays:
            self._apply_overlay(new_doc, overlay)

        # Save with garbage collection and compression
        new_doc.save(output_path, garbage=4, deflate=True)
        new_doc.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_overlay(self, doc: fitz.Document, overlay: TextOverlay) -> None:
        """
        Insert a text annotation on the page identified by *overlay.page_index*
        inside *doc* (the already-reordered export document).
        """
        page = doc.load_page(overlay.page_index)
        # fitz uses a point at the baseline-left of the text
        point = fitz.Point(overlay.x, overlay.y)
        page.insert_text(
            point,
            overlay.text,
            fontname=overlay.font_name,
            fontsize=overlay.font_size,
            color=overlay.color,
        )
