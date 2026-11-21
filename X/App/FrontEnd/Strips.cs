// Menu strips, tool strips, status strips and context menus: their items are the original ToolStripItems (the
// successor of StripWidget/MenuWidget in X/UI/main_form.py). A drop-down raises DropDownOpening before its items are
// shown (the original handlers enable and fill them there); clicks are PerformClick.
using System;
using System.Collections.Generic;
using System.Linq;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Layout;
using Avalonia.Media;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEnd
{
    /// <summary>Menu entries of ToolStripItems, shared by the menu strip, drop-down buttons and context menus.</summary>
    internal static class MenuEntries
    {
        internal static List<object> Build(IEnumerable<WinForms.ToolStripItem> items, Action closed = null)
        {
            var entries = new List<object>();
            foreach (WinForms.ToolStripItem item in items)
            {
                if (!item.Visible) continue;
                if (item is WinForms.ToolStripSeparator) { if (entries.Count > 0 && !(entries[entries.Count - 1] is Separator)) entries.Add(new Separator()); continue; }
                entries.Add(Entry(item));
            }
            while (entries.Count > 0 && entries[entries.Count - 1] is Separator) entries.RemoveAt(entries.Count - 1);
            return entries;
        }

        internal static MenuItem Entry(WinForms.ToolStripItem item)
        {
            var entry = new MenuItem { Header = Ui.AccessText(item.Text), IsEnabled = item.Enabled, Icon = Ui.Icon(item.Image), Tag = item };
            if (item is WinForms.ToolStripMenuItem menuItem)
            {
                if (menuItem.CheckOnClick || menuItem.Checked) { entry.ToggleType = MenuItemToggleType.CheckBox; entry.IsChecked = menuItem.Checked; }
                if (menuItem.ShowShortcutKeys) entry.InputGesture = Keyboard.Gesture(menuItem.ShortcutKeys);
            }
            if (item is WinForms.ToolStripDropDownItem drop && drop.HasDropDownItems)
            {
                // Filled when it opens, after DropDownOpening (the original enables and fills the items there)
                entry.ItemsSource = new object[] { new MenuItem { Header = "" } };
                entry.SubmenuOpened += (s, e) =>
                {
                    if (e.Source != entry) return;
                    Ui.Input(drop.RaiseDropDownOpening);
                    entry.ItemsSource = Build(drop.DropDownItems.Cast<WinForms.ToolStripItem>());
                };
                entry.PropertyChanged += (s, e) =>
                {
                    if (e.Property == MenuItem.IsSubMenuOpenProperty && e.NewValue is false) Ui.Input(drop.RaiseDropDownClosed);
                };
            }
            else entry.Click += (s, e) => { if (item.Enabled) Ui.Input(item.PerformClick); };
            return entry;
        }
    }

    /// <summary>The main menu (MenuStrip) as an Avalonia menu bar in the window, where the original layout places it.</summary>
    internal sealed class MenuStripView : Menu, IMirror
    {
        protected override Type StyleKeyOverride => typeof(Menu);
        readonly WinForms.MenuStrip _strip;
        List<WinForms.ToolStripItem> _items = new List<WinForms.ToolStripItem>();
        readonly List<MenuItem> _entries = new List<MenuItem>();

        public MenuStripView(WinForms.MenuStrip strip) { _strip = strip; Background = Look.Window; Update(); }

        public void Update()
        {
            var items = _strip.Items.Cast<WinForms.ToolStripItem>().ToList();
            if (!items.SequenceEqual(_items))
            {
                _items = items;
                _entries.Clear();
                foreach (var item in items)
                {
                    MenuItem entry = MenuEntries.Entry(item);
                    entry.Padding = new Thickness(7, 2);
                    _entries.Add(entry);
                }
                ItemsSource = _entries.ToList();
            }
            for (int i = 0; i < _items.Count; i++)
            {
                _entries[i].IsEnabled = _items[i].Enabled;
                _entries[i].IsVisible = _items[i].Visible;
                string header = Ui.AccessText(_items[i].Text);
                if (!Equals(_entries[i].Header, header)) _entries[i].Header = header;
            }
        }
        public void Refresh(string property) => Update();
    }

    /// <summary>A ToolStrip or StatusStrip: its items in a row, updated when an item changes.</summary>
    internal sealed class ToolStripView : Border, IMirror
    {
        readonly WinForms.ToolStrip _strip;
        readonly bool _status;
        readonly Grid _row = new Grid();
        List<WinForms.ToolStripItem> _items = new List<WinForms.ToolStripItem>();
        readonly List<(WinForms.ToolStripItem Item, Control Visual, Action Update)> _entries = new List<(WinForms.ToolStripItem, Control, Action)>();

        public ToolStripView(WinForms.ToolStrip strip)
        {
            _strip = strip;
            _status = strip is WinForms.StatusStrip;
            Child = _row;
            Background = _status ? Look.Control : Look.Control;
            if (_status) { BorderBrush = Look.LightFrame; BorderThickness = new Thickness(0, 1, 0, 0); }
            Update();
        }

        public void Refresh(string property) => Update();

        public void Update()
        {
            var items = _strip.Items.Cast<WinForms.ToolStripItem>().ToList();
            if (!items.SequenceEqual(_items))
            {
                _items = items;
                _entries.Clear();
                _row.Children.Clear();
                _row.ColumnDefinitions.Clear();
                foreach (var item in items)
                {
                    var (visual, update) = Create(item);
                    bool spring = item is WinForms.ToolStripStatusLabel s && s.Spring;
                    _row.ColumnDefinitions.Add(new ColumnDefinition(spring ? GridLength.Star : GridLength.Auto));
                    Grid.SetColumn(visual, _row.Children.Count);
                    visual.VerticalAlignment = VerticalAlignment.Center;
                    _row.Children.Add(visual);
                    _entries.Add((item, visual, update));
                }
                if (!_status) _row.ColumnDefinitions.Add(new ColumnDefinition(GridLength.Star));
            }
            foreach (var (item, visual, update) in _entries)
            {
                visual.IsVisible = item.Visible;
                visual.IsEnabled = item.Enabled;
                update?.Invoke();
            }
        }

        static void Tip(Control control, WinForms.ToolStripItem item)
        {
            string tip = string.IsNullOrEmpty(item.ToolTipText) ? Ui.Visible(item.Text).Replace("&", "") : item.ToolTipText;
            ToolTip.SetTip(control, string.IsNullOrEmpty(tip) ? null : tip);
        }

        (Control, Action) Create(WinForms.ToolStripItem item)
        {
            switch (item)
            {
                case WinForms.ToolStripSeparator _:
                    return (new Border { Width = 1, Height = 18, Margin = new Thickness(3, 0), Background = Look.ButtonBorder }, null);
                case WinForms.ToolStripComboBox combo:
                {
                    var box = new ComboBox { Height = 21, MaxDropDownHeight = 400, Margin = new Thickness(1, 0) };
                    bool syncing = false;
                    List<string> shown = new List<string>();
                    box.SelectionChanged += (s, e) =>
                    {
                        if (syncing || box.SelectedIndex < 0) return;
                        int index = box.SelectedIndex;
                        Ui.Input(() => combo.ComboBox.RaiseSelectionChangeCommitted(index));
                    };
                    return (box, () =>
                    {
                        syncing = true;
                        try
                        {
                            var texts = combo.Items.Cast<object>().Select(o => o?.ToString() ?? "").ToList();
                            if (!texts.SequenceEqual(shown)) { shown = texts; box.ItemsSource = texts; }
                            if (box.SelectedIndex != combo.SelectedIndex) box.SelectedIndex = combo.SelectedIndex;
                            box.Width = Math.Max(40, combo.Size.Width);
                            Tip(box, item);
                        }
                        finally { syncing = false; }
                    });
                }
                case WinForms.ToolStripTextBox text:
                {
                    var box = new TextBox { Height = 21, Margin = new Thickness(1, 0), VerticalContentAlignment = VerticalAlignment.Center };
                    void Commit() { string value = box.Text ?? ""; if (value != text.Text) Ui.Input(() => text.TextBox.SetUserText(value)); }
                    box.LostFocus += (s, e) => { Commit(); Ui.Input(text.TextBox.RaiseLeave); };
                    box.GotFocus += (s, e) => Ui.Input(text.TextBox.RaiseEnter);
                    box.KeyDown += (s, e) =>
                    {
                        if (e.Key != Key.Enter && e.Key != Key.Escape) return;
                        Commit();
                        var keys = Keyboard.Keys(e);
                        Ui.Input(() => { text.TextBox.RaiseKeyDown(keys); text.TextBox.RaiseKeyUp(keys); });
                        e.Handled = true;
                    };
                    return (box, () =>
                    {
                        if (!box.IsFocused && box.Text != text.Text) box.Text = text.Text;
                        box.IsReadOnly = text.ReadOnly;
                        box.Width = Math.Max(30, text.Size.Width);
                        Tip(box, item);
                    });
                }
                case WinForms.ToolStripProgressBar progress:
                {
                    var bar = new ProgressBar { Height = 14, Margin = new Thickness(4, 0) };
                    return (bar, () =>
                    {
                        bar.Width = Math.Max(60, progress.Size.Width);
                        bar.IsIndeterminate = progress.Style == WinForms.ProgressBarStyle.Marquee;
                        bar.Minimum = progress.Minimum; bar.Maximum = progress.Maximum; bar.Value = progress.Value;
                    });
                }
                case WinForms.ToolStripLabel label:
                {
                    var block = new TextBlock { Margin = new Thickness(4, 0), VerticalAlignment = VerticalAlignment.Center, TextTrimming = TextTrimming.CharacterEllipsis };
                    var holder = new Border { Child = block, Background = Brushes.Transparent };
                    holder.PointerReleased += (s, e) => Ui.Input(label.PerformClick);
                    return (holder, () =>
                    {
                        if (block.Text != label.Text) block.Text = label.Text;
                        block.Foreground = label.Enabled ? (label.ForeColor == System.Drawing.SystemColors.ControlText ? Brushes.Black : Ui.Brush(label.ForeColor)) : Look.GrayText;
                        Tip(holder, item);
                    });
                }
                default:
                    return ToolButton(item);
            }
        }

        /// <summary>A tool button: an icon (or text), the checked face of a checked button, a drop-down of its items.</summary>
        (Control, Action) ToolButton(WinForms.ToolStripItem item)
        {
            var drop = item as WinForms.ToolStripDropDownItem;
            ContentControl button;
            if (drop != null && drop.HasDropDownItems)
            {
                var flyout = new MenuFlyout { Placement = PlacementMode.BottomEdgeAlignedLeft };
                flyout.Opening += (s, e) =>
                {
                    Ui.Input(drop.RaiseDropDownOpening);
                    flyout.ItemsSource = MenuEntries.Build(drop.DropDownItems.Cast<WinForms.ToolStripItem>());
                };
                flyout.Closed += (s, e) => Ui.Input(drop.RaiseDropDownClosed);
                var b = new Button { Classes = { "tool" }, Flyout = flyout };
                button = b;
            }
            else
            {
                var toggle = new ToggleButton { Classes = { "tool" } };
                // The model decides the state (CheckOnClick, the original handlers); the sync shows it
                toggle.IsCheckedChanged += (s, e) => { };
                toggle.Click += (s, e) => { Ui.Input(item.PerformClick); toggle.IsChecked = Checked(item); };
                button = toggle;
            }
            button.Focusable = false;
            button.Height = 23;
            System.Drawing.Image image = null;
            string text = null;
            return (button, () =>
            {
                if (image != item.Image || text != item.Text)
                {
                    image = item.Image; text = item.Text;
                    Image icon = item.DisplayStyle == WinForms.ToolStripItemDisplayStyle.Text ? null : Ui.Icon(image);
                    bool showText = icon == null || item.DisplayStyle == WinForms.ToolStripItemDisplayStyle.ImageAndText &&
                                    item.TextImageRelation != WinForms.TextImageRelation.Overlay && !string.IsNullOrEmpty(text);
                    if (icon != null && !showText) button.Content = icon;
                    else if (icon != null)
                    {
                        var row = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 3 };
                        row.Children.Add(icon); row.Children.Add(new TextBlock { Text = Ui.Visible(text).Replace("&", ""), VerticalAlignment = VerticalAlignment.Center });
                        button.Content = row;
                    }
                    else button.Content = new TextBlock { Text = Ui.Visible(text).Replace("&", ""), VerticalAlignment = VerticalAlignment.Center };
                    Tip(button, item);
                }
                if (button is ToggleButton toggle && toggle.IsChecked != Checked(item)) toggle.IsChecked = Checked(item);
            });
        }

        static bool Checked(WinForms.ToolStripItem item) =>
            item is WinForms.ToolStripButton b ? b.Checked : item is WinForms.ToolStripMenuItem m && m.Checked;
    }

    /// <summary>The context menus the original shows (ContextMenuStrip.Show on a control): Opening, then its visible
    /// items at the point it gives, in the control's units.</summary>
    internal static class ContextMenus
    {
        static readonly Dictionary<WinForms.ToolStripDropDown, ContextMenu> s_open = new Dictionary<WinForms.ToolStripDropDown, ContextMenu>();

        internal static void Show(WinForms.ToolStripDropDown strip)
        {
            if (s_open.ContainsKey(strip)) return;
            WinForms.Control source = strip.SourceControl;
            FormWindow window = source?.FindForm() is WinForms.Form form && Ui.Windows.TryGetValue(form, out FormWindow w) ? w : Ui.Main;
            Control target = source != null ? window?.VisualOf(source) : null;
            target = target ?? (Control)window?.Content;
            if (target == null) return;
            if (strip is WinForms.ContextMenuStrip context && !Ui.Input(() => context.OpenFor(source))) { Ui.Guard(() => strip.Close(WinForms.ToolStripDropDownCloseReason.CloseCalled)); return; }
            bool clicked = false;
            var menu = new ContextMenu
            {
                ItemsSource = MenuEntries.Build(strip.Items.Cast<WinForms.ToolStripItem>()),
                Placement = PlacementMode.AnchorAndGravity, PlacementAnchor = Avalonia.Controls.Primitives.PopupPositioning.PopupAnchor.TopLeft,
                PlacementGravity = Avalonia.Controls.Primitives.PopupPositioning.PopupGravity.BottomRight,
            };
            var at = strip.ShownAt;
            menu.PlacementRect = source != null ? new Rect(at.X, at.Y, 1, 1) : new Rect(0, 0, 1, 1);
            menu.AddHandler(MenuItem.ClickEvent, (s, e) => clicked = true, RoutingStrategies.Bubble, true);
            menu.Closed += (s, e) =>
            {
                s_open.Remove(strip);
                var reason = clicked ? WinForms.ToolStripDropDownCloseReason.ItemClicked : WinForms.ToolStripDropDownCloseReason.AppClicked;
                Ui.Input(() => strip.Close(reason));
            };
            s_open[strip] = menu;
            menu.Open(target);
        }

        internal static void Close(WinForms.ToolStripDropDown strip)
        {
            if (s_open.TryGetValue(strip, out ContextMenu menu)) { s_open.Remove(strip); menu.Close(); }
        }
    }

    /// <summary>The main menu's shortcuts (ToolStripMenuItem.ShortcutKeys) work while the menus are closed, as in WinForms.</summary>
    internal static class Shortcuts
    {
        static readonly Dictionary<WinForms.Keys, List<WinForms.ToolStripMenuItem>> s_items = new Dictionary<WinForms.Keys, List<WinForms.ToolStripMenuItem>>();
        static IEnumerable<WinForms.ToolStripItem> Walk(IEnumerable<WinForms.ToolStripItem> items)
        {
            foreach (var item in items)
            {
                yield return item;
                if (item is WinForms.ToolStripDropDownItem drop)
                    foreach (var child in Walk(drop.DropDownItems.Cast<WinForms.ToolStripItem>())) yield return child;
            }
        }
        internal static void Install(FormWindow window)
        {
            s_items.Clear();
            WinForms.MenuStrip menu = window.Form.MainMenuStrip;
            if (menu == null) return;
            foreach (var item in Walk(menu.Items.Cast<WinForms.ToolStripItem>()).OfType<WinForms.ToolStripMenuItem>())
            {
                if (item.ShortcutKeys == WinForms.Keys.None) continue;
                if (!s_items.TryGetValue(item.ShortcutKeys, out var list)) s_items[item.ShortcutKeys] = list = new List<WinForms.ToolStripMenuItem>();
                list.Add(item);
            }
        }
        internal static bool Handle(WinForms.Form form, WinForms.Keys keys)
        {
            if (!s_items.TryGetValue(keys, out var items)) return false;
            // A shortcut of an item that is enabled when its menu opens (the original enables items in DropDownOpening)
            foreach (var item in items)
            {
                if (item.OwnerItem is WinForms.ToolStripDropDownItem owner) Ui.Guard(owner.RaiseDropDownOpening);
                if (item.Enabled) { Ui.Input(item.PerformClick); return true; }
            }
            return false;
        }
    }
}
