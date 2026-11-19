// Headless TreeView model (System.Windows.Forms semantics) for the original CodersLabTreeView and the forms that
// use it (FrmMaterial, FrmSurfaceInteraction, FrmMaterialLibrary, FrmTransformation, FrmStepControls). Node
// geometry follows the native control at 96 DPI (row height, indent, image and label rectangles) so the original
// hit tests (GetNodeAt, node Bounds, the +/- rule) see the coordinates the renderer draws.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;

namespace System.Windows.Forms
{
    public enum TreeViewAction { Unknown, ByKeyboard, ByMouse, Collapse, Expand }
    public enum TreeViewDrawMode { Normal, OwnerDrawText, OwnerDrawAll }
    [Flags] public enum TreeViewHitTestLocations { None = 1, Image = 2, Label = 4, Indent = 8, AboveClientArea = 256, BelowClientArea = 512, LeftOfClientArea = 2048, RightOfClientArea = 1024, RightOfLabel = 32, StateImage = 64, PlusMinus = 16 }

    public class TreeViewEventArgs : EventArgs
    {
        public TreeNode Node { get; }
        public TreeViewAction Action { get; }
        public TreeViewEventArgs(TreeNode node) : this(node, TreeViewAction.Unknown) { }
        public TreeViewEventArgs(TreeNode node, TreeViewAction action) { Node = node; Action = action; }
    }
    public class TreeViewCancelEventArgs : System.ComponentModel.CancelEventArgs
    {
        public TreeNode Node { get; }
        public TreeViewAction Action { get; }
        public TreeViewCancelEventArgs(TreeNode node, bool cancel, TreeViewAction action) : base(cancel) { Node = node; Action = action; }
    }
    public class NodeLabelEditEventArgs : EventArgs
    {
        public TreeNode Node { get; }
        public string Label { get; }
        public bool CancelEdit { get; set; }
        public NodeLabelEditEventArgs(TreeNode node) { Node = node; }
        public NodeLabelEditEventArgs(TreeNode node, string label) { Node = node; Label = label; }
    }
    public class TreeNodeMouseClickEventArgs : MouseEventArgs
    {
        public TreeNode Node { get; }
        public TreeNodeMouseClickEventArgs(TreeNode node, MouseButtons button, int clicks, int x, int y) : base(button, clicks, x, y, 0) { Node = node; }
    }
    public class TreeNodeMouseHoverEventArgs : EventArgs { public TreeNode Node { get; } public TreeNodeMouseHoverEventArgs(TreeNode node) { Node = node; } }
    public class ItemDragEventArgs : EventArgs
    {
        public MouseButtons Button { get; }
        public object Item { get; }
        public ItemDragEventArgs(MouseButtons button) : this(button, null) { }
        public ItemDragEventArgs(MouseButtons button, object item) { Button = button; Item = item; }
    }
    public class TreeViewHitTestInfo
    {
        public TreeNode Node { get; }
        public TreeViewHitTestLocations Location { get; }
        public TreeViewHitTestInfo(TreeNode node, TreeViewHitTestLocations location) { Node = node; Location = location; }
    }
    public class DrawTreeNodeEventArgs : EventArgs
    {
        public TreeNode Node { get; }
        public Rectangle Bounds { get; }
        public bool DrawDefault { get; set; }
        public DrawTreeNodeEventArgs(Graphics graphics, TreeNode node, Rectangle bounds, TreeNodeStates state) { Node = node; Bounds = bounds; }
    }
    [Flags] public enum TreeNodeStates { Selected = 1, Grayed = 2, Checked = 8, Focused = 16, Default = 32, Hot = 64, Marked = 128, Indeterminate = 256, ShowKeyboardCues = 512 }
    public delegate void TreeViewEventHandler(object sender, TreeViewEventArgs e);
    public delegate void TreeViewCancelEventHandler(object sender, TreeViewCancelEventArgs e);
    public delegate void NodeLabelEditEventHandler(object sender, NodeLabelEditEventArgs e);
    public delegate void TreeNodeMouseClickEventHandler(object sender, TreeNodeMouseClickEventArgs e);
    public delegate void TreeNodeMouseHoverEventHandler(object sender, TreeNodeMouseHoverEventArgs e);
    public delegate void ItemDragEventHandler(object sender, ItemDragEventArgs e);
    public delegate void DrawTreeNodeEventHandler(object sender, DrawTreeNodeEventArgs e);

    /// <summary>Text measurement for layout that the original code reads (node bounds); the renderer installs
    /// its font metrics, the fallback is Segoe UI 9 pt's average advance.</summary>
    public static class TextRenderer
    {
        public static Func<string, Font, Size> MeasureHandler;
        public static Size MeasureText(string text, Font font)
            => MeasureHandler != null ? ToolkitSynchronizationContext.OnUiThread(() => MeasureHandler(text ?? "", font ?? Control.DefaultFont)) : new Size((int)Math.Ceiling((text ?? "").Length * 6.5), 15);
        /// <summary>Text on a painting surface (System.Drawing.Graphics records it; the renderer draws it).</summary>
        public static void DrawText(IDeviceContext dc, string text, Font font, Point pt, Color foreColor)
            => ((Graphics)dc).DrawText(text, font ?? Control.DefaultFont, new RectangleF(pt.X, pt.Y, 0, 0), foreColor, (int)TextFormatFlags.Default);
        public static void DrawText(IDeviceContext dc, string text, Font font, Point pt, Color foreColor, TextFormatFlags flags)
            => ((Graphics)dc).DrawText(text, font ?? Control.DefaultFont, new RectangleF(pt.X, pt.Y, 0, 0), foreColor, (int)flags);
        public static void DrawText(IDeviceContext dc, string text, Font font, Rectangle bounds, Color foreColor)
            => DrawText(dc, text, font, bounds, foreColor, TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
        public static void DrawText(IDeviceContext dc, string text, Font font, Rectangle bounds, Color foreColor, TextFormatFlags flags)
            => ((Graphics)dc).DrawText(text, font ?? Control.DefaultFont, new RectangleF(bounds.X, bounds.Y, bounds.Width, bounds.Height), foreColor, (int)flags);
        public static Size MeasureText(IDeviceContext dc, string text, Font font) => MeasureText(text, font);
        public static Size MeasureText(string text, Font font, Size proposedSize, TextFormatFlags flags) => MeasureText(text, font);
        /// <summary>Graphics.MeasureString equivalent (GDI+ adds about 1/6 em of padding to the TextRenderer width).</summary>
        public static SizeF MeasureString(string text, Font font) { Size size = MeasureText(text, font); return new SizeF(size.Width + (font ?? Control.DefaultFont).Size * 96f / 72f / 3f, size.Height); }
    }

    public class TreeNode : ICloneable
    {
        string _text = "";
        Color _backColor = Color.Empty, _foreColor = Color.Empty;
        internal bool _expanded;
        internal TreeNode _parent;
        internal TreeView _treeView;

        public TreeNode() { Nodes = new TreeNodeCollection(this); }
        public TreeNode(string text) : this() { _text = text ?? ""; }
        public TreeNode(string text, TreeNode[] children) : this(text) { Nodes.AddRange(children); }
        public TreeNode(string text, int imageIndex, int selectedImageIndex) : this(text) { ImageIndex = imageIndex; SelectedImageIndex = selectedImageIndex; }

        public string Text { get => _text; set { _text = value ?? ""; Changed(); } }
        public string Name { get; set; } = "";
        public object Tag { get; set; }
        public string ToolTipText { get; set; } = "";
        public string ImageKey { get; set; } = "";
        public string SelectedImageKey { get; set; } = "";
        public string StateImageKey { get; set; } = "";
        public int ImageIndex { get; set; } = -1;
        public int SelectedImageIndex { get; set; } = -1;
        public int StateImageIndex { get; set; } = -1;
        public Color BackColor { get => _backColor; set { if (_backColor == value) return; _backColor = value; Changed(); } }
        public Color ForeColor { get => _foreColor; set { if (_foreColor == value) return; _foreColor = value; Changed(); } }
        public Font NodeFont { get; set; }
        public bool Checked { get; set; }
        public ContextMenuStrip ContextMenuStrip { get; set; }
        public TreeNodeCollection Nodes { get; }
        public TreeNode Parent => _parent;
        public TreeView TreeView => _treeView;
        public int Level => _parent == null ? 0 : _parent.Level + 1;
        public int Index => Siblings?.IndexOf(this) ?? 0;
        public bool IsExpanded => _expanded;
        public bool IsSelected => _treeView != null && ReferenceEquals(_treeView.SelectedNode, this);
        public bool IsEditing => _treeView != null && ReferenceEquals(_treeView.EditingNode, this);
        public bool IsVisible
        {
            get
            {
                if (_treeView == null) return false;
                for (TreeNode p = _parent; p != null; p = p._parent) if (!p._expanded) return false;
                Rectangle b = Bounds;
                return b.Bottom > 0 && b.Top < _treeView.ClientSize.Height;
            }
        }
        public TreeNode FirstNode => Nodes.Count > 0 ? Nodes[0] : null;
        public TreeNode LastNode => Nodes.Count > 0 ? Nodes[Nodes.Count - 1] : null;
        TreeNodeCollection Siblings => _parent != null ? _parent.Nodes : _treeView?.Nodes;
        public TreeNode NextNode { get { var s = Siblings; int i = s?.IndexOf(this) ?? -1; return s != null && i >= 0 && i + 1 < s.Count ? s[i + 1] : null; } }
        public TreeNode PrevNode { get { var s = Siblings; int i = s?.IndexOf(this) ?? -1; return s != null && i > 0 ? s[i - 1] : null; } }
        public TreeNode NextVisibleNode { get { var rows = _treeView?.VisibleRows(); int i = rows?.IndexOf(this) ?? -1; return i >= 0 && i + 1 < rows.Count ? rows[i + 1] : null; } }
        public TreeNode PrevVisibleNode { get { var rows = _treeView?.VisibleRows(); int i = rows?.IndexOf(this) ?? -1; return i > 0 ? rows[i - 1] : null; } }
        public string FullPath
        {
            get
            {
                if (_treeView == null) throw new InvalidOperationException("TreeNode is not attached to a TreeView.");
                return _parent == null ? Text : _parent.FullPath + _treeView.PathSeparator + Text;
            }
        }
        /// <summary>The label rectangle in tree client coordinates (empty while an ancestor is collapsed).</summary>
        public Rectangle Bounds => _treeView?.NodeBounds(this) ?? Rectangle.Empty;

        public void Expand()
        {
            if (_expanded || _treeView == null) { _expanded = true; return; }
            var e = new TreeViewCancelEventArgs(this, false, TreeViewAction.Expand);
            _treeView.RaiseBeforeExpand(e);
            if (e.Cancel) return;
            _expanded = true;
            _treeView.RaiseAfterExpand(new TreeViewEventArgs(this, TreeViewAction.Expand));
            Changed();
        }
        public void ExpandAll() { Expand(); foreach (TreeNode n in Nodes) n.ExpandAll(); }
        public void Collapse() => Collapse(false);
        public void Collapse(bool ignoreChildren)
        {
            if (!ignoreChildren) foreach (TreeNode n in Nodes) n.Collapse(false);
            if (!_expanded) return;
            if (_treeView == null) { _expanded = false; return; }
            var e = new TreeViewCancelEventArgs(this, false, TreeViewAction.Collapse);
            _treeView.RaiseBeforeCollapse(e);
            if (e.Cancel) return;
            _expanded = false;
            // Native: collapsing the parent of the selected node selects the parent.
            if (_treeView.SelectedNode != null && IsAncestorOf(_treeView.SelectedNode)) _treeView.SetSelectedNode(this, TreeViewAction.Collapse);
            _treeView.RaiseAfterCollapse(new TreeViewEventArgs(this, TreeViewAction.Collapse));
            Changed();
        }
        bool IsAncestorOf(TreeNode node) { for (TreeNode p = node._parent; p != null; p = p._parent) if (p == this) return true; return false; }
        public void Toggle() { if (_expanded) Collapse(); else Expand(); }
        public void EnsureVisible()
        {
            for (TreeNode p = _parent; p != null; p = p._parent) p.Expand();
            _treeView?.ScrollIntoView(this);
        }
        public void BeginEdit() => _treeView?.BeginEditNode(this);
        public void EndEdit(bool cancel) => _treeView?.EndEditNode(cancel, null);
        public void Remove() => Siblings?.Remove(this);
        public int GetNodeCount(bool includeSubTrees) => Nodes.Count + (includeSubTrees ? Nodes.Cast<TreeNode>().Sum(n => n.GetNodeCount(true)) : 0);
        public virtual object Clone()
        {
            var node = (TreeNode)MemberwiseCloneNode();
            return node;
        }
        TreeNode MemberwiseCloneNode()
        {
            var node = (TreeNode)Activator.CreateInstance(GetType());
            node._text = _text; node.Name = Name; node.Tag = Tag; node.ToolTipText = ToolTipText;
            node.ImageKey = ImageKey; node.SelectedImageKey = SelectedImageKey; node.StateImageKey = StateImageKey;
            node.ImageIndex = ImageIndex; node.SelectedImageIndex = SelectedImageIndex; node.StateImageIndex = StateImageIndex;
            node._backColor = _backColor; node._foreColor = _foreColor; node.NodeFont = NodeFont; node.Checked = Checked;
            node.ContextMenuStrip = ContextMenuStrip; node._expanded = _expanded;
            foreach (TreeNode child in Nodes) node.Nodes.Add((TreeNode)child.Clone());
            return node;
        }
        internal void Attach(TreeView view) { _treeView = view; foreach (TreeNode n in Nodes) n.Attach(view); }
        void Changed() => _treeView?.NodesChanged();
        public override string ToString() => "TreeNode: " + (Text ?? "");
    }

    public class TreeNodeCollection : IList, IEnumerable<TreeNode>
    {
        readonly TreeNode _owner;
        readonly TreeView _view;
        readonly List<TreeNode> _items = new List<TreeNode>();
        internal TreeNodeCollection(TreeNode owner) { _owner = owner; }
        internal TreeNodeCollection(TreeView view) { _view = view; }
        TreeView View => _view ?? _owner?._treeView;

        public int Count => _items.Count;
        public TreeNode this[int index] { get => _items[index]; set { RemoveAt(index); Insert(index, value); } }
        public virtual TreeNode this[string key] => _items.FirstOrDefault(n => string.Equals(n.Name, key, StringComparison.OrdinalIgnoreCase));
        public TreeNode Add(string text) { var n = new TreeNode(text); Add(n); return n; }
        public TreeNode Add(string key, string text) { var n = new TreeNode(text) { Name = key }; Add(n); return n; }
        public TreeNode Add(string key, string text, int imageIndex) { var n = Add(key, text); n.ImageIndex = imageIndex; return n; }
        public TreeNode Add(string key, string text, string imageKey) { var n = Add(key, text); n.ImageKey = imageKey; return n; }
        public TreeNode Add(string key, string text, int imageIndex, int selectedImageIndex) { var n = Add(key, text, imageIndex); n.SelectedImageIndex = selectedImageIndex; return n; }
        public TreeNode Add(string key, string text, string imageKey, string selectedImageKey) { var n = Add(key, text, imageKey); n.SelectedImageKey = selectedImageKey; return n; }
        public int Add(TreeNode node) { Insert(_items.Count, node); return _items.Count - 1; }
        public void AddRange(TreeNode[] nodes) { foreach (TreeNode n in nodes) Add(n); }
        public void Insert(int index, TreeNode node)
        {
            if (node._treeView != null || node._parent != null) throw new ArgumentException($"Cannot add or insert the item '{node.Text}' in more than one place.");
            _items.Insert(Math.Min(index, _items.Count), node);
            node._parent = _owner;
            node.Attach(View);
            View?.NodesChanged();
        }
        public TreeNode Insert(int index, string text) { var n = new TreeNode(text); Insert(index, n); return n; }
        public TreeNode Insert(int index, string key, string text) { var n = new TreeNode(text) { Name = key }; Insert(index, n); return n; }
        public void Remove(TreeNode node)
        {
            int index = _items.IndexOf(node);
            if (index >= 0) RemoveAt(index);
        }
        public void RemoveAt(int index)
        {
            TreeNode node = _items[index];
            TreeView view = View;
            _items.RemoveAt(index);
            view?.NodeRemoving(node, _owner);
            node._parent = null;
            node.Attach(null);
            view?.NodesChanged();
        }
        public void RemoveByKey(string key) { int i = IndexOfKey(key); if (i >= 0) RemoveAt(i); }
        public virtual void Clear() { while (_items.Count > 0) RemoveAt(_items.Count - 1); }
        public bool Contains(TreeNode node) => _items.Contains(node);
        public bool ContainsKey(string key) => IndexOfKey(key) >= 0;
        public int IndexOf(TreeNode node) => _items.IndexOf(node);
        public int IndexOfKey(string key) => _items.FindIndex(n => string.Equals(n.Name, key, StringComparison.OrdinalIgnoreCase));
        public TreeNode[] Find(string key, bool searchAllChildren)
        {
            var found = new List<TreeNode>();
            foreach (TreeNode n in _items)
            {
                if (string.Equals(n.Name, key, StringComparison.OrdinalIgnoreCase)) found.Add(n);
                if (searchAllChildren) found.AddRange(n.Nodes.Find(key, true));
            }
            return found.ToArray();
        }
        public void CopyTo(Array dest, int index) => ((ICollection)_items).CopyTo(dest, index);
        public IEnumerator<TreeNode> GetEnumerator() => _items.ToList().GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
        int IList.Add(object value) => Add((TreeNode)value);
        bool IList.Contains(object value) => _items.Contains(value as TreeNode);
        int IList.IndexOf(object value) => _items.IndexOf(value as TreeNode);
        void IList.Insert(int index, object value) => Insert(index, (TreeNode)value);
        void IList.Remove(object value) => Remove((TreeNode)value);
        bool IList.IsFixedSize => false;
        public bool IsReadOnly => false;
        object IList.this[int index] { get => _items[index]; set => this[index] = (TreeNode)value; }
        bool ICollection.IsSynchronized => false;
        object ICollection.SyncRoot => this;
    }

    public class TreeView : Control
    {
        TreeNode _selected;
        int _updateCount, _topRow;
        public TreeView()
        {
            Nodes = new TreeNodeCollection(this);
            BackColor = SystemColors.Window;
            ForeColor = SystemColors.WindowText;
        }
        public TreeNodeCollection Nodes { get; }
        public ImageList ImageList { get; set; }
        public ImageList StateImageList { get; set; }
        public string ImageKey { get; set; } = "";
        public string SelectedImageKey { get; set; } = "";
        public int ImageIndex { get; set; } = -1;
        public int SelectedImageIndex { get; set; } = -1;
        /// <summary>Native row height for the font (Segoe UI 9 pt: 18 px at 96 DPI) unless set.</summary>
        public int ItemHeight { get; set; } = 18;
        public int Indent { get; set; } = 19;
        public bool ShowLines { get; set; } = true;
        public bool ShowRootLines { get; set; } = true;
        public bool ShowPlusMinus { get; set; } = true;
        public bool ShowNodeToolTips { get; set; }
        public bool HideSelection { get; set; } = true;
        public bool FullRowSelect { get; set; }
        public bool HotTracking { get; set; }
        public bool LabelEdit { get; set; }
        public bool CheckBoxes { get; set; }
        public bool Scrollable { get; set; } = true;
        public bool Sorted { get; set; }
        public string PathSeparator { get; set; } = "\\";
        public BorderStyle BorderStyle { get; set; } = BorderStyle.Fixed3D;
        public Color LineColor { get; set; } = Color.Black;
        public TreeViewDrawMode DrawMode { get; set; }
        public TreeNode EditingNode { get; private set; }

        public TreeNode SelectedNode
        {
            get => _selected;
            set => SetSelectedNode(value, TreeViewAction.Unknown);
        }
        internal void SetSelectedNode(TreeNode node, TreeViewAction action)
        {
            if (ReferenceEquals(_selected, node)) return;
            if (node != null)
            {
                var e = new TreeViewCancelEventArgs(node, false, action);
                OnBeforeSelect(e);
                if (e.Cancel) return;
                for (TreeNode p = node.Parent; p != null; p = p.Parent) p.Expand();
            }
            _selected = node;
            Notify("Tree");
            if (node != null) { ScrollIntoView(node); OnAfterSelect(new TreeViewEventArgs(node, action)); }
        }

        // Layout: one row per visible node, from TopNode down.
        internal List<TreeNode> VisibleRows()
        {
            var rows = new List<TreeNode>();
            void Add(TreeNodeCollection nodes) { foreach (TreeNode n in nodes) { rows.Add(n); if (n._expanded) Add(n.Nodes); } }
            Add(Nodes);
            return rows;
        }
        int RowsPerPage => Math.Max(1, (ClientSize.Height - 4) / Math.Max(1, ItemHeight));
        public TreeNode TopNode
        {
            get { var rows = VisibleRows(); return rows.Count == 0 ? null : rows[Math.Min(_topRow, rows.Count - 1)]; }
            set { int i = VisibleRows().IndexOf(value); if (i >= 0) SetTopRow(i); }
        }
        public int VisibleCount => RowsPerPage;
        public int TopRow => _topRow;
        /// <summary>Win32 GetScrollPos for the tree: SB_VERT is the top row; the model does not scroll horizontally.</summary>
        protected int NativeGetScrollPos(int bar) => bar == 1 ? _topRow : 0;
        void SetTopRow(int row)
        {
            int max = Math.Max(0, VisibleRows().Count - RowsPerPage);
            row = Math.Max(0, Math.Min(row, max));
            if (row == _topRow) return;
            _topRow = row;
            Notify("Tree");
        }
        internal void ScrollIntoView(TreeNode node)
        {
            int i = VisibleRows().IndexOf(node);
            if (i < 0) return;
            if (i < _topRow) SetTopRow(i);
            else if (i >= _topRow + RowsPerPage) SetTopRow(i - RowsPerPage + 1);
        }
        /// <summary>Left edge of the node's image (or label) cell: the indent per level, plus the root-line column.</summary>
        public int NodeIndentX(TreeNode node) => 2 + (node.Level + ((ShowRootLines || ShowPlusMinus) && (ShowLines || ShowPlusMinus) ? 1 : 0)) * Indent;
        public int ImageWidth => ImageList == null ? 0 : ImageList.ImageSize.Width + 3;
        internal Rectangle NodeBounds(TreeNode node)
        {
            int row = VisibleRows().IndexOf(node);
            if (row < 0) return Rectangle.Empty;
            Size text = TextRenderer.MeasureText(node.Text, node.NodeFont ?? Font);
            int x = NodeIndentX(node) + ImageWidth;
            return new Rectangle(x, 2 + (row - _topRow) * ItemHeight, text.Width + 6, ItemHeight);
        }
        public TreeNode GetNodeAt(Point point) => GetNodeAt(point.X, point.Y);
        /// <summary>Native TVM_HITTEST: the node of the row under the point (anywhere on the row).</summary>
        public TreeNode GetNodeAt(int x, int y)
        {
            if (y < 2) return null;
            int row = (y - 2) / ItemHeight + _topRow;
            var rows = VisibleRows();
            return row >= 0 && row < rows.Count && x >= 0 && x < ClientSize.Width ? rows[row] : null;
        }
        public TreeViewHitTestInfo HitTest(Point point) => HitTest(point.X, point.Y);
        public TreeViewHitTestInfo HitTest(int x, int y)
        {
            TreeNode node = GetNodeAt(x, y);
            if (node == null) return new TreeViewHitTestInfo(null, TreeViewHitTestLocations.None);
            int indent = NodeIndentX(node);
            if (x < indent - Indent) return new TreeViewHitTestInfo(node, TreeViewHitTestLocations.Indent);
            if (x < indent) return new TreeViewHitTestInfo(node, node.Nodes.Count > 0 && ShowPlusMinus ? TreeViewHitTestLocations.PlusMinus : TreeViewHitTestLocations.Indent);
            if (x < indent + ImageWidth) return new TreeViewHitTestInfo(node, TreeViewHitTestLocations.Image);
            return new TreeViewHitTestInfo(node, x < node.Bounds.Right ? TreeViewHitTestLocations.Label : TreeViewHitTestLocations.RightOfLabel);
        }
        public int GetNodeCount(bool includeSubTrees) => Nodes.Count + (includeSubTrees ? Nodes.Cast<TreeNode>().Sum(n => n.GetNodeCount(true)) : 0);
        public void ExpandAll() { foreach (TreeNode n in Nodes) n.ExpandAll(); }
        public void CollapseAll() { foreach (TreeNode n in Nodes) n.Collapse(); }
        public void BeginUpdate() => _updateCount++;
        public void EndUpdate() { if (_updateCount > 0 && --_updateCount == 0) Notify("Tree"); }
        public void Sort() { }
        internal void NodesChanged() { if (_updateCount == 0) Notify("Tree"); }
        internal void NodeRemoving(TreeNode node, TreeNode parent)
        {
            for (TreeNode n = _selected; n != null; n = n.Parent)
                if (n == node)
                {
                    // Native: removing the selected node (or its ancestor) selects a neighbour without BeforeSelect.
                    _selected = null;
                    break;
                }
            if (EditingNode != null) for (TreeNode n = EditingNode; n != null; n = n.Parent) if (n == node) { EditingNode = null; break; }
        }

        // Label editing (native: BeginEdit raises BeforeLabelEdit; the edit ends with AfterLabelEdit).
        internal void BeginEditNode(TreeNode node)
        {
            if (!LabelEdit) throw new InvalidOperationException("LabelEdit is not enabled on this TreeView.");
            var e = new NodeLabelEditEventArgs(node);
            OnBeforeLabelEdit(e);
            if (e.CancelEdit) return;
            EditingNode = node;
            Notify("TreeEdit");
        }
        internal void EndEditNode(bool cancel, string label)
        {
            TreeNode node = EditingNode;
            if (node == null) return;
            var e = new NodeLabelEditEventArgs(node, cancel ? null : label);
            EditingNode = null;
            OnAfterLabelEdit(e);
            if (!cancel && !e.CancelEdit && label != null) node.Text = label;
            Notify("TreeEdit");
        }

        public event TreeViewCancelEventHandler BeforeSelect, BeforeExpand, BeforeCollapse, BeforeCheck;
        public event TreeViewEventHandler AfterSelect, AfterExpand, AfterCollapse, AfterCheck;
        public event NodeLabelEditEventHandler BeforeLabelEdit, AfterLabelEdit;
        public event TreeNodeMouseClickEventHandler NodeMouseClick, NodeMouseDoubleClick;
        public event TreeNodeMouseHoverEventHandler NodeMouseHover;
        public event ItemDragEventHandler ItemDrag;
        public event DrawTreeNodeEventHandler DrawNode;

        protected virtual void OnBeforeSelect(TreeViewCancelEventArgs e) => BeforeSelect?.Invoke(this, e);
        protected virtual void OnAfterSelect(TreeViewEventArgs e) => AfterSelect?.Invoke(this, e);
        protected virtual void OnBeforeExpand(TreeViewCancelEventArgs e) => BeforeExpand?.Invoke(this, e);
        protected virtual void OnAfterExpand(TreeViewEventArgs e) => AfterExpand?.Invoke(this, e);
        protected virtual void OnBeforeCollapse(TreeViewCancelEventArgs e) => BeforeCollapse?.Invoke(this, e);
        protected virtual void OnAfterCollapse(TreeViewEventArgs e) => AfterCollapse?.Invoke(this, e);
        protected virtual void OnBeforeLabelEdit(NodeLabelEditEventArgs e) => BeforeLabelEdit?.Invoke(this, e);
        protected virtual void OnAfterLabelEdit(NodeLabelEditEventArgs e) => AfterLabelEdit?.Invoke(this, e);
        protected virtual void OnNodeMouseClick(TreeNodeMouseClickEventArgs e) => NodeMouseClick?.Invoke(this, e);
        protected virtual void OnNodeMouseDoubleClick(TreeNodeMouseClickEventArgs e) => NodeMouseDoubleClick?.Invoke(this, e);
        protected virtual void OnNodeMouseHover(TreeNodeMouseHoverEventArgs e) => NodeMouseHover?.Invoke(this, e);
        protected virtual void OnItemDrag(ItemDragEventArgs e) => ItemDrag?.Invoke(this, e);
        protected virtual void OnDrawNode(DrawTreeNodeEventArgs e) => DrawNode?.Invoke(this, e);
        internal void RaiseBeforeExpand(TreeViewCancelEventArgs e) => OnBeforeExpand(e);
        internal void RaiseAfterExpand(TreeViewEventArgs e) => OnAfterExpand(e);
        internal void RaiseBeforeCollapse(TreeViewCancelEventArgs e) => OnBeforeCollapse(e);
        internal void RaiseAfterCollapse(TreeViewEventArgs e) => OnAfterCollapse(e);

        // Renderer input, in the order the native control and WinForms raise them.
        /// <summary>Mouse press: MouseDown, then the native control toggles on +/- or selects the row's node
        /// (TVN_SELCHANGING → BeforeSelect, which CodersLabTreeView cancels to keep its own selection).</summary>
        public void UserMouseDown(MouseButtons button, int clicks, int x, int y)
        {
            Focus();
            Control.MouseButtons = button;
            OnMouseDown(new MouseEventArgs(button, clicks, x, y, 0));
            TreeViewHitTestInfo hit = HitTest(x, y);
            if (hit.Node == null) return;
            if (button == MouseButtons.Left && hit.Location == TreeViewHitTestLocations.PlusMinus) hit.Node.Toggle();
            else if (button == MouseButtons.Left && clicks == 1) SetSelectedNode(hit.Node, TreeViewAction.ByMouse);
        }
        /// <summary>Mouse release: NodeMouseClick (or NodeMouseDoubleClick and the native expand toggle on a
        /// double click), Click/MouseClick, then MouseUp.</summary>
        public void UserMouseUp(MouseButtons button, int clicks, int x, int y)
        {
            TreeViewHitTestInfo hit = HitTest(x, y);
            if (hit.Node != null && hit.Location != TreeViewHitTestLocations.None)
            {
                if (clicks == 2)
                {
                    OnNodeMouseDoubleClick(new TreeNodeMouseClickEventArgs(hit.Node, button, clicks, x, y));
                    OnDoubleClick(EventArgs.Empty);
                    OnMouseDoubleClick(new MouseEventArgs(button, clicks, x, y, 0));
                    if (button == MouseButtons.Left && hit.Location != TreeViewHitTestLocations.PlusMinus && hit.Node.Nodes.Count > 0) hit.Node.Toggle();
                }
                else OnNodeMouseClick(new TreeNodeMouseClickEventArgs(hit.Node, button, clicks, x, y));
            }
            if (clicks == 1) { OnClick(EventArgs.Empty); OnMouseClick(new MouseEventArgs(button, clicks, x, y, 0)); }
            OnMouseUp(new MouseEventArgs(button, clicks, x, y, 0));
            Control.MouseButtons = MouseButtons.None;
        }
        public void UserMouseMove(int x, int y) => OnMouseMove(new MouseEventArgs(Control.MouseButtons, 0, x, y, 0));
        public void UserScroll(int topRow) => SetTopRow(topRow);
        public void UserEndEdit(bool cancel, string label) => EndEditNode(cancel, label);
        /// <summary>Rows the renderer draws: node, row index from TopNode, label bounds.</summary>
        public TreeNode[] RenderRows() => VisibleRows().ToArray();
    }
}

namespace System.Windows.Forms
{
    /// <summary>Stand-in for the Graphics an original control creates to draw a focus rectangle over itself
    /// (GDI+ is Windows-only on .NET 10): the rectangle is recorded on the control and the renderer draws it.</summary>
    public sealed class FocusSurface
    {
        readonly Control _control;
        public FocusSurface(Control control) { _control = control; }
        public void DrawRectangle(Color color, Rectangle rect) => _control.SetFocusRectangle(color, rect);
        public void DrawRectangle(Color color, int x, int y, int width, int height) => _control.SetFocusRectangle(color, new Rectangle(x, y, width, height));
    }
}
