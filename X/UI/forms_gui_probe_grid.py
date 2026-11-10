"""Probe helpers for the original data grids: the Qt table of a DataGridView and a user cell edit through the
cell editor (delegate: BeginEdit, typed text, EndEdit)."""
from PyQt6 import QtCore, QtWidgets


def grid_widget(window, grid):
    return window.widgets[grid]


def edit_cell(app, table, row, column, text):
    table.setFocus()
    table.setCurrentCell(row, column)
    index = table.model().index(row, column)
    table.edit(index)
    app.processEvents()
    editor = table.indexWidget(index)
    if editor is None:
        raise AssertionError(f'no cell editor for ({row}, {column})')
    editor.setText(text)
    editor.textEdited.emit(text)
    table.commitData(editor)
    table.closeEditor(editor, QtWidgets.QAbstractItemDelegate.EndEditHint.NoHint)
    app.processEvents()


def cancel_cell(app, table, row, column):
    """Escape in the cell editor: the edit is cancelled (DataGridView.CancelEdit)."""
    app.processEvents()
    editor = table.indexWidget(table.model().index(row, column))
    if editor is None:
        raise AssertionError(f'no open cell editor at ({row}, {column})')
    text = editor.text()
    table.closeEditor(editor, QtWidgets.QAbstractItemDelegate.EndEditHint.RevertModelCache)
    app.processEvents()
    return text
