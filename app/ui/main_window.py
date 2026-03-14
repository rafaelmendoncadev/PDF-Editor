"""
Main Window — root CustomTkinter window and application mediator.

Layout (3-column grid):
  ┌─────────────────────────────────────────────────┐
  │                    Toolbar                       │
  ├──────────┬──────────────────────────┬────────────┤
  │ PagePanel│       PDFViewer          │  (future)  │
  │(sidebar) │     (center canvas)      │            │
  └──────────┴──────────────────────────┴────────────┘

The window mediates all interactions between the UI components and
the core layer (PDFDocument, PDFRenderer, PDFExporter).
"""

from __future__ import annotations

import os
import logging
from tkinter import filedialog, messagebox
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_editor_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

import customtkinter as ctk
from PIL import Image

from app.core.pdf_document import PDFDocument
from app.core.pdf_exporter import PDFExporter
from app.core.pdf_renderer import PDFRenderer
from app.core.selection_manager import SelectionMode, SelectionRegion, SelectionManager
from app.core.content_remover import ContentRemover
from app.core.content_inserter import ContentInserter
from app.core.pdf_to_word import convert_pdf_to_word
from app.ui.page_panel import PagePanel
from app.ui.pdf_viewer import PDFViewer
from app.ui.toolbar import Toolbar
from app.ui.dialogs.text_editor_dialog import TextEditorDialog
from app.ui.dialogs.selection_preview_dialog import SelectionActionDialog


class MainWindow(ctk.CTk):
    """Root application window."""

    APP_TITLE = "PDF Editor"
    MIN_WIDTH = 900
    MIN_HEIGHT = 600

    def __init__(self) -> None:
        super().__init__()

        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(self.APP_TITLE)
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.geometry("1200x750")

        # Core objects
        self._document = PDFDocument()
        self._renderer = PDFRenderer()
        self._exporter = PDFExporter()
        self._selection_manager = SelectionManager()
        self._content_remover = ContentRemover()
        self._content_inserter = ContentInserter()
        self._current_page_index: int = 0

        # Selection state
        self._current_page_image: Optional[Image.Image] = None
        self._selection_active: bool = False

        self._build_layout()
        self._wire_callbacks()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        """Create and arrange all top-level widgets."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Toolbar (spans full width)
        self._toolbar = Toolbar(self)
        self._toolbar.grid(row=0, column=0, columnspan=3, sticky="ew")

        # Left sidebar — page thumbnails
        self._page_panel = PagePanel(self)
        self._page_panel.grid(row=1, column=0, sticky="ns", padx=(4, 0), pady=4)

        # Center — PDF viewer
        self._pdf_viewer = PDFViewer(self)
        self._pdf_viewer.grid(row=1, column=1, sticky="nsew", padx=4, pady=4)

        # Status bar
        self._status_var = ctk.StringVar(value="Nenhum documento aberto.")
        status_bar = ctk.CTkLabel(
            self,
            textvariable=self._status_var,
            anchor="w",
            height=24,
            text_color="gray",
        )
        status_bar.grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 4))

    # ------------------------------------------------------------------
    # Callback wiring
    # ------------------------------------------------------------------

    def _wire_callbacks(self) -> None:
        """Inject callbacks into child components."""
        self._toolbar.set_callbacks(
            on_open=self._action_open,
            on_save=self._action_save,
            on_export_word=self._action_export_word,
            on_add_text=self._action_add_text,
            on_remove_content=self._action_remove_content,
            on_move_up=self._action_move_page_up,
            on_move_down=self._action_move_page_down,
            on_delete_page=self._action_delete_page,
            on_select_rect=self._action_select_rectangular,
            on_select_freehand=self._action_select_freehand,
            on_cancel_selection=self._action_cancel_selection,
        )
        self._page_panel.set_on_page_selected(self._on_page_selected)

    # ------------------------------------------------------------------
    # Actions (called by toolbar)
    # ------------------------------------------------------------------

    def _action_open(self) -> None:
        """Show a file picker dialog and open the chosen PDF."""
        path = filedialog.askopenfilename(
            title="Abrir PDF",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        try:
            self._document.open(path)
        except Exception as exc:
            messagebox.showerror("Erro ao abrir PDF", str(exc))
            return

        self._current_page_index = 0
        self._refresh_all()
        self._toolbar.set_document_loaded(True)
        filename = os.path.basename(path)
        self.title(f"{self.APP_TITLE} — {filename}")
        self._set_status(f"Aberto: {filename}  ({self._document.page_count} páginas)")

    def _action_save(self) -> None:
        """Prompt for an output path and export the modified PDF."""
        if not self._document.is_open:
            return
        default_name = "editado_" + os.path.basename(self._document.path or "documento.pdf")
        path = filedialog.asksaveasfilename(
            title="Salvar PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if not path:
            return
        try:
            self._exporter.export(self._document, path)
            messagebox.showinfo("Salvo", f"PDF salvo em:\n{path}")
            self._set_status(f"Salvo: {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("Erro ao salvar PDF", str(exc))

    def _action_export_word(self) -> None:
        """Convert the open PDF to a Word (.docx) file."""
        if not self._document.is_open or not self._document.path:
            return

        # First, export the current state (with edits) to a temp PDF so
        # the conversion reflects any overlays / page changes the user made.
        import tempfile
        try:
            tmp_pdf = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False
            )
            tmp_pdf_path = tmp_pdf.name
            tmp_pdf.close()
            self._exporter.export(self._document, tmp_pdf_path)
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao preparar PDF para conversão:\n{exc}")
            return

        # Ask where to save the .docx
        base = os.path.splitext(os.path.basename(self._document.path))[0]
        default_name = f"{base}.docx"
        docx_path = filedialog.asksaveasfilename(
            title="Exportar como Word",
            defaultextension=".docx",
            initialfile=default_name,
            filetypes=[("Documento Word", "*.docx")],
        )
        if not docx_path:
            # Clean up temp file
            try:
                os.unlink(tmp_pdf_path)
            except OSError:
                pass
            return

        self._set_status("Convertendo PDF para Word…")
        self.update_idletasks()

        try:
            convert_pdf_to_word(tmp_pdf_path, docx_path)
            messagebox.showinfo(
                "Exportado",
                f"Arquivo Word salvo em:\n{docx_path}\n\n"
                "Abra o arquivo no Microsoft Word ou LibreOffice para editar.",
            )
            self._set_status(f"Exportado: {os.path.basename(docx_path)}")

            # Try to open the file in the default application
            try:
                os.startfile(docx_path)
            except Exception:
                pass  # Not critical if auto-open fails
        except Exception as exc:
            logger.exception("Export to Word failed")
            messagebox.showerror("Erro na conversão", str(exc))
            self._set_status("Erro ao exportar para Word.")
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_pdf_path)
            except OSError:
                pass

    def _action_add_text(self) -> None:
        """Open the TextEditorDialog for the current page."""
        if not self._document.is_open:
            return
        self._open_text_editor_dialog()

    def _action_remove_content(self) -> None:
        """Start rectangular selection to remove content from a region."""
        if not self._document.is_open:
            return
        self._selection_active = True
        self._toolbar.set_selection_mode(True)
        self._pdf_viewer.enable_selection(
            SelectionMode.RECTANGULAR,
            self._on_remove_selection_complete
        )
        self._set_status("Selecione a área com o conteúdo a ser removido. Clique e arraste.")

    def _action_move_page_up(self) -> None:
        """Move the current page one position earlier in the document."""
        idx = self._current_page_index
        if idx <= 0 or not self._document.is_open:
            return
        self._document.move_page(idx, idx - 1)
        self._current_page_index = idx - 1
        self._refresh_all()
        self._set_status(f"Página {idx + 1} movida para cima.")

    def _action_move_page_down(self) -> None:
        """Move the current page one position later in the document."""
        idx = self._current_page_index
        if idx >= self._document.page_count - 1 or not self._document.is_open:
            return
        self._document.move_page(idx, idx + 1)
        self._current_page_index = idx + 1
        self._refresh_all()
        self._set_status(f"Página {idx + 1} movida para baixo.")

    def _action_delete_page(self) -> None:
        """Delete the current page after user confirmation."""
        if not self._document.is_open:
            return
        confirmed = messagebox.askyesno(
            "Excluir Página",
            f"Excluir página {self._current_page_index + 1}? Esta ação não pode ser desfeita.",
        )
        if not confirmed:
            return
        try:
            self._document.delete_page(self._current_page_index)
        except ValueError as exc:
            messagebox.showwarning("Não é possível excluir", str(exc))
            return

        self._current_page_index = max(0, self._current_page_index - 1)
        self._refresh_all()
        self._set_status(f"Página excluída. {self._document.page_count} páginas restantes.")

    # ------------------------------------------------------------------
    # Page selection (called by PagePanel)
    # ------------------------------------------------------------------

    def _on_page_selected(self, index: int) -> None:
        """Called when the user clicks a thumbnail in the page panel."""
        self._current_page_index = index
        self._show_current_page()
        self._set_status(f"Página {index + 1} de {self._document.page_count}")

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def _refresh_all(self) -> None:
        """Rebuild thumbnails and re-render the current page."""
        self._rebuild_thumbnails()
        self._page_panel.select_page(self._current_page_index)
        self._show_current_page()

    def _rebuild_thumbnails(self) -> None:
        """Render all pages at thumbnail DPI and push to PagePanel."""
        thumbnails = []
        for i in range(self._document.page_count):
            page = self._document.get_page(i)
            img = self._renderer.render_thumbnail(page)
            thumbnails.append(img)
        self._page_panel.load_thumbnails(thumbnails)

    def _show_current_page(self) -> None:
        """Render the current page at viewer DPI and display it."""
        if not self._document.is_open:
            self._pdf_viewer.clear()
            return
        page = self._document.get_page(self._current_page_index)
        img = self._renderer.render_viewer(page)
        self._current_page_image = img

        # Get page dimensions
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height

        # Show page with dimensions for selection
        self._pdf_viewer.show_page(
            img,
            page_width=page_width,
            page_height=page_height,
            page_index=self._current_page_index
        )

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def _set_status(self, message: str) -> None:
        self._status_var.set(message)

    # ------------------------------------------------------------------
    # Selection actions
    # ------------------------------------------------------------------

    def _action_select_rectangular(self) -> None:
        """Start rectangular area selection."""
        if not self._document.is_open:
            return
        self._selection_active = True
        self._toolbar.set_selection_mode(True)
        self._pdf_viewer.enable_selection(
            SelectionMode.RECTANGULAR,
            self._on_selection_complete,
        )
        self._set_status("Seleção retangular ativa. Clique e arraste para selecionar uma área.")

    def _action_select_freehand(self) -> None:
        """Start freehand area selection."""
        if not self._document.is_open:
            return
        self._selection_active = True
        self._toolbar.set_selection_mode(True)
        self._pdf_viewer.enable_selection(
            SelectionMode.FREEHAND,
            self._on_selection_complete,
        )
        self._set_status("Seleção livre ativa. Clique e arraste para desenhar a seleção.")

    def _action_cancel_selection(self) -> None:
        """Cancel the active selection."""
        self._finish_selection()
        self._set_status("Seleção cancelada.")

    def _finish_selection(self) -> None:
        """Reset selection state in toolbar and viewer."""
        self._selection_active = False
        self._toolbar.set_selection_mode(False)
        self._pdf_viewer.disable_selection()

    # ------------------------------------------------------------------
    # Selection complete → Action dialog
    # ------------------------------------------------------------------

    def _on_selection_complete(self, region: SelectionRegion) -> None:
        """
        Called when the user finishes drawing a selection (rect or freehand).
        Shows the action dialog: Remove / Insert Text / Cancel.
        """
        self._finish_selection()

        if not self._current_page_image:
            messagebox.showerror("Erro", "Imagem da página não disponível.")
            return

        page = self._document.get_page(self._current_page_index)

        # Detect content inside the selected area
        content_info = self._content_remover.detect_content_in_region(page, region)
        summary = content_info.content_summary if content_info.has_content else ""

        SelectionActionDialog(
            self,
            region=region,
            page=page,
            page_image=self._current_page_image,
            content_summary=summary,
            on_remove=self._do_remove_region,
            on_insert_text=self._do_insert_text_in_region,
            on_cancel=lambda: self._set_status("Seleção cancelada."),
        )

    # ------------------------------------------------------------------
    # Content removal (direct from "Remover Conteúdo" button)
    # ------------------------------------------------------------------

    def _on_remove_selection_complete(self, region: SelectionRegion) -> None:
        """
        Shortcut path: user clicked "Remover Conteúdo" toolbar button,
        drew a selection — go straight to removal confirmation.
        """
        self._finish_selection()
        page = self._document.get_page(self._current_page_index)

        content_info = self._content_remover.detect_content_in_region(page, region)

        if not content_info.has_content:
            messagebox.showinfo(
                "Nenhum conteúdo",
                "A área selecionada não contém conteúdo para remover.",
            )
            self._set_status("Nenhum conteúdo encontrado na área selecionada.")
            return

        summary = content_info.content_summary
        confirmed = messagebox.askyesno(
            "Confirmar Remoção",
            f"Conteúdo encontrado na área selecionada:\n\n"
            f"{summary}\n\n"
            f"Deseja remover todo o conteúdo desta área?",
        )
        if not confirmed:
            self._set_status("Remoção cancelada.")
            return

        self._do_remove_region(region)

    # ------------------------------------------------------------------
    # Shared action helpers
    # ------------------------------------------------------------------

    def _do_remove_region(self, region: SelectionRegion) -> None:
        """Remove all content from *region* on the current page."""
        page = self._document.get_page(self._current_page_index)

        # Detect content for status message
        content_info = self._content_remover.detect_content_in_region(page, region)
        summary = content_info.content_summary if content_info.has_content else ""

        if not content_info.has_content:
            messagebox.showinfo(
                "Nenhum conteúdo",
                "A área selecionada não contém conteúdo para remover.",
            )
            self._set_status("Nenhum conteúdo encontrado na área selecionada.")
            return

        try:
            success = self._content_remover.clear_region(page, region)
            if success:
                self._show_current_page()
                self._rebuild_thumbnails()
                self._set_status(
                    f"Conteúdo removido da página {self._current_page_index + 1}: {summary}"
                )
            else:
                messagebox.showerror("Erro", "Falha ao remover conteúdo da área selecionada.")
                self._set_status("Erro ao remover conteúdo.")
        except Exception as exc:
            logger.exception(f"Error removing content: {exc}")
            messagebox.showerror("Erro", f"Erro ao remover conteúdo:\n\n{exc}")
            self._set_status("Erro ao remover conteúdo.")

    def _do_insert_text_in_region(self, region: SelectionRegion) -> None:
        """Open text editor dialog with coordinates pre-filled from the selection."""
        self._open_text_editor_dialog(
            default_x=region.x0,
            default_y=region.y0,
        )

    def _open_text_editor_dialog(
        self,
        default_x: float = 72.0,
        default_y: float = 72.0,
    ) -> None:
        """Open TextEditorDialog, optionally with pre-filled coordinates."""

        def on_confirm(text, x, y, font_size, color_rgb):
            self._document.add_text_overlay(
                page_index=self._current_page_index,
                x=x,
                y=y,
                text=text,
                font_size=font_size,
                color=color_rgb,
            )
            self._show_current_page()
            self._set_status(f"Texto adicionado à página {self._current_page_index + 1}")

        TextEditorDialog(
            self,
            page_index=self._current_page_index,
            on_confirm=on_confirm,
            default_x=default_x,
            default_y=default_y,
        )

