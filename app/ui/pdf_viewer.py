"""
PDF Viewer — scrollable canvas that displays the currently selected page.

The viewer receives a PIL.Image from PDFRenderer and renders it using
a Tkinter Canvas (with scrollbars) rather than CTkScrollableFrame, so we
get precise pixel control and zoom via Ctrl+scroll wheel.

Enhanced with interactive area selection tools supporting:
- Rectangular selection
- Freehand selection
- Visual feedback and preview
"""

from __future__ import annotations

from typing import Optional, Callable, Tuple, List

import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter as tk

from app.core.selection_manager import SelectionMode, SelectionRegion


class PDFViewer(ctk.CTkFrame):
    """
    Scrollable canvas panel that renders a single PDF page image.

    Usage:
        viewer.show_page(pil_image)   # display a new page
        viewer.clear()                # blank the canvas
    """

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, corner_radius=0, **kwargs)

        self._zoom: float = 1.0
        self._pil_image: Optional[Image.Image] = None
        self._tk_image: Optional[ImageTk.PhotoImage] = None
        self._image_id: Optional[int] = None
        
        # Selection state
        self._selection_mode: Optional[SelectionMode] = None
        self._selection_active: bool = False
        self._selection_start: Optional[Tuple[float, float]] = None
        self._selection_points: List[Tuple[float, float]] = []
        self._selection_rect_id: Optional[int] = None
        self._on_selection_callback: Optional[Callable[[SelectionRegion], None]] = None
        self._pdf_page_width: float = 0
        self._pdf_page_height: float = 0
        self._current_page_index: int = 0

        self._build_widgets()
        self._bind_events()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_page(
        self,
        image: Image.Image,
        page_width: float = 595.28,  # A4 width in points
        page_height: float = 841.89,  # A4 height in points
        page_index: int = 0
    ) -> None:
        """
        Display *image* (PIL.Image) on the canvas, centered.
        
        Args:
            image: PIL Image to display
            page_width: PDF page width in points
            page_height: PDF page height in points
            page_index: Current page index for selection tracking
        """
        self._pil_image = image
        self._zoom = 1.0
        self._pdf_page_width = page_width
        self._pdf_page_height = page_height
        self._current_page_index = page_index
        self._clear_selection_visual()
        self._render()

    def clear(self) -> None:
        """Clear the canvas and remove any displayed image."""
        self._canvas.delete("all")
        self._pil_image = None
        self._tk_image = None
        self._image_id = None
        self._canvas.configure(scrollregion=(0, 0, 0, 0))
        self._clear_selection_visual()
    
    # ------------------------------------------------------------------
    # Selection API
    # ------------------------------------------------------------------
    
    def enable_selection(
        self,
        mode: SelectionMode,
        callback: Callable[[SelectionRegion], None]
    ) -> None:
        """
        Enable area selection mode.
        
        Args:
            mode: Selection mode (rectangular, freehand, etc.)
            callback: Called with SelectionRegion when user completes selection
        """
        self._selection_mode = mode
        self._selection_active = True
        self._on_selection_callback = callback
        self._selection_points = []
        self._selection_start = None
        self._canvas.configure(cursor="crosshair")
    
    def disable_selection(self) -> None:
        """Disable selection mode and clear any active selection."""
        self._selection_active = False
        self._selection_mode = None
        self._on_selection_callback = None
        self._clear_selection_visual()
        self._canvas.configure(cursor="")
    
    def cancel_selection(self) -> None:
        """Cancel the current selection."""
        self._clear_selection_visual()
        self._selection_points = []
        self._selection_start = None

    # ------------------------------------------------------------------
    # Private — widget construction
    # ------------------------------------------------------------------

    def _build_widgets(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Canvas
        self._canvas = tk.Canvas(
            self,
            bg="#2b2b2b",
            highlightthickness=0,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")

        # Vertical scrollbar
        self._vscroll = ctk.CTkScrollbar(
            self, orientation="vertical", command=self._canvas.yview
        )
        self._vscroll.grid(row=0, column=1, sticky="ns")

        # Horizontal scrollbar
        self._hscroll = ctk.CTkScrollbar(
            self, orientation="horizontal", command=self._canvas.xview
        )
        self._hscroll.grid(row=1, column=0, sticky="ew")

        self._canvas.configure(
            yscrollcommand=self._vscroll.set,
            xscrollcommand=self._hscroll.set,
        )

        # Zoom label
        self._zoom_label = ctk.CTkLabel(
            self, text="100%", width=60, anchor="e", text_color="gray"
        )
        self._zoom_label.grid(row=1, column=1, sticky="e", padx=4)

    # ------------------------------------------------------------------
    # Private — rendering
    # ------------------------------------------------------------------

    def _render(self) -> None:
        """Convert the current PIL image with zoom and draw on canvas."""
        if self._pil_image is None:
            return

        img = self._pil_image
        if self._zoom != 1.0:
            new_w = int(img.width * self._zoom)
            new_h = int(img.height * self._zoom)
            img = img.resize((new_w, new_h), Image.LANCZOS)

        self._tk_image = ImageTk.PhotoImage(img)
        self._canvas.delete("all")
        # Center the image on the canvas
        canvas_w = self._canvas.winfo_width() or img.width
        canvas_h = self._canvas.winfo_height() or img.height
        x = max(img.width // 2, canvas_w // 2)
        y = max(img.height // 2, canvas_h // 2)
        self._image_id = self._canvas.create_image(x, y, image=self._tk_image, anchor="center")
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._zoom_label.configure(text=f"{int(self._zoom * 100)}%")

    # ------------------------------------------------------------------
    # Private — events
    # ------------------------------------------------------------------

    def _bind_events(self) -> None:
        # Zoom with Ctrl+scroll wheel
        self._canvas.bind("<Control-MouseWheel>", self._on_zoom_scroll)
        # Re-render when canvas is resized
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        # Selection events
        self._canvas.bind("<Button-1>", self._on_mouse_press)
        self._canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self._canvas.bind("<Escape>", self._on_escape)

    def _on_zoom_scroll(self, event: tk.Event) -> None:
        """Increase/decrease zoom on Ctrl+MouseWheel."""
        if event.delta > 0:
            self._zoom = min(self._zoom * 1.1, 5.0)
        else:
            self._zoom = max(self._zoom / 1.1, 0.2)
        self._render()

    def _on_canvas_resize(self, event: tk.Event) -> None:
        """Re-center the image when the canvas is resized."""
        if self._pil_image is not None:
            self._render()
    
    # ------------------------------------------------------------------
    # Selection event handlers
    # ------------------------------------------------------------------
    
    def _on_mouse_press(self, event: tk.Event) -> None:
        """Handle mouse button press."""
        if not self._selection_active or self._selection_mode is None:
            return
        
        self._selection_start = (event.x, event.y)
        
        if self._selection_mode == SelectionMode.RECTANGULAR:
            pass  # Will be drawn on drag
        elif self._selection_mode == SelectionMode.FREEHAND:
            self._selection_points = [(event.x, event.y)]
    
    def _on_mouse_drag(self, event: tk.Event) -> None:
        """Handle mouse drag."""
        if not self._selection_active or self._selection_start is None:
            return
        
        if self._selection_mode == SelectionMode.RECTANGULAR:
            self._draw_rectangular_selection(
                self._selection_start[0],
                self._selection_start[1],
                event.x,
                event.y
            )
        elif self._selection_mode == SelectionMode.FREEHAND:
            self._selection_points.append((event.x, event.y))
            self._draw_freehand_selection()
    
    def _on_mouse_release(self, event: tk.Event) -> None:
        """Handle mouse button release."""
        if not self._selection_active or self._selection_start is None:
            return
        
        if self._selection_mode == SelectionMode.RECTANGULAR:
            self._finalize_rectangular_selection(
                self._selection_start[0],
                self._selection_start[1],
                event.x,
                event.y
            )
        elif self._selection_mode == SelectionMode.FREEHAND:
            self._finalize_freehand_selection()
        
        self._selection_start = None
    
    def _on_escape(self, event: tk.Event) -> None:
        """Handle Escape key to cancel selection."""
        self.cancel_selection()
    
    # ------------------------------------------------------------------
    # Selection visualization
    # ------------------------------------------------------------------
    
    def _draw_rectangular_selection(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """Draw a rectangular selection outline."""
        self._clear_selection_visual()
        
        if self._image_id is None:
            return
        
        # Draw rectangle outline
        self._selection_rect_id = self._canvas.create_rectangle(
            x0, y0, x1, y1,
            outline="#00ff00",
            width=2,
            fill=""
        )
        # Draw corner handles
        handle_size = 6
        for hx, hy in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
            self._canvas.create_rectangle(
                hx - handle_size, hy - handle_size,
                hx + handle_size, hy + handle_size,
                outline="#00ff00",
                fill="#00ff00",
                tags="sel_handle"
            )
    
    def _draw_freehand_selection(self) -> None:
        """Draw a freehand selection path."""
        if len(self._selection_points) < 2:
            return
        
        self._clear_selection_visual()
        
        # Draw line connecting all points
        points_flat = []
        for px, py in self._selection_points:
            points_flat.extend([px, py])
        
        if len(points_flat) >= 4:
            self._selection_rect_id = self._canvas.create_line(
                *points_flat,
                fill="#00ff00",
                width=2,
                smooth=True
            )
    
    def _clear_selection_visual(self) -> None:
        """Clear all selection visual elements from canvas."""
        if self._selection_rect_id is not None:
            self._canvas.delete(self._selection_rect_id)
            self._selection_rect_id = None
        # Also delete any leftover handle rectangles
        self._canvas.delete("sel_handle")
    
    # ------------------------------------------------------------------
    # Selection finalization
    # ------------------------------------------------------------------
    
    def _finalize_rectangular_selection(
        self, x0: int, y0: int, x1: int, y1: int
    ) -> None:
        """Finalize a rectangular selection."""
        # Convert canvas coordinates to PDF coordinates
        from app.core.selection_manager import SelectionManager
        
        canvas_width = self._canvas.winfo_width()
        canvas_height = self._canvas.winfo_height()
        
        # Normalize coordinates
        min_x = min(x0, x1)
        max_x = max(x0, x1)
        min_y = min(y0, y1)
        max_y = max(y0, y1)
        
        # Convert to PDF space
        pdf_x0, pdf_y0 = SelectionManager.canvas_to_pdf(
            min_x, min_y, canvas_width, canvas_height,
            self._pdf_page_width, self._pdf_page_height, self._zoom
        )
        pdf_x1, pdf_y1 = SelectionManager.canvas_to_pdf(
            max_x, max_y, canvas_width, canvas_height,
            self._pdf_page_width, self._pdf_page_height, self._zoom
        )
        
        # Create selection region
        region = SelectionRegion(
            x0=pdf_x0,
            y0=pdf_y0,
            x1=pdf_x1,
            y1=pdf_y1,
            page_index=self._current_page_index,
            mode=SelectionMode.RECTANGULAR
        )
        
        # Call callback
        if self._on_selection_callback:
            self._on_selection_callback(region)
    
    def _finalize_freehand_selection(self) -> None:
        """Finalize a freehand selection."""
        from app.core.selection_manager import SelectionManager
        
        if len(self._selection_points) < 3:
            return
        
        canvas_width = self._canvas.winfo_width()
        canvas_height = self._canvas.winfo_height()
        
        # Find bounding box of freehand path
        xs = [p[0] for p in self._selection_points]
        ys = [p[1] for p in self._selection_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Convert to PDF space
        pdf_x0, pdf_y0 = SelectionManager.canvas_to_pdf(
            min_x, min_y, canvas_width, canvas_height,
            self._pdf_page_width, self._pdf_page_height, self._zoom
        )
        pdf_x1, pdf_y1 = SelectionManager.canvas_to_pdf(
            max_x, max_y, canvas_width, canvas_height,
            self._pdf_page_width, self._pdf_page_height, self._zoom
        )
        
        # Convert points to PDF space for storage
        pdf_points = [
            SelectionManager.canvas_to_pdf(
                px, py, canvas_width, canvas_height,
                self._pdf_page_width, self._pdf_page_height, self._zoom
            )
            for px, py in self._selection_points
        ]
        
        # Create selection region
        region = SelectionRegion(
            x0=pdf_x0,
            y0=pdf_y0,
            x1=pdf_x1,
            y1=pdf_y1,
            page_index=self._current_page_index,
            mode=SelectionMode.FREEHAND,
            points=pdf_points
        )
        
        # Call callback
        if self._on_selection_callback:
            self._on_selection_callback(region)
