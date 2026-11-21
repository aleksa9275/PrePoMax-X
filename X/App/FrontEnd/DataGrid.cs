// DataGridView drawn on the model's own geometry (GetCellDisplayRectangle, HitTest, FirstDisplayedScrollingRowIndex):
// columns, rows (the new row marked '*'), cell text, selection and current cell; selection, edits, keys and the context
// menu go back through the WinForms events (the successor of DataGridWidget and GridDelegate in original_forms.py).
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Input;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Threading;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEnd
{
    internal sealed class DataGridView : Grid, IMirror
    {
        readonly WinForms.DataGridView _grid;
        readonly Surface _surface;
        readonly ScrollBar _bar = new ScrollBar { Orientation = Orientation.Vertical, AllowAutoHide = false, Width = 14 };
        bool _syncing;

        public DataGridView(WinForms.DataGridView grid)
        {
            _grid = grid;
            _surface = new Surface(this);
            ColumnDefinitions = new ColumnDefinitions("*,Auto");
            Children.Add(_surface);
            Grid.SetColumn(_bar, 1);
            Children.Add(_bar);
            _bar.Scroll += (s, e) => { if (!_syncing) { int first = (int)Math.Round(e.NewValue); Ui.Input(() => _grid.FirstDisplayedScrollingRowIndex = first); } };
            Update();
        }

        public void Update()
        {
            FitColumns();
            int rows = _grid.RowCount;
            int page = Math.Max(1, (_grid.ClientSize.Height - (_grid.ColumnHeadersVisible ? _grid.ColumnHeadersHeight : 0)) / 22);
            _syncing = true;
            try
            {
                _bar.Maximum = Math.Max(0, rows - page);
                _bar.ViewportSize = page; _bar.LargeChange = page; _bar.SmallChange = 1;
                _bar.Value = Math.Max(0, _grid.FirstDisplayedScrollingRowIndex);
                _bar.IsVisible = rows > page;
            }
            finally { _syncing = false; }
            _surface.SyncEditor();
            _surface.InvalidateVisual();
        }
        public void Refresh(string property) => Update();

        /// <summary>Fill columns share the width the others leave (WinForms sets their Width).</summary>
        void FitColumns()
        {
            var columns = _grid.Columns.Cast<WinForms.DataGridViewColumn>().Where(c => c.Visible).ToList();
            var fill = columns.Where(c => c.InheritedAutoSizeMode == WinForms.DataGridViewAutoSizeColumnMode.Fill).ToList();
            if (fill.Count == 0) return;
            int available = _grid.ClientSize.Width - 2 - (_grid.RowHeadersVisible ? _grid.RowHeadersWidth : 0) - (_bar.IsVisible ? 17 : 0)
                            - columns.Except(fill).Sum(c => c.Width);
            double weights = fill.Sum(c => Math.Max(1e-3, c.FillWeight));
            int left = Math.Max(0, available);
            for (int i = 0; i < fill.Count; i++)
            {
                int width = i == fill.Count - 1 ? left : (int)Math.Floor(available * Math.Max(1e-3, fill[i].FillWeight) / weights);
                width = Math.Max(fill[i].MinimumWidth, width);
                left -= width;
                if (fill[i].Width != width) { var column = fill[i]; Ui.Guard(() => column.Width = width); }
            }
        }

        internal sealed class Surface : DrawnCanvas
        {
            readonly DataGridView _owner;
            WinForms.DataGridView Grid => _owner._grid;
            (int Row, int Column)? _anchor;
            readonly HashSet<int> _headerRows = new HashSet<int>();
            bool _dragging;
            TextBox _editor;
            (int Row, int Column, string Text)? _reopen;

            public Surface(DataGridView owner) { _owner = owner; Focusable = true; ClipToBounds = true; Background = Brushes.White; }

            static IBrush Brush(System.Drawing.Color color, IBrush fallback) => color.IsEmpty || color.A == 0 ? fallback : Ui.Brush(color);

            static (TextAlignment, VerticalAlignment) Align(WinForms.DataGridViewContentAlignment alignment)
            {
                int value = (int)alignment == 0 ? 16 : (int)alignment;
                var vertical = value < 16 ? VerticalAlignment.Top : value < 256 ? VerticalAlignment.Center : VerticalAlignment.Bottom;
                int column = value < 16 ? value : value < 256 ? value >> 4 : value >> 8;
                return (column == 2 ? TextAlignment.Center : column == 4 ? TextAlignment.Right : TextAlignment.Left, vertical);
            }
            WinForms.DataGridViewContentAlignment CellAlignment(int column)
            {
                var alignment = Grid.Columns[column].DefaultCellStyle.Alignment;
                return alignment != WinForms.DataGridViewContentAlignment.NotSet ? alignment : Grid.DefaultCellStyle.Alignment;
            }

            void DrawText(DrawingContext context, string text, Rect rect, WinForms.DataGridViewContentAlignment alignment, IBrush brush, bool bold = false)
            {
                if (string.IsNullOrEmpty(text) || rect.Width <= 4) return;
                var (horizontal, vertical) = Align(alignment);
                var formatted = new FormattedText(text, CultureInfo.CurrentCulture, FlowDirection.LeftToRight,
                                                  bold ? new Typeface(FontFamily.Default, FontStyle.Normal, FontWeight.Bold) : Look.Typeface, Look.FontSize, brush)
                { MaxTextWidth = Math.Max(1, rect.Width - 4), TextAlignment = horizontal, Trimming = TextTrimming.CharacterEllipsis, MaxLineCount = 1 };
                double y = vertical == VerticalAlignment.Top ? rect.Y + 2 : vertical == VerticalAlignment.Bottom ? rect.Bottom - formatted.Height - 2 : rect.Y + (rect.Height - formatted.Height) / 2;
                using (context.PushClip(rect)) context.DrawText(formatted, new Point(rect.X + 2, y));
            }

            static Rect R(System.Drawing.Rectangle r) => new Rect(r.X, r.Y, r.Width, r.Height);

            protected override void Draw(DrawingContext context)
            {
                var grid = Grid;
                context.FillRectangle(Brush(grid.BackgroundColor, Brushes.White), new Rect(Bounds.Size));
                var gridPen = new Pen(Brush(grid.GridColor, Look.LightFrame), 1);
                var headerFace = new SolidColorBrush(Color.FromRgb(0xF7, 0xF7, 0xF7));
                var selected = new HashSet<(int, int)>(grid.SelectionRows.Zip(grid.SelectionColumns, (r, c) => (r, c)));
                var current = grid.CurrentCellAddress;
                int columns = grid.Columns.Count;
                IBrush cellBack = Brush(grid.DefaultCellStyle.BackColor, Brushes.White);
                IBrush cellFore = Brush(grid.DefaultCellStyle.ForeColor, Brushes.Black);
                for (int r = Math.Max(0, grid.FirstDisplayedScrollingRowIndex); r < grid.RowCount; r++)
                {
                    var rowRect = grid.GetRowDisplayRectangle(r, false);
                    if (rowRect.IsEmpty) break;
                    if (rowRect.Y > Bounds.Height) break;
                    for (int c = 0; c < columns; c++)
                    {
                        var column = grid.Columns[c];
                        if (!column.Visible) continue;
                        Rect rect = R(grid.GetCellDisplayRectangle(c, r, false));
                        bool isSelected = selected.Contains((r, c));
                        var style = grid.Rows[r].Cells[c].Style;
                        IBrush back = isSelected ? Look.Highlight : Brush(style?.BackColor ?? System.Drawing.Color.Empty, Brush(column.DefaultCellStyle.BackColor, cellBack));
                        IBrush fore = isSelected ? Brushes.White : Brush(style?.ForeColor ?? System.Drawing.Color.Empty, Brush(column.DefaultCellStyle.ForeColor, cellFore));
                        context.FillRectangle(back, rect);
                        if (!(_editor != null && grid.IsCurrentCellInEditMode && current.X == c && current.Y == r))
                            DrawText(context, grid.GetCellText(r, c), rect, CellAlignment(c), fore);
                        context.DrawLine(gridPen, new Point(rect.Right - 0.5, rect.Top), new Point(rect.Right - 0.5, rect.Bottom));
                        context.DrawLine(gridPen, new Point(rect.Left, rect.Bottom - 0.5), new Point(rect.Right, rect.Bottom - 0.5));
                        if (current.X == c && current.Y == r && IsFocused) context.DrawRectangle(new Pen(Brushes.Black, 1, DashStyle.Dot), rect.Deflate(1.5));
                    }
                    if (grid.RowHeadersVisible)
                    {
                        Rect head = R(grid.GetCellDisplayRectangle(-1, r, false));
                        context.FillRectangle(_headerRows.Contains(r) || current.Y == r ? new SolidColorBrush(Color.FromRgb(0xD9, 0xEB, 0xF9)) : headerFace, head);
                        context.DrawRectangle(gridPen, head.Deflate(0.5));
                        string mark = r == grid.NewRowIndex ? "*" : current.Y == r ? "▶" : "";
                        DrawText(context, mark, head, WinForms.DataGridViewContentAlignment.MiddleCenter, Brushes.Black);
                    }
                }
                if (grid.ColumnHeadersVisible)
                {
                    for (int c = 0; c < columns; c++)
                    {
                        var column = grid.Columns[c];
                        if (!column.Visible) continue;
                        Rect rect = R(grid.GetCellDisplayRectangle(c, -1, false));
                        context.FillRectangle(headerFace, rect);
                        context.DrawRectangle(gridPen, rect.Deflate(0.5));
                        var alignment = column.HeaderCell.Style.Alignment;
                        DrawText(context, column.HeaderText, rect, alignment == WinForms.DataGridViewContentAlignment.NotSet ? WinForms.DataGridViewContentAlignment.MiddleLeft : alignment, Brushes.Black);
                    }
                    if (grid.RowHeadersVisible)
                    {
                        var corner = new Rect(1, 1, grid.RowHeadersWidth, grid.ColumnHeadersHeight);
                        context.FillRectangle(headerFace, corner);
                        context.DrawRectangle(gridPen, corner.Deflate(0.5));
                    }
                }
                if (grid.BorderStyle != WinForms.BorderStyle.None) context.DrawRectangle(new Pen(Look.ButtonBorder), new Rect(Bounds.Size).Deflate(0.5));
            }

            // Selection --------------------------------------------------------------------------------------------------
            void Select(IEnumerable<(int Row, int Column)> cells, int currentRow, int currentColumn)
            {
                var list = cells.Distinct().ToList();
                int[] rows = list.Select(c => c.Row).ToArray(), columns = list.Select(c => c.Column).ToArray();
                int[] headers = _headerRows.OrderBy(r => r).ToArray();
                Ui.Input(() => Grid.SelectByUser(rows, columns, headers, currentRow, currentColumn));
                InvalidateVisual();
            }
            IEnumerable<(int, int)> Range((int Row, int Column) a, (int Row, int Column) b)
            {
                for (int r = Math.Min(a.Row, b.Row); r <= Math.Max(a.Row, b.Row); r++)
                    for (int c = Math.Min(a.Column, b.Column); c <= Math.Max(a.Column, b.Column); c++)
                        if (Grid.Columns[c].Visible) yield return (r, c);
            }
            IEnumerable<(int, int)> Row(int r) => Enumerable.Range(0, Grid.Columns.Count).Where(c => Grid.Columns[c].Visible).Select(c => (r, c));
            List<(int, int)> Current() => Grid.SelectionRows.Zip(Grid.SelectionColumns, (r, c) => (r, c)).ToList();

            protected override void OnPointerPressed(PointerPressedEventArgs e)
            {
                Keyboard.SetModifiers(e.KeyModifiers);
                Focus();
                Point p = e.GetPosition(this);
                var hit = Grid.HitTest((int)p.X, (int)p.Y);
                var kind = e.GetCurrentPoint(this).Properties.PointerUpdateKind;
                bool control = (e.KeyModifiers & (KeyModifiers.Control | KeyModifiers.Meta)) != 0, shift = (e.KeyModifiers & KeyModifiers.Shift) != 0;
                if (kind == PointerUpdateKind.RightButtonPressed)
                {
                    // WinForms: a right click opens the context menu without changing the selection
                    var cell = Grid.GetCellDisplayRectangle(Math.Max(-1, hit.ColumnIndex), hit.RowIndex, false);
                    int x = (int)p.X - cell.X, y = (int)p.Y - cell.Y;
                    Ui.Input(() => Grid.RaiseCellMouseDown(hit.RowIndex, hit.ColumnIndex, WinForms.MouseButtons.Right, x, y));
                    if (Grid.ContextMenuStrip != null) { var strip = Grid.ContextMenuStrip; Ui.Input(() => strip.Show(Grid, new System.Drawing.Point((int)p.X, (int)p.Y))); }
                    e.Handled = true;
                    return;
                }
                CommitEditor();
                if (hit.Type == WinForms.DataGridViewHitTestType.ColumnHeader)
                {
                    int column = hit.ColumnIndex;
                    Ui.Input(() => Grid.RaiseColumnHeaderMouseClick(column, WinForms.MouseButtons.Left, e.ClickCount));
                    return;
                }
                if (hit.RowIndex < 0) return;
                if (hit.Type == WinForms.DataGridViewHitTestType.RowHeader)
                {
                    if (!control && !shift) _headerRows.Clear();
                    int first = _anchor.HasValue && shift ? _anchor.Value.Row : hit.RowIndex;
                    for (int r = Math.Min(first, hit.RowIndex); r <= Math.Max(first, hit.RowIndex); r++) _headerRows.Add(r);
                    var cells = (control ? Current() : new List<(int, int)>()).Concat(_headerRows.SelectMany(Row));
                    _anchor = (hit.RowIndex, 0);
                    Select(cells, hit.RowIndex, Math.Max(0, Grid.CurrentCellAddress.X));
                    _dragging = true;
                    e.Handled = true;
                    return;
                }
                if (!control && !shift) _headerRows.Clear();
                var at = (hit.RowIndex, hit.ColumnIndex);
                if (e.ClickCount >= 2)
                {
                    var rect = Grid.GetCellDisplayRectangle(at.Item2, at.Item1, false);
                    int x = (int)p.X - rect.X, y = (int)p.Y - rect.Y;
                    Ui.Input(() => Grid.RaiseCellDoubleClick(at.Item1, at.Item2, x, y));
                    if (!Grid.ReadOnly && !Grid.Columns[at.Item2].ReadOnly) BeginEdit(at.Item1, at.Item2, null);
                    e.Handled = true;
                    return;
                }
                if (shift && _anchor.HasValue) Select(Range(_anchor.Value, at), at.Item1, at.Item2);
                else if (control)
                {
                    var cells = Current();
                    if (cells.Contains(at)) cells.Remove(at); else cells.Add(at);
                    _anchor = at;
                    Select(cells, at.Item1, at.Item2);
                }
                else { _anchor = at; Select(new[] { at }, at.Item1, at.Item2); }
                _dragging = true;
                e.Pointer.Capture(this);
                e.Handled = true;
            }

            protected override void OnPointerMoved(PointerEventArgs e)
            {
                if (!_dragging || !_anchor.HasValue || !e.GetCurrentPoint(this).Properties.IsLeftButtonPressed) return;
                Point p = e.GetPosition(this);
                var hit = Grid.HitTest((int)p.X, Math.Max(0, (int)p.Y));
                if (hit.RowIndex < 0) return;
                if (hit.Type == WinForms.DataGridViewHitTestType.RowHeader)
                {
                    for (int r = Math.Min(_anchor.Value.Row, hit.RowIndex); r <= Math.Max(_anchor.Value.Row, hit.RowIndex); r++) _headerRows.Add(r);
                    Select(_headerRows.SelectMany(Row), hit.RowIndex, Math.Max(0, Grid.CurrentCellAddress.X));
                    return;
                }
                if (hit.ColumnIndex < 0) return;
                var at = (hit.RowIndex, hit.ColumnIndex);
                if (Grid.CurrentCellAddress.Y == at.Item1 && Grid.CurrentCellAddress.X == at.Item2) return;
                Select(Range(_anchor.Value, at), _anchor.Value.Row, _anchor.Value.Column);
            }

            protected override void OnPointerReleased(PointerReleasedEventArgs e) { _dragging = false; e.Pointer.Capture(null); }

            protected override void OnPointerWheelChanged(PointerWheelEventArgs e)
            {
                int first = Math.Max(0, Math.Min(Math.Max(0, Grid.RowCount - 1), Grid.FirstDisplayedScrollingRowIndex - (int)Math.Round(e.Delta.Y * 3)));
                Ui.Input(() => Grid.FirstDisplayedScrollingRowIndex = first);
                CommitEditor();
                e.Handled = true;
            }

            void Move(int row, int column, bool extend)
            {
                row = Math.Max(0, Math.Min(Grid.RowCount - 1, row));
                column = Math.Max(0, Math.Min(Grid.Columns.Count - 1, column));
                if (Grid.RowCount == 0) return;
                var at = (row, column);
                _headerRows.Clear();
                if (extend && _anchor.HasValue) Select(Range(_anchor.Value, at), row, column);
                else { _anchor = at; Select(new[] { at }, row, column); }
                // Keep the current row in view
                int first = Math.Max(0, Grid.FirstDisplayedScrollingRowIndex);
                int visible = Math.Max(1, (int)((Bounds.Height - (Grid.ColumnHeadersVisible ? Grid.ColumnHeadersHeight : 0)) / 22) - 1);
                if (row < first) Ui.Input(() => Grid.FirstDisplayedScrollingRowIndex = row);
                else if (row >= first + visible) Ui.Input(() => Grid.FirstDisplayedScrollingRowIndex = row - visible + 1);
            }

            protected override void OnKeyDown(KeyEventArgs e)
            {
                Keyboard.SetModifiers(e.KeyModifiers);
                var current = Grid.CurrentCellAddress;
                bool control = (e.KeyModifiers & (KeyModifiers.Control | KeyModifiers.Meta)) != 0, shift = (e.KeyModifiers & KeyModifiers.Shift) != 0;
                if (control && (e.Key == Key.C || e.Key == Key.X || e.Key == Key.V || e.Key == Key.P))
                {
                    var keys = WinForms.Keys.Control | Keyboard.Code(e.Key);
                    Ui.Input(() => Grid.RaiseKeyDown(keys));
                    e.Handled = true;
                    return;
                }
                switch (e.Key)
                {
                    case Key.Delete: case Key.Back:
                        Ui.Input(() => Grid.RaiseKeyDown(WinForms.Keys.Delete));
                        e.Handled = true; return;
                    case Key.Up: Move(current.Y - 1, current.X, shift); e.Handled = true; return;
                    case Key.Down: Move(current.Y + 1, current.X, shift); e.Handled = true; return;
                    case Key.Left: Move(current.Y, current.X - 1, shift); e.Handled = true; return;
                    case Key.Right: Move(current.Y, current.X + 1, shift); e.Handled = true; return;
                    case Key.Home: Move(control ? 0 : current.Y, 0, shift); e.Handled = true; return;
                    case Key.End: Move(control ? Grid.RowCount - 1 : current.Y, Grid.Columns.Count - 1, shift); e.Handled = true; return;
                    case Key.PageDown: Move(current.Y + 10, current.X, shift); e.Handled = true; return;
                    case Key.PageUp: Move(current.Y - 10, current.X, shift); e.Handled = true; return;
                    case Key.Enter:
                        // WinForms: Enter moves to the cell below and stays in the grid
                        Move(current.Y + 1, Math.Max(0, current.X), false); e.Handled = true; return;
                    case Key.Tab:
                        if (Grid.StandardTab) return;
                        Move(current.Y, current.X + (shift ? -1 : 1), false); e.Handled = true; return;
                    case Key.F2:
                        if (current.Y >= 0 && current.X >= 0) BeginEdit(current.Y, current.X, null);
                        e.Handled = true; return;
                }
            }

            protected override void OnTextInput(TextInputEventArgs e)
            {
                var current = Grid.CurrentCellAddress;
                if (string.IsNullOrEmpty(e.Text) || current.Y < 0 || current.X < 0 || char.IsControl(e.Text[0])) return;
                // EditOnKeystroke: the typed character starts the edit
                BeginEdit(current.Y, current.X, e.Text);
                e.Handled = true;
            }

            // Editing ------------------------------------------------------------------------------------------------------
            void BeginEdit(int row, int column, string typed)
            {
                if (!Ui.Input(() => Grid.BeginEditByUser(row, column))) return;
                string text = typed ?? Grid.EditingControl?.Text ?? Grid.GetCellText(row, column);
                if (typed != null) Ui.Input(() => Grid.EditTextByUser(typed));
                OpenEditor(row, column, text, typed == null);
            }

            void OpenEditor(int row, int column, string text, bool selectAll)
            {
                CloseEditor();
                var (alignment, _) = Align(CellAlignment(column));
                _editor = new TextBox { Text = text, BorderThickness = new Thickness(0), Padding = new Thickness(2, 0), TextAlignment = alignment,
                                        VerticalContentAlignment = VerticalAlignment.Center, Tag = (row, column) };
                _editor.TextChanged += (s, e) => { string t = _editor?.Text ?? ""; if (_editor != null) Ui.Guard(() => Grid.EditTextByUser(t)); };
                _editor.KeyDown += (s, e) =>
                {
                    if (e.Key == Key.Escape) { CloseEditor(); Ui.Input(() => Grid.CancelEdit()); Focus(); e.Handled = true; }
                    else if (e.Key == Key.Enter || e.Key == Key.Tab)
                    {
                        bool committed = CommitEditor();
                        Focus();
                        if (committed)
                        {
                            var current = Grid.CurrentCellAddress;
                            if (e.Key == Key.Enter) Move(current.Y + 1, current.X, false);
                            else Move(current.Y, current.X + ((e.KeyModifiers & KeyModifiers.Shift) != 0 ? -1 : 1), false);
                        }
                        e.Handled = true;
                    }
                    else if (e.Key == Key.Up || e.Key == Key.Down)
                    {
                        if (CommitEditor()) { Focus(); var current = Grid.CurrentCellAddress; Move(current.Y + (e.Key == Key.Up ? -1 : 1), current.X, false); }
                        e.Handled = true;
                    }
                };
                _editor.LostFocus += (s, e) => Dispatcher.UIThread.Post(() => { if (_editor != null && !_editor.IsFocused) CommitEditor(); });
                Children.Add(_editor);
                PlaceEditor();
                Dispatcher.UIThread.Post(() =>
                {
                    if (_editor == null) return;
                    _editor.Focus();
                    if (selectAll) _editor.SelectAll(); else _editor.CaretIndex = (_editor.Text ?? "").Length;
                });
                InvalidateVisual();
            }

            void PlaceEditor()
            {
                if (_editor == null) return;
                var (row, column) = ((int, int))_editor.Tag;
                if (row >= Grid.RowCount) { CloseEditor(); return; }
                var rect = Grid.GetCellDisplayRectangle(column, row, false);
                SetLeft(_editor, rect.X); SetTop(_editor, rect.Y);
                _editor.Width = Math.Max(10, rect.Width - 1); _editor.Height = Math.Max(10, rect.Height - 1);
                _editor.IsVisible = !rect.IsEmpty;
            }

            /// <summary>EndEdit with the typed text; a rejected value (OnDataError) keeps the cell in edit mode with the text.</summary>
            bool CommitEditor()
            {
                if (_editor == null) return true;
                string text = _editor.Text ?? "";
                var (row, column) = ((int, int))_editor.Tag;
                CloseEditor();
                Ui.Input(() => { Grid.EditTextByUser(text); Grid.EndEdit(); });
                if (Grid.IsCurrentCellInEditMode)
                {
                    _reopen = (row, column, text);
                    Dispatcher.UIThread.Post(() => { if (_reopen.HasValue) { var r = _reopen.Value; _reopen = null; OpenEditor(r.Row, r.Column, r.Text, false); } });
                    return false;
                }
                InvalidateVisual();
                return true;
            }

            void CloseEditor()
            {
                if (_editor == null) return;
                var editor = _editor;
                _editor = null;
                Children.Remove(editor);
                InvalidateVisual();
            }

            internal void SyncEditor()
            {
                if (_editor != null && !Grid.IsCurrentCellInEditMode) CloseEditor();
                PlaceEditor();
            }

            protected override void OnGotFocus(GotFocusEventArgs e) { base.OnGotFocus(e); InvalidateVisual(); }
            protected override void OnLostFocus(Avalonia.Interactivity.RoutedEventArgs e) { base.OnLostFocus(e); InvalidateVisual(); }
        }
    }
}
