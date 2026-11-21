// The WinForms PropertyGrid look (the successor of PropertyGridWidget in X/UI/original_forms.py): categorized rows, a
// value column, a help pane with the name and description. The model's grid items, texts, standard values and value
// conversions are the original type converters'; the "..." editors are the original UITypeEditors (file, folder and
// colour editors use the platform dialogs).
using System;
using System.Collections.Generic;
using System.ComponentModel;
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
    internal sealed class PropertyGridView : DockPanel, IMirror
    {
        const double RowHeight = 20;
        const string MissingValueTip = "Select at least one item.";   // UserControls/ProperyGrid/MySite.cs MissingValueToolTip
        static readonly Type MissingValues = Type.GetType("UserControls.IMissingPropertyValues, UserControls", false);
        static readonly IBrush CategoryBack = new SolidColorBrush(Color.FromRgb(0xF0, 0xF0, 0xF0));
        static readonly IBrush LineBrush = new SolidColorBrush(Color.FromRgb(0xE6, 0xE6, 0xE6));
        static readonly IBrush ReadOnlyText = new SolidColorBrush(Color.FromRgb(80, 80, 80));

        readonly WinForms.PropertyGrid _grid;
        readonly StackPanel _rows = new StackPanel();
        readonly ScrollViewer _scroll;
        readonly TextBlock _helpTitle = new TextBlock { FontWeight = FontWeight.Bold, TextTrimming = TextTrimming.CharacterEllipsis };
        readonly TextBlock _helpText = new TextBlock { TextWrapping = TextWrapping.Wrap };
        readonly Border _help;
        readonly Dictionary<string, Row> _byKey = new Dictionary<string, Row>();
        readonly List<Row> _ordered = new List<Row>();
        Row _selected;
        bool _updating;

        sealed class Row
        {
            public WinForms.GridItem Item;
            public string Key;
            public Border Visual;
            public Control Editor;
            public TextBlock Label;
        }

        public PropertyGridView(WinForms.PropertyGrid grid)
        {
            _grid = grid;
            LastChildFill = true;
            _help = new Border
            {
                Height = 4 * Look.FontSize + 14, BorderBrush = Look.LightFrame, BorderThickness = new Thickness(1), Padding = new Thickness(4, 2), Background = Look.Control,
                Child = new StackPanel { Children = { _helpTitle, _helpText } }, Margin = new Thickness(0, 3, 0, 0),
            };
            DockPanel.SetDock(_help, Dock.Bottom);
            Children.Add(_help);
            _scroll = new ScrollViewer { Content = _rows, HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled, VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                                         Background = Brushes.White };
            Children.Add(new Border { Child = _scroll, BorderBrush = Look.LightFrame, BorderThickness = new Thickness(1) });
            Rebuild();
        }

        internal int RowCount => _ordered.Count;
        internal string Describe() => (_grid.Root?.GridItems.Count ?? -1) + " root items, selected " + (_grid.SelectedObject?.GetType().Name ?? "none") + ", " + _ordered.Count + " rows";
        public void Update()
        {
            _help.IsVisible = _grid.HelpVisible;
            double width = LabelWidth();
            foreach (Row row in _ordered) if (row.Visual.Child is Grid g && g.ColumnDefinitions.Count == 2) g.ColumnDefinitions[0].Width = new GridLength(width);
        }

        public void Refresh(string property)
        {
            if (property == "SelectedGridItem" || property == "Selection") { SelectCurrent(); UpdateHelp(); return; }
            Rebuild();
        }

        double LabelWidth()
        {
            // TabEnabledPropertyGrid.SetLabelColumnWidth: the label ratio (default 2: half the width)
            double ratio = _grid is UserControls.TabEnabledPropertyGrid tab && tab.LabelRatio > 0 ? tab.LabelRatio : 2.0;
            double width = Bounds.Width > 0 ? Bounds.Width : _grid.Width;
            return Math.Max(40, (width - 16) / ratio);
        }

        static string KeyOf(WinForms.GridItem item)
        {
            var parts = new List<string>();
            for (; item != null && item.GridItemType != WinForms.GridItemType.Root; item = item.Parent) parts.Add(item.GridItemType + ":" + item.Label);
            parts.Reverse();
            return string.Join("/", parts);
        }

        void Rebuild()
        {
            // An edit in progress survives a rebuild (the model may refresh while the user types)
            string focusedKey = null, focusedText = null;
            if (_ordered.FirstOrDefault(r => r.Editor is TextBox t && t.IsFocused) is Row editing) { focusedKey = editing.Key; focusedText = ((TextBox)editing.Editor).Text; }
            double offset = _scroll.Offset.Y;
            _updating = true;
            try
            {
                _rows.Children.Clear();
                _byKey.Clear();
                _ordered.Clear();
                _selected = null;
                WinForms.GridItem root = _grid.Root;
                if (root != null) foreach (WinForms.GridItem child in root.GridItems) Add(child, 0);
                SelectCurrent();
            }
            finally { _updating = false; }
            Dispatcher.UIThread.Post(() => _scroll.Offset = new Vector(0, offset), DispatcherPriority.Loaded);
            if (focusedKey != null && _byKey.TryGetValue(focusedKey, out Row again) && again.Editor is TextBox box)
            {
                box.Text = focusedText;
                Dispatcher.UIThread.Post(() => { box.Focus(); box.CaretIndex = (box.Text ?? "").Length; });
            }
            UpdateHelp();
        }

        void Add(WinForms.GridItem item, int level)
        {
            var row = new Row { Item = item, Key = KeyOf(item) };
            _byKey[row.Key] = row;
            _ordered.Add(row);
            bool category = item.GridItemType == WinForms.GridItemType.Category;
            bool expandable = item.GridItems.Count > 0;
            var glyph = new TextBlock { Text = expandable ? (item.Expanded ? "▾" : "▸") : "", Width = 12, VerticalAlignment = VerticalAlignment.Center,
                                        TextAlignment = TextAlignment.Center, Cursor = expandable ? new Cursor(StandardCursorType.Hand) : null };
            if (expandable) glyph.PointerPressed += (s, e) => { var it = item; bool value = !it.Expanded; Ui.Input(() => _grid.SetExpanded(it, value)); e.Handled = true; };
            row.Label = new TextBlock { Text = Ui.Visible(item.Label), VerticalAlignment = VerticalAlignment.Center, TextTrimming = TextTrimming.CharacterEllipsis,
                                        FontWeight = category ? FontWeight.Bold : FontWeight.Normal };
            var head = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(2 + level * 12, 0, 0, 0), Children = { glyph } };
            var visual = new Border { Height = RowHeight, BorderBrush = LineBrush, BorderThickness = new Thickness(0, 0, 0, 1), Background = category ? CategoryBack : Brushes.White };
            row.Visual = visual;
            if (category)
            {
                head.Children.Add(row.Label);
                visual.Child = head;
            }
            else
            {
                bool missing = ValueMissing(item.PropertyDescriptor);
                if (missing)
                {
                    // 3.0.1 missing values (IMissingPropertyValues): the red dot with its tooltip and the value in red
                    head.Children.Add(new Avalonia.Controls.Shapes.Ellipse { Width = 7, Height = 7, Fill = Brushes.Red, Margin = new Thickness(0, 0, 3, 0), VerticalAlignment = VerticalAlignment.Center });
                    ToolTip.SetTip(visual, MissingValueTip);
                }
                head.Children.Add(row.Label);
                var line = new Grid { ColumnDefinitions = new ColumnDefinitions { new ColumnDefinition(new GridLength(LabelWidth())), new ColumnDefinition(GridLength.Star) } };
                line.Children.Add(new Border { Child = head, BorderBrush = LineBrush, BorderThickness = new Thickness(0, 0, 1, 0), ClipToBounds = true });
                row.Editor = ValueEditor(item, missing);
                Grid.SetColumn(row.Editor, 1);
                line.Children.Add(row.Editor);
                visual.Child = line;
            }
            visual.PointerPressed += (s, e) => Choose(row, false);
            _rows.Children.Add(visual);
            if (item.Expanded) foreach (WinForms.GridItem child in item.GridItems) Add(child, level + 1);
        }

        bool ValueMissing(PropertyDescriptor descriptor)
        {
            object selected = _grid.SelectedObject;
            if (selected == null || descriptor == null || MissingValues == null || !MissingValues.IsInstanceOfType(selected)) return false;
            return Ui.Guard(() => (bool)MissingValues.GetMethod("IsPropertyValueMissing").Invoke(selected, new object[] { descriptor.Name }));
        }

        static string EditorName(PropertyDescriptor descriptor)
        {
            var attribute = descriptor?.Attributes[typeof(EditorAttribute)] as EditorAttribute;
            if (attribute == null) return null;
            string name = attribute.EditorTypeName.Split(',')[0];
            return name.Substring(name.LastIndexOf('.') + 1);
        }

        Control ValueEditor(WinForms.GridItem item, bool missing)
        {
            string text = Ui.Guard(() => _grid.GetText(item)) ?? "";
            PropertyDescriptor descriptor = item.PropertyDescriptor;
            bool readOnly = descriptor == null || descriptor.IsReadOnly || _grid is UserControls.TabEnabledPropertyGrid tab && tab.ReadOnly;
            bool exclusive = false;
            string[] choices = Ui.Guard(() => _grid.GetStandardValues(item, out exclusive)) ?? new string[0];
            string editor = EditorName(descriptor);
            bool canEdit = Ui.Guard(() => _grid.CanEditText(item));
            IBrush fore = missing ? Brushes.Red : Brushes.Black;
            if (readOnly || !canEdit && choices.Length == 0 && editor == null)
                return new TextBlock { Text = text, Foreground = missing ? Brushes.Red : ReadOnlyText, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(4, 0),
                                       TextTrimming = TextTrimming.CharacterEllipsis };
            var panel = new DockPanel { LastChildFill = true };
            if (editor != null)
            {
                var button = new Button { Content = "…", Width = 20, Padding = new Thickness(0), Focusable = false };
                button.Click += (s, e) => EditModal(item, editor);
                DockPanel.SetDock(button, Dock.Right);
                panel.Children.Add(button);
            }
            if (choices.Length > 0 && exclusive)
            {
                var combo = new ComboBox { BorderThickness = new Thickness(0), Background = Brushes.Transparent, Foreground = fore, HorizontalAlignment = HorizontalAlignment.Stretch };
                var list = choices.ToList();
                if (!list.Contains(text)) list.Add(text);
                combo.ItemsSource = list;
                combo.SelectedIndex = list.IndexOf(text);
                combo.SelectionChanged += (s, e) => { if (!_updating && combo.SelectedItem is string value) Commit(item, value); };
                combo.GotFocus += (s, e) => Choose(item);
                panel.Children.Add(combo);
                return panel;
            }
            var box = new TextBox { Text = text, BorderThickness = new Thickness(0), Background = Brushes.Transparent, Foreground = fore, IsReadOnly = !canEdit,
                                    Padding = new Thickness(3, 0), VerticalContentAlignment = VerticalAlignment.Center };
            if (choices.Length > 0)
            {
                // Standard values that are not exclusive: the text or one of the values
                var drop = new Button { Content = "▾", Width = 18, Padding = new Thickness(0), Focusable = false };
                var flyout = new MenuFlyout();
                flyout.ItemsSource = choices.Select(c => { var entry = new MenuItem { Header = c }; entry.Click += (s, e) => Commit(item, c); return entry; }).ToList();
                drop.Flyout = flyout;
                DockPanel.SetDock(drop, Dock.Right);
                panel.Children.Add(drop);
            }
            box.GotFocus += (s, e) => Choose(item);
            box.LostFocus += (s, e) => Commit(item, box.Text ?? "");
            box.KeyDown += (s, e) =>
            {
                if (e.Key == Key.Enter) { Commit(item, box.Text ?? ""); e.Handled = true; }
                else if (e.Key == Key.Escape) { box.Text = Ui.Guard(() => _grid.GetText(item)) ?? ""; }
                else if (e.Key == Key.Tab && _grid is UserControls.TabEnabledPropertyGrid tab)
                {
                    // TabEnabledPropertyGrid: Tab moves to the next property row
                    Commit(item, box.Text ?? "");
                    if (Ui.Input(() => tab.SelectNextGridItem())) { Ui.Flush(); Dispatcher.UIThread.Post(FocusSelectedValue); e.Handled = true; }
                }
            };
            panel.Children.Add(box);
            return panel;
        }

        void FocusSelectedValue()
        {
            SelectCurrent();
            if (_selected?.Editor is Panel panel && panel.Children.OfType<TextBox>().FirstOrDefault() is TextBox box) { box.Focus(); box.SelectAll(); }
            else if (_selected?.Editor is Panel p && p.Children.OfType<ComboBox>().FirstOrDefault() is ComboBox combo) combo.Focus();
        }

        void Commit(WinForms.GridItem item, string text)
        {
            if (_updating) return;
            if ((Ui.Guard(() => _grid.GetText(item)) ?? "") == text) return;
            Ui.Input(() => _grid.SetValueFromText(item, text));
        }

        void Choose(WinForms.GridItem item) { if (_byKey.TryGetValue(KeyOf(item), out Row row)) Choose(row, true); }

        void Choose(Row row, bool fromEditor)
        {
            if (_updating) return;
            if (_grid.SelectedGridItem != row.Item) { var item = row.Item; Ui.Guard(() => _grid.SelectedGridItem = item); }
            Highlight(row);
            UpdateHelp();
        }

        void Highlight(Row row)
        {
            if (_selected != null && _selected.Label != null) { _selected.Label.Foreground = Brushes.Black; (_selected.Label.Parent?.Parent as Border ?? _selected.Label.Parent as Border)?.SetValue(Border.BackgroundProperty, null); }
            _selected = row;
            if (row?.Label != null && row.Item.GridItemType != WinForms.GridItemType.Category)
            {
                row.Label.Foreground = Brushes.White;
                if (row.Label.Parent?.Parent is Border labelCell) labelCell.Background = Look.Highlight;
            }
        }

        void SelectCurrent()
        {
            WinForms.GridItem selected = _grid.SelectedGridItem;
            Row row = selected != null && _byKey.TryGetValue(KeyOf(selected), out Row found) ? found : null;
            if (row != _selected) Highlight(row);
            if (row != null) row.Visual.BringIntoView();
        }

        void UpdateHelp()
        {
            WinForms.GridItem selected = _grid.SelectedGridItem;
            if (selected == null || selected.GridItemType == WinForms.GridItemType.Root) { _helpTitle.Text = ""; _helpText.Text = ""; return; }
            _helpTitle.Text = Ui.Visible(selected.Label);
            _helpText.Text = selected.PropertyDescriptor?.Description ?? "";
        }

        // The "..." editors ---------------------------------------------------------------------------------------------
        sealed class EditorService : System.Windows.Forms.Design.IWindowsFormsEditorService, IServiceProvider
        {
            public object GetService(Type serviceType) => serviceType == typeof(System.Windows.Forms.Design.IWindowsFormsEditorService) ? this : null;
            public void CloseDropDown() { }
            public void DropDownControl(WinForms.Control control) { }
            public WinForms.DialogResult ShowDialog(WinForms.Form dialog) => dialog.ShowDialog();
        }

        void EditModal(WinForms.GridItem item, string editor)
        {
            string current = Ui.Guard(() => _grid.GetText(item)) ?? "";
            string value = null;
            switch (editor)
            {
                case "FileNameEditor": case "FilteredFileNameEditor": value = Services.OpenFile(current, false); break;
                case "CreateFileNameEditor": value = Services.OpenFile(current, true); break;
                case "FolderNameEditor": value = Services.Folder(current); break;
                case "ColorEditorEx": case "ColorEditor": value = ColorPicker.Pick(current); break;
                default:
                    // The original UITypeEditor runs unchanged (e.g. EnvVarsUIEditor -> FrmGetEnvVars, SinglePointDataEditor)
                    Ui.Input(() =>
                    {
                        var attribute = (EditorAttribute)item.PropertyDescriptor.Attributes[typeof(EditorAttribute)];
                        string name = attribute.EditorTypeName.Split(',')[0];
                        Type type = AppDomain.CurrentDomain.GetAssemblies().Select(a => a.GetType(name, false)).FirstOrDefault(t => t != null) ?? throw new TypeLoadException(name);
                        var uiEditor = (System.Drawing.Design.UITypeEditor)Activator.CreateInstance(type, true);
                        var context = _grid.GetContext(item);
                        object old = item.PropertyDescriptor.GetValue(context.Instance);
                        object result = uiEditor.EditValue(context, new EditorService(), old);
                        if (!ReferenceEquals(result, old)) _grid.SetValue(item, result);
                    });
                    return;
            }
            if (value != null) Ui.Input(() => _grid.SetValueFromText(item, value));
        }
    }

    /// <summary>The colour editor: a small modal palette with the current colour (ARGB text as the original converter
    /// writes it, "A, R, G, B" or "R, G, B").</summary>
    internal static class ColorPicker
    {
        internal static string Pick(string current)
        {
            Color start = Colors.White;
            var parts = (current ?? "").Split(',').Select(p => p.Trim()).ToArray();
            if (parts.Length >= 3 && parts.All(p => byte.TryParse(p, out _)))
            {
                byte[] v = parts.Select(byte.Parse).ToArray();
                start = v.Length == 4 ? Color.FromArgb(v[0], v[1], v[2], v[3]) : Color.FromRgb(v[0], v[1], v[2]);
            }
            var view = new ColorView { Color = start, IsAlphaVisible = true, Width = 520, Height = 400 };
            var ok = new Button { Content = "OK", Width = 75, IsDefault = true };
            var cancel = new Button { Content = "Cancel", Width = 75, IsCancel = true };
            var window = new Window { Title = "Color", SizeToContent = SizeToContent.WidthAndHeight, CanResize = false, WindowStartupLocation = WindowStartupLocation.CenterOwner,
                                      Content = new StackPanel { Margin = new Thickness(10), Spacing = 8, Children = { view,
                                          new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Spacing = 8, Children = { ok, cancel } } } } };
            bool accepted = false;
            ok.Click += (s, e) => { accepted = true; window.Close(); };
            cancel.Click += (s, e) => window.Close();
            using (var done = new System.Threading.CancellationTokenSource())
            {
                window.Closed += (s, e) => done.Cancel();
                Window owner = Services.ActiveWindow();
                if (owner != null) window.ShowDialog(owner); else window.Show();
                Dispatcher.UIThread.MainLoop(done.Token);
            }
            if (!accepted) return null;
            Color c = view.Color;
            return c.A + ", " + c.R + ", " + c.G + ", " + c.B;
        }
    }
}
