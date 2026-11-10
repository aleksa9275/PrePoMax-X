// Stand-ins for original UserControls types whose originals depend on Win32 internals.
// TabEnabledPropertyGrid: the original reaches the WinForms grid view through private reflection
// (label ratio, edit-control autocomplete); its public behaviour is reproduced here from
// UserControls/ProperyGrid/TabEnabledPropertyGrid.cs. ChildMouseWheelManagedForm only routes Win32
// wheel messages; the toolkit routes wheel events itself.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;

namespace UserControls
{
    public class ChildMouseWheelManagedForm : Form, IMessageFilter
    {
        public ChildMouseWheelManagedForm() { }
        public ChildMouseWheelManagedForm(bool start) { }
        public bool PreFilterMessage(ref Message m) => false;
    }

    public class TabEnabledPropertyGrid : PropertyGrid
    {
        bool _selectFirstProperty, _selectFirstCategory;
        public bool ReadOnly { get; set; }
        public bool FocusOnSelectedObjectChanged { get; set; } = true;
        public double LabelRatio { get; private set; } = 2.0;
        public string[] AutocompleteItems { get; private set; } = new string[0];

        public TabEnabledPropertyGrid()
        {
            LineColor = System.Drawing.SystemColors.Control;
            DisabledItemForeColor = System.Drawing.Color.FromArgb(80, 80, 80);
            SetSelectFirstProperty();
        }
        protected override void OnSelectedObjectsChanged(EventArgs e)
        {
            base.OnSelectedObjectsChanged(e);
            if (Parent?.FindForm() is Form form) form.KeyPreview = true;
            SelectFirstItem();
        }
        protected override void OnSelectedGridItemChanged(SelectedGridItemChangedEventArgs e)
        {
            if (ReadOnly && e.NewSelection?.GridItemType == GridItemType.Property)
            {
                for (GridItem item = e.NewSelection; item.Parent != null; item = item.Parent)
                    if (item.Parent.GridItemType == GridItemType.Category) { SelectedGridItem = item.Parent; return; }
            }
            base.OnSelectedGridItemChanged(e);
        }
        protected override void OnEnter(EventArgs e)
        {
            var root = Root;
            var first = root == null ? null : Flatten(root).Where(i => i.GridItemType != GridItemType.Root).FirstOrDefault();
            if (first != null && first.Expanded) SelectedGridItem = first;
            base.OnEnter(e);
        }
        public void SetLabelColumnWidth(double labelRatio) { LabelRatio = labelRatio; Notify("LabelRatio"); }
        public void SetSelectFirstByDefault() { _selectFirstProperty = false; _selectFirstCategory = false; }
        public void SetSelectFirstProperty() { _selectFirstProperty = true; _selectFirstCategory = false; }
        public void SetSelectFirstCategory() { _selectFirstProperty = false; _selectFirstCategory = true; }
        void SelectFirstItem()
        {
            if (_selectFirstProperty) SelectFirstVisibleProperty();
            else if (_selectFirstCategory) SelectFirstVisibleCategory();
            if (FocusOnSelectedObjectChanged) Focus();
        }
        public void SelectFirstVisibleProperty()
        {
            if (Root == null) return;
            foreach (GridItem category in Root.GridItems)
            {
                if (!category.Expanded) category.Expanded = true;
                foreach (GridItem item in category.GridItems) { SelectedGridItem = item; return; }
            }
        }
        public void SelectFirstVisibleCategory()
        {
            if (Root == null) return;
            foreach (GridItem category in Root.GridItems) { SelectedGridItem = category; return; }
        }
        /// <summary>Original: parameter names, NCalc constants (sorted) and function snippets.</summary>
        public void BuildAutocompleteMenu(IEnumerable<string> items)
        {
            var names = new List<string>(items ?? new string[0]);
            names.AddRange(CaeGlobals.MyNCalc.GetFunctionConstants());
            names.Sort();
            names.AddRange(CaeGlobals.MyNCalc.GetFunctionSnippets().Select(s => s.ToString()));
            AutocompleteItems = names.ToArray();
            Notify("Autocomplete");
        }
        /// <summary>Original Form_KeyDown Tab rule: the next property row (categories are skipped,
        /// expanded child rows included); returns false on the last row so focus leaves the grid.</summary>
        public bool SelectNextGridItem()
        {
            GridItem gridItem = SelectedGridItem;
            if (gridItem == null) return true;
            GridItem root = gridItem;
            while (root.GridItemType != GridItemType.Root) root = root.Parent;
            var gridItems = new List<GridItem>();
            FindItems(root, gridItems);
            int nextIndex = gridItems.IndexOf(gridItem) + 1;
            if (nextIndex >= gridItems.Count) return false;
            SelectedGridItem = gridItems[nextIndex];
            return true;
        }
        static void FindItems(GridItem item, List<GridItem> gridItems)
        {
            switch (item.GridItemType)
            {
                case GridItemType.Root:
                case GridItemType.Category:
                    foreach (GridItem i in item.GridItems) FindItems(i, gridItems);
                    break;
                case GridItemType.Property:
                    gridItems.Add(item);
                    if (item.Expanded) foreach (GridItem i in item.GridItems) FindItems(i, gridItems);
                    break;
            }
        }
    }
}

namespace System.Windows.Forms.Design
{
    public interface IWindowsFormsEditorService
    {
        void CloseDropDown();
        void DropDownControl(Control control);
        DialogResult ShowDialog(Form dialog);
    }
}
