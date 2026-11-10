// Headless DataGridView / BindingSource / clipboard data model for the original grid forms (D062).
// Semantics follow System.Windows.Forms: columns are generated from the bound list's item properties
// (DisplayName -> HeaderText, the property's TypeConverter formats and parses cell text), the last row is the
// "new row" while AllowUserToAddRows, committing a value there adds an item through the BindingSource, parse
// and commit failures go to OnDataError, and Ctrl+key input reaches KeyDown before ProcessDataGridViewKey.
// The renderer (X/UI/original_forms.py) draws the cells and feeds user edits, selection and keys back.
using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.Globalization;
using System.Linq;
using System.Text;

namespace System.Windows.Forms
{
    public enum DataGridViewContentAlignment { NotSet = 0, TopLeft = 1, TopCenter = 2, TopRight = 4, MiddleLeft = 16, MiddleCenter = 32, MiddleRight = 64, BottomLeft = 256, BottomCenter = 512, BottomRight = 1024 }
    public enum DataGridViewTriState { NotSet, True, False }
    public enum DataGridViewColumnHeadersHeightSizeMode { EnableResizing, DisableResizing, AutoSize }
    public enum DataGridViewRowHeadersWidthSizeMode { EnableResizing, DisableResizing, AutoSizeToAllHeaders, AutoSizeToDisplayedHeaders, AutoSizeToFirstHeader }
    public enum DataGridViewAutoSizeColumnMode { NotSet = 0, None = 1, ColumnHeader = 2, AllCellsExceptHeader = 4, AllCells = 6, DisplayedCellsExceptHeader = 8, DisplayedCells = 10, Fill = 16 }
    public enum DataGridViewAutoSizeColumnsMode { None = 1, ColumnHeader = 2, AllCellsExceptHeader = 4, AllCells = 6, DisplayedCellsExceptHeader = 8, DisplayedCells = 10, Fill = 16 }
    public enum DataGridViewAutoSizeRowsMode { None = 0, AllHeaders = 5, AllCellsExceptHeaders = 6, AllCells = 7, DisplayedHeaders = 9, DisplayedCellsExceptHeaders = 10, DisplayedCells = 11 }
    public enum DataGridViewColumnSortMode { NotSortable, Automatic, Programmatic }
    public enum DataGridViewClipboardCopyMode { Disable, EnableWithAutoHeaderText, EnableWithoutHeaderText, EnableAlwaysIncludeHeaderText }
    public enum DataGridViewSelectionMode { CellSelect, FullRowSelect, FullColumnSelect, RowHeaderSelect, ColumnHeaderSelect }
    public enum DataGridViewEditMode { EditOnEnter, EditOnKeystroke, EditOnKeystrokeOrF2, EditOnF2, EditProgrammatically }
    public enum DataGridViewCellBorderStyle { Custom, Single, Raised, Sunken, None, SingleVertical, RaisedVertical, SunkenVertical, SingleHorizontal, RaisedHorizontal, SunkenHorizontal }
    public enum DataGridViewHeaderBorderStyle { Custom, Single, Raised, Sunken, None }
    [Flags]
    public enum DataGridViewDataErrorContexts { Formatting = 1, Display = 2, PreferredSize = 4, RowDeletion = 8, Parsing = 256, Commit = 512, InitialValueRestoration = 1024, LeaveControl = 2048, CurrentCellChange = 4096, Scroll = 8192, ClipboardContent = 16384 }

    public class DataGridViewCellStyle
    {
        public DataGridViewCellStyle() { }
        public DataGridViewCellStyle(DataGridViewCellStyle style)
        {
            if (style == null) return;
            Alignment = style.Alignment; BackColor = style.BackColor; ForeColor = style.ForeColor; Font = style.Font;
            SelectionBackColor = style.SelectionBackColor; SelectionForeColor = style.SelectionForeColor; WrapMode = style.WrapMode;
            Format = style.Format; NullValue = style.NullValue; DataSourceNullValue = style.DataSourceNullValue; Padding = style.Padding;
        }
        public DataGridViewContentAlignment Alignment { get; set; }
        public Color BackColor { get; set; }
        public Color ForeColor { get; set; }
        public Color SelectionBackColor { get; set; }
        public Color SelectionForeColor { get; set; }
        public FontSpec Font { get; set; }
        public DataGridViewTriState WrapMode { get; set; }
        public string Format { get; set; } = "";
        public object NullValue { get; set; } = "";
        public object DataSourceNullValue { get; set; } = DBNull.Value;
        public Padding Padding { get; set; }
        public IFormatProvider FormatProvider { get; set; }
    }

    public class DataGridViewHeaderCell
    {
        public DataGridViewCellStyle Style { get; set; } = new DataGridViewCellStyle();
        public object Value { get; set; }
        public string ToolTipText { get; set; } = "";
    }
    public class DataGridViewColumnHeaderCell : DataGridViewHeaderCell { public SortOrder SortGlyphDirection { get; set; } }
    public class DataGridViewRowHeaderCell : DataGridViewHeaderCell { }

    public class DataGridViewColumn : Component
    {
        string _headerText = "", _name = "";
        int _width = 100;
        bool _readOnly, _visible = true;
        DataGridViewAutoSizeColumnMode _autoSizeMode = DataGridViewAutoSizeColumnMode.NotSet;
        public DataGridViewColumn() { }
        public DataGridView DataGridView { get; internal set; }
        public int Index => DataGridView?.Columns.IndexOf(this) ?? -1;
        public string Name { get => _name; set { _name = value ?? ""; Changed(); } }
        public string HeaderText { get => _headerText; set { _headerText = value ?? ""; Changed(); } }
        public int Width { get => _width; set { _width = Math.Max(MinimumWidth, value); Changed(); } }
        public int MinimumWidth { get; set; } = 5;
        public float FillWeight { get; set; } = 100;
        public bool ReadOnly { get => _readOnly; set { _readOnly = value; Changed(); } }
        public bool Visible { get => _visible; set { _visible = value; Changed(); } }
        public bool Frozen { get; set; }
        public bool Resizable { get; set; } = true;
        public object Tag { get; set; }
        public string ToolTipText { get; set; } = "";
        public string DataPropertyName { get; set; } = "";
        public bool IsDataBound => Property != null;
        public Type ValueType { get; set; }
        public DataGridViewAutoSizeColumnMode AutoSizeMode { get => _autoSizeMode; set { _autoSizeMode = value; Changed(); } }
        public DataGridViewAutoSizeColumnMode InheritedAutoSizeMode =>
            _autoSizeMode != DataGridViewAutoSizeColumnMode.NotSet ? _autoSizeMode
            : (DataGridViewAutoSizeColumnMode)(DataGridView?.AutoSizeColumnsMode ?? DataGridViewAutoSizeColumnsMode.None);
        public DataGridViewColumnSortMode SortMode { get; set; } = DataGridViewColumnSortMode.Automatic;
        public DataGridViewCellStyle DefaultCellStyle { get; set; } = new DataGridViewCellStyle();
        public DataGridViewColumnHeaderCell HeaderCell { get; set; } = new DataGridViewColumnHeaderCell();
        public DataGridViewCell CellTemplate { get; set; }
        /// <summary>Bound column: the list item property and its converter (WinForms BoundColumnConverter).</summary>
        internal PropertyDescriptor Property { get; set; }
        internal bool AutoGenerated { get; set; }
        public TypeConverter BoundColumnConverter => Property?.Converter;
        void Changed() => DataGridView?.GridChanged();
        public override string ToString() => "DataGridViewColumn { Name=" + Name + ", Index=" + Index + " }";
    }
    public class DataGridViewTextBoxColumn : DataGridViewColumn { public int MaxInputLength { get; set; } = 32767; }
    public class DataGridViewCheckBoxColumn : DataGridViewColumn { }
    public class DataGridViewComboBoxColumn : DataGridViewColumn { public ArrayList Items { get; } = new ArrayList(); public object DataSource { get; set; } }

    public class DataGridViewCell
    {
        internal DataGridViewCell(DataGridView owner, int column, int row) { DataGridView = owner; ColumnIndex = column; RowIndex = row; }
        public DataGridViewCell() { }
        public DataGridView DataGridView { get; }
        public int ColumnIndex { get; }
        public int RowIndex { get; }
        public DataGridViewColumn OwningColumn => DataGridView?.Columns[ColumnIndex];
        public DataGridViewRow OwningRow => DataGridView?.Rows[RowIndex];
        public object Value { get => DataGridView.GetCellValue(RowIndex, ColumnIndex); set => DataGridView.SetCellValue(RowIndex, ColumnIndex, value); }
        public object FormattedValue => DataGridView.GetCellText(RowIndex, ColumnIndex);
        public bool Selected { get => DataGridView.IsSelected(RowIndex, ColumnIndex); set => DataGridView.SetSelected(RowIndex, ColumnIndex, value); }
        public bool ReadOnly => DataGridView.ReadOnly || OwningColumn.ReadOnly;
        public bool Visible => OwningColumn.Visible;
        public bool IsInEditMode => DataGridView.IsCurrentCellInEditMode && DataGridView.CurrentCell?.Equals(this) == true;
        public string ErrorText { get; set; } = "";
        public string ToolTipText { get; set; } = "";
        public object Tag { get; set; }
        public DataGridViewCellStyle Style { get; set; } = new DataGridViewCellStyle();
        public Type ValueType => OwningColumn?.Property?.PropertyType ?? OwningColumn?.ValueType;
        public override bool Equals(object obj) => obj is DataGridViewCell c && c.DataGridView == DataGridView && c.ColumnIndex == ColumnIndex && c.RowIndex == RowIndex;
        public override int GetHashCode() => (RowIndex * 397) ^ ColumnIndex;
        public override string ToString() => "DataGridViewCell { ColumnIndex=" + ColumnIndex + ", RowIndex=" + RowIndex + " }";
    }
    public class DataGridViewTextBoxCell : DataGridViewCell { public DataGridViewTextBoxCell() { } internal DataGridViewTextBoxCell(DataGridView owner, int column, int row) : base(owner, column, row) { } }

    public class DataGridViewRow
    {
        internal DataGridViewRow(DataGridView owner, int index) { DataGridView = owner; Index = index; Cells = new DataGridViewCellCollection(this); }
        public DataGridViewRow() { Index = -1; Cells = new DataGridViewCellCollection(this); }
        public DataGridView DataGridView { get; }
        public int Index { get; }
        public bool IsNewRow => DataGridView != null && DataGridView.IsNewRowIndex(Index);
        public DataGridViewCellCollection Cells { get; }
        public object DataBoundItem => DataGridView?.GetItem(Index);
        /// <summary>WinForms RowHeaderSelect: a row is selected through its header (or in code), not by selecting
        /// all of its cells.</summary>
        public bool Selected { get => DataGridView.IsRowSelected(Index); set => DataGridView.SetRowSelected(Index, value); }
        public bool ReadOnly { get; set; }
        public bool Visible { get; set; } = true;
        public int Height { get; set; } = 22;
        public object Tag { get; set; }
        public string ErrorText { get; set; } = "";
        public DataGridViewRowHeaderCell HeaderCell { get; set; } = new DataGridViewRowHeaderCell();
        public DataGridViewCellStyle DefaultCellStyle { get; set; } = new DataGridViewCellStyle();
    }
    public class DataGridViewCellCollection : IEnumerable
    {
        readonly DataGridViewRow row;
        internal DataGridViewCellCollection(DataGridViewRow row) { this.row = row; }
        public int Count => row.DataGridView?.Columns.Count ?? 0;
        public DataGridViewCell this[int index] => row.DataGridView[index, row.Index];
        public DataGridViewCell this[string columnName] => row.DataGridView[row.DataGridView.Columns[columnName].Index, row.Index];
        public IEnumerator GetEnumerator() { for (int i = 0; i < Count; i++) yield return this[i]; }
    }

    public class DataGridViewColumnCollection : IList, IEnumerable<DataGridViewColumn>
    {
        readonly DataGridView owner;
        readonly List<DataGridViewColumn> columns = new List<DataGridViewColumn>();
        internal DataGridViewColumnCollection(DataGridView owner) { this.owner = owner; }
        public int Count => columns.Count;
        public DataGridViewColumn this[int index] => columns[index];
        public DataGridViewColumn this[string name] => columns.FirstOrDefault(c => string.Equals(c.Name, name, StringComparison.OrdinalIgnoreCase));
        public int Add(DataGridViewColumn column) { column.DataGridView = owner; columns.Add(column); owner.ColumnsChanged(); return columns.Count - 1; }
        public int Add(string name, string headerText) => Add(new DataGridViewTextBoxColumn { Name = name, HeaderText = headerText });
        public void AddRange(params DataGridViewColumn[] values) { foreach (var c in values) Add(c); }
        public void Insert(int index, DataGridViewColumn column) { column.DataGridView = owner; columns.Insert(index, column); owner.ColumnsChanged(); }
        public void Remove(DataGridViewColumn column) { if (columns.Remove(column)) { column.DataGridView = null; owner.ColumnsChanged(); } }
        public void Remove(string name) { var c = this[name]; if (c != null) Remove(c); }
        public void RemoveAt(int index) => Remove(columns[index]);
        public void Clear() { foreach (var c in columns) c.DataGridView = null; columns.Clear(); owner.ColumnsChanged(); }
        public bool Contains(string name) => this[name] != null;
        public bool Contains(DataGridViewColumn column) => columns.Contains(column);
        public int IndexOf(DataGridViewColumn column) => columns.IndexOf(column);
        public int GetColumnCount(DataGridViewElementStates states) => columns.Count(c => (states & DataGridViewElementStates.Visible) == 0 || c.Visible);
        internal void RemoveWhere(Func<DataGridViewColumn, bool> predicate) { foreach (var c in columns.Where(predicate).ToArray()) { columns.Remove(c); c.DataGridView = null; } }
        internal void AddSilently(DataGridViewColumn column) { column.DataGridView = owner; columns.Add(column); }
        public IEnumerator<DataGridViewColumn> GetEnumerator() => columns.GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => columns.GetEnumerator();
        object IList.this[int index] { get => columns[index]; set => throw new NotSupportedException(); }
        int IList.Add(object value) => Add((DataGridViewColumn)value);
        bool IList.Contains(object value) => columns.Contains(value as DataGridViewColumn);
        int IList.IndexOf(object value) => columns.IndexOf(value as DataGridViewColumn);
        void IList.Insert(int index, object value) => Insert(index, (DataGridViewColumn)value);
        void IList.Remove(object value) => Remove((DataGridViewColumn)value);
        bool IList.IsFixedSize => false;
        bool IList.IsReadOnly => false;
        void ICollection.CopyTo(Array array, int index) => ((ICollection)columns).CopyTo(array, index);
        bool ICollection.IsSynchronized => false;
        object ICollection.SyncRoot => this;
    }
    [Flags] public enum DataGridViewElementStates { None = 0, Displayed = 1, Frozen = 2, ReadOnly = 4, Resizable = 8, ResizableSet = 16, Selected = 32, Visible = 64 }

    public class DataGridViewRowCollection : IEnumerable
    {
        readonly DataGridView owner;
        internal DataGridViewRowCollection(DataGridView owner) { this.owner = owner; }
        public int Count => owner.RowCount;
        public DataGridViewRow this[int index] => index >= 0 && index < Count ? new DataGridViewRow(owner, index) : throw new ArgumentOutOfRangeException(nameof(index));
        /// <summary>Unbound grid: appends a row with the given cell values.</summary>
        public int Add(params object[] values) => owner.AddUnboundRow(values);
        public int Add() => owner.AddUnboundRow(new object[0]);
        public int Add(int count) { int index = -1; for (int i = 0; i < count; i++) index = Add(); return index; }
        public void RemoveAt(int index) => owner.RemoveRow(index);
        public void Remove(DataGridViewRow row) => owner.RemoveRow(row.Index);
        public void Clear() => owner.ClearRows();
        public IEnumerator GetEnumerator() { for (int i = 0; i < Count; i++) yield return this[i]; }
    }
    public class DataGridViewSelectedCellCollection : IEnumerable
    {
        readonly List<DataGridViewCell> cells;
        internal DataGridViewSelectedCellCollection(List<DataGridViewCell> cells) { this.cells = cells; }
        public int Count => cells.Count;
        public DataGridViewCell this[int index] => cells[index];
        public bool Contains(DataGridViewCell cell) => cells.Contains(cell);
        public IEnumerator GetEnumerator() => cells.GetEnumerator();
    }
    public class DataGridViewSelectedRowCollection : IEnumerable
    {
        readonly List<DataGridViewRow> rows;
        internal DataGridViewSelectedRowCollection(List<DataGridViewRow> rows) { this.rows = rows; }
        public int Count => rows.Count;
        public DataGridViewRow this[int index] => rows[index];
        public IEnumerator GetEnumerator() => rows.GetEnumerator();
    }

    public class DataGridViewCellEventArgs : EventArgs { public int ColumnIndex { get; } public int RowIndex { get; } public DataGridViewCellEventArgs(int columnIndex, int rowIndex) { ColumnIndex = columnIndex; RowIndex = rowIndex; } }
    public class DataGridViewCellCancelEventArgs : CancelEventArgs { public int ColumnIndex { get; } public int RowIndex { get; } public DataGridViewCellCancelEventArgs(int columnIndex, int rowIndex) { ColumnIndex = columnIndex; RowIndex = rowIndex; } }
    public class DataGridViewCellMouseEventArgs : MouseEventArgs { public int ColumnIndex { get; } public int RowIndex { get; } public DataGridViewCellMouseEventArgs(int columnIndex, int rowIndex, int x, int y, MouseEventArgs e) : base(e.Button, e.Clicks, x, y, e.Delta) { ColumnIndex = columnIndex; RowIndex = rowIndex; } }
    public class DataGridViewEditingControlShowingEventArgs : EventArgs { public Control Control { get; } public DataGridViewCellStyle CellStyle { get; set; } public DataGridViewEditingControlShowingEventArgs(Control control, DataGridViewCellStyle cellStyle) { Control = control; CellStyle = cellStyle; } }
    public class DataGridViewDataErrorEventArgs : DataGridViewCellCancelEventArgs
    {
        public DataGridViewDataErrorEventArgs(Exception exception, int columnIndex, int rowIndex, DataGridViewDataErrorContexts context) : base(columnIndex, rowIndex) { Exception = exception; Context = context; }
        public DataGridViewDataErrorContexts Context { get; }
        public Exception Exception { get; }
        public bool ThrowException { get; set; }
    }
    public class DataGridViewRowEventArgs : EventArgs { public DataGridViewRow Row { get; } public DataGridViewRowEventArgs(DataGridViewRow row) { Row = row; } }
    public class DataGridViewRowCancelEventArgs : CancelEventArgs { public DataGridViewRow Row { get; } public DataGridViewRowCancelEventArgs(DataGridViewRow row) { Row = row; } }
    public delegate void DataGridViewCellEventHandler(object sender, DataGridViewCellEventArgs e);
    public delegate void DataGridViewCellCancelEventHandler(object sender, DataGridViewCellCancelEventArgs e);
    public delegate void DataGridViewCellMouseEventHandler(object sender, DataGridViewCellMouseEventArgs e);
    public delegate void DataGridViewEditingControlShowingEventHandler(object sender, DataGridViewEditingControlShowingEventArgs e);
    public delegate void DataGridViewDataErrorEventHandler(object sender, DataGridViewDataErrorEventArgs e);
    public delegate void DataGridViewRowEventHandler(object sender, DataGridViewRowEventArgs e);
    public delegate void DataGridViewRowCancelEventHandler(object sender, DataGridViewRowCancelEventArgs e);

    /// <summary>The cell editor (WinForms DataGridViewTextBoxEditingControl); the renderer mirrors the typed text into it.</summary>
    public class DataGridViewTextBoxEditingControl : TextBox { }

    public class DataGridView : Control, ISupportInitialize
    {
        object _dataSource;
        IList _list;
        PropertyDescriptorCollection _properties;
        readonly List<object[]> _unbound = new List<object[]>();
        readonly HashSet<(int Row, int Column)> _selection = new HashSet<(int, int)>();
        readonly HashSet<int> _selectedRows = new HashSet<int>();
        (int Row, int Column)? _current;
        bool _allowUserToAddRows = true, _readOnly;
        TextBox _editingControl;

        public DataGridView()
        {
            Columns = new DataGridViewColumnCollection(this);
            Rows = new DataGridViewRowCollection(this);
        }
        public DataGridViewColumnCollection Columns { get; }
        public DataGridViewRowCollection Rows { get; }
        public bool AutoGenerateColumns { get; set; } = true;
        public string DataMember { get; set; } = "";
        public object DataSource { get => _dataSource; set => Bind(value); }
        public bool AllowUserToAddRows { get => _allowUserToAddRows; set { _allowUserToAddRows = value; GridChanged(); } }
        public bool AllowUserToDeleteRows { get; set; } = true;
        public bool AllowUserToResizeRows { get; set; } = true;
        public bool AllowUserToResizeColumns { get; set; } = true;
        public bool AllowUserToOrderColumns { get; set; }
        public bool ReadOnly { get => _readOnly; set { _readOnly = value; GridChanged(); } }
        public bool MultiSelect { get; set; } = true;
        public bool RowHeadersVisible { get; set; } = true;
        public bool ColumnHeadersVisible { get; set; } = true;
        public int RowHeadersWidth { get; set; } = 41;
        public int ColumnHeadersHeight { get; set; } = 23;
        public DataGridViewSelectionMode SelectionMode { get; set; } = DataGridViewSelectionMode.RowHeaderSelect;
        public DataGridViewEditMode EditMode { get; set; } = DataGridViewEditMode.EditOnKeystrokeOrF2;
        public DataGridViewClipboardCopyMode ClipboardCopyMode { get; set; } = DataGridViewClipboardCopyMode.EnableWithAutoHeaderText;
        public DataGridViewAutoSizeColumnsMode AutoSizeColumnsMode { get; set; } = DataGridViewAutoSizeColumnsMode.None;
        public DataGridViewAutoSizeRowsMode AutoSizeRowsMode { get; set; }
        public DataGridViewColumnHeadersHeightSizeMode ColumnHeadersHeightSizeMode { get; set; } = DataGridViewColumnHeadersHeightSizeMode.EnableResizing;
        public DataGridViewRowHeadersWidthSizeMode RowHeadersWidthSizeMode { get; set; }
        public DataGridViewCellStyle DefaultCellStyle { get; set; } = new DataGridViewCellStyle();
        public DataGridViewCellStyle ColumnHeadersDefaultCellStyle { get; set; } = new DataGridViewCellStyle();
        public DataGridViewCellStyle RowHeadersDefaultCellStyle { get; set; } = new DataGridViewCellStyle();
        public DataGridViewCellStyle AlternatingRowsDefaultCellStyle { get; set; } = new DataGridViewCellStyle();
        public DataGridViewCellStyle RowsDefaultCellStyle { get; set; } = new DataGridViewCellStyle();
        public DataGridViewRow RowTemplate { get; set; } = new DataGridViewRow();
        public DataGridViewCellBorderStyle CellBorderStyle { get; set; } = DataGridViewCellBorderStyle.Single;
        public DataGridViewHeaderBorderStyle ColumnHeadersBorderStyle { get; set; }
        public DataGridViewHeaderBorderStyle RowHeadersBorderStyle { get; set; }
        public BorderStyle BorderStyle { get; set; } = BorderStyle.FixedSingle;
        public Color BackgroundColor { get; set; } = SystemColors.AppWorkspace;
        public Color GridColor { get; set; } = SystemColors.ControlDark;
        public bool EnableHeadersVisualStyles { get; set; } = true;
        public bool ShowCellToolTips { get; set; } = true;
        public bool StandardTab { get; set; }
        public ScrollBars ScrollBars { get; set; } = ScrollBars.Both;
        public void BeginInit() { }
        public void EndInit() { }

        public event DataGridViewCellEventHandler CellEndEdit, CellValueChanged, CellClick, CellDoubleClick, CellEnter, CellLeave;
        public event DataGridViewCellCancelEventHandler CellBeginEdit;
        public event DataGridViewCellMouseEventHandler CellMouseDown, CellMouseClick;
        public event DataGridViewEditingControlShowingEventHandler EditingControlShowing;
        public event DataGridViewDataErrorEventHandler DataError;
        public event DataGridViewRowEventHandler UserAddedRow, UserDeletedRow;
        public event DataGridViewRowCancelEventHandler UserDeletingRow;
        public event EventHandler SelectionChanged, CurrentCellChanged, DataSourceChanged;

        // Binding -----------------------------------------------------------------------------------------------------------------
        void Bind(object dataSource)
        {
            if (_dataSource is BindingSource oldSource) oldSource.ListChanged -= List_ListChanged;
            else if (_list is IBindingList oldList) oldList.ListChanged -= List_ListChanged;
            _dataSource = dataSource;
            _list = ResolveList(dataSource);
            _properties = null;
            _selection.Clear();
            _selectedRows.Clear();
            _current = null;
            _editingControl = null;
            IsCurrentCellInEditMode = false;
            // WinForms: the columns generated for the previous data source go; a new one generates its own.
            Columns.RemoveWhere(c => c.AutoGenerated);
            foreach (DataGridViewColumn column in Columns) column.Property = null;
            if (_list != null)
            {
                _properties = BindingSource.GetListItemProperties(_list);
                foreach (DataGridViewColumn column in Columns)
                    if (column.DataPropertyName.Length > 0) column.Property = _properties.Find(column.DataPropertyName, true);
                if (AutoGenerateColumns)
                {
                    foreach (PropertyDescriptor property in _properties)
                    {
                        if (!property.IsBrowsable || Columns.Cast<DataGridViewColumn>().Any(c => c.Property == property)) continue;
                        Columns.AddSilently(new DataGridViewTextBoxColumn
                        {
                            Name = property.Name, HeaderText = property.DisplayName, DataPropertyName = property.Name,
                            ReadOnly = property.IsReadOnly, ValueType = property.PropertyType, Property = property, AutoGenerated = true,
                        });
                    }
                }
                if (_dataSource is BindingSource source) source.ListChanged += List_ListChanged;
                else if (_list is IBindingList bindingList) bindingList.ListChanged += List_ListChanged;
            }
            if (RowCount > 0 && Columns.Count > 0) _current = (0, FirstVisibleColumn());
            if (_current.HasValue) _selection.Add(_current.Value);
            DataSourceChanged?.Invoke(this, EventArgs.Empty);
            GridChanged("Columns");
        }
        static IList ResolveList(object dataSource)
        {
            if (dataSource is BindingSource source) return source;
            if (dataSource is IListSource listSource) return listSource.GetList();
            return dataSource as IList;
        }
        void List_ListChanged(object sender, ListChangedEventArgs e) => GridChanged();
        int FirstVisibleColumn() { foreach (DataGridViewColumn c in Columns) if (c.Visible) return c.Index; return 0; }
        internal void ColumnsChanged() => GridChanged("Columns");
        internal void GridChanged(string what = "Grid") => Notify(what);
        bool AllowsNew => _list == null || (_list is BindingSource bs ? bs.AllowNew : _list is IBindingList bl ? bl.AllowNew : !_list.IsFixedSize && !_list.IsReadOnly);
        internal int DataRowCount => _list?.Count ?? _unbound.Count;
        public int RowCount => DataRowCount + (NewRowShown ? 1 : 0);
        bool NewRowShown => _allowUserToAddRows && !_readOnly && Columns.Count > 0 && AllowsNew;
        public int NewRowIndex => NewRowShown ? DataRowCount : -1;
        internal bool IsNewRowIndex(int row) => NewRowShown && row == DataRowCount;
        internal object GetItem(int row) => _list != null && row >= 0 && row < _list.Count ? _list[row] : null;

        // Cells -------------------------------------------------------------------------------------------------------------------
        public DataGridViewCell this[int columnIndex, int rowIndex]
        {
            get
            {
                if (columnIndex < 0 || columnIndex >= Columns.Count) throw new ArgumentOutOfRangeException(nameof(columnIndex));
                if (rowIndex < 0 || rowIndex >= RowCount) throw new ArgumentOutOfRangeException(nameof(rowIndex));
                return new DataGridViewTextBoxCell(this, columnIndex, rowIndex);
            }
        }
        public DataGridViewCell this[string columnName, int rowIndex] => this[Columns[columnName].Index, rowIndex];

        internal object GetCellValue(int row, int column)
        {
            if (IsNewRowIndex(row)) return null;
            DataGridViewColumn col = Columns[column];
            if (_list != null) return col.Property?.GetValue(_list[row]);
            object[] values = _unbound[row];
            return column < values.Length ? values[column] : null;
        }
        /// <summary>WinForms DataGridViewDataConnection.PushValue: a value of another type is parsed with the column
        /// converter; on the new row the item is created first (BindingSource.AddNew).</summary>
        internal void SetCellValue(int row, int column, object value)
        {
            DataGridViewColumn col = Columns[column];
            if (IsNewRowIndex(row)) row = AddNewRow();
            if (_list != null)
            {
                if (col.Property == null) throw new InvalidOperationException("The column is not data bound.");
                Type type = col.Property.PropertyType;
                if (value != null && value != DBNull.Value && !type.IsInstanceOfType(value))
                {
                    TypeConverter converter = col.Property.Converter;
                    if (value is string text && converter != null && converter.CanConvertFrom(typeof(string)))
                        value = converter.ConvertFrom(null, CultureInfo.CurrentCulture, text);
                    else value = Convert.ChangeType(value, Nullable.GetUnderlyingType(type) ?? type, CultureInfo.CurrentCulture);
                }
                object item = _list[row];
                col.Property.SetValue(item, value);
                if (_list is BindingSource source) source.RaiseItemChanged(row);
            }
            else
            {
                object[] values = _unbound[row];
                if (values.Length <= column) { Array.Resize(ref values, Columns.Count); _unbound[row] = values; }
                values[column] = value;
            }
            CellValueChanged?.Invoke(this, new DataGridViewCellEventArgs(column, row));
            GridChanged();
        }
        int AddNewRow()
        {
            if (_list == null) { _unbound.Add(new object[Columns.Count]); UserAddedRow?.Invoke(this, new DataGridViewRowEventArgs(Rows[_unbound.Count - 1])); return _unbound.Count - 1; }
            object item = _list is BindingSource source ? source.AddNew() : _list is IBindingList bl ? bl.AddNew() : AddDefaultItem();
            // The new row is committed at once (WinForms commits it when the row is left).
            (item as IEditableObject)?.EndEdit();
            int index = _list.IndexOf(item);
            UserAddedRow?.Invoke(this, new DataGridViewRowEventArgs(Rows[index]));
            return index;
        }
        object AddDefaultItem()
        {
            Type type = BindingSource.GetListItemType(_list);
            object item = Activator.CreateInstance(type);
            _list.Add(item);
            return item;
        }
        internal int AddUnboundRow(object[] values)
        {
            if (_list != null) throw new InvalidOperationException("Rows cannot be added programmatically to a data-bound DataGridView.");
            object[] row = new object[Math.Max(Columns.Count, values.Length)];
            Array.Copy(values, row, values.Length);
            _unbound.Add(row);
            GridChanged();
            return _unbound.Count - 1;
        }
        internal void RemoveRow(int index)
        {
            if (IsNewRowIndex(index)) throw new InvalidOperationException("The uncommitted new row cannot be deleted.");
            if (_list != null) _list.RemoveAt(index); else _unbound.RemoveAt(index);
            _selection.Clear();
            _selectedRows.Clear();
            if (_current.HasValue && _current.Value.Row >= RowCount) _current = RowCount > 0 ? (RowCount - 1, _current.Value.Column) : ((int, int)?)null;
            GridChanged();
        }
        internal void ClearRows()
        {
            if (_list != null) throw new InvalidOperationException("Rows of a data-bound DataGridView cannot be cleared.");
            _unbound.Clear(); _selection.Clear(); _selectedRows.Clear(); _current = null;
            GridChanged();
        }

        /// <summary>Cell display text: the column converter (or the value type's) formats it; null shows the NullValue.</summary>
        public string GetCellText(int row, int column)
        {
            object value = GetCellValue(row, column);
            if (value == null || value == DBNull.Value) return Convert.ToString(Columns[column].DefaultCellStyle.NullValue ?? DefaultCellStyle.NullValue ?? "", CultureInfo.CurrentCulture);
            TypeConverter converter = Columns[column].BoundColumnConverter ?? TypeDescriptor.GetConverter(value.GetType());
            try
            {
                if (converter != null && converter.CanConvertTo(typeof(string))) return converter.ConvertToString(null, CultureInfo.CurrentCulture, value);
                return Convert.ToString(value, CultureInfo.CurrentCulture);
            }
            catch (Exception ex)
            {
                OnDataError(true, new DataGridViewDataErrorEventArgs(ex, column, row, DataGridViewDataErrorContexts.Formatting | DataGridViewDataErrorContexts.Display));
                return "";
            }
        }
        /// <summary>WinForms DataGridViewCell.ParseFormattedValue: the NullValue text becomes DataSourceNullValue,
        /// other text goes through the column converter (or the value type's).</summary>
        object ParseCellText(int column, string text)
        {
            DataGridViewColumn col = Columns[column];
            if (text == Convert.ToString(col.DefaultCellStyle.NullValue ?? "", CultureInfo.CurrentCulture)) return col.DefaultCellStyle.DataSourceNullValue;
            Type type = col.Property?.PropertyType ?? col.ValueType;
            if (type == null || type == typeof(string) || type == typeof(object)) return text;
            TypeConverter converter = col.BoundColumnConverter ?? TypeDescriptor.GetConverter(type);
            return converter.ConvertFrom(null, CultureInfo.CurrentCulture, text);
        }

        // Selection and editing ---------------------------------------------------------------------------------------------------
        internal bool IsSelected(int row, int column) => _selection.Contains((row, column));
        internal void SetSelected(int row, int column, bool value)
        {
            bool changed = value ? _selection.Add((row, column)) : _selection.Remove((row, column));
            if (changed) { GridChanged("Selection"); SelectionChanged?.Invoke(this, EventArgs.Empty); }
        }
        public DataGridViewSelectedCellCollection SelectedCells =>
            new DataGridViewSelectedCellCollection(_selection.Where(s => s.Row < RowCount && s.Column < Columns.Count)
                .OrderByDescending(s => s.Row).ThenByDescending(s => s.Column).Select(s => this[s.Column, s.Row]).ToList());
        public DataGridViewSelectedRowCollection SelectedRows =>
            new DataGridViewSelectedRowCollection(_selectedRows.Where(r => r < RowCount).OrderByDescending(r => r).Select(r => Rows[r]).ToList());
        internal bool IsRowSelected(int row) => _selectedRows.Contains(row);
        internal void SetRowSelected(int row, bool value)
        {
            if (value) { _selectedRows.Add(row); foreach (DataGridViewColumn c in Columns) _selection.Add((row, c.Index)); }
            else { _selectedRows.Remove(row); foreach (DataGridViewColumn c in Columns) _selection.Remove((row, c.Index)); }
            GridChanged("Selection");
            SelectionChanged?.Invoke(this, EventArgs.Empty);
        }
        public int[] SelectionRows => _selection.Select(s => s.Row).ToArray();
        public int[] SelectionColumns => _selection.Select(s => s.Column).ToArray();
        public int[] SelectedRowIndices => _selectedRows.ToArray();
        public void ClearSelection() { if (_selection.Count == 0 && _selectedRows.Count == 0) return; _selection.Clear(); _selectedRows.Clear(); GridChanged("Selection"); SelectionChanged?.Invoke(this, EventArgs.Empty); }
        public void SelectAll() { for (int r = 0; r < RowCount; r++) foreach (DataGridViewColumn c in Columns) _selection.Add((r, c.Index)); GridChanged("Selection"); SelectionChanged?.Invoke(this, EventArgs.Empty); }
        public DataGridViewCell CurrentCell
        {
            get => _current.HasValue && _current.Value.Row < RowCount && _current.Value.Column < Columns.Count ? this[_current.Value.Column, _current.Value.Row] : null;
            set
            {
                if (IsCurrentCellInEditMode) EndEdit();
                _current = value == null ? ((int, int)?)null : (value.RowIndex, value.ColumnIndex);
                if (value != null) { _selection.Clear(); _selectedRows.Clear(); _selection.Add((value.RowIndex, value.ColumnIndex)); }
                GridChanged("Selection");
                CurrentCellChanged?.Invoke(this, EventArgs.Empty);
            }
        }
        public Point CurrentCellAddress => _current.HasValue ? new Point(_current.Value.Column, _current.Value.Row) : new Point(-1, -1);
        public DataGridViewRow CurrentRow => _current.HasValue && _current.Value.Row < RowCount ? Rows[_current.Value.Row] : null;
        public bool IsCurrentCellInEditMode { get; private set; }
        public Control EditingControl => _editingControl;
        public bool BeginEdit(bool selectAll)
        {
            DataGridViewCell cell = CurrentCell;
            if (cell == null || cell.ReadOnly) return false;
            if (IsCurrentCellInEditMode) return true;
            var e = new DataGridViewCellCancelEventArgs(cell.ColumnIndex, cell.RowIndex);
            CellBeginEdit?.Invoke(this, e);
            if (e.Cancel) return false;
            _editingControl = new DataGridViewTextBoxEditingControl();
            _editingControl.Text = GetCellText(cell.RowIndex, cell.ColumnIndex);
            IsCurrentCellInEditMode = true;
            EditingControlShowing?.Invoke(this, new DataGridViewEditingControlShowingEventArgs(_editingControl, new DataGridViewCellStyle(DefaultCellStyle)));
            return true;
        }
        /// <summary>Commits the editing control's text: parse errors and commit errors go to OnDataError and the cell
        /// stays in edit mode (WinForms); returns false then.</summary>
        public bool EndEdit()
        {
            if (!IsCurrentCellInEditMode) return true;
            var (row, column) = _current.Value;
            string text = _editingControl?.Text ?? "";
            if (text != GetCellText(row, column) || IsNewRowIndex(row))
            {
                if (IsNewRowIndex(row) && text.Length == 0) { FinishEdit(row, column); return true; }
                object value;
                try { value = ParseCellText(column, text); }
                catch (Exception ex) { return Failed(ex, row, column, DataGridViewDataErrorContexts.Parsing | DataGridViewDataErrorContexts.Commit); }
                try
                {
                    bool added = IsNewRowIndex(row);
                    SetCellValue(row, column, value);
                    if (added) _current = (DataRowCount - 1, column);
                    row = _current.Value.Row;
                }
                catch (Exception ex) { return Failed(ex, row, column, DataGridViewDataErrorContexts.Commit); }
            }
            FinishEdit(row, column);
            return true;
        }
        bool Failed(Exception ex, int row, int column, DataGridViewDataErrorContexts context)
        {
            // WinForms (PushFormattedValue/CommitEdit): Cancel defaults to true, so the cell stays in edit mode with
            // the typed text until it is corrected or the edit is cancelled.
            var e = new DataGridViewDataErrorEventArgs(ex.InnerException ?? ex, column, row, context) { Cancel = true };
            OnDataError(true, e);
            if (e.ThrowException) throw e.Exception;
            if (e.Cancel) return false;
            // Not cancelled: the edit is abandoned and the cell keeps its value.
            FinishEdit(row, column);
            return false;
        }
        void FinishEdit(int row, int column)
        {
            IsCurrentCellInEditMode = false;
            CellEndEdit?.Invoke(this, new DataGridViewCellEventArgs(column, row));
            _editingControl = null;
            GridChanged();
        }
        public bool CancelEdit()
        {
            if (!IsCurrentCellInEditMode) return true;
            var (row, column) = _current.Value;
            FinishEdit(row, column);
            return true;
        }
        public bool CommitEdit(DataGridViewDataErrorContexts context) => EndEdit();
        public void Refresh() => GridChanged();
        public void AutoResizeColumns() { }
        public void AutoResizeColumns(DataGridViewAutoSizeColumnsMode mode) { }
        public void AutoResizeRows() { }
        public void AutoResizeColumnHeadersHeight() { }

        protected virtual void OnDataError(bool displayErrorDialogIfNoHandler, DataGridViewDataErrorEventArgs e)
        {
            if (DataError != null) DataError(this, e);
            // WinForms shows its default error dialog when nothing handles the error.
            else if (displayErrorDialogIfNoHandler) CaeGlobals.MessageBoxes.ShowError("The following exception occurred in the DataGridView:\n\n" + e.Exception);
        }
        protected virtual void OnCellMouseDown(DataGridViewCellMouseEventArgs e) => CellMouseDown?.Invoke(this, e);
        /// <summary>WinForms DataGridView key handling after KeyDown: Delete removes fully selected rows (when allowed).</summary>
        protected virtual bool ProcessDataGridViewKey(KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Delete && !IsCurrentCellInEditMode && AllowUserToDeleteRows && !_readOnly)
            {
                int[] rows = SelectedRows.Cast<DataGridViewRow>().Where(r => !r.IsNewRow).Select(r => r.Index).OrderByDescending(i => i).ToArray();
                if (rows.Length == 0) return false;
                foreach (int index in rows)
                {
                    var cancel = new DataGridViewRowCancelEventArgs(Rows[index]);
                    UserDeletingRow?.Invoke(this, cancel);
                    if (cancel.Cancel) continue;
                    RemoveRow(index);
                    UserDeletedRow?.Invoke(this, new DataGridViewRowEventArgs(new DataGridViewRow()));
                }
                _selection.Clear();
                return true;
            }
            return false;
        }
        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            if (!e.Handled) e.Handled = ProcessDataGridViewKey(e);
        }

        // Clipboard ---------------------------------------------------------------------------------------------------------------
        /// <summary>WinForms GetClipboardContent: the rows and columns that hold selected cells, tab separated
        /// (unselected cells inside are empty), with header text per ClipboardCopyMode.</summary>
        public virtual DataObject GetClipboardContent()
        {
            if (ClipboardCopyMode == DataGridViewClipboardCopyMode.Disable) throw new NotSupportedException("The ClipboardCopyMode is Disable.");
            var cells = _selection.Where(s => s.Row < RowCount && s.Column < Columns.Count && Columns[s.Column].Visible).ToList();
            if (cells.Count == 0) return null;
            int[] rows = cells.Select(s => s.Row).Distinct().OrderBy(r => r).ToArray();
            int[] columns = cells.Select(s => s.Column).Distinct().OrderBy(c => c).ToArray();
            bool fullRows = _selectedRows.Count > 0;
            bool headers = ClipboardCopyMode == DataGridViewClipboardCopyMode.EnableAlwaysIncludeHeaderText ||
                           (ClipboardCopyMode == DataGridViewClipboardCopyMode.EnableWithAutoHeaderText && fullRows &&
                            (SelectionMode == DataGridViewSelectionMode.RowHeaderSelect || SelectionMode == DataGridViewSelectionMode.FullRowSelect));
            var lines = new List<string>();
            if (headers)
                lines.Add((RowHeadersVisible ? "\t" : "") + string.Join("\t", columns.Select(c => Columns[c].HeaderText)));
            foreach (int r in rows)
                lines.Add((headers && RowHeadersVisible ? "\t" : "") + string.Join("\t", columns.Select(c => _selection.Contains((r, c)) ? GetCellText(r, c) : "")));
            string text = string.Join("\r\n", lines);
            var data = new DataObject();
            data.SetData(DataFormats.UnicodeText, text);
            data.SetData(DataFormats.Text, text);
            data.SetData(DataFormats.CommaSeparatedValue, string.Join("\r\n", lines.Select(l => l.Replace('\t', ','))));
            return data;
        }

        // Renderer input ----------------------------------------------------------------------------------------------------------
        /// <summary>User selection: the given cells (rows[i], columns[i]), the rows selected through their row
        /// header, and the current cell.</summary>
        public void SelectByUser(int[] rows, int[] columns, int currentRow, int currentColumn) => SelectByUser(rows, columns, new int[0], currentRow, currentColumn);
        public void SelectByUser(int[] rows, int[] columns, int[] headerRows, int currentRow, int currentColumn)
        {
            if (IsCurrentCellInEditMode) EndEdit();
            _selection.Clear();
            _selectedRows.Clear();
            for (int i = 0; i < rows.Length; i++) _selection.Add((rows[i], columns[i]));
            foreach (int row in headerRows) { _selectedRows.Add(row); foreach (DataGridViewColumn c in Columns) _selection.Add((row, c.Index)); }
            if (currentRow >= 0 && currentColumn >= 0 && currentRow < RowCount) { _current = (currentRow, currentColumn); CurrentCellChanged?.Invoke(this, EventArgs.Empty); }
            GridChanged("Selection");
            SelectionChanged?.Invoke(this, EventArgs.Empty);
        }
        /// <summary>User starts typing in a cell: it becomes current and enters edit mode.</summary>
        public bool BeginEditByUser(int row, int column)
        {
            if (IsCurrentCellInEditMode && _current == (row, column)) return true;
            if (IsCurrentCellInEditMode) EndEdit();
            _current = (row, column);
            if (!_selection.Contains((row, column))) { _selection.Clear(); _selectedRows.Clear(); _selection.Add((row, column)); }
            return BeginEdit(false);
        }
        /// <summary>User typing: the editing control text follows the cell editor.</summary>
        public void EditTextByUser(string text) { if (_editingControl != null) _editingControl.Text = text; }
        /// <summary>User commits a cell (Enter, Tab or leaving the cell).</summary>
        public bool CommitByUser(int row, int column, string text)
        {
            if (!BeginEditByUser(row, column)) return false;
            _editingControl.Text = text;
            return EndEdit();
        }
        public void RaiseCellMouseDown(int row, int column, MouseButtons button, int x, int y)
            => OnCellMouseDown(new DataGridViewCellMouseEventArgs(column, row, x, y, new MouseEventArgs(button, 1, x, y, 0)));
    }

    /// <summary>WinForms BindingSource over a list, an IListSource (DataTable -> DataView) or an IBindingList.</summary>
    public class BindingSource : Component, IBindingList, ITypedList, ICancelAddNew
    {
        object _dataSource;
        IList _list = new List<object>();
        readonly List<IEditableObject> _pending = new List<IEditableObject>();
        public BindingSource() { }
        public BindingSource(object dataSource, string dataMember) { DataMember = dataMember; DataSource = dataSource; }
        public string DataMember { get; set; } = "";
        public object DataSource
        {
            get => _dataSource;
            set
            {
                if (_list is IBindingList old) old.ListChanged -= Inner_ListChanged;
                _dataSource = value;
                _list = value is IListSource source ? source.GetList() : value as IList ?? (value == null ? new List<object>() : new List<object> { value });
                if (_list is IBindingList inner) inner.ListChanged += Inner_ListChanged;
                OnListChanged(new ListChangedEventArgs(ListChangedType.Reset, -1));
            }
        }
        public IList List => _list;
        public event ListChangedEventHandler ListChanged;
        public event AddingNewEventHandler AddingNew;
        public event EventHandler CurrentChanged, PositionChanged;
        public bool RaiseListChangedEvents { get; set; } = true;
        public int Position { get; set; }
        public object Current => Position >= 0 && Position < Count ? _list[Position] : null;
        void Inner_ListChanged(object sender, ListChangedEventArgs e) => OnListChanged(e);
        protected virtual void OnListChanged(ListChangedEventArgs e) { if (RaiseListChangedEvents) ListChanged?.Invoke(this, e); }
        internal void RaiseItemChanged(int index) { if (!(_list is IBindingList)) OnListChanged(new ListChangedEventArgs(ListChangedType.ItemChanged, index)); }
        public void ResetBindings(bool metadataChanged) => OnListChanged(new ListChangedEventArgs(metadataChanged ? ListChangedType.PropertyDescriptorChanged : ListChangedType.Reset, -1));
        public void ResetItem(int itemIndex) => OnListChanged(new ListChangedEventArgs(ListChangedType.ItemChanged, itemIndex));
        public bool AllowNew
        {
            get
            {
                if (_list is IBindingList bl) return bl.AllowNew;
                if (_list.IsFixedSize || _list.IsReadOnly) return false;
                Type type = GetListItemType(_list);
                return type != null && (type.IsValueType || type.GetConstructor(Type.EmptyTypes) != null);
            }
            set { }
        }
        public object AddNew()
        {
            var e = new AddingNewEventArgs();
            AddingNew?.Invoke(this, e);
            object item = e.NewObject;
            if (item != null) _list.Add(item);
            else if (_list is IBindingList bl) item = bl.AddNew();
            else { item = Activator.CreateInstance(GetListItemType(_list)); _list.Add(item); }
            if (item is IEditableObject editable) _pending.Add(editable);
            if (!(_list is IBindingList)) OnListChanged(new ListChangedEventArgs(ListChangedType.ItemAdded, _list.IndexOf(item)));
            Position = _list.IndexOf(item);
            return item;
        }
        public void EndEdit() { foreach (var item in _pending) item.EndEdit(); _pending.Clear(); }
        public void CancelEdit() { foreach (var item in _pending) item.CancelEdit(); _pending.Clear(); }
        void ICancelAddNew.CancelNew(int itemIndex) { }
        void ICancelAddNew.EndNew(int itemIndex) => EndEdit();

        internal static Type GetListItemType(IList list)
        {
            if (list is BindingSource source) return GetListItemType(source._list);
            foreach (Type i in list.GetType().GetInterfaces())
                if (i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IList<>)) return i.GetGenericArguments()[0];
            if (list.GetType().IsArray) return list.GetType().GetElementType();
            return list.Count > 0 ? list[0]?.GetType() : typeof(object);
        }
        internal static PropertyDescriptorCollection GetListItemProperties(IList list)
        {
            if (list is ITypedList typed) return typed.GetItemProperties(null);
            return TypeDescriptor.GetProperties(GetListItemType(list));
        }
        public PropertyDescriptorCollection GetItemProperties(PropertyDescriptor[] listAccessors) =>
            _list is ITypedList typed ? typed.GetItemProperties(listAccessors) : TypeDescriptor.GetProperties(GetListItemType(_list));
        public string GetListName(PropertyDescriptor[] listAccessors) => "";

        // IList
        public int Count => _list.Count;
        public object this[int index] { get => _list[index]; set { _list[index] = value; RaiseItemChanged(index); } }
        public int Add(object value) { int index = _list.Add(value); if (!(_list is IBindingList)) OnListChanged(new ListChangedEventArgs(ListChangedType.ItemAdded, index)); return index; }
        public void Clear() { _list.Clear(); if (!(_list is IBindingList)) OnListChanged(new ListChangedEventArgs(ListChangedType.Reset, -1)); }
        public bool Contains(object value) => _list.Contains(value);
        public int IndexOf(object value) => _list.IndexOf(value);
        public void Insert(int index, object value) { _list.Insert(index, value); if (!(_list is IBindingList)) OnListChanged(new ListChangedEventArgs(ListChangedType.ItemAdded, index)); }
        public void Remove(object value) { int index = _list.IndexOf(value); if (index >= 0) RemoveAt(index); }
        public void RemoveAt(int index) { _list.RemoveAt(index); if (!(_list is IBindingList)) OnListChanged(new ListChangedEventArgs(ListChangedType.ItemDeleted, index)); }
        public bool IsFixedSize => _list.IsFixedSize;
        public bool IsReadOnly => _list.IsReadOnly;
        public bool IsSynchronized => false;
        public object SyncRoot => this;
        public void CopyTo(Array array, int index) => _list.CopyTo(array, index);
        public IEnumerator GetEnumerator() => _list.GetEnumerator();
        // IBindingList
        public bool AllowEdit => true;
        public bool AllowRemove => !_list.IsFixedSize && !_list.IsReadOnly;
        public bool SupportsChangeNotification => true;
        public bool SupportsSearching => false;
        public bool SupportsSorting => false;
        public bool IsSorted => false;
        public PropertyDescriptor SortProperty => null;
        public ListSortDirection SortDirection => ListSortDirection.Ascending;
        public void AddIndex(PropertyDescriptor property) { }
        public void ApplySort(PropertyDescriptor property, ListSortDirection direction) => throw new NotSupportedException();
        public int Find(PropertyDescriptor property, object key) => throw new NotSupportedException();
        public void RemoveIndex(PropertyDescriptor property) { }
        public void RemoveSort() { }
        protected override void Dispose(bool disposing) { if (disposing && _list is IBindingList inner) inner.ListChanged -= Inner_ListChanged; base.Dispose(disposing); }
    }

    // Clipboard data objects ------------------------------------------------------------------------------------------------------
    public static class DataFormats
    {
        public const string Text = "Text", UnicodeText = "UnicodeText", CommaSeparatedValue = "Csv", Html = "HTML Format", Rtf = "Rich Text Format", FileDrop = "FileDrop";
    }
    public interface IDataObject
    {
        object GetData(string format);
        object GetData(Type format);
        bool GetDataPresent(string format);
        bool GetDataPresent(Type format);
        string[] GetFormats();
        void SetData(string format, object data);
        void SetData(object data);
    }
    public class DataObject : IDataObject
    {
        readonly Dictionary<string, object> data = new Dictionary<string, object>();
        public DataObject() { }
        public DataObject(object data) { SetData(data); }
        public DataObject(string format, object data) { SetData(format, data); }
        public object GetData(string format) => data.TryGetValue(format, out object value) ? value : null;
        public object GetData(Type format) => GetData(format.FullName);
        public bool GetDataPresent(string format) => data.ContainsKey(format);
        public bool GetDataPresent(Type format) => data.ContainsKey(format.FullName);
        public string[] GetFormats() => data.Keys.ToArray();
        public void SetData(string format, object value) => data[format] = value;
        public void SetData(object value) { if (value is string s) { SetData(DataFormats.UnicodeText, s); SetData(DataFormats.Text, s); } else if (value != null) SetData(value.GetType().FullName, value); }
        public bool ContainsText() => GetDataPresent(DataFormats.UnicodeText) || GetDataPresent(DataFormats.Text);
        public string GetText() => (GetData(DataFormats.UnicodeText) ?? GetData(DataFormats.Text)) as string ?? "";
        public void SetText(string text) => SetData((object)text);
    }
}
