"""
Selection Action Dialog — appears after user completes an area selection.

Offers direct actions on the selected region:
- Remove content (text, images, graphics)
- Insert text into the area
- Cancel
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
import fitz  # PyMuPDF

from app.core.selection_manager import SelectionRegion

logger = logging.getLogger(__name__)


class SelectionActionDialog(ctk.CTkToplevel):
    """
    Simple modal dialog shown after the user selects a region on the PDF.

    Shows a cropped preview of the selected area and offers action buttons:
    - Remove content from the area
    - Insert text into the area
    - Cancel
    """

    def __init__(
        self,
        master,
        region: SelectionRegion,
        page: fitz.Page,
        page_image: Image.Image,
        content_summary: str,
        on_remove: Callable[[SelectionRegion], None],
        on_insert_text: Callable[[SelectionRegion], None],
        on_cancel: Optional[Callable] = None,
    ) -> None:
        super().__init__(master)
        self.title("Ação na Seleção")
        self.resizable(False, False)

        self._region = region.normalize()
        self._page = page
        self._page_image = page_image
        self._content_summary = content_summary
        self._on_remove = on_remove
        self._on_insert_text = on_insert_text
        self._on_cancel = on_cancel

        self._preview_tk_image: Optional[ImageTk.PhotoImage] = None

        self._build_widgets()
        self._center_on_parent()

        # Make dialog modal
        self.transient(master)
        self.grab_set()

    # ------------------------------------------------------------------
    # Widget Construction
    # ------------------------------------------------------------------

    def _build_widgets(self) -> None:
        """Build the dialog UI."""
        pad = {"padx": 16, "pady": 8}

        # ── Header ────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="O que deseja fazer com a área selecionada?",
            font=("Arial", 15, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 4))

        # ── Region info ───────────────────────────────────────────────
        info_text = (
            f"Página {self._region.page_index + 1}  •  "
            f"{self._region.width:.0f} × {self._region.height:.0f} pt"
        )
        ctk.CTkLabel(
            self, text=info_text, text_color="gray", font=("Arial", 11)
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 4))

        # ── Content summary ───────────────────────────────────────────
        if self._content_summary:
            ctk.CTkLabel(
                self,
                text=f"Conteúdo detectado: {self._content_summary}",
                text_color="#f0c040",
                font=("Arial", 11),
            ).grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 8))
        else:
            ctk.CTkLabel(
                self,
                text="Nenhum conteúdo detectado na área.",
                text_color="gray",
                font=("Arial", 11),
            ).grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 8))

        # ── Preview ───────────────────────────────────────────────────
        preview_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=8)
        preview_frame.grid(row=3, column=0, columnspan=2, sticky="ew", **pad)

        self._preview_label = ctk.CTkLabel(preview_frame, text="")
        self._preview_label.pack(padx=8, pady=8)
        self._render_preview()

        # ── Action buttons ────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=16, pady=(8, 16))

        # Remove content button
        self._btn_remove = ctk.CTkButton(
            btn_frame,
            text="🗑  Remover Conteúdo",
            width=180,
            height=38,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=("Arial", 13, "bold"),
            command=self._on_remove_click,
        )
        self._btn_remove.pack(side="left", padx=(0, 8))
        # Disable if no content
        if not self._content_summary:
            self._btn_remove.configure(state="disabled")

        # Insert text button
        self._btn_insert = ctk.CTkButton(
            btn_frame,
            text="✏️  Inserir Texto",
            width=160,
            height=38,
            fg_color="#2980b9",
            hover_color="#1f6da3",
            font=("Arial", 13, "bold"),
            command=self._on_insert_click,
        )
        self._btn_insert.pack(side="left", padx=(0, 8))

        # Cancel button
        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            width=100,
            height=38,
            fg_color="#444444",
            hover_color="#555555",
            command=self._on_cancel_click,
        ).pack(side="left")

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _render_preview(self) -> None:
        """Render a cropped preview of the selected region."""
        try:
            page_rect = self._page.rect
            img_w, img_h = self._page_image.size

            # Map region to image pixels
            x_min = max(0.0, self._region.x0 / page_rect.width)
            y_min = max(0.0, self._region.y0 / page_rect.height)
            x_max = min(1.0, self._region.x1 / page_rect.width)
            y_max = min(1.0, self._region.y1 / page_rect.height)

            left = int(x_min * img_w)
            top = int(y_min * img_h)
            right = int(x_max * img_w)
            bottom = int(y_max * img_h)

            # Ensure valid crop box
            if right <= left or bottom <= top:
                return

            cropped = self._page_image.crop((left, top, right, bottom))

            # Draw a thin border around the crop
            draw = ImageDraw.Draw(cropped)
            w, h = cropped.size
            draw.rectangle([0, 0, w - 1, h - 1], outline="#00ff00", width=2)

            # Scale to fit a max preview size
            max_w, max_h = 460, 220
            cropped.thumbnail((max_w, max_h), Image.LANCZOS)

            self._preview_tk_image = ctk.CTkImage(
                light_image=cropped, dark_image=cropped,
                size=(cropped.width, cropped.height),
            )
            self._preview_label.configure(image=self._preview_tk_image)

        except Exception as e:
            logger.error(f"Error rendering preview: {e}")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_remove_click(self) -> None:
        self.destroy()
        self._on_remove(self._region)

    def _on_insert_click(self) -> None:
        self.destroy()
        self._on_insert_text(self._region)

    def _on_cancel_click(self) -> None:
        if self._on_cancel:
            self._on_cancel()
        self.destroy()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _center_on_parent(self) -> None:
        """Center the dialog on the parent window."""
        self.update_idletasks()
        pw = self.master.winfo_width()
        ph = self.master.winfo_height()
        px = self.master.winfo_x()
        py = self.master.winfo_y()
        dw = self.winfo_width()
        dh = self.winfo_height()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.geometry(f"+{x}+{y}")
