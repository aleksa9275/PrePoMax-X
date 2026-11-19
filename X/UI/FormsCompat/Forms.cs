// Headless Form, ListView, PropertyGrid, TabControl and ToolStrip models (see Controls.cs).
using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.Globalization;
using System.Linq;

namespace System.Windows.Forms
{
    public class Form : ContainerControl
    {
        static readonly List<Form> openForms = new List<Form>();
        Size _clientSize;
        Form _owner;
        bool _closing;

        public static IReadOnlyList<Form> OpenForms => openForms;
        public Form() { SetVisibleCore(false); }
        public override Size Size { get => base.Size; set { _clientSize = new Size(Math.Max(0, value.Width - FrameWidth), Math.Max(0, value.Height - FrameHeight)); SetSizeCore(value); } }
        protected override Size ClientSizeCore { get => _clientSize; set { _clientSize = value; SetSizeCore(new Size(value.Width + FrameWidth, value.Height + FrameHeight)); } }
        // WinForms sizable window frame at 96 DPI (Windows 10): 16 px horizontally, 39 px vertically.
        public const int FrameWidth = 16, FrameHeight = 39;
        public FormStartPosition StartPosition { get; set; } = FormStartPosition.WindowsDefaultLocation;
        public FormBorderStyle FormBorderStyle { get; set; } = FormBorderStyle.Sizable;
        public bool MaximizeBox { get; set; } = true;
        public bool MinimizeBox { get; set; } = true;
        public bool ControlBox { get; set; } = true;
        public bool ShowIcon { get; set; } = true;
        public bool ShowInTaskbar { get; set; } = true;
        public bool TopMost { get; set; }
        public bool KeyPreview { get; set; }
        public bool HelpButton { get; set; }
        public double Opacity { get; set; } = 1;
        public Icon Icon { get; set; }
        public SizeGripStyle SizeGripStyle { get; set; }
        public FormWindowState WindowState { get; set; }
        public IButtonControl AcceptButton { get; set; }
        public IButtonControl CancelButton { get; set; }
        DialogResult _dialogResult;
        /// <summary>WinForms: setting a result on a modal form closes it.</summary>
        public DialogResult DialogResult { get => _dialogResult; set { _dialogResult = value; if (Modal && value != DialogResult.None && Visible) CloseCore(CloseReason.None); } }
        public bool Modal { get; private set; }
        public bool IsMdiContainer { get; set; }
        public Form Owner { get => _owner; set { _owner = value; Notify(nameof(Owner)); } }
        public MenuStrip MainMenuStrip { get; set; }
        public static Form ActiveForm { get; private set; }

        protected virtual bool ShowWithoutActivation => false;
        public Color TransparencyKey { get; set; } = Color.Empty;

        public event FormClosingEventHandler FormClosing;
        public event FormClosedEventHandler FormClosed;
        public event EventHandler Load, Shown, Activated, Deactivate, ResizeBegin, ResizeEnd;

        public void Show(IWin32Window owner) { if ((owner as Control)?.FindForm() is Form f && f != this) Owner = f; Show(); }
        /// <summary>Set by a run without a renderer: showing a form creates its controls, which raises the Load event of
        /// its user controls before the form's own Load (WinForms CreateControl); a renderer raises them itself.</summary>
        public static bool CreateControlsOnShow;
        static void CreateChildControls(Control control)
        {
            foreach (Control child in control.Controls.Cast<Control>().ToArray()) CreateControlTree(child);
        }
        internal static void CreateControlTree(Control control)
        {
            CreateChildControls(control);
            if (control is UserControl userControl) userControl.RaiseLoad();
        }
        /// <summary>The form's controls were created (a run without a renderer, after the first Show).</summary>
        internal bool ControlsCreated { get; private set; }
        public new void Show()
        {
            bool first = !openForms.Contains(this);
            if (first && CreateControlsOnShow) { CreateChildControls(this); ControlsCreated = true; }
            if (first) { openForms.Add(this); OnLoad(EventArgs.Empty); }
            Visible = true;
            // WinForms raises Shown through a posted message once the window is displayed; with a message loop it is
            // posted here too (the loop shows the window first), without one it is raised at once
            if (first)
            {
                if (UiThreadContext != null) UiThreadContext.Post(_ => OnShown(EventArgs.Empty), null);
                else OnShown(EventArgs.Empty);
            }
            Activate();
        }
        /// <summary>Modal display needs the renderer's nested event loop (FormHost.ShowDialog).</summary>
        public static Func<Form, DialogResult> ShowDialogHandler;
        public DialogResult ShowDialog() => ShowDialog(null);
        public DialogResult ShowDialog(IWin32Window owner)
        {
            if (owner is Form f && f != this) Owner = f;
            if (ShowDialogHandler == null) throw new InvalidOperationException("No form renderer is attached for modal forms.");
            ToolkitSynchronizationContext ui = ToolkitSynchronizationContext.Installed;
            if (ui != null && !ui.IsUiThread)
            {
                // Shown from another thread (the original splash screen runs on a thread of its own): the window is
                // the user-interface thread's, whose event loop keeps running; this thread waits for the form to
                // close, as in its own modal loop
                _dialogResult = DialogResult.None;
                ui.Send(_ => { Modal = true; Show(); }, null);
                while (Visible) System.Threading.Thread.Sleep(20);
                ui.Send(_ => Modal = false, null);
                return _dialogResult == DialogResult.None ? DialogResult.Cancel : _dialogResult;
            }
            Modal = true;
            _dialogResult = DialogResult.None;
            try
            {
                DialogResult result = ShowDialogHandler(this);
                if (Visible) { Visible = false; }
                return result == DialogResult.None ? DialogResult.Cancel : result;
            }
            finally { Modal = false; }
        }
        public void Activate() { ActiveForm = this; Notify("Activate"); OnActivated(EventArgs.Empty); }
        public void Close() => CloseCore(CloseReason.UserClosing);
        /// <summary>The size and location of the window in its normal state (the renderer reports them while the
        /// window is maximized or minimized).</summary>
        public Rectangle RestoreBounds { get => _restoreBounds ?? Bounds; set => _restoreBounds = value; }
        Rectangle? _restoreBounds;
        internal void CloseForExit() => CloseCore(CloseReason.ApplicationExitCall);
        /// <summary>Renderer input: the window close button.</summary>
        public bool CloseByUser() { CloseCore(CloseReason.UserClosing); return !Visible; }
        void CloseCore(CloseReason reason)
        {
            if (_closing) return;
            _closing = true;
            try
            {
                var e = new FormClosingEventArgs(reason, false);
                OnFormClosing(e);
                if (e.Cancel) return;
                Visible = false;
                openForms.Remove(this);
                OnFormClosed(new FormClosedEventArgs(reason));
                if (!Modal) Dispose();
            }
            finally { _closing = false; }
        }
        internal bool ProcessCmdKeyInternal(ref Message msg, Keys keyData) => ProcessCmdKey(ref msg, keyData);
        protected virtual void OnLoad(EventArgs e) => Load?.Invoke(this, e);
        protected virtual void OnShown(EventArgs e) => Shown?.Invoke(this, e);
        protected virtual void OnActivated(EventArgs e) => Activated?.Invoke(this, e);
        protected virtual void OnDeactivate(EventArgs e) => Deactivate?.Invoke(this, e);
        protected virtual void OnFormClosing(FormClosingEventArgs e) => FormClosing?.Invoke(this, e);
        protected virtual void OnFormClosed(FormClosedEventArgs e) => FormClosed?.Invoke(this, e);
        protected virtual void OnResizeBegin(EventArgs e) => ResizeBegin?.Invoke(this, e);
        protected virtual void OnResizeEnd(EventArgs e) => ResizeEnd?.Invoke(this, e);
        public void RaiseDeactivate() => OnDeactivate(EventArgs.Empty);
        /// <summary>Renderer input: Enter/Escape reach AcceptButton/CancelButton as in WinForms.</summary>
        public bool ProcessDialogKeyInput(Keys keyData)
        {
            if (ProcessDialogKey(keyData)) return true;
            if (keyData == Keys.Enter && AcceptButton != null) { AcceptButton.PerformClick(); return true; }
            if (keyData == Keys.Escape && CancelButton != null) { CancelButton.PerformClick(); return true; }
            return false;
        }
    }
    public enum SizeGripStyle { Auto, Show, Hide }

    public class ColumnHeader : Component
    {
        public string Text { get; set; } = "ColumnHeader";
        public int Width { get; set; } = 60;
        public string Name { get; set; } = "";
        public HorizontalAlignment TextAlign { get; set; }
        public int DisplayIndex { get; set; }
        public ListView ListView { get; internal set; }
        public int Index => ListView?.Columns.IndexOf(this) ?? -1;
    }

    public class ListViewItem : ICloneable
    {
        bool _selected, _checked;
        string _text = "";
        internal ListView owner;
        public ListViewItem() { SubItems = new ListViewSubItemCollection(this); }
        public ListViewItem(string text) : this() { _text = text ?? ""; }
        public ListViewItem(string text, int imageIndex) : this(text) { ImageIndex = imageIndex; }
        public ListViewItem(string text, string imageKey) : this(text) { ImageKey = imageKey; }
        public ListViewItem(string[] items) : this(items != null && items.Length > 0 ? items[0] : "") { if (items != null) foreach (string s in items.Skip(1)) SubItems.Add(s); }
        public ListViewItem(ListViewGroup group) : this() { Group = group; }
        public string Text { get => _text; set { _text = value ?? ""; owner?.NotifyItems(); } }
        public string Name { get; set; } = "";
        public object Tag { get; set; }
        public int ImageIndex { get; set; } = -1;
        public string ImageKey { get; set; } = "";
        public string ToolTipText { get; set; } = "";
        public Color ForeColor { get; set; } = SystemColors.WindowText;
        public Color BackColor { get; set; } = SystemColors.Window;
        public Font Font { get; set; }
        public ListViewGroup Group { get; set; }
        public ListView ListView => owner;
        public int Index => owner?.Items.IndexOf(this) ?? -1;
        public int IndentCount { get; set; }
        public bool Focused { get; set; }
        public ListViewSubItemCollection SubItems { get; }
        public bool Selected
        {
            get => _selected;
            set
            {
                if (_selected == value) return;
                if (value && owner != null && !owner.MultiSelect)
                    foreach (ListViewItem other in owner.Items.Cast<ListViewItem>().Where(i => i != this && i._selected).ToArray()) other.SetSelectedCore(false);
                SetSelectedCore(value);
            }
        }
        internal void SetSelectedCore(bool value)
        {
            _selected = value;
            if (owner == null) return;
            owner.NotifyItems();
            owner.RaiseItemSelectionChanged(this, value);
        }
        public bool Checked { get => _checked; set { if (_checked == value) return; _checked = value; owner?.NotifyItems(); owner?.RaiseItemChecked(this); } }
        /// <summary>Row geometry for the original list-view sizing rules: 17 px rows (Segoe UI 9 pt, 96 DPI).</summary>
        public Rectangle Bounds => new Rectangle(0, Math.Max(0, Index) * ListView.RowHeight, owner?.Width ?? 100, ListView.RowHeight);
        public void EnsureVisible() => owner?.EnsureVisible(Index);
        public void Remove() => owner?.Items.Remove(this);
        public virtual object Clone() { var item = new ListViewItem(Text) { Tag = Tag, ImageIndex = ImageIndex, ImageKey = ImageKey, ToolTipText = ToolTipText, ForeColor = ForeColor, BackColor = BackColor }; foreach (ListViewSubItem s in SubItems.Cast<ListViewSubItem>().Skip(1)) item.SubItems.Add(s.Text); return item; }
        public class ListViewSubItem { public string Text { get; set; } = ""; public object Tag { get; set; } public string Name { get; set; } = ""; public Color ForeColor { get; set; } public Color BackColor { get; set; } public ListViewSubItem() { } public ListViewSubItem(ListViewItem owner, string text) { Text = text; } }
        public class ListViewSubItemCollection : IList
        {
            readonly ListViewItem item;
            readonly List<ListViewSubItem> extra = new List<ListViewSubItem>();
            public ListViewSubItemCollection(ListViewItem owner) { item = owner; }
            public int Count => extra.Count + 1;
            public ListViewSubItem this[int index] { get => index == 0 ? new ListViewSubItem(item, item.Text) : extra[index - 1]; set { if (index == 0) item.Text = value.Text; else extra[index - 1] = value; } }
            public ListViewSubItem Add(string text) { var s = new ListViewSubItem(item, text); extra.Add(s); item.owner?.NotifyItems(); return s; }
            public ListViewSubItem Add(ListViewSubItem s) { extra.Add(s); item.owner?.NotifyItems(); return s; }
            public void AddRange(string[] items) { foreach (string s in items) Add(s); }
            public void Clear() => extra.Clear();
            public IEnumerator GetEnumerator() { yield return this[0]; foreach (var s in extra) yield return s; }
            object IList.this[int index] { get => this[index]; set => this[index] = (ListViewSubItem)value; }
            int IList.Add(object value) { Add((ListViewSubItem)value); return Count - 1; }
            bool IList.Contains(object value) => extra.Contains(value as ListViewSubItem);
            int IList.IndexOf(object value) => extra.IndexOf(value as ListViewSubItem) + 1;
            void IList.Insert(int index, object value) => extra.Insert(index - 1, (ListViewSubItem)value);
            void IList.Remove(object value) => extra.Remove(value as ListViewSubItem);
            public void RemoveAt(int index) => extra.RemoveAt(index - 1);
            bool IList.IsFixedSize => false;
            bool IList.IsReadOnly => false;
            void ICollection.CopyTo(Array array, int index) { }
            bool ICollection.IsSynchronized => false;
            object ICollection.SyncRoot => this;
        }
    }
    public class ListViewGroup { public string Header { get; set; } public string Name { get; set; } public ListViewGroup() { } public ListViewGroup(string header) { Header = header; } public ListViewGroup(string key, string header) { Name = key; Header = header; } }

    public class ListView : Control
    {
        public const int RowHeight = 17;
        bool _raisingSuspended;
        public ListView()
        {
            Columns = new ColumnHeaderCollection(this);
            Items = new ListViewItemCollection(this);
            SelectedItems = new SelectedListViewItemCollection(this);
            SelectedIndices = new SelectedIndexCollection(this);
            CheckedItems = new CheckedListViewItemCollection(this);
        }
        public View View { get; set; } = View.LargeIcon;
        public bool FullRowSelect { get; set; }
        public bool MultiSelect { get; set; } = true;
        public bool HideSelection { get; set; } = true;
        public bool ShowGroups { get; set; } = true;
        public bool CheckBoxes { get; set; }
        public bool GridLines { get; set; }
        public bool LabelEdit { get; set; }
        public bool Scrollable { get; set; } = true;
        public bool UseCompatibleStateImageBehavior { get; set; } = true;
        public bool ShowItemToolTips { get; set; }
        public bool HotTracking { get; set; }
        public bool HoverSelection { get; set; }
        public SortOrder Sorting { get; set; }
        public IComparer ListViewItemSorter { get; set; }
        public ColumnHeaderStyle HeaderStyle { get; set; } = ColumnHeaderStyle.Clickable;
        public BorderStyle BorderStyle { get; set; } = BorderStyle.Fixed3D;
        public ImageList SmallImageList { get; set; }
        public ImageList LargeImageList { get; set; }
        public ImageList StateImageList { get; set; }
        public List<ListViewGroup> Groups { get; } = new List<ListViewGroup>();
        public ColumnHeaderCollection Columns { get; }
        public virtual ListViewItemCollection Items { get; }
        public SelectedListViewItemCollection SelectedItems { get; }
        public SelectedIndexCollection SelectedIndices { get; }
        public CheckedListViewItemCollection CheckedItems { get; }
        public ListViewItem FocusedItem { get; set; }
        public ListViewItem TopItem { get; set; }
        public int VisibleRowsCount => Math.Max(1, Height / RowHeight);

        public event EventHandler SelectedIndexChanged;
        public event ListViewItemSelectionChangedEventHandler ItemSelectionChanged;
        public event ItemCheckedEventHandler ItemChecked;
        public event ColumnClickEventHandler ColumnClick;
        public event EventHandler ItemActivate;
        public event ListViewItemMouseHoverEventHandler ItemMouseHover;

        internal void NotifyItems() => Notify("Items");
        internal void RaiseItemSelectionChanged(ListViewItem item, bool selected)
        {
            if (_raisingSuspended) return;
            OnItemSelectionChanged(new ListViewItemSelectionChangedEventArgs(item, item.Index, selected));
            OnSelectedIndexChanged(EventArgs.Empty);
        }
        internal void RaiseItemChecked(ListViewItem item) => ItemChecked?.Invoke(this, new ItemCheckedEventArgs(item));
        protected virtual void OnSelectedIndexChanged(EventArgs e) => SelectedIndexChanged?.Invoke(this, e);
        protected virtual void OnItemSelectionChanged(ListViewItemSelectionChangedEventArgs e) => ItemSelectionChanged?.Invoke(this, e);
        public void BeginUpdate() { }
        public void EndUpdate() => Notify("Items");
        public void Clear() { Items.Clear(); Columns.Clear(); }
        public void Sort() => Notify("Items");
        public void EnsureVisible(int index) => Notify("EnsureVisible");
        public ListViewItem FindItemWithText(string text) => FindItemWithText(text, true, 0, true);
        public ListViewItem FindItemWithText(string text, bool includeSubItemsInSearch, int startIndex) => FindItemWithText(text, includeSubItemsInSearch, startIndex, true);
        public ListViewItem FindItemWithText(string text, bool includeSubItemsInSearch, int startIndex, bool isPrefixSearch)
        {
            // WinForms: case-insensitive prefix match on the item text.
            for (int i = Math.Max(0, startIndex); i < Items.Count; i++)
            {
                string t = Items[i].Text ?? "";
                if (isPrefixSearch ? t.StartsWith(text ?? "", StringComparison.OrdinalIgnoreCase) : string.Equals(t, text, StringComparison.OrdinalIgnoreCase)) return Items[i];
            }
            return null;
        }
        public ListViewItem GetItemAt(int x, int y) { int i = y / RowHeight; return i >= 0 && i < Items.Count ? Items[i] : null; }
        public ListViewHitTestInfo HitTest(Point p) => new ListViewHitTestInfo(GetItemAt(p.X, p.Y), ClientRectangle.Contains(p) ? (GetItemAt(p.X, p.Y) != null ? ListViewHitTestLocations.Label : ListViewHitTestLocations.None) : ListViewHitTestLocations.BelowClientArea);
        public void AutoResizeColumn(int columnIndex, ColumnHeaderAutoResizeStyle style) => Notify("Columns");
        public void AutoResizeColumns(ColumnHeaderAutoResizeStyle style) => Notify("Columns");
        public ListViewHitTestInfo HitTest(int x, int y) => HitTest(new Point(x, y));
        /// <summary>Renderer input: a user click selects exactly the given rows (WinForms raises one change per item).</summary>
        public void SelectByUser(int[] indices)
        {
            var set = new HashSet<int>(indices ?? new int[0]);
            foreach (ListViewItem item in Items.Cast<ListViewItem>().ToArray()) if (item.Selected && !set.Contains(item.Index)) item.Selected = false;
            foreach (int index in set.OrderBy(i => i)) if (index >= 0 && index < Items.Count) Items[index].Selected = true;
        }

        public class ColumnHeaderCollection : IList
        {
            readonly ListView owner;
            readonly List<ColumnHeader> items = new List<ColumnHeader>();
            public ColumnHeaderCollection(ListView owner) { this.owner = owner; }
            public int Count => items.Count;
            public ColumnHeader this[int index] => items[index];
            public ColumnHeader Add(string text) => Add(text, 60);
            public ColumnHeader Add(string text, int width) { var c = new ColumnHeader { Text = text, Width = width }; Add(c); return c; }
            public ColumnHeader Add(string key, string text, int width) { var c = new ColumnHeader { Name = key, Text = text, Width = width }; Add(c); return c; }
            public int Add(ColumnHeader c) { c.ListView = owner; items.Add(c); owner.Notify("Columns"); return items.Count - 1; }
            public void AddRange(ColumnHeader[] values) { foreach (var c in values) Add(c); }
            public void Clear() { items.Clear(); owner.Notify("Columns"); }
            public int IndexOf(ColumnHeader c) => items.IndexOf(c);
            public void Remove(ColumnHeader c) { items.Remove(c); owner.Notify("Columns"); }
            public void RemoveAt(int index) { items.RemoveAt(index); owner.Notify("Columns"); }
            public IEnumerator GetEnumerator() => items.GetEnumerator();
            object IList.this[int index] { get => items[index]; set => throw new NotSupportedException(); }
            int IList.Add(object value) => Add((ColumnHeader)value);
            bool IList.Contains(object value) => items.Contains(value as ColumnHeader);
            int IList.IndexOf(object value) => items.IndexOf(value as ColumnHeader);
            void IList.Insert(int index, object value) => items.Insert(index, (ColumnHeader)value);
            void IList.Remove(object value) => Remove((ColumnHeader)value);
            bool IList.IsFixedSize => false;
            bool IList.IsReadOnly => false;
            void ICollection.CopyTo(Array array, int index) => ((ICollection)items).CopyTo(array, index);
            bool ICollection.IsSynchronized => false;
            object ICollection.SyncRoot => this;
        }

        internal readonly List<ListViewItem> itemList = new List<ListViewItem>();
        public class ListViewItemCollection : IList
        {
            readonly ListView owner;
            List<ListViewItem> items => owner.itemList;
            // Like WinForms, every collection created for an owner is a view of the owner's one item list.
            public ListViewItemCollection(ListView owner) { this.owner = owner; }
            public int Count => items.Count;
            public virtual ListViewItem this[int index] { get => items[index]; set { items[index] = value; value.owner = owner; owner.NotifyItems(); } }
            public virtual ListViewItem this[string key] => items.FirstOrDefault(i => i.Name == key);
            public virtual ListViewItem Add(ListViewItem item) { Attach(item); items.Add(item); owner.NotifyItems(); if (item.Selected) owner.RaiseItemSelectionChanged(item, true); return item; }
            public virtual ListViewItem Add(string text) => Add(new ListViewItem(text));
            public virtual ListViewItem Add(string text, int imageIndex) => Add(new ListViewItem(text, imageIndex));
            public virtual ListViewItem Add(string text, string imageKey) => Add(new ListViewItem(text, imageKey));
            public virtual ListViewItem Add(string key, string text, string imageKey) => Add(new ListViewItem(text, imageKey) { Name = key });
            public virtual ListViewItem Add(string key, string text, int imageIndex) => Add(new ListViewItem(text, imageIndex) { Name = key });
            public void AddRange(ListViewItem[] values) { foreach (var item in values) Add(item); }
            public virtual ListViewItem Insert(int index, ListViewItem item) { Attach(item); items.Insert(index, item); owner.NotifyItems(); return item; }
            public virtual ListViewItem Insert(int index, string text) => Insert(index, new ListViewItem(text));
            void Attach(ListViewItem item)
            {
                if (item.owner != null && item.owner != owner) throw new ArgumentException("Cannot add or insert the item '" + item.Text + "' in more than one place.");
                item.owner = owner;
                if (item.Selected && !owner.MultiSelect) foreach (var other in items.Where(i => i.Selected)) other.SetSelectedCore(false);
            }
            public virtual void Clear()
            {
                bool hadSelection = items.Any(i => i.Selected);
                foreach (var item in items) item.owner = null;
                items.Clear();
                owner.NotifyItems();
                if (hadSelection) owner.OnSelectedIndexChanged(EventArgs.Empty);
            }
            public virtual void Remove(ListViewItem item)
            {
                int index = items.IndexOf(item);
                if (index >= 0) RemoveAt(index);
            }
            public virtual void RemoveAt(int index)
            {
                var item = items[index];
                bool selected = item.Selected;
                items.RemoveAt(index);
                item.owner = null;
                owner.NotifyItems();
                if (selected) owner.OnSelectedIndexChanged(EventArgs.Empty);
            }
            public virtual void RemoveByKey(string key) { var item = this[key]; if (item != null) Remove(item); }
            public bool Contains(ListViewItem item) => items.Contains(item);
            public bool ContainsKey(string key) => items.Any(i => i.Name == key);
            public int IndexOf(ListViewItem item) => items.IndexOf(item);
            public int IndexOfKey(string key) => items.FindIndex(i => i.Name == key);
            public ListViewItem[] Find(string key, bool searchAllSubItems) => items.Where(i => i.Name == key).ToArray();
            public void CopyTo(Array array, int index) => ((ICollection)items).CopyTo(array, index);
            public IEnumerator GetEnumerator() => items.GetEnumerator();
            object IList.this[int index] { get => items[index]; set => this[index] = (ListViewItem)value; }
            int IList.Add(object value) { Add((ListViewItem)value); return items.Count - 1; }
            bool IList.Contains(object value) => items.Contains(value as ListViewItem);
            int IList.IndexOf(object value) => items.IndexOf(value as ListViewItem);
            void IList.Insert(int index, object value) => Insert(index, (ListViewItem)value);
            void IList.Remove(object value) => Remove((ListViewItem)value);
            bool IList.IsFixedSize => false;
            bool IList.IsReadOnly => false;
            bool ICollection.IsSynchronized => false;
            object ICollection.SyncRoot => this;
        }
        public class SelectedListViewItemCollection : IList
        {
            readonly ListView owner;
            public SelectedListViewItemCollection(ListView owner) { this.owner = owner; }
            List<ListViewItem> Selected => owner.Items.Cast<ListViewItem>().Where(i => i.Selected).ToList();
            public int Count => Selected.Count;
            public ListViewItem this[int index] => Selected[index];
            public bool Contains(ListViewItem item) => Selected.Contains(item);
            public int IndexOf(ListViewItem item) => Selected.IndexOf(item);
            public void Clear() { foreach (var item in Selected) item.Selected = false; }
            public IEnumerator GetEnumerator() => Selected.GetEnumerator();
            public void CopyTo(Array array, int index) => ((ICollection)Selected).CopyTo(array, index);
            object IList.this[int index] { get => this[index]; set => throw new NotSupportedException(); }
            int IList.Add(object value) => throw new NotSupportedException();
            bool IList.Contains(object value) => Contains(value as ListViewItem);
            int IList.IndexOf(object value) => IndexOf(value as ListViewItem);
            void IList.Insert(int index, object value) => throw new NotSupportedException();
            void IList.Remove(object value) => throw new NotSupportedException();
            void IList.RemoveAt(int index) => throw new NotSupportedException();
            bool IList.IsFixedSize => true;
            bool IList.IsReadOnly => true;
            bool ICollection.IsSynchronized => false;
            object ICollection.SyncRoot => this;
        }
        public class SelectedIndexCollection : IEnumerable
        {
            readonly ListView owner;
            public SelectedIndexCollection(ListView owner) { this.owner = owner; }
            List<int> Indices => owner.Items.Cast<ListViewItem>().Where(i => i.Selected).Select(i => i.Index).ToList();
            public int Count => Indices.Count;
            public int this[int index] => Indices[index];
            public bool Contains(int index) => Indices.Contains(index);
            public int Add(int index) { owner.Items[index].Selected = true; return Count; }
            public void Clear() => owner.SelectedItems.Clear();
            public IEnumerator GetEnumerator() => Indices.GetEnumerator();
        }
        public class CheckedListViewItemCollection : IEnumerable
        {
            readonly ListView owner;
            public CheckedListViewItemCollection(ListView owner) { this.owner = owner; }
            List<ListViewItem> Checked => owner.Items.Cast<ListViewItem>().Where(i => i.Checked).ToList();
            public int Count => Checked.Count;
            public ListViewItem this[int index] => Checked[index];
            public IEnumerator GetEnumerator() => Checked.GetEnumerator();
        }
    }
    public enum SortOrder { None, Ascending, Descending }
    public class ListViewHitTestInfo { public ListViewItem Item { get; } public ListViewHitTestLocations Location { get; } public ListViewHitTestInfo(ListViewItem item, ListViewHitTestLocations location = ListViewHitTestLocations.None) { Item = item; Location = location; } }
    [Flags] public enum ListViewHitTestLocations { None = 1, AboveClientArea = 256, BelowClientArea = 16, LeftOfClientArea = 64, RightOfClientArea = 32, Image = 2, StateImage = 512, Label = 4 }
    public enum ColumnHeaderAutoResizeStyle { None, HeaderSize, ColumnContent }
    public class ItemCheckedEventArgs : EventArgs { public ListViewItem Item { get; } public ItemCheckedEventArgs(ListViewItem item) { Item = item; } }
    public delegate void ItemCheckedEventHandler(object sender, ItemCheckedEventArgs e);
    public class ColumnClickEventArgs : EventArgs { public int Column { get; } public ColumnClickEventArgs(int column) { Column = column; } }
    public delegate void ColumnClickEventHandler(object sender, ColumnClickEventArgs e);
    public class ListViewItemMouseHoverEventArgs : EventArgs { public ListViewItem Item { get; } public ListViewItemMouseHoverEventArgs(ListViewItem item) { Item = item; } }
    public delegate void ListViewItemMouseHoverEventHandler(object sender, ListViewItemMouseHoverEventArgs e);

    public class TabPage : Panel
    {
        public TabPage() { }
        public TabPage(string text) { Text = text; }
        public bool UseVisualStyleBackColor { get; set; }
        public string ToolTipText { get; set; } = "";
        public int ImageIndex { get; set; } = -1;
        public string ImageKey { get; set; } = "";
    }
    public class TabControl : Control
    {
        int _selectedIndex = -1;
        public TabControl() { TabPages = new TabPageCollection(this); }
        public TabPageCollection TabPages { get; }
        readonly List<TabPage> _allPages = new List<TabPage>();
        /// <summary>Renderer: every page ever added (forms remove and re-add their pages per item type).</summary>
        public TabPage[] AllPages => _allPages.ToArray();
        internal void Remember(TabPage page) { if (!_allPages.Contains(page)) _allPages.Add(page); }
        public TabAlignment Alignment { get; set; }
        public TabSizeMode SizeMode { get; set; }
        public Size ItemSize { get; set; }
        public Point Padding2 { get; set; }
        public bool Multiline { get; set; }
        public bool ShowToolTips { get; set; }
        public ImageList ImageList { get; set; }
        public TabDrawMode DrawMode { get; set; }
        public int TabCount => TabPages.Count;
        public int SelectedIndex
        {
            get => _selectedIndex;
            set
            {
                if (value < -1 || value >= TabPages.Count) return;
                if (_selectedIndex == value) return;
                // WinForms order: Deselecting (the current page), Selecting (the new page), then Deselected/Selected
                if (_selectedIndex >= 0 && _selectedIndex < TabPages.Count)
                {
                    var d = new TabControlCancelEventArgs(TabPages[_selectedIndex], _selectedIndex, false);
                    Deselecting?.Invoke(this, d);
                    if (d.Cancel) return;
                }
                var e = new TabControlCancelEventArgs(value >= 0 ? TabPages[value] : null, value, false);
                Selecting?.Invoke(this, e);
                if (e.Cancel) return;
                int previous = _selectedIndex;
                _selectedIndex = value;
                if (previous >= 0 && previous < TabPages.Count) Deselected?.Invoke(this, new TabControlEventArgs(TabPages[previous], previous));
                Notify(nameof(SelectedIndex));
                SelectedIndexChanged?.Invoke(this, EventArgs.Empty);
                Selected?.Invoke(this, new TabControlEventArgs(SelectedTab, value));
            }
        }
        public TabPage SelectedTab { get => _selectedIndex >= 0 && _selectedIndex < TabPages.Count ? TabPages[_selectedIndex] : null; set => SelectedIndex = TabPages.IndexOf(value); }
        public event EventHandler SelectedIndexChanged;
        public event TabControlEventHandler Selected;
        public event TabControlCancelEventHandler Selecting;
        public event TabControlCancelEventHandler Deselecting;
        public event TabControlEventHandler Deselected;
        public event DrawItemEventHandler DrawItem;
        public Rectangle GetTabRect(int index) => new Rectangle(index * 80, 0, 80, 24);
        /// <summary>WinForms page area at 96 DPI with Segoe UI 9 pt tabs: 4 px border, 24 px tab row.</summary>
        public new Rectangle DisplayRectangle => new Rectangle(4, 24, Math.Max(0, Width - 8), Math.Max(0, Height - 28));
        protected override void LayoutChildren() { foreach (TabPage page in TabPages) page.Bounds = DisplayRectangle; }
        // WinForms TabControl.ControlCollection: a TabPage added or removed through Controls (designer code) is
        // added to or removed from TabPages.
        protected override void OnControlAdded(ControlEventArgs e)
        {
            if (e.Control is TabPage page && !TabPages.Contains(page)) TabPages.AddFromControls(page);
            base.OnControlAdded(e);
        }
        protected override void OnControlRemoved(ControlEventArgs e)
        {
            if (e.Control is TabPage page && TabPages.Contains(page)) TabPages.RemoveFromControls(page);
            base.OnControlRemoved(e);
        }
        public class TabPageCollection : IList
        {
            readonly TabControl owner;
            readonly List<TabPage> pages = new List<TabPage>();
            public TabPageCollection(TabControl owner) { this.owner = owner; }
            public int Count => pages.Count;
            public TabPage this[int index] => pages[index];
            public TabPage this[string key] => pages.FirstOrDefault(p => p.Name == key);
            public void Add(TabPage page)
            {
                owner.Remember(page);
                pages.Add(page);
                owner.Controls.Add(page);
                if (owner._selectedIndex < 0) owner.SelectedIndex = 0;
                owner.Notify("TabPages");
            }
            public void Add(string text) => Add(new TabPage(text));
            internal void AddFromControls(TabPage page)
            {
                owner.Remember(page);
                pages.Add(page);
                if (owner._selectedIndex < 0) owner.SelectedIndex = 0;
                owner.Notify("TabPages");
            }
            internal void RemoveFromControls(TabPage page) { pages.Remove(page); FixSelection(); }
            public void AddRange(TabPage[] values) { foreach (var p in values) Add(p); }
            public void Insert(int index, TabPage page) { owner.Remember(page); pages.Insert(index, page); owner.Controls.Add(page); owner.Notify("TabPages"); }
            public void Remove(TabPage page)
            {
                int index = pages.IndexOf(page);
                if (index < 0) return;
                pages.RemoveAt(index);
                owner.Controls.Remove(page);
                FixSelection();
            }
            public void RemoveAt(int index) => Remove(pages[index]);
            public void Clear() { foreach (var p in pages.ToArray()) owner.Controls.Remove(p); pages.Clear(); FixSelection(); }
            void FixSelection()
            {
                if (owner._selectedIndex >= pages.Count) { owner._selectedIndex = -1; if (pages.Count > 0) owner.SelectedIndex = pages.Count - 1; }
                else if (pages.Count == 0) owner._selectedIndex = -1;
                owner.Notify("TabPages");
            }
            public bool Contains(TabPage page) => pages.Contains(page);
            public bool ContainsKey(string key) => pages.Any(p => p.Name == key);
            public int IndexOf(TabPage page) => pages.IndexOf(page);
            public IEnumerator GetEnumerator() => pages.GetEnumerator();
            object IList.this[int index] { get => pages[index]; set => throw new NotSupportedException(); }
            int IList.Add(object value) { Add((TabPage)value); return pages.Count - 1; }
            bool IList.Contains(object value) => pages.Contains(value as TabPage);
            int IList.IndexOf(object value) => pages.IndexOf(value as TabPage);
            void IList.Insert(int index, object value) => Insert(index, (TabPage)value);
            void IList.Remove(object value) => Remove((TabPage)value);
            bool IList.IsFixedSize => false;
            bool IList.IsReadOnly => false;
            void ICollection.CopyTo(Array array, int index) => ((ICollection)pages).CopyTo(array, index);
            bool ICollection.IsSynchronized => false;
            object ICollection.SyncRoot => this;
        }
    }
    public enum TabDrawMode { Normal, OwnerDrawFixed }
    public class TabControlCancelEventArgs : CancelEventArgs { public TabPage TabPage { get; } public int TabPageIndex { get; } public TabControlCancelEventArgs(TabPage page, int index, bool cancel) : base(cancel) { TabPage = page; TabPageIndex = index; } }
    public delegate void TabControlCancelEventHandler(object sender, TabControlCancelEventArgs e);
    public class DrawItemEventArgs : EventArgs { public Graphics Graphics { get; } public int Index { get; } public Rectangle Bounds { get; } public DrawItemEventArgs(Graphics g, Font font, Rectangle bounds, int index, DrawItemState state) { Graphics = g; Bounds = bounds; Index = index; } }
    public enum DrawItemState { None = 0, Selected = 1 }
    public delegate void DrawItemEventHandler(object sender, DrawItemEventArgs e);

    // Tool strips: menu state only; the renderer shows context menus on request.
    public class ToolStripItem : Component
    {
        string _text = "";
        bool _enabled = true, _visible = true;
        public ToolStripItem() { }
        public ToolStripItem(string text) { _text = text ?? ""; }
        public string Name { get; set; } = "";
        public virtual string Text { get => _text; set { _text = value ?? ""; NotifyItem(); } }
        public string ToolTipText { get; set; } = "";
        public object Tag { get; set; }
        Image _image;
        public Image Image { get => _image; set { _image = value; NotifyItem(); } }
        /// <summary>The tool strip the item is shown on changed: the renderer updates it (a drop-down item's strip is
        /// the strip of its top item; open drop-downs are rebuilt when they open).</summary>
        protected void NotifyItem()
        {
            ToolStripItem item = this;
            ToolStrip strip = Owner;
            while (strip == null && item.OwnerItem != null) { item = item.OwnerItem; strip = item.Owner; }
            if (strip != null) ControlNotifications.Raise(strip, "Items");
        }
        public ToolStripItemDisplayStyle DisplayStyle { get; set; } = ToolStripItemDisplayStyle.ImageAndText;
        public Color ImageTransparentColor { get; set; }
        public bool Enabled { get => _enabled; set { if (_enabled == value) return; _enabled = value; EnabledChanged?.Invoke(this, EventArgs.Empty); NotifyItem(); } }
        public bool Visible { get => _visible; set { if (_visible == value) return; _visible = value; VisibleChanged?.Invoke(this, EventArgs.Empty); NotifyItem(); } }
        public bool Available { get => _visible; set => Visible = value; }
        public Size Size { get; set; }
        public ToolStrip Owner { get; internal set; }
        public ToolStripItem OwnerItem { get; internal set; }
        public Font Font { get; set; }
        public Padding Margin { get; set; }
        public Padding Padding { get; set; }
        public bool AutoSize { get; set; } = true;
        public ToolStripItemImageScaling ImageScaling { get; set; } = ToolStripItemImageScaling.SizeToFit;
        public ContentAlignment TextAlign { get; set; } = ContentAlignment.MiddleCenter;
        public ContentAlignment ImageAlign { get; set; } = ContentAlignment.MiddleCenter;
        public TextImageRelation TextImageRelation { get; set; } = TextImageRelation.ImageBeforeText;
        public bool AutoToolTip { get; set; }
        public int Height { get => Size.Height; set => Size = new Size(Size.Width, value); }
        public int Width { get => Size.Width; set => Size = new Size(value, Size.Height); }
        public Color ForeColor { get; set; } = SystemColors.ControlText;
        public Color BackColor { get; set; } = SystemColors.Control;
        public ToolStripItemOverflow Overflow { get; set; }
        /// <summary>The renderer reports the item under the mouse or keyboard selection.</summary>
        public bool Selected { get; set; }
        public ToolStripItemAlignment Alignment { get; set; }
        public event EventHandler Click, MouseHover, MouseEnter, MouseLeave, VisibleChanged, EnabledChanged;
        public event MouseEventHandler MouseUp, MouseDown;
        public void PerformClick() { if (Enabled) OnClick(EventArgs.Empty); }
        protected virtual void OnClick(EventArgs e) { Click?.Invoke(this, e); Owner?.RaiseItemClicked(this); }
    }
    public enum ToolStripItemAlignment { Left, Right }
    public class ToolStripSeparator : ToolStripItem { public ToolStripSeparator() : base("-") { } }
    public class ToolStripLabel : ToolStripItem { public ToolStripLabel() { } public ToolStripLabel(string text) : base(text) { } }
    public class ToolStripStatusLabel : ToolStripLabel
    {
        public ToolStripStatusLabel() { }
        public ToolStripStatusLabel(string text) : base(text) { }
        public bool Spring { get; set; }
        public ToolStripStatusLabelBorderSides BorderSides { get; set; }
        public Border3DStyle BorderStyle { get; set; } = Border3DStyle.Flat;
    }
    [Flags] public enum ToolStripStatusLabelBorderSides { None = 0, Left = 1, Top = 2, Right = 4, Bottom = 8, All = 15 }
    public enum Border3DStyle { Adjust = 8192, Bump = 9, Etched = 6, Flat = 16394, Raised = 5, RaisedInner = 4, RaisedOuter = 1, Sunken = 10, SunkenInner = 8, SunkenOuter = 2 }
    public enum ToolStripItemImageScaling { None, SizeToFit }
    public class ToolStripButton : ToolStripItem
    {
        bool _checked;
        public bool Checked { get => _checked; set { if (_checked == value) return; _checked = value; CheckedChanged?.Invoke(this, EventArgs.Empty); NotifyItem(); } }
        public CheckState CheckState { get => _checked ? CheckState.Checked : CheckState.Unchecked; set => Checked = value != CheckState.Unchecked; }
        public bool CheckOnClick { get; set; }
        public event EventHandler CheckedChanged;
        public ToolStripButton() { }
        public ToolStripButton(string text) : base(text) { }
        public ToolStripButton(string text, Image image) : base(text) { Image = image; }
        public ToolStripButton(string text, Image image, EventHandler onClick) : base(text) { Image = image; if (onClick != null) Click += onClick; }
        protected override void OnClick(EventArgs e) { if (CheckOnClick) Checked = !Checked; base.OnClick(e); }
    }
    public class ToolStripDropDownItem : ToolStripItem
    {
        public ToolStripDropDownItem() { DropDownItems = new ToolStripItemCollection(null, this); }
        public ToolStripDropDownItem(string text) : base(text) { DropDownItems = new ToolStripItemCollection(null, this); }
        public ToolStripItemCollection DropDownItems { get; }
        public bool HasDropDownItems => DropDownItems.Count > 0;
        ToolStripDropDownMenu _dropDown;
        /// <summary>The drop-down window of the item (its events; the items are DropDownItems).</summary>
        public ToolStripDropDown DropDown => _dropDown ??= new ToolStripDropDownMenu();
        /// <summary>Renderer input: the item's drop-down is closing; false when a Closing handler cancelled it.</summary>
        public bool RaiseDropDownClosing(ToolStripDropDownCloseReason reason) => _dropDown == null || _dropDown.RaiseClosing(reason);
        public event EventHandler DropDownOpening, DropDownOpened, DropDownClosed;
        /// <summary>Renderer input: the item's drop-down opens (DropDownOpening, then DropDownOpened) and closes
        /// (Closing may cancel; DropDownClosed).</summary>
        public void RaiseDropDownOpening() { DropDownOpening?.Invoke(this, EventArgs.Empty); DropDownOpened?.Invoke(this, EventArgs.Empty); }
        public void RaiseDropDownClosed() => DropDownClosed?.Invoke(this, EventArgs.Empty);
        public event ToolStripItemClickedEventHandler DropDownItemClicked;
        internal void RaiseDropDownItemClicked(ToolStripItem item) => DropDownItemClicked?.Invoke(this, new ToolStripItemClickedEventArgs(item));
    }
    public class ToolStripMenuItem : ToolStripDropDownItem
    {
        bool _checked;
        public ToolStripMenuItem() { }
        public ToolStripMenuItem(string text) : base(text) { }
        public ToolStripMenuItem(string text, Image image) : base(text) { Image = image; }
        public ToolStripMenuItem(string text, Image image, EventHandler onClick) : base(text) { Image = image; if (onClick != null) Click += onClick; }
        public bool Checked { get => _checked; set { if (_checked == value) return; _checked = value; CheckedChanged?.Invoke(this, EventArgs.Empty); NotifyItem(); } }
        public bool CheckOnClick { get; set; }
        public CheckState CheckState { get => _checked ? CheckState.Checked : CheckState.Unchecked; set => Checked = value != CheckState.Unchecked; }
        public Keys ShortcutKeys { get; set; }
        public string ShortcutKeyDisplayString { get; set; }
        public bool ShowShortcutKeys { get; set; } = true;
        public event EventHandler CheckedChanged;
        protected override void OnClick(EventArgs e) { if (CheckOnClick) Checked = !Checked; base.OnClick(e); }
    }
    /// <summary>A combo box on a tool strip: the item forwards the hosted combo box.</summary>
    public class ToolStripComboBox : ToolStripControlHost
    {
        public ToolStripComboBox() : base(new ComboBox())
        {
            ComboBox.SelectedIndexChanged += (s, e) => OnSelectedIndexChanged(e);
            ComboBox.DropDown += (s, e) => DropDown?.Invoke(this, e);
            ComboBox.DropDownClosed += (s, e) => DropDownClosed?.Invoke(this, e);
            ComboBox.SelectionChangeCommitted += (s, e) => SelectionChangeCommitted?.Invoke(this, e);
        }
        public ComboBox ComboBox => (ComboBox)Control;
        public ComboBox.ObjectCollection Items => ComboBox.Items;
        public int SelectedIndex { get => ComboBox.SelectedIndex; set => ComboBox.SelectedIndex = value; }
        public object SelectedItem { get => ComboBox.SelectedItem; set => ComboBox.SelectedItem = value; }
        public override string Text { get => ComboBox.Text; set => ComboBox.Text = value; }
        public ComboBoxStyle DropDownStyle { get => ComboBox.DropDownStyle; set => ComboBox.DropDownStyle = value; }
        public int DropDownWidth { get => ComboBox.DropDownWidth; set => ComboBox.DropDownWidth = value; }
        public int MaxDropDownItems { get => ComboBox.MaxDropDownItems; set => ComboBox.MaxDropDownItems = value; }
        public FlatStyle FlatStyle { get; set; } = FlatStyle.Popup;
        public bool Sorted { get => ComboBox.Sorted; set => ComboBox.Sorted = value; }
        public event EventHandler SelectedIndexChanged, DropDown, DropDownClosed, SelectionChangeCommitted;
        protected virtual void OnSelectedIndexChanged(EventArgs e) => SelectedIndexChanged?.Invoke(this, e);
        public void BeginUpdate() { }
        public void EndUpdate() { }
    }
    /// <summary>A text box on a tool strip: the item forwards the hosted text box's text, keys and focus.</summary>
    public class ToolStripTextBox : ToolStripControlHost
    {
        public ToolStripTextBox() : base(new TextBox()) { }
        public TextBox TextBox => (TextBox)Control;
        public override string Text { get => TextBox.Text; set => TextBox.Text = value; }
        public bool ShortcutsEnabled { get => TextBox.ShortcutsEnabled; set => TextBox.ShortcutsEnabled = value; }
        public bool ReadOnly { get => TextBox.ReadOnly; set => TextBox.ReadOnly = value; }
        public HorizontalAlignment TextBoxTextAlign { get => TextBox.TextAlign; set => TextBox.TextAlign = value; }
        public int SelectionStart { get => TextBox.SelectionStart; set => TextBox.SelectionStart = value; }
        public int SelectionLength { get => TextBox.SelectionLength; set => TextBox.SelectionLength = value; }
        public void SelectAll() => TextBox.SelectAll();
    }
    public class ToolStripItemCollection : IList, IEnumerable<ToolStripItem>
    {
        readonly ToolStrip owner;
        readonly ToolStripItem ownerItem;
        readonly List<ToolStripItem> items = new List<ToolStripItem>();
        public ToolStripItemCollection(ToolStrip owner, ToolStripItem ownerItem) { this.owner = owner; this.ownerItem = ownerItem; }
        public int Count => items.Count;
        public ToolStripItem this[int index] => items[index];
        public ToolStripItem this[string key] => items.FirstOrDefault(i => i.Name == key);
        public int Add(ToolStripItem item) { item.Owner = owner; item.OwnerItem = ownerItem; items.Add(item); return items.Count - 1; }
        public ToolStripItem Add(string text) { var item = new ToolStripMenuItem(text); Add(item); return item; }
        public ToolStripItem Add(string text, Image image, EventHandler onClick) { var item = new ToolStripMenuItem(text, image, onClick); Add(item); return item; }
        public void AddRange(ToolStripItem[] values) { foreach (var item in values) Add(item); }
        public void Insert(int index, ToolStripItem item) { item.Owner = owner; item.OwnerItem = ownerItem; items.Insert(index, item); }
        public void Remove(ToolStripItem item) => items.Remove(item);
        public void RemoveAt(int index) => items.RemoveAt(index);
        public void Clear() => items.Clear();
        public bool Contains(ToolStripItem item) => items.Contains(item);
        public int IndexOf(ToolStripItem item) => items.IndexOf(item);
        public IEnumerator<ToolStripItem> GetEnumerator() => items.GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => items.GetEnumerator();
        object IList.this[int index] { get => items[index]; set => throw new NotSupportedException(); }
        int IList.Add(object value) => Add((ToolStripItem)value);
        bool IList.Contains(object value) => items.Contains(value as ToolStripItem);
        int IList.IndexOf(object value) => items.IndexOf(value as ToolStripItem);
        void IList.Insert(int index, object value) => Insert(index, (ToolStripItem)value);
        void IList.Remove(object value) => Remove((ToolStripItem)value);
        bool IList.IsFixedSize => false;
        bool IList.IsReadOnly => false;
        void ICollection.CopyTo(Array array, int index) => ((ICollection)items).CopyTo(array, index);
        bool ICollection.IsSynchronized => false;
        object ICollection.SyncRoot => this;
    }
    public class ToolStrip : ScrollableControl
    {
        public ToolStrip() { Items = new ToolStripItemCollection(this, null); }
        public ToolStripItemCollection Items { get; }
        public ImageList ImageList { get; set; }
        public Size ImageScalingSize { get; set; } = new Size(16, 16);
        public bool ShowItemToolTips { get; set; } = true;
        public ToolStripGripStyle GripStyle { get; set; }
        public ToolStripLayoutStyle LayoutStyle { get; set; }
        public ToolStripRenderMode RenderMode { get; set; }
        public event ToolStripItemClickedEventHandler ItemClicked;
        internal void RaiseItemClicked(ToolStripItem item) => ItemClicked?.Invoke(this, new ToolStripItemClickedEventArgs(item));
    }
    public enum ToolStripGripStyle { Hidden, Visible }
    public enum ToolStripLayoutStyle { StackWithOverflow, HorizontalStackWithOverflow, VerticalStackWithOverflow, Flow, Table }
    public enum ToolStripRenderMode { Custom, System, Professional, ManagerRenderMode }
    // WinForms DefaultDock: a menu strip docks at the top and a status strip at the bottom (the designer omits it)
    public class MenuStrip : ToolStrip { public MenuStrip() { Dock = DockStyle.Top; } }
    public class StatusStrip : ToolStrip { public StatusStrip() { Dock = DockStyle.Bottom; } }
    public class ToolStripDropDown : ToolStrip
    {
        public event ToolStripDropDownClosedEventHandler Closed;
        public event ToolStripDropDownClosingEventHandler Closing;
        public event CancelEventHandler Opening;
        public event EventHandler Opened;
        public bool AutoClose { get; set; } = true;
        public bool DropShadowEnabled { get; set; } = true;
        public double Opacity { get; set; } = 1;
        public Control SourceControl { get; protected set; }
        internal void RaiseOpening(CancelEventArgs e) => Opening?.Invoke(this, e);
        internal void RaiseOpened() => Opened?.Invoke(this, EventArgs.Empty);
        /// <summary>Shows the drop-down at a point of a control (client coordinates); the renderer opens it.</summary>
        public void Show(Control control, Point position) { SourceControl = control; ShownAt = position; Visible = true; ControlNotifications.Raise(control, "ContextMenu"); Notify("Show"); }
        public void Show(Control control, int x, int y) => Show(control, new Point(x, y));
        public void Show(Point screenLocation) { ShownAt = screenLocation; Visible = true; Notify("Show"); }
        public Point ShownAt { get; private set; }
        public void Close() => Close(ToolStripDropDownCloseReason.CloseCalled);
        internal bool RaiseClosing(ToolStripDropDownCloseReason reason)
        {
            var closing = new ToolStripDropDownClosingEventArgs(reason);
            Closing?.Invoke(this, closing);
            return !closing.Cancel;
        }
        public void Close(ToolStripDropDownCloseReason reason)
        {
            if (!Visible) return;
            var closing = new ToolStripDropDownClosingEventArgs(reason);
            Closing?.Invoke(this, closing);
            if (closing.Cancel) return;
            Visible = false;
            Notify("Close");
            Closed?.Invoke(this, new ToolStripDropDownClosedEventArgs());
        }
    }
    public class ToolStripDropDownClosedEventArgs : EventArgs { }
    public delegate void ToolStripDropDownClosedEventHandler(object sender, ToolStripDropDownClosedEventArgs e);
    public class ToolStripDropDownMenu : ToolStripDropDown { public bool ShowImageMargin { get; set; } = true; public bool ShowCheckMargin { get; set; } }
    public class ContextMenuStrip : ToolStripDropDownMenu
    {
        public ContextMenuStrip() { }
        public ContextMenuStrip(IContainer container) { container?.Add(this); }
        /// <summary>Renderer input: opens the menu for a control; returns false when Opening cancelled it.</summary>
        public bool OpenFor(Control source)
        {
            SourceControl = source;
            var e = new CancelEventArgs();
            RaiseOpening(e);
            if (e.Cancel) return false;
            RaiseOpened();
            return true;
        }
    }

    // Property grid ------------------------------------------------------------------------------------------------------------
    public abstract class GridItem
    {
        public abstract GridItemCollection GridItems { get; }
        public abstract GridItemType GridItemType { get; }
        public abstract string Label { get; }
        public abstract GridItem Parent { get; }
        public abstract PropertyDescriptor PropertyDescriptor { get; }
        public abstract object Value { get; }
        public virtual bool Expandable => GridItems.Count > 0;
        public virtual bool Expanded { get; set; } = true;
        public object Tag { get; set; }
        public abstract bool Select();
    }
    public class GridItemCollection : IEnumerable<GridItem>
    {
        readonly List<GridItem> items;
        public static readonly GridItemCollection Empty = new GridItemCollection(new List<GridItem>());
        public GridItemCollection(List<GridItem> items) { this.items = items; }
        public int Count => items.Count;
        public GridItem this[int index] => items[index];
        public GridItem this[string label] => items.FirstOrDefault(i => i.Label == label);
        public IEnumerator<GridItem> GetEnumerator() => items.GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => items.GetEnumerator();
    }
    public class PropertyValueChangedEventArgs : EventArgs { public GridItem ChangedItem { get; } public object OldValue { get; } public PropertyValueChangedEventArgs(GridItem changedItem, object oldValue) { ChangedItem = changedItem; OldValue = oldValue; } }
    public class SelectedGridItemChangedEventArgs : EventArgs { public GridItem OldSelection { get; } public GridItem NewSelection { get; } public SelectedGridItemChangedEventArgs(GridItem oldSel, GridItem newSel) { OldSelection = oldSel; NewSelection = newSel; } }

    /// <summary>WinForms PropertyGrid state model. Rows follow PropertySort.CategorizedAlphabetical, the
    /// WinForms default the original forms use; leading tab / zero-width-space ordering prefixes (the original
    /// OrderedDisplayName and DynamicTypeDescriptor category ordering) sort first, as under .NET Framework NLS.</summary>
    public class PropertyGrid : ContainerControl
    {
        object[] _selectedObjects = new object[0];
        GridItem _selected;
        RootItem _root;
        readonly Dictionary<string, bool> _expanded = new Dictionary<string, bool>();
        public PropertyGrid() { }
        public PropertySort PropertySort { get; set; } = PropertySort.CategorizedAlphabetical;
        public bool ToolbarVisible { get; set; } = true;
        public bool HelpVisible { get; set; } = true;
        public bool CommandsVisibleIfAvailable { get; set; } = true;
        public Color LineColor { get; set; }
        public Color DisabledItemForeColor { get; set; }
        public Color CategoryForeColor { get; set; }
        public Color ViewBackColor { get; set; }
        public Color HelpBackColor { get; set; }
        public bool CanShowVisualStyleGlyphs { get; set; } = true;
        public ISite SiteOverride { get; set; }
        public object SelectedObject
        {
            get => _selectedObjects.Length == 1 ? _selectedObjects[0] : null;
            set => SelectedObjects = value == null ? new object[0] : new[] { value };
        }
        public object[] SelectedObjects
        {
            get => (object[])_selectedObjects.Clone();
            set
            {
                _selectedObjects = value ?? new object[0];
                string previousLabel = _selected?.Label;
                GridItemType previousType = _selected?.GridItemType ?? GridItemType.Root;
                Rebuild();
                // WinForms restores the previous selection by label when it still exists.
                GridItem restored = previousLabel == null ? null : Flatten(_root).FirstOrDefault(i => i.Label == previousLabel && i.GridItemType == previousType);
                SetSelected(restored ?? Flatten(_root).FirstOrDefault(i => i.GridItemType != GridItemType.Root), false);
                Notify(nameof(SelectedObject));
                OnSelectedObjectsChanged(EventArgs.Empty);
            }
        }
        public GridItem SelectedGridItem
        {
            get => _selected;
            set
            {
                if (value == null) throw new ArgumentNullException(nameof(value));
                SetSelected(value, true);
            }
        }
        void SetSelected(GridItem item, bool raise)
        {
            if (item == _selected) return;
            GridItem old = _selected;
            _selected = item;
            Notify(nameof(SelectedGridItem));
            if (raise || old != null) OnSelectedGridItemChanged(new SelectedGridItemChangedEventArgs(old, item));
        }
        public event PropertyValueChangedEventHandler PropertyValueChanged;
        public event SelectedGridItemChangedEventHandler SelectedGridItemChanged;
        public event EventHandler SelectedObjectsChanged, PropertySortChanged;
        protected virtual void OnSelectedObjectsChanged(EventArgs e) => SelectedObjectsChanged?.Invoke(this, e);
        protected virtual void OnSelectedGridItemChanged(SelectedGridItemChangedEventArgs e) => SelectedGridItemChanged?.Invoke(this, e);
        protected virtual void OnPropertyValueChanged(PropertyValueChangedEventArgs e) => PropertyValueChanged?.Invoke(this, e);
        public override void Refresh()
        {
            // Re-reads browsable properties (dynamic visibility) and keeps the selected row by label.
            string label = _selected?.Label;
            GridItemType type = _selected?.GridItemType ?? GridItemType.Root;
            string parent = _selected?.Parent?.Label;
            Rebuild();
            _selected = Flatten(_root).FirstOrDefault(i => i.Label == label && i.GridItemType == type && i.Parent?.Label == parent)
                        ?? Flatten(_root).FirstOrDefault(i => i.Label == label && i.GridItemType == type)
                        ?? _selected;
            base.Refresh();
        }
        public void RefreshTabs(PropertyTabScope scope) { }
        public void ExpandAllGridItems() { foreach (var item in Flatten(_root)) item.Expanded = true; Notify("Expanded"); }
        public void CollapseAllGridItems() { foreach (var item in Flatten(_root)) if (item.GridItemType != GridItemType.Root) item.Expanded = false; Notify("Expanded"); }
        public void ResetSelectedProperty() { }
        public GridItem Root => _root;

        /// <summary>Renderer input: a committed text edit of a property row (WinForms grid edit + PropertyValueChanged).</summary>
        public void SetValueFromText(GridItem item, string text)
        {
            if (!(item is PropertyItem p)) throw new ArgumentException("Not a property row.");
            object component = p.Component;
            var context = new GridContext(component, p.PropertyDescriptor, this);
            object oldValue = p.PropertyDescriptor.GetValue(component);
            object value = p.PropertyDescriptor.Converter.ConvertFromString(context, CultureInfo.CurrentCulture, text);
            SetValue(p, value, oldValue);
        }
        /// <summary>Renderer input: a value chosen in the drop-down or produced by a modal editor.</summary>
        public void SetValue(GridItem item, object value)
        {
            if (!(item is PropertyItem p)) throw new ArgumentException("Not a property row.");
            SetValue(p, value, p.PropertyDescriptor.GetValue(p.Component));
        }
        void SetValue(PropertyItem p, object value, object oldValue)
        {
            if (p.PropertyDescriptor.IsReadOnly) throw new InvalidOperationException("Property is read-only: " + p.Label);
            if (_selected != p) SetSelected(p, true);
            p.PropertyDescriptor.SetValue(p.Component, value);
            // Child (expandable) values are written back to their parent property as WinForms does.
            for (var parent = p.Parent as PropertyItem; parent != null; parent = parent.Parent as PropertyItem)
                if (!parent.PropertyDescriptor.IsReadOnly && parent.PropertyDescriptor.PropertyType.IsValueType)
                    parent.PropertyDescriptor.SetValue(parent.Component, p.Component);
            Refresh();
            GridItem current = _selected ?? p;
            OnPropertyValueChanged(new PropertyValueChangedEventArgs(current, oldValue));
        }
        public string GetText(GridItem item)
        {
            if (!(item is PropertyItem p)) return "";
            var context = new GridContext(p.Component, p.PropertyDescriptor, this);
            try { return p.PropertyDescriptor.Converter.ConvertToString(context, CultureInfo.CurrentCulture, p.PropertyDescriptor.GetValue(p.Component)); }
            catch (Exception e) { return e.Message; }
        }
        public string[] GetStandardValues(GridItem item, out bool exclusive)
        {
            exclusive = false;
            if (!(item is PropertyItem p)) return new string[0];
            var context = new GridContext(p.Component, p.PropertyDescriptor, this);
            var converter = p.PropertyDescriptor.Converter;
            if (!converter.GetStandardValuesSupported(context)) return new string[0];
            exclusive = converter.GetStandardValuesExclusive(context);
            var values = converter.GetStandardValues(context);
            return values == null ? new string[0] : values.Cast<object>().Select(v => converter.ConvertToString(context, CultureInfo.CurrentCulture, v)).ToArray();
        }
        public object[] GetStandardValueObjects(GridItem item)
        {
            if (!(item is PropertyItem p)) return new object[0];
            var context = new GridContext(p.Component, p.PropertyDescriptor, this);
            var converter = p.PropertyDescriptor.Converter;
            return converter.GetStandardValuesSupported(context) ? converter.GetStandardValues(context)?.Cast<object>().ToArray() ?? new object[0] : new object[0];
        }
        public bool CanEditText(GridItem item)
        {
            if (!(item is PropertyItem p) || p.PropertyDescriptor.IsReadOnly) return false;
            var context = new GridContext(p.Component, p.PropertyDescriptor, this);
            return p.PropertyDescriptor.Converter.CanConvertFrom(context, typeof(string));
        }
        public ITypeDescriptorContext GetContext(GridItem item) => item is PropertyItem p ? new GridContext(p.Component, p.PropertyDescriptor, this) : null;
        public void SetExpanded(GridItem item, bool expanded) { item.Expanded = expanded; _expanded[Key(item)] = expanded; Notify("Expanded"); }
        static string Key(GridItem item) => (item.Parent == null ? "" : Key(item.Parent) + "/") + item.GridItemType + ":" + item.Label;

        void Rebuild()
        {
            _root = new RootItem(this);
            if (_selectedObjects.Length != 1 || _selectedObjects[0] == null) return;
            object component = _selectedObjects[0];
            var properties = Browsable(component, null);
            if (PropertySort == PropertySort.NoSort || PropertySort == PropertySort.Alphabetical)
            {
                foreach (var p in Order(properties, PropertySort == PropertySort.Alphabetical)) _root.Children.Add(MakeProperty(component, p, _root));
                return;
            }
            bool alphabetical = PropertySort == PropertySort.CategorizedAlphabetical;
            var categories = properties.GroupBy(p => p.Category ?? "Misc").ToList();
            IEnumerable<IGrouping<string, PropertyDescriptor>> ordered = alphabetical ? categories.OrderBy(g => g.Key, OrderedNameComparer.Instance) : categories;
            foreach (var group in ordered)
            {
                var category = new CategoryItem(this, _root, group.Key);
                category.Expanded = !_expanded.TryGetValue(Key(category), out bool e) || e;
                foreach (var p in Order(group, alphabetical)) category.Children.Add(MakeProperty(component, p, category));
                _root.Children.Add(category);
            }
        }
        static IEnumerable<PropertyDescriptor> Order(IEnumerable<PropertyDescriptor> properties, bool alphabetical) =>
            alphabetical ? properties.OrderBy(p => p.DisplayName, OrderedNameComparer.Instance) : properties;
        List<PropertyDescriptor> Browsable(object component, PropertyDescriptor owner)
        {
            PropertyDescriptorCollection all;
            var context = owner == null ? null : new GridContext(component, owner, this);
            if (owner != null && owner.Converter.GetPropertiesSupported(context))
                all = owner.Converter.GetProperties(context, component, new Attribute[] { BrowsableAttribute.Yes });
            else
                all = TypeDescriptor.GetProperties(component, new Attribute[] { BrowsableAttribute.Yes });
            return all == null ? new List<PropertyDescriptor>() : all.Cast<PropertyDescriptor>().Where(p => p.IsBrowsable).ToList();
        }
        PropertyItem MakeProperty(object component, PropertyDescriptor descriptor, GridItem parent)
        {
            var item = new PropertyItem(this, parent, component, descriptor);
            var context = new GridContext(component, descriptor, this);
            object value = null;
            try { value = descriptor.GetValue(component); } catch { }
            if (value != null && descriptor.Converter.GetPropertiesSupported(context))
            {
                foreach (var child in Order(Browsable(value, descriptor), true)) item.Children.Add(MakeProperty(value, child, item));
                item.Expanded = _expanded.TryGetValue(Key(item), out bool e) && e;
            }
            return item;
        }
        public static IEnumerable<GridItem> Flatten(GridItem item)
        {
            if (item == null) yield break;
            yield return item;
            foreach (GridItem child in item.GridItems) foreach (var x in Flatten(child)) yield return x;
        }

        sealed class GridContext : ITypeDescriptorContext
        {
            readonly object instance; readonly PropertyDescriptor descriptor; readonly PropertyGrid grid;
            public GridContext(object instance, PropertyDescriptor descriptor, PropertyGrid grid) { this.instance = instance; this.descriptor = descriptor; this.grid = grid; }
            public IContainer Container => null;
            public object Instance => instance;
            public PropertyDescriptor PropertyDescriptor => descriptor;
            public object GetService(Type serviceType) => grid.Site?.GetService(serviceType);
            public bool OnComponentChanging() => true;
            public void OnComponentChanged() { }
        }
        class RootItem : GridItem
        {
            public readonly List<GridItem> Children = new List<GridItem>();
            readonly PropertyGrid grid;
            public RootItem(PropertyGrid grid) { this.grid = grid; }
            public override GridItemCollection GridItems => new GridItemCollection(Children);
            public override GridItemType GridItemType => GridItemType.Root;
            public override string Label => grid.SelectedObject?.GetType().Name ?? "";
            public override GridItem Parent => null;
            public override PropertyDescriptor PropertyDescriptor => null;
            public override object Value => grid.SelectedObject;
            public override bool Select() => false;
        }
        class CategoryItem : GridItem
        {
            public readonly List<GridItem> Children = new List<GridItem>();
            readonly PropertyGrid grid; readonly GridItem parent; readonly string label;
            public CategoryItem(PropertyGrid grid, GridItem parent, string label) { this.grid = grid; this.parent = parent; this.label = label; }
            public override GridItemCollection GridItems => new GridItemCollection(Children);
            public override GridItemType GridItemType => GridItemType.Category;
            public override string Label => label;
            public override GridItem Parent => parent;
            public override PropertyDescriptor PropertyDescriptor => null;
            public override object Value => null;
            public override bool Expanded { get => base.Expanded; set { base.Expanded = value; grid._expanded[Key(this)] = value; } }
            public override bool Select() { grid.SelectedGridItem = this; return true; }
        }
        internal class PropertyItem : GridItem
        {
            public readonly List<GridItem> Children = new List<GridItem>();
            readonly PropertyGrid grid; readonly GridItem parent;
            public object Component { get; }
            readonly PropertyDescriptor descriptor;
            public PropertyItem(PropertyGrid grid, GridItem parent, object component, PropertyDescriptor descriptor) { this.grid = grid; this.parent = parent; Component = component; this.descriptor = descriptor; Expanded = false; }
            public override GridItemCollection GridItems => new GridItemCollection(Children);
            public override GridItemType GridItemType => GridItemType.Property;
            public override string Label => descriptor.DisplayName;
            public override GridItem Parent => parent;
            public override PropertyDescriptor PropertyDescriptor => descriptor;
            public override object Value { get { try { return descriptor.GetValue(Component); } catch { return null; } } }
            public override bool Expanded { get => base.Expanded; set { base.Expanded = value; grid._expanded[Key(this)] = value; } }
            public override bool Select() { grid.SelectedGridItem = this; return true; }
        }
    }
    public enum PropertyTabScope { Static, Global, Document, Component }

    /// <summary>NLS-like ordering of names that carry invisible ordering prefixes (tabs, U+200B): more
    /// prefixes sort first; the visible names then compare case-insensitively.</summary>
    public sealed class OrderedNameComparer : IComparer<string>
    {
        public static readonly OrderedNameComparer Instance = new OrderedNameComparer();
        static int Prefix(string s) { int n = 0; while (n < s.Length && (s[n] == '\t' || s[n] == '​')) n++; return n; }
        public static string Visible(string s) => (s ?? "").TrimStart('\t', '​');
        public int Compare(string x, string y)
        {
            x ??= ""; y ??= "";
            int px = Prefix(x), py = Prefix(y);
            if (px != py) return py.CompareTo(px);
            int c = string.Compare(x.Substring(px), y.Substring(py), CultureInfo.InvariantCulture, CompareOptions.IgnoreCase);
            return c != 0 ? c : string.CompareOrdinal(x, y);
        }
    }
}
namespace CaeGlobals
{
    /// <summary>The WinForms-only extension methods of the original CaeGlobals/Extensions.WinForms.cs, which the
    /// portable CaeGlobals leaves out, for the original forms on this model (same bodies as the original).</summary>
    public static class WinFormsExtensionMethods
    {
        public static void SetLocationInsideWorkingArea(this System.Windows.Forms.Form form, System.Drawing.Point location)
        {
            System.Drawing.Rectangle workingArea = System.Windows.Forms.Screen.FromPoint(location).WorkingArea;
            System.Drawing.Size size = new System.Drawing.Size(System.Math.Min(form.Width, workingArea.Width), System.Math.Min(form.Height, workingArea.Height));
            //
            if (size != form.Size)
            {
                form.MinimumSize = new System.Drawing.Size(System.Math.Min(form.MinimumSize.Width, size.Width),
                                                           System.Math.Min(form.MinimumSize.Height, size.Height));
                form.Size = size;
            }
            //
            location.X = System.Math.Max(workingArea.Left, System.Math.Min(location.X, workingArea.Right - form.Width));
            location.Y = System.Math.Max(workingArea.Top, System.Math.Min(location.Y, workingArea.Bottom - form.Height));
            //
            if (form.Location != location) form.Location = location;
        }
    }
}
