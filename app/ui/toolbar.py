"""
Toolbar — top control strip with buttons for all PDF editor actions.

Callbacks are injected by MainWindow via the `set_callbacks` method so
the toolbar remains decoupled from application logic.
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk


class Toolbar(ctk.CTkFrame):
    """Top toolbar containing action buttons for the PDF editor."""

    def __init__(self, master: ctk.CTk, **kwargs) -> None:
        super().__init__(master, height=48, corner_radius=0, **kwargs)
        self.pack_propagate(False)

        # Callbacks — set by MainWindow
        self._on_open: Optional[Callable] = None
        self._on_save: Optional[Callable] = None
        self._on_export_word: Optional[Callable] = None
        self._on_add_text: Optional[Callable] = None
        self._on_remove_content: Optional[Callable] = None
        self._on_move_up: Optional[Callable] = None
        self._on_move_down: Optional[Callable] = None
        self._on_delete_page: Optional[Callable] = None
        self._on_select_rect: Optional[Callable] = None
        self._on_select_freehand: Optional[Callable] = None
        self._on_cancel_selection: Optional[Callable] = None

        # Button references for state management
        self._btn_export_word: Optional[ctk.CTkButton] = None
        self._btn_select_rect: Optional[ctk.CTkButton] = None
        self._btn_select_freehand: Optional[ctk.CTkButton] = None
        self._btn_cancel_sel: Optional[ctk.CTkButton] = None

        self._build_widgets()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def set_callbacks(
        self,
        on_open: Callable,
        on_save: Callable,
        on_export_word: Callable,
        on_add_text: Callable,
        on_remove_content: Callable,
        on_move_up: Callable,
        on_move_down: Callable,
        on_delete_page: Callable,
        on_select_rect: Callable = None,
        on_select_freehand: Callable = None,
        on_cancel_selection: Callable = None,
    ) -> None:
        """Inject action callbacks from the owning MainWindow."""
        self._on_open = on_open
        self._on_save = on_save
        self._on_export_word = on_export_word
        self._on_add_text = on_add_text
        self._on_remove_content = on_remove_content
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self._on_delete_page = on_delete_page
        self._on_select_rect = on_select_rect
        self._on_select_freehand = on_select_freehand
        self._on_cancel_selection = on_cancel_selection

    def set_document_loaded(self, loaded: bool) -> None:
        """Enable/disable document-dependent buttons based on *loaded*."""
        state = "normal" if loaded else "disabled"
        for btn in (
            self._btn_save,
            self._btn_export_word,
            self._btn_add_text,
            self._btn_remove_content,
            self._btn_move_up,
            self._btn_move_down,
            self._btn_delete_page,
            self._btn_select_rect,
            self._btn_select_freehand,
        ):
            btn.configure(state=state)

    def set_selection_mode(self, active: bool) -> None:
        """Enable/disable selection-related buttons."""
        state = "normal" if active else "disabled"
        self._btn_cancel_sel.configure(state=state)

    # ------------------------------------------------------------------
    # Private — widget construction
    # ------------------------------------------------------------------

    def _build_widgets(self) -> None:
        # Left group — file actions
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.pack(side="left", padx=8, pady=6)

        self._btn_open = ctk.CTkButton(
            left_frame,
            text="📂 Abrir PDF",
            width=110,
            command=self._cb_open,
        )
        self._btn_open.pack(side="left", padx=4)

        self._btn_save = ctk.CTkButton(
            left_frame,
            text="💾 Salvar PDF",
            width=110,
            state="disabled",
            command=self._cb_save,
        )
        self._btn_save.pack(side="left", padx=4)

        self._btn_export_word = ctk.CTkButton(
            left_frame,
            text="📄 Exportar Word",
            width=130,
            state="disabled",
            fg_color="#2b5797",
            hover_color="#1e3f6f",
            command=self._cb_export_word,
        )
        self._btn_export_word.pack(side="left", padx=4)

        # Separator
        ctk.CTkLabel(self, text="|", text_color="gray").pack(side="left", padx=4)

        # Selection tools group
        sel_frame = ctk.CTkFrame(self, fg_color="transparent")
        sel_frame.pack(side="left", padx=4, pady=6)

        self._btn_select_rect = ctk.CTkButton(
            sel_frame,
            text="⬜ Seleção Retangular",
            width=140,
            state="disabled",
            command=self._cb_select_rect,
        )
        self._btn_select_rect.pack(side="left", padx=4)

        self._btn_select_freehand = ctk.CTkButton(
            sel_frame,
            text="✏️ Seleção Livre",
            width=120,
            state="disabled",
            command=self._cb_select_freehand,
        )
        self._btn_select_freehand.pack(side="left", padx=4)

        self._btn_cancel_sel = ctk.CTkButton(
            sel_frame,
            text="✖ Cancelar",
            width=90,
            state="disabled",
            fg_color="#c0392b",
            hover_color="#922b21",
            command=self._cb_cancel_selection,
        )
        self._btn_cancel_sel.pack(side="left", padx=4)

        # Separator
        ctk.CTkLabel(self, text="|", text_color="gray").pack(side="left", padx=4)

        # Editing group
        edit_frame = ctk.CTkFrame(self, fg_color="transparent")
        edit_frame.pack(side="left", padx=4, pady=6)

        self._btn_add_text = ctk.CTkButton(
            edit_frame,
            text="✏️ Inserir Texto",
            width=110,
            state="disabled",
            command=self._cb_add_text,
        )
        self._btn_add_text.pack(side="left", padx=4)

        self._btn_remove_content = ctk.CTkButton(
            edit_frame,
            text="🗑 Remover Conteúdo",
            width=140,
            state="disabled",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self._cb_remove_content,
        )
        self._btn_remove_content.pack(side="left", padx=4)

        # Separator
        ctk.CTkLabel(self, text="|", text_color="gray").pack(side="left", padx=4)

        # Right group — page management
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(side="left", padx=4, pady=6)

        self._btn_move_up = ctk.CTkButton(
            right_frame,
            text="⬆ Mover Cima",
            width=110,
            state="disabled",
            command=self._cb_move_up,
        )
        self._btn_move_up.pack(side="left", padx=4)

        self._btn_move_down = ctk.CTkButton(
            right_frame,
            text="⬇ Mover Baixo",
            width=110,
            state="disabled",
            command=self._cb_move_down,
        )
        self._btn_move_down.pack(side="left", padx=4)

        self._btn_delete_page = ctk.CTkButton(
            right_frame,
            text="🗑 Excluir Página",
            width=120,
            state="disabled",
            fg_color="#c0392b",
            hover_color="#922b21",
            command=self._cb_delete_page,
        )
        self._btn_delete_page.pack(side="left", padx=4)

    # ------------------------------------------------------------------
    # Internal callbacks — delegate to injected handlers
    # ------------------------------------------------------------------

    def _cb_open(self) -> None:
        if self._on_open:
            self._on_open()

    def _cb_save(self) -> None:
        if self._on_save:
            self._on_save()

    def _cb_export_word(self) -> None:
        if self._on_export_word:
            self._on_export_word()

    def _cb_add_text(self) -> None:
        if self._on_add_text:
            self._on_add_text()

    def _cb_remove_content(self) -> None:
        if self._on_remove_content:
            self._on_remove_content()

    def _cb_move_up(self) -> None:
        if self._on_move_up:
            self._on_move_up()

    def _cb_move_down(self) -> None:
        if self._on_move_down:
            self._on_move_down()

    def _cb_delete_page(self) -> None:
        if self._on_delete_page:
            self._on_delete_page()

    def _cb_select_rect(self) -> None:
        if self._on_select_rect:
            self._on_select_rect()

    def _cb_select_freehand(self) -> None:
        if self._on_select_freehand:
            self._on_select_freehand()

    def _cb_cancel_selection(self) -> None:
        if self._on_cancel_selection:
            self._on_cancel_selection()

