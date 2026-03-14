# PDF Area Selection Feature — Complete Documentation

## Overview

The PDF Editor now includes a comprehensive interactive area selection system that allows users to precisely select and delimit specific regions of PDF documents for targeted editing operations. The system provides multiple selection modes with visual feedback, preview capabilities, and fine-tuning controls.

## Features

### 1. **Multiple Selection Modes**

#### Rectangular Selection (⬜ Rectangle)
- Click and drag to create rectangular selections
- Visual feedback with green outline and corner handles
- Best for precise, axis-aligned regions (text blocks, tables, etc.)

#### Freehand Selection (✏️ Freehand)
- Click and drag to draw custom shaped selections
- Creates smooth curves following user's mouse movement
- Best for irregular shapes, specific content areas
- Automatically converts to bounding box for PDF operations

### 2. **Visual Feedback**
- **Live outline** while drawing (green color for clarity)
- **Corner handles** on rectangular selections for easy identification
- **Real-time preview** of selected area in dialog
- **Dimension indicators** showing exact size and aspect ratio

### 3. **Selection Preview Dialog**

When a selection is completed, a comprehensive preview dialog appears with:

#### Preview Panel
- Live crop preview of the selected region
- Scaled to fit dialog size while maintaining aspect ratio
- Updates in real-time as coordinates change

#### Coordinate Controls
Four adjustable parameters with dual input methods:

1. **X Position (X0)**: Horizontal offset from page left
   - Slider: 0 to 2000 points (drag for quick adjustment)
   - Entry field: Type exact value (press Enter to confirm)

2. **Y Position (Y0)**: Vertical offset from page top
   - Slider: 0 to 2000 points
   - Entry field: Numeric input

3. **Width**: Selection width in points
   - Slider: 10 to 2000 points (minimum 10)
   - Entry field: Automatic right edge adjustment

4. **Height**: Selection height in points
   - Slider: 10 to 2000 points (minimum 10)
   - Entry field: Automatic bottom edge adjustment

#### Statistics Panel
- **Area**: Total selection area in square points (pt²)
- **Aspect Ratio**: Width-to-height ratio (e.g., 1.00 for square)

### 4. **Selection Management**

#### Coordinate System
- **PDF Points**: Standard measurement (72 points = 1 inch)
- **Automatic Conversion**: Canvas ↔ PDF coordinate transformation
- **Zoom-Aware**: Accounts for current viewer zoom level
- **Page-Relative**: All coordinates relative to page boundaries

#### Validation
- Selections automatically constrained within page bounds
- Minimum dimensions enforced (10×10 points)
- Invalid coordinate rejections with visual feedback

## User Workflow

### Step 1: Open PDF Document
```
1. Click "📂 Open PDF" button
2. Select PDF file from file browser
3. Document loads and displays first page
```

### Step 2: Activate Selection Mode
```
Option A - Rectangular:
  • Click "⬜ Rectangle" button in toolbar
  • Cursor changes to crosshair
  • Status bar shows "Rectangular selection active..."

Option B - Freehand:
  • Click "✏️ Freehand" button in toolbar
  • Cursor changes to crosshair
  • Status bar shows "Freehand selection active..."
```

### Step 3: Draw Selection
```
Rectangular Mode:
  1. Click at desired top-left corner
  2. Drag to bottom-right corner
  3. Release mouse to complete
  
Freehand Mode:
  1. Click starting point
  2. Drag along desired path
  3. Release mouse to complete (min 3 points required)
```

### Step 4: Adjust Selection (Optional)
```
In the Preview Dialog:
  
Using Sliders:
  1. Locate desired parameter (X, Y, Width, Height)
  2. Drag slider left/right for coarse adjustment
  3. Preview updates in real-time
  
Using Entry Fields:
  1. Click entry field (shows current value)
  2. Clear and type new value
  3. Press Enter to apply
  4. Tab to next field or click elsewhere

Fine-Tuning Tips:
  • Adjust Width/Height before X/Y for better control
  • Check Area and Aspect statistics while adjusting
  • Preview shows exactly what will be selected
```

### Step 5: Confirm or Cancel
```
To Confirm Selection:
  • Click "Confirm Selection" button
  • Selection stored in SelectionManager
  • Dialog closes, ready for next operation
  
To Discard and Retry:
  • Click "Cancel" button
  • Selection discarded
  • Returns to selection mode for new attempt
  
To Cancel Mode Entirely:
  • Click "✖ Cancel" button in toolbar
  • Exits selection mode
  • Selection tools disabled until reactivated
```

## Technical Architecture

### Core Components

#### 1. **SelectionManager** (`app/core/selection_manager.py`)
Manages selection state and coordinate transformations:

```python
class SelectionManager:
    - set_selection(region)       # Store current selection
    - get_current_selection()     # Retrieve active selection
    - clear_selection()           # Remove current selection
    - has_selection()             # Check if selection exists
    - canvas_to_pdf()             # Transform canvas → PDF coords
    - pdf_to_canvas()             # Transform PDF → canvas coords
    - validate_region()           # Check selection validity
```

Key Data Classes:
```python
class SelectionRegion:
    x0, y0                        # Top-left corner (PDF points)
    x1, y1                        # Bottom-right corner
    page_index                    # Which page this selection is on
    mode                          # RECTANGULAR, FREEHAND, BOUNDING_BOX
    points                        # For freehand: path points
    
    Properties:
    - width, height               # Dimensions
    - area                        # Total area
    - normalize()                 # Get normalized coords
    - to_rect()                   # Convert to fitz.Rect
```

#### 2. **Enhanced PDFViewer** (`app/ui/pdf_viewer.py`)
Handles visual selection and mouse interaction:

```python
class PDFViewer (enhanced):
    # Selection API
    - enable_selection(mode, callback)     # Activate selection
    - disable_selection()                  # Deactivate selection
    - cancel_selection()                   # Clear current selection
    
    # Mouse Event Handlers
    - _on_mouse_press()                    # Start selection
    - _on_mouse_drag()                     # Update visual feedback
    - _on_mouse_release()                  # Finalize selection
    
    # Visual Feedback
    - _draw_rectangular_selection()        # Green outline + handles
    - _draw_freehand_selection()           # Smooth path drawing
    - _clear_selection_visual()            # Remove graphics
```

#### 3. **SelectionPreviewDialog** (`app/ui/dialogs/selection_preview_dialog.py`)
Provides coordinate adjustment interface:

```python
class SelectionPreviewDialog(CTkToplevel):
    - Preview panel                        # Cropped image display
    - Coordinate input groups              # Sliders + entry fields
    - Statistics display                   # Area, aspect ratio
    - Action buttons                       # Confirm/Cancel
    
    Features:
    - Real-time preview update
    - Synchronized slider/entry values
    - Bounds validation
    - Dynamic statistics calculation
```

#### 4. **Enhanced Toolbar** (`app/ui/toolbar.py`)
New selection-related buttons:

```
Before:  [Open] [Save] | [Add Text] | [Move Up] [Move Down] [Delete]
After:   [Open] [Save] | [Add Text] [⬜ Rect] [✏️ Free] [✖ Cancel] | ...
```

Selection button states:
- Disabled when no PDF open
- "Cancel" only enabled during active selection
- Visual feedback (color change) when active

#### 5. **MainWindow Integration** (`app/ui/main_window.py`)
Orchestrates selection workflow:

```python
class MainWindow (enhanced):
    _selection_manager                     # Manages selections
    _current_page_image                    # Cache for preview dialog
    
    # Selection Actions
    - _action_select_rectangular()         # Activate rect mode
    - _action_select_freehand()            # Activate freehand mode
    - _action_cancel_selection()           # Deactivate selection
    - _on_selection_complete()             # Show preview dialog
```

### Coordinate System Details

#### Canvas → PDF Transformation
1. Account for current zoom level
2. Calculate scale factors:
   - `scale_x = pdf_width / (canvas_width * zoom)`
   - `scale_y = pdf_height / (canvas_height * zoom)`
3. Apply transformation:
   - `pdf_x = canvas_x * scale_x`
   - `pdf_y = canvas_y * scale_y`

#### PDF → Canvas Transformation (Reverse)
1. Calculate inverse scale factors
2. Account for zoom:
   - `effective_width = canvas_width * zoom`
3. Transform:
   - `canvas_x = pdf_x * (effective_width / pdf_width)`

#### Zoom Compensation
- Selection coordinates remain independent of zoom
- Visual representation scales with zoom
- PDF coordinates always in standard 72 DPI points

### Event Flow Diagram

```
User Clicks Rectangle Button
    ↓
_action_select_rectangular() called
    ↓
PDFViewer.enable_selection(RECTANGULAR, callback)
    ↓
User draws selection on canvas
    ↓
_on_mouse_press() → Record start point
_on_mouse_drag() → Draw visual feedback
_on_mouse_release() → Finalize selection
    ↓
SelectionRegion created with converted coords
    ↓
_on_selection_complete() called with region
    ↓
SelectionPreviewDialog displayed
    ↓
User adjusts coordinates in dialog
    ↓
On Confirm → SelectionManager.set_selection()
On Cancel → Selection discarded
```

## API Reference

### SelectionManager Methods

```python
# Selection State
selection_mgr.set_selection(region: SelectionRegion)
selection_mgr.get_current_selection() -> Optional[SelectionRegion]
selection_mgr.clear_selection()
selection_mgr.has_selection() -> bool

# Coordinate Transformation
SelectionManager.canvas_to_pdf(
    canvas_x, canvas_y,
    canvas_width, canvas_height,
    pdf_width, pdf_height,
    zoom=1.0
) -> (pdf_x, pdf_y)

SelectionManager.pdf_to_canvas(
    pdf_x, pdf_y,
    canvas_width, canvas_height,
    pdf_width, pdf_height,
    zoom=1.0
) -> (canvas_x, canvas_y)

# Validation
SelectionManager.validate_region(region, page) -> bool
```

### PDFViewer Selection Methods

```python
# Activation/Deactivation
viewer.enable_selection(
    mode: SelectionMode,
    callback: Callable[[SelectionRegion], None]
)
viewer.disable_selection()
viewer.cancel_selection()

# State Query
viewer._selection_active -> bool
viewer._selection_mode -> Optional[SelectionMode]
```

### SelectionPreviewDialog Constructor

```python
SelectionPreviewDialog(
    master,                           # Parent window
    region: SelectionRegion,          # Initial selection
    page: fitz.Page,                 # PDF page object
    page_image: PIL.Image.Image,     # Rendered page
    on_confirm: Callable,            # Confirmation callback
    on_cancel: Optional[Callable]    # Cancel callback
)
```

## Usage Examples

### Example 1: Programmatic Selection

```python
from app.core.selection_manager import SelectionRegion, SelectionMode

# Create selection programmatically
region = SelectionRegion(
    x0=50,                           # 50 points from left
    y0=100,                          # 100 points from top
    x1=400,                          # 400 points from left
    y1=300,                          # 300 points from top
    page_index=0,                    # On page 1
    mode=SelectionMode.RECTANGULAR
)

# Store in manager
selection_manager.set_selection(region)

# Check validity
if SelectionManager.validate_region(region, page):
    print(f"Area: {region.area} pt²")
    print(f"Size: {region.width}x{region.height}")
```

### Example 2: Coordinate Conversion

```python
# Convert mouse position to PDF coordinates
canvas_x, canvas_y = event.x, event.y

pdf_x, pdf_y = SelectionManager.canvas_to_pdf(
    canvas_x, canvas_y,
    canvas_width=1000,
    canvas_height=1500,
    pdf_page_width=595.28,    # A4 width
    pdf_page_height=841.89,   # A4 height
    zoom=1.2                  # 120% zoom
)

# Use PDF coordinates for operations
print(f"Selected at: ({pdf_x:.1f}, {pdf_y:.1f})")
```

### Example 3: Working with Selection Data

```python
selection = selection_manager.get_current_selection()

if selection:
    # Get normalized bounds
    normalized = selection.normalize()
    
    # Convert to fitz.Rect for PDF operations
    rect = selection.to_rect()
    
    # Extract statistics
    print(f"Aspect ratio: {selection.width / selection.height:.2f}")
    print(f"Area: {selection.area:.0f} points²")
    
    # Check containment
    if selection.contains_point(100, 150):
        print("Point is within selection")
```

## Performance Considerations

### Rendering Optimization
- **Lazy Preview**: Preview only updates when coordinates change
- **Debounced Updates**: Slider changes batched to reduce redraws
- **Canvas Caching**: Page image cached to avoid re-rendering

### Memory Management
- **Selection History**: Limited to prevent unbounded growth
- **Image Cropping**: Preview uses cropped image, not full page
- **Coordinate Storage**: Points stored as float pairs (minimal memory)

### Event Handling
- **Non-blocking**: Mouse events processed without dialog blocking
- **Event Coalescing**: Rapid updates merged (esp. drag operations)
- **Escape Key**: Cancel operation instantly (Escape key support)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Escape` | Cancel current selection |
| `Enter` | Confirm coordinate entry in preview dialog |
| `Tab` | Move to next coordinate field |
| `Ctrl+Z` | Undo last selection (future enhancement) |

## Future Enhancement Opportunities

1. **Selection Persistence**
   - Save selections as part of document
   - Recall and modify previous selections
   - Selection templates for common regions

2. **Multi-Selection**
   - Select multiple regions simultaneously
   - Union/intersection operations
   - Bulk operations on multiple areas

3. **Advanced Shapes**
   - Circular/elliptical selections
   - Polygon selections with arbitrary points
   - Bezier curve selection boundaries

4. **Selection Operations**
   - Copy selected region to clipboard
   - Export selected area as separate PDF
   - Apply transformations (rotate, scale) to selection

5. **Smart Selection**
   - Auto-detect text blocks
   - Detect table boundaries
   - Image boundary detection via ML

6. **Undo/Redo**
   - Full undo/redo for selection changes
   - History visualization
   - Selection revert functionality

## Troubleshooting

### Issue: Selection appears outside PDF bounds
- **Cause**: Zoom level not synchronized
- **Solution**: Check `_zoom` value matches viewer zoom
- **Verify**: Coordinates should always be within page rect

### Issue: Preview shows incorrect area
- **Cause**: DPI mismatch in rendering
- **Solution**: Ensure page render DPI matches coordinates
- **Check**: `PDFRenderer.DEFAULT_VIEWER_DPI = 150`

### Issue: Slider values don't match entry field
- **Cause**: Rounding difference in display
- **Solution**: This is expected (preview is rounded)
- **Note**: Confirmation uses actual float values

### Issue: Selection dialog appears off-screen
- **Cause**: Large font size or high DPI
- **Solution**: Dialog centers on parent window
- **Workaround**: Resize parent window to be larger

## Support and Feedback

For issues, improvements, or feature requests:
1. Check this documentation first
2. Review code comments in selection modules
3. Test with provided example PDFs
4. Report with:
   - PDF file (if possible)
   - Steps to reproduce
   - Expected vs. actual behavior
   - Screenshot if applicable
