"""
Edit History Manager — manages undo/redo functionality for PDF editing.

Maintains a history of edit operations allowing users to undo and redo changes
while editing PDF documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import fitz  # PyMuPDF


class OperationType(Enum):
    """Types of edit operations"""
    DELETE = "delete"
    INSERT = "insert"
    MODIFY = "modify"
    BATCH = "batch"


@dataclass
class EditOperation:
    """
    Represents a single edit operation on a PDF.
    
    Stores complete information needed to undo or redo an operation.
    """
    operation_type: OperationType
    page_index: int
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Content snapshots
    region_before: Optional[Dict[str, Any]] = None  # Previous state
    region_after: Optional[Dict[str, Any]] = None   # New state
    
    # For deletion: what was removed
    deleted_content: Optional[bytes] = None
    
    # For insertion: what was added
    inserted_text: Optional[str] = None
    text_properties: Optional[Dict[str, Any]] = None
    
    # Operation result
    success: bool = True
    error_message: Optional[str] = None
    
    def __str__(self) -> str:
        """Human-readable operation description"""
        return f"{self.timestamp.strftime('%H:%M:%S')} - {self.description}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize operation to dictionary"""
        return {
            "type": self.operation_type.value,
            "page": self.page_index,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
        }


class EditHistory:
    """
    Manages complete edit history with undo/redo functionality.
    
    Usage:
        history = EditHistory(max_size=50)
        
        # Record an operation
        operation = EditOperation(...)
        history.record_operation(operation)
        
        # Undo/redo
        if history.can_undo():
            previous = history.undo()
        if history.can_redo():
            next_op = history.redo()
    """
    
    def __init__(self, max_size: int = 50) -> None:
        """
        Initialize edit history.
        
        Args:
            max_size: Maximum number of operations to keep in history
        """
        self._undo_stack: List[EditOperation] = []
        self._redo_stack: List[EditOperation] = []
        self._max_size = max_size
        self._current_index = -1
    
    # ------------------------------------------------------------------
    # Recording Operations
    # ------------------------------------------------------------------
    
    def record_operation(self, operation: EditOperation) -> None:
        """
        Record a new operation and clear redo stack.
        
        When a new operation is performed, all "undone" operations
        are discarded from the redo stack.
        
        Args:
            operation: The edit operation to record
        """
        # Enforce max history size
        if len(self._undo_stack) >= self._max_size:
            self._undo_stack.pop(0)
        
        self._undo_stack.append(operation)
        self._redo_stack.clear()
        self._current_index = len(self._undo_stack) - 1
    
    def record_batch_operation(self, operations: List[EditOperation], description: str) -> None:
        """
        Record multiple operations as a single batch.
        
        Useful for multi-step operations (e.g., delete + insert).
        
        Args:
            operations: List of operations to group
            description: Description of the batch operation
        """
        if not operations:
            return
        
        # Create batch operation
        batch = EditOperation(
            operation_type=OperationType.BATCH,
            page_index=operations[0].page_index,
            description=description,
            success=all(op.success for op in operations)
        )
        
        self.record_operation(batch)
    
    # ------------------------------------------------------------------
    # Undo/Redo Operations
    # ------------------------------------------------------------------
    
    def undo(self) -> Optional[EditOperation]:
        """
        Undo the last operation.
        
        Returns:
            The operation that was undone, or None if nothing to undo
        """
        if not self.can_undo():
            return None
        
        operation = self._undo_stack.pop()
        self._redo_stack.append(operation)
        self._current_index -= 1
        return operation
    
    def redo(self) -> Optional[EditOperation]:
        """
        Redo the last undone operation.
        
        Returns:
            The operation that was redone, or None if nothing to redo
        """
        if not self.can_redo():
            return None
        
        operation = self._redo_stack.pop()
        self._undo_stack.append(operation)
        self._current_index += 1
        return operation
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self._redo_stack) > 0
    
    # ------------------------------------------------------------------
    # History Query
    # ------------------------------------------------------------------
    
    def get_history_summary(self) -> List[str]:
        """
        Get human-readable summary of all operations.
        
        Returns:
            List of operation descriptions
        """
        return [str(op) for op in self._undo_stack]
    
    def get_current_operation(self) -> Optional[EditOperation]:
        """Get the currently active operation"""
        if self._current_index >= 0 and self._current_index < len(self._undo_stack):
            return self._undo_stack[self._current_index]
        return None
    
    def get_undo_description(self) -> str:
        """Get description of operation that would be undone"""
        if self.can_undo():
            op = self._undo_stack[-1]
            return f"Undo: {op.description}"
        return "Nothing to undo"
    
    def get_redo_description(self) -> str:
        """Get description of operation that would be redone"""
        if self.can_redo():
            op = self._redo_stack[-1]
            return f"Redo: {op.description}"
        return "Nothing to redo"
    
    def get_operations_by_page(self, page_index: int) -> List[EditOperation]:
        """
        Get all operations affecting a specific page.
        
        Args:
            page_index: The page index to filter by
        
        Returns:
            List of operations on that page
        """
        return [op for op in self._undo_stack if op.page_index == page_index]
    
    # ------------------------------------------------------------------
    # History Management
    # ------------------------------------------------------------------
    
    def clear_history(self) -> None:
        """Clear all undo and redo history"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._current_index = -1
    
    def clear_redo_stack(self) -> None:
        """Clear only the redo stack"""
        self._redo_stack.clear()
    
    def set_max_size(self, size: int) -> None:
        """
        Change the maximum history size.
        
        If current history exceeds new size, oldest operations are removed.
        """
        self._max_size = size
        
        # Trim undo stack if needed
        if len(self._undo_stack) > size:
            self._undo_stack = self._undo_stack[-size:]
    
    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    
    @property
    def undo_count(self) -> int:
        """Number of operations that can be undone"""
        return len(self._undo_stack)
    
    @property
    def redo_count(self) -> int:
        """Number of operations that can be redone"""
        return len(self._redo_stack)
    
    @property
    def total_operations(self) -> int:
        """Total operations in history (undo + redo)"""
        return self.undo_count + self.redo_count
    
    @property
    def is_empty(self) -> bool:
        """Check if history is empty"""
        return self.total_operations == 0
    
    def get_memory_estimate(self) -> int:
        """
        Estimate memory usage in bytes.
        
        Returns:
            Approximate memory usage of history
        """
        # Rough estimate: 1KB per operation + content
        size = 0
        for op in self._undo_stack + self._redo_stack:
            size += 1024  # Base operation size
            if op.deleted_content:
                size += len(op.deleted_content)
            if op.inserted_text:
                size += len(op.inserted_text) * 2  # UTF-16 estimate
        return size
    
    # ------------------------------------------------------------------
    # Export/Import
    # ------------------------------------------------------------------
    
    def export_history(self) -> List[Dict[str, Any]]:
        """
        Export history as list of dictionaries.
        
        Returns:
            Serializable history data
        """
        return [op.to_dict() for op in self._undo_stack]
    
    def import_history(self, data: List[Dict[str, Any]]) -> None:
        """
        Import history from exported format.
        
        Note: This is for logging/reporting, not restoration.
        Full operation restoration requires the actual EditOperation objects.
        
        Args:
            data: List of operation dictionaries
        """
        self.clear_history()
        # Import is primarily for analysis/reporting
        # Full restoration would require serializing operation details
