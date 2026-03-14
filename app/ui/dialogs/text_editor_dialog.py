"""
Text Editor Dialog — modal window for adding a text overlay to a PDF page.

The user enters:
  - The text to insert
  - Font size
  - Position (X, Y) in points from the top-left of the page
  - Color (hex string, e.g. "#000000")

On confirm the caller receives the data via a callback.
"""

from __future__ import annotations

import re
from typing import Callable, Optional, Tuple

import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser


class TextEditorDialog(ctk.CTkToplevel):
    """
    Modal dialog for composing a text overlay.

    Usage::

        def on_confirm(text, x, y, font_size, color_rgb):
            doc.add_text_overlay(page_idx, x, y, text, font_size, color_rgb)

        dlg = TextEditorDialog(master, page_index=current_page,
                               on_confirm=on_confirm)
        dlg.grab_set()  # make modal
    """

    def __init__(
        self,
        master,
        page_index: int,
        on_confirm: Callable[[str, float, float, float, Tuple[float, float, float]], None],
        default_x: float = 72.0,
        default_y: float = 72.0,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self.title(f"Inserir Texto — Página {page_index + 1}")
        self.resizable(False, False)
        self.grab_set()  # modal

        self._page_index = page_index
        self._on_confirm = on_confirm
        self._color_hex: str = "#000000"
        self._default_x = default_x
        self._default_y = default_y

        self._build_widgets()
        self._center_on_parent(master)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    # (no public methods beyond __init__; result delivered via callback)

    # ------------------------------------------------------------------
    # Private — widget construction
    # ------------------------------------------------------------------

    def _build_widgets(self) -> None:
        pad = {"padx": 12, "pady": 6}

        # ── Text content ─────────────────────────────────────────────
        ctk.CTkLabel(self, text="Texto:").grid(row=0, column=0, sticky="w", **pad)
        self._text_entry = ctk.CTkTextbox(self, width=300, height=80)
        self._text_entry.grid(row=0, column=1, columnspan=2, **pad)

        # ── Font size ─────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Tamanho (pt):").grid(row=1, column=0, sticky="w", **pad)
        self._font_size_var = tk.StringVar(value="12")
        self._font_size_entry = ctk.CTkEntry(self, textvariable=self._font_size_var, width=80)
        self._font_size_entry.grid(row=1, column=1, sticky="w", **pad)

        # ── Position ──────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Posição X (pt):").grid(row=2, column=0, sticky="w", **pad)
        self._x_var = tk.StringVar(value=f"{self._default_x:.1f}")
        ctk.CTkEntry(self, textvariable=self._x_var, width=80).grid(
            row=2, column=1, sticky="w", **pad
        )

        ctk.CTkLabel(self, text="Posição Y (pt):").grid(row=3, column=0, sticky="w", **pad)
        self._y_var = tk.StringVar(value=f"{self._default_y:.1f}")
        ctk.CTkEntry(self, textvariable=self._y_var, width=80).grid(
            row=3, column=1, sticky="w", **pad
        )

        # ── Color ─────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Cor:").grid(row=4, column=0, sticky="w", **pad)
        self._color_preview = ctk.CTkButton(
            self,
            text="",
            width=36,
            height=24,
            fg_color=self._color_hex,
            hover=False,
            corner_radius=4,
            command=self._pick_color,
        )
        self._color_preview.grid(row=4, column=1, sticky="w", **pad)
        ctk.CTkButton(self, text="Escolher…", width=80, command=self._pick_color).grid(
            row=4, column=2, sticky="w", **pad
        )

        # ── Helper note ───────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Dica: X=0, Y=0 é o canto superior esquerdo da página.",
            text_color="gray",
            font=("", 11),
        ).grid(row=5, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 6))

        # ── Buttons ───────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=6, column=0, columnspan=3, pady=8)

        ctk.CTkButton(btn_frame, text="Cancelar", width=90, command=self.destroy).pack(
            side="left", padx=8
        )
        ctk.CTkButton(
            btn_frame,
            text="Inserir Texto",
            width=100,
            command=self._confirm,
        ).pack(side="left", padx=8)

    # ------------------------------------------------------------------
    # Private — event handlers
    # ------------------------------------------------------------------

    def _pick_color(self) -> None:
        """Open a system color chooser dialog."""
        result = colorchooser.askcolor(color=self._color_hex, parent=self, title="Pick text color")
        if result and result[1]:
            self._color_hex = result[1]
            self._color_preview.configure(fg_color=self._color_hex)

    def _confirm(self) -> None:
        """Validate input and fire the on_confirm callback."""
        text = self._text_entry.get("1.0", "end").strip()
        if not text:
            self._shake()
            return

        try:
            font_size = float(self._font_size_var.get())
            x = float(self._x_var.get())
            y = float(self._y_var.get())
        except ValueError:
            self._shake()
            return

        color_rgb = self._hex_to_rgb(self._color_hex)
        self._on_confirm(text, x, y, font_size, color_rgb)
        self.destroy()

    def _shake(self) -> None:
        """Visual feedback for invalid input — briefly flash the window border."""
        self.title("⚠ Verifique os dados informados")
        self.after(1200, lambda: self.title(f"Inserir Texto — Página {self._page_index + 1}"))

    # ------------------------------------------------------------------
    # Private — helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
        """Convert a '#RRGGBB' string to a (r, g, b) tuple of floats in [0, 1]."""
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i: i + 2], 16) / 255.0 for i in (0, 2, 4))
        return (r, g, b)

    def _center_on_parent(self, parent) -> None:
        """Position this window in the center of *parent*."""
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        dw = self.winfo_width()
        dh = self.winfo_height()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.geometry(f"+{x}+{y}")
