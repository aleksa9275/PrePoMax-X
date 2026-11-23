// The Avalonia control of each original control kind (the successor of FormWindow.create in X/UI/original_forms.py).
// Every input goes to the original control through the events WinForms raises; the state is read back on each sync.
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
    internal static class Controls
    {
        internal readonly struct Created
        {
            public readonly Control Visual;
            public readonly IMirror Content;
            public readonly bool Leaf, Above;
            public Created(Control visual, IMirror content = null, bool leaf = false, bool above = false) { Visual = visual; Content = content; Leaf = leaf; Above = above; }
        }

        sealed class Updater : IMirror
        {
            readonly Action _update;
            readonly Action<string> _refresh;
            public Updater(Action update, Action<string> refresh = null) { _update = update; _refresh = refresh; }
            public void Update() => _update?.Invoke();
            public void Refresh(string property) => _refresh?.Invoke(property);
        }

        static Created Leaf(Control visual, Action update = null, Action<string> refresh = null) =>
            new Created(visual, update != null || refresh != null ? new Updater(update, refresh) : null, true);

        internal static Created Create(FormWindow window, WinForms.Control control)
        {
            switch (control)
            {
                case vtkControl.vtkControl view: return new Created(new ViewHost(view), null, true);
                case WinForms.MenuStrip menu: return new Created(new MenuStripView(menu), null, true);
                case WinForms.ToolStrip strip: return new Created(new ToolStripView(strip), null, true);
                case WinForms.ToolStripPanel panel when window != null && window.IsMain && panel.Parent is WinForms.ToolStripContainer container
                                                         && container.TopToolStripPanel == panel:
                    return TopToolStripPanel(panel);
                case WinForms.PropertyGrid grid: return new Created(new PropertyGridView(grid), null, true);
                case WinForms.ListView list: return new Created(new ListViewView(list), null, true);
                case WinForms.DataGridView grid: return new Created(new DataGridView(grid), null, true);
                case ZedGraph.ZedGraphControl graph: return new Created(new GraphView(graph), null, true);
                case WinForms.TreeView tree: return new Created(new TreeViewView(tree), null, true);
                case FastColoredTextBoxNS.FastColoredTextBox code: return new Created(new CodeView(code), null, true);
                case WinForms.SplitContainer split: return SplitContainer(split);
                case WinForms.TrackBar track: return TrackBar(track);
                case WinForms.ScrollBar bar: return ScrollBar(bar);
                case WinForms.ProgressBar progress: return ProgressBar(progress);
                case WinForms.PictureBox picture: return PictureBox(picture);
                case WinForms.LinkLabel link: return LinkLabel(link);
                case WinForms.TextBoxBase text: return TextBox(text);
                case WinForms.GroupBox group: return GroupBox(group);
                case WinForms.CheckBox check: return CheckBox(check);
                case WinForms.RadioButton radio: return RadioButton(radio);
                case WinForms.ButtonBase button: return Button(button);
                case WinForms.Label label: return Label(label);
                case WinForms.ComboBox combo: return ComboBox(combo);
                case WinForms.NumericUpDown number: return NumericUpDown(number);
                case WinForms.TabControl tabs: return TabControl(tabs);
            }
            // Panels and containers; a control with a Paint handler shows its own painting below its children
            if (control.HasPaintHandler) return new Created(new PaintedView(control));
            return Container(control);
        }

        static IBrush BackOf(WinForms.Control control) =>
            control.BackColor.A == 0 || control.BackColor == System.Drawing.SystemColors.Control ? null : Ui.Brush(control.BackColor);
        static IBrush ForeOf(WinForms.Control control) =>
            control.ForeColor == System.Drawing.SystemColors.ControlText ? null : Ui.Fore(control.ForeColor);

        static Created Container(WinForms.Control control)
        {
            var border = new Border();
            WinForms.BorderStyle style = control is WinForms.Panel panel ? panel.BorderStyle : control is WinForms.UserControl user ? user.BorderStyle : WinForms.BorderStyle.None;
            if (style != WinForms.BorderStyle.None) { border.BorderBrush = style == WinForms.BorderStyle.FixedSingle ? Look.Frame : Look.ButtonBorder; border.BorderThickness = new Thickness(1); }
            return new Created(border, new Updater(() => border.Background = BackOf(control)));
        }

        /// <summary>The main window's top tool strip panel, with the appearance toggle at the right end of its first row
        /// (behind the strips, which leave that end free).</summary>
        static Created TopToolStripPanel(WinForms.ToolStripPanel panel)
        {
            var grid = new Grid();
            var toggle = new AppearanceToggle();
            grid.Children.Add(toggle);
            return new Created(grid, new Updater(() =>
            {
                grid.Background = BackOf(panel);
                int top = int.MaxValue, height = 0;
                foreach (WinForms.Control strip in panel.Controls)
                    if (strip.Visible && strip.Top <= top) { height = strip.Top < top ? strip.Height : Math.Max(height, strip.Height); top = strip.Top; }
                toggle.Height = height > 0 ? height : 25;
            }));
        }

        // Buttons -------------------------------------------------------------------------------------------------------
        static object Content(string text, System.Drawing.Image image, bool mnemonic = true)
        {
            Image icon = Ui.Icon(image, image != null && image.Width > 0 ? Math.Min(32, image.Width) : 16);
            string shown = mnemonic ? Ui.AccessText(text) : text;
            if (icon == null) return new AccessText { Text = shown };
            if (string.IsNullOrEmpty(text)) return icon;
            var row = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 4 };
            row.Children.Add(icon);
            row.Children.Add(new AccessText { Text = shown, VerticalAlignment = VerticalAlignment.Center });
            return row;
        }

        static Created Button(WinForms.ButtonBase control)
        {
            var button = new Button { Focusable = true };
            button.Click += (s, e) => Ui.Input(control.RaiseClick);
            string text = null;
            return Leaf(button, () =>
            {
                if (text == control.Text) return;
                text = control.Text;
                button.Content = Content(text, control.Image, control.UseMnemonic);
                if (control.FlatStyle == WinForms.FlatStyle.Flat && control.FlatAppearance.BorderSize == 0) button.BorderThickness = new Thickness(0);
            });
        }

        static Created CheckBox(WinForms.CheckBox control)
        {
            ToggleButton box = control.Appearance == WinForms.Appearance.Button ? new ToggleButton { Classes = { "tool" } } : new CheckBox();
            box.IsThreeState = false;
            bool syncing = false;
            box.Click += (s, e) => { if (!syncing) Ui.Input(control.RaiseClick); };
            string text = null;
            return Leaf(box, () =>
            {
                syncing = true;
                try
                {
                    if (box.IsChecked != control.Checked) box.IsChecked = control.Checked;
                    if (text != control.Text) { text = control.Text; box.Content = Content(text, control.Image); }
                    if (ForeOf(control) is IBrush fore) box.Foreground = fore;
                }
                finally { syncing = false; }
            });
        }

        static Created RadioButton(WinForms.RadioButton control)
        {
            // The model checks and unchecks the group (RaiseClick): each Avalonia button is a group of its own
            var radio = new RadioButton { GroupName = "radio" + System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(control) };
            bool syncing = false;
            radio.Click += (s, e) => { if (!syncing) Ui.Input(control.RaiseClick); };
            string text = null;
            return Leaf(radio, () =>
            {
                syncing = true;
                try
                {
                    if (radio.IsChecked != control.Checked) radio.IsChecked = control.Checked;
                    if (text != control.Text) { text = control.Text; radio.Content = Content(text, control.Image); }
                }
                finally { syncing = false; }
            });
        }

        // Text ------------------------------------------------------------------------------------------------------------
        static Created Label(WinForms.Label control)
        {
            var block = new TextBlock { TextWrapping = control.AutoSize ? TextWrapping.NoWrap : TextWrapping.Wrap,
                                        TextTrimming = control.AutoEllipsis ? TextTrimming.CharacterEllipsis : TextTrimming.None };
            var border = new Border { Child = block };
            if (control.BorderStyle != WinForms.BorderStyle.None) { border.BorderBrush = Look.ButtonBorder; border.BorderThickness = new Thickness(1); }
            int align = (int)control.TextAlign;
            // ContentAlignment: 1/2/4 top, 16/32/64 middle, 256/512/1024 bottom (left, centre, right)
            block.VerticalAlignment = align < 16 ? VerticalAlignment.Top : align < 256 ? VerticalAlignment.Center : VerticalAlignment.Bottom;
            int column = align < 16 ? align : align < 256 ? align >> 4 : align >> 8;
            block.TextAlignment = column == 2 ? TextAlignment.Center : column == 4 ? TextAlignment.Right : TextAlignment.Left;
            block.HorizontalAlignment = HorizontalAlignment.Stretch;
            return Leaf(border, () =>
            {
                string text = control.UseMnemonic ? (control.Text ?? "").Replace("&&", "\u0001").Replace("&", "").Replace("\u0001", "&") : control.Text;
                if (block.Text != text) block.Text = text;
                block.Foreground = ForeOf(control) ?? (control.Enabled ? Look.Text : Look.GrayText);
                border.Background = BackOf(control);
            });
        }

        static Created LinkLabel(WinForms.LinkLabel control)
        {
            var block = new TextBlock { Foreground = Ui.Fore(control.LinkColor), TextDecorations = TextDecorations.Underline, Cursor = new Cursor(StandardCursorType.Hand) };
            block.PointerReleased += (s, e) => Ui.Input(control.RaiseLinkClicked);
            return Leaf(block, () => block.Text = control.Text);
        }

        static Created TextBox(WinForms.TextBoxBase control)
        {
            var box = new TextBox
            {
                AcceptsReturn = control.Multiline, AcceptsTab = control is WinForms.TextBox t && t.AcceptsTab,
                TextWrapping = control.Multiline && control.WordWrap ? TextWrapping.Wrap : TextWrapping.NoWrap,
            };
            if (control is WinForms.TextBox plain)
            {
                if (plain.PasswordChar != '\0') box.PasswordChar = plain.PasswordChar;
                box.TextAlignment = plain.TextAlign == WinForms.HorizontalAlignment.Right ? TextAlignment.Right : plain.TextAlign == WinForms.HorizontalAlignment.Center ? TextAlignment.Center : TextAlignment.Left;
            }
            if (control.BorderStyle == WinForms.BorderStyle.None) box.BorderThickness = new Thickness(0);
            if (control.Multiline) ScrollViewer.SetVerticalScrollBarVisibility(box, Avalonia.Controls.Primitives.ScrollBarVisibility.Auto);
            string Normal(string s) => (s ?? "").Replace("\r\n", "\n");
            void Commit()
            {
                string text = control.Multiline ? (box.Text ?? "").Replace("\n", Environment.NewLine) : box.Text ?? "";
                if (Normal(text) != Normal(control.Text)) Ui.Input(() => { if (control is WinForms.TextBox tb) tb.SetUserText(text); else control.Text = text; });
            }
            box.LostFocus += (s, e) => Commit();
            box.KeyDown += (s, e) =>
            {
                if (e.Key == Key.Enter && !control.Multiline)
                {
                    // WinForms: Enter in a text box is a key of the control (KeyDown/KeyUp handlers commit values)
                    Commit();
                    Ui.Input(() => { control.RaiseKeyDown(WinForms.Keys.Enter); control.RaiseKeyUp(WinForms.Keys.Enter); });
                }
                else if (e.Key == Key.Escape || e.Key == Key.Up || e.Key == Key.Down)
                    Ui.Input(() => control.RaiseKeyDown(Keyboard.Keys(e)));
            };
            return Leaf(box, () =>
            {
                box.IsReadOnly = control.ReadOnly;
                if (box.IsFocused) return;
                string text = Normal(control.Text);
                if (box.Text == text) return;
                bool atEnd = (box.CaretIndex >= (box.Text ?? "").Length);
                box.Text = text;
                if (control.Multiline && atEnd) box.CaretIndex = text.Length;
            }, property => { if (property == "ScrollToEnd") box.CaretIndex = (box.Text ?? "").Length; });
        }

        static Created ComboBox(WinForms.ComboBox control)
        {
            var combo = new ComboBox { MaxDropDownHeight = 400 };
            bool syncing = false;
            List<string> shown = new List<string>();
            combo.SelectionChanged += (s, e) =>
            {
                if (syncing || combo.SelectedIndex < 0) return;
                int index = combo.SelectedIndex;
                Ui.Input(() => control.RaiseSelectionChangeCommitted(index));
            };
            return Leaf(combo, () =>
            {
                syncing = true;
                try
                {
                    var texts = control.Items.Cast<object>().Select(i => i?.ToString() ?? "").ToList();
                    if (!texts.SequenceEqual(shown)) { shown = texts; combo.ItemsSource = texts; }
                    if (combo.SelectedIndex != control.SelectedIndex) combo.SelectedIndex = control.SelectedIndex;
                }
                finally { syncing = false; }
            });
        }

        static Created NumericUpDown(WinForms.NumericUpDown control)
        {
            var number = new NumericUpDown { ClipValueToMinMax = true, AllowSpin = true, ShowButtonSpinner = true };
            bool syncing = false;
            number.ValueChanged += (s, e) =>
            {
                if (syncing || !e.NewValue.HasValue) return;
                decimal value = e.NewValue.Value;
                Ui.Input(() => control.UserSetValue(value));
            };
            return Leaf(number, () =>
            {
                syncing = true;
                try
                {
                    number.Minimum = control.Minimum; number.Maximum = control.Maximum; number.Increment = control.Increment;
                    number.FormatString = "F" + control.DecimalPlaces;
                    number.IsReadOnly = control.ReadOnly;
                    if (number.Value != control.Value) number.Value = control.Value;
                }
                finally { syncing = false; }
            });
        }

        static Created TrackBar(WinForms.TrackBar control)
        {
            var slider = new Slider { Orientation = control.Orientation == WinForms.Orientation.Vertical ? Orientation.Vertical : Orientation.Horizontal,
                                      IsSnapToTickEnabled = true, TickPlacement = TickPlacement.BottomRight };
            bool syncing = false;
            slider.ValueChanged += (s, e) => { if (!syncing) { int value = (int)Math.Round(e.NewValue); Ui.Input(() => control.UserScroll(value)); } };
            return Leaf(slider, () =>
            {
                syncing = true;
                try
                {
                    slider.Minimum = control.Minimum; slider.Maximum = control.Maximum; slider.SmallChange = control.SmallChange;
                    slider.LargeChange = control.LargeChange; slider.TickFrequency = Math.Max(1, control.TickFrequency); slider.Value = control.Value;
                }
                finally { syncing = false; }
            });
        }

        static Created ScrollBar(WinForms.ScrollBar control)
        {
            var bar = new Avalonia.Controls.Primitives.ScrollBar { Orientation = control is WinForms.HScrollBar ? Orientation.Horizontal : Orientation.Vertical, Visibility = ScrollBarVisibility.Visible };
            bool syncing = false;
            bar.Scroll += (s, e) =>
            {
                if (syncing) return;
                WinForms.ScrollEventType kind;
                switch (e.ScrollEventType)
                {
                    case Avalonia.Controls.Primitives.ScrollEventType.SmallIncrement: kind = WinForms.ScrollEventType.SmallIncrement; break;
                    case Avalonia.Controls.Primitives.ScrollEventType.SmallDecrement: kind = WinForms.ScrollEventType.SmallDecrement; break;
                    case Avalonia.Controls.Primitives.ScrollEventType.LargeIncrement: kind = WinForms.ScrollEventType.LargeIncrement; break;
                    case Avalonia.Controls.Primitives.ScrollEventType.LargeDecrement: kind = WinForms.ScrollEventType.LargeDecrement; break;
                    case Avalonia.Controls.Primitives.ScrollEventType.ThumbTrack: kind = WinForms.ScrollEventType.ThumbTrack; break;
                    default: kind = WinForms.ScrollEventType.ThumbPosition; break;
                }
                int value = (int)Math.Round(e.NewValue);
                Ui.Input(() => control.UserScroll(kind, value));
            };
            return Leaf(bar, () =>
            {
                syncing = true;
                try
                {
                    // WinForms reaches Maximum - LargeChange + 1
                    bar.Minimum = control.Minimum; bar.Maximum = Math.Max(control.Minimum, control.Maximum - control.LargeChange + 1);
                    bar.SmallChange = control.SmallChange; bar.LargeChange = control.LargeChange; bar.ViewportSize = control.LargeChange;
                    bar.Value = control.Value;
                }
                finally { syncing = false; }
            });
        }

        static Created ProgressBar(WinForms.ProgressBar control)
        {
            var bar = new ProgressBar();
            return Leaf(bar, () =>
            {
                bar.IsIndeterminate = control.Style == WinForms.ProgressBarStyle.Marquee;
                bar.Minimum = control.Minimum; bar.Maximum = control.Maximum; bar.Value = control.Value;
            });
        }

        static Created PictureBox(WinForms.PictureBox control)
        {
            var image = new Image();
            System.Drawing.Image shown = null;
            return Leaf(image, () =>
            {
                image.Stretch = control.SizeMode == WinForms.PictureBoxSizeMode.StretchImage ? Stretch.Fill :
                                control.SizeMode == WinForms.PictureBoxSizeMode.Zoom ? Stretch.Uniform : Stretch.None;
                image.HorizontalAlignment = control.SizeMode == WinForms.PictureBoxSizeMode.CenterImage ? HorizontalAlignment.Center : HorizontalAlignment.Left;
                if (shown != control.Image) { shown = control.Image; image.Source = Ui.Bitmap(shown); }
            });
        }

        // Containers ----------------------------------------------------------------------------------------------------
        static Created GroupBox(WinForms.GroupBox control)
        {
            var frame = new Canvas();
            var line = new Border { BorderBrush = Look.LightFrame, BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(3) };
            var caption = new TextBlock { Background = Look.Control, Padding = new Thickness(2, 0) };
            frame.Children.Add(line);
            frame.Children.Add(caption);
            if (control.GetType().Name == "CollapsableGroupBox")
            {
                // The original toggles on its +/- button (MouseUp)
                frame.Background = Brushes.Transparent;
                frame.PointerReleased += (s, e) =>
                {
                    Point p = e.GetPosition(frame);
                    var button = Keyboard.Button(e.GetCurrentPoint(frame).Properties.PointerUpdateKind);
                    Ui.Input(() => control.RaiseMouse("up", button, 1, (int)p.X, (int)p.Y));
                };
            }
            return new Created(frame, new Updater(() =>
            {
                caption.Text = control.Text;
                Canvas.SetLeft(caption, 6);
                Canvas.SetTop(line, 7);
                line.Width = Math.Max(0, frame.Width); line.Height = Math.Max(0, frame.Height - 7);
                caption.IsVisible = !string.IsNullOrEmpty(control.Text);
                caption.Background = BackOf(control) ?? (control.Parent != null ? BackOf(control.Parent) : null) ?? Look.Control;
            }));
        }

        static Created TabControl(WinForms.TabControl control)
        {
            // The header row above the pages (FormsCompat lays the pages out below a 24-unit row)
            var frame = new Canvas();
            var line = new Border { Background = Look.Window, BorderBrush = Look.LightFrame, BorderThickness = new Thickness(1) };
            var headers = new StackPanel { Orientation = Orientation.Horizontal, Height = 24, Margin = new Thickness(2, 0, 0, 0) };
            frame.Children.Add(line);
            frame.Children.Add(headers);
            var shown = new List<(WinForms.TabPage, string)>();
            int selected = -2;
            return new Created(frame, new Updater(() =>
            {
                Canvas.SetTop(line, 23);
                line.Width = Math.Max(0, frame.Width); line.Height = Math.Max(0, frame.Height - 23);
                var pages = control.TabPages.Cast<WinForms.TabPage>().Select(p => (p, p.Text)).ToList();
                if (pages.SequenceEqual(shown) && selected == control.SelectedIndex) return;
                shown = pages; selected = control.SelectedIndex;
                headers.Children.Clear();
                for (int i = 0; i < pages.Count; i++)
                {
                    int index = i;
                    bool current = i == selected;
                    var header = new Border
                    {
                        Child = new TextBlock { Text = pages[i].Item2, VerticalAlignment = VerticalAlignment.Center },
                        Padding = new Thickness(8, 0), Height = current ? 24 : 21, Margin = new Thickness(0, current ? 0 : 3, -1, 0),
                        Background = current ? Look.Window : Look.Control, BorderBrush = Look.LightFrame,
                        BorderThickness = new Thickness(1, 1, 1, current ? 0 : 1), VerticalAlignment = VerticalAlignment.Top, Cursor = new Cursor(StandardCursorType.Hand),
                    };
                    header.PointerPressed += (s, e) => { Ui.Input(() => control.SelectedIndex = index); e.Handled = true; };
                    headers.Children.Add(header);
                }
            }));
        }

        static Created SplitContainer(WinForms.SplitContainer split)
        {
            // The splitter bar between the panels: dragging it moves the splitter (SplitContainer.UserMoveSplitter).
            // Above the panels; only the bar takes the mouse (the canvas has no background)
            var frame = new Canvas();
            bool vertical = split.Orientation == WinForms.Orientation.Vertical;
            var bar = new Border { Background = Brushes.Transparent, Cursor = new Cursor(vertical ? StandardCursorType.SizeWestEast : StandardCursorType.SizeNorthSouth) };
            frame.Children.Add(bar);
            bool dragging = false;
            bar.PointerPressed += (s, e) => { if (split.IsSplitterFixed) return; dragging = true; e.Pointer.Capture(bar); e.Handled = true; };
            bar.PointerReleased += (s, e) => { dragging = false; e.Pointer.Capture(null); e.Handled = true; };
            bar.PointerMoved += (s, e) =>
            {
                if (!dragging) return;
                Point p = e.GetPosition(frame);
                int distance = (int)Math.Round((vertical ? p.X : p.Y) - split.SplitterWidth / 2.0);
                Ui.Input(() => split.UserMoveSplitter(distance));
                e.Handled = true;
            };
            var created = new Created(frame, new Updater(() =>
            {
                frame.ZIndex = 1000;
                var r = split.SplitterRectangle;
                bar.IsVisible = !split.Panel1Collapsed && !split.Panel2Collapsed;
                // A few units wider than the splitter, so it is easy to take
                Canvas.SetLeft(bar, vertical ? r.X - 2 : r.X); Canvas.SetTop(bar, vertical ? r.Y : r.Y - 2);
                bar.Width = vertical ? r.Width + 4 : r.Width; bar.Height = vertical ? r.Height : r.Height + 4;
            }));
            return created;
        }
    }

    /// <summary>ListView (Details, one column): rows in the item colours the original sets (ListViewWithSelection
    /// paints the chosen type itself and keeps no list-view selection); clicks select through the model.</summary>
    internal sealed class ListViewView : Control, IMirror
    {
        readonly WinForms.ListView _list;
        int _top;
        public ListViewView(WinForms.ListView list) { _list = list; ClipToBounds = true; Focusable = true; Background = Look.Window; }
        public IBrush Background { get; set; }
        public void Update() => InvalidateVisual();
        public void Refresh(string property) => InvalidateVisual();

        public override void Render(DrawingContext context)
        {
            context.FillRectangle(Background, new Rect(Bounds.Size));
            int row = WinForms.ListView.RowHeight;
            var items = _list.Items.Cast<WinForms.ListViewItem>().ToList();
            for (int i = _top; i < items.Count; i++)
            {
                double y = 2 + (i - _top) * row;
                if (y > Bounds.Height) break;
                var item = items[i];
                var rect = new Rect(2, y, Math.Max(0, Bounds.Width - 4), row);
                if (item.BackColor.A > 0) context.FillRectangle(Ui.Brush(item.BackColor), rect);
                var text = new FormattedText(item.Text ?? "", System.Globalization.CultureInfo.CurrentCulture, FlowDirection.LeftToRight, Look.Typeface, Look.FontSize,
                                             item.ForeColor.A > 0 ? Ui.Fore(item.ForeColor) : Look.Text);
                context.DrawText(text, new Point(6, y + (row - text.Height) / 2));
            }
            context.DrawRectangle(new Pen(Look.ButtonBorder), new Rect(Bounds.Size).Deflate(0.5));
        }

        int RowAt(Point p) => _top + (int)Math.Floor((p.Y - 2) / WinForms.ListView.RowHeight);

        protected override void OnPointerPressed(PointerPressedEventArgs e)
        {
            Focus();
            Point p = e.GetPosition(this);
            int index = RowAt(p);
            if (index < 0 || index >= _list.Items.Count) return;
            Ui.Input(() => _list.SelectByUser(new[] { index }));
            Ui.Input(() => _list.RaiseMouse("up", WinForms.MouseButtons.Left, 1, 4, (index - _top) * WinForms.ListView.RowHeight + 4));
            InvalidateVisual();
            e.Handled = true;
        }
        protected override void OnPointerMoved(PointerEventArgs e)
        {
            Point p = e.GetPosition(this);
            Ui.Input(() => _list.RaiseMouse("move", WinForms.MouseButtons.None, 0, (int)p.X, (int)p.Y));
            InvalidateVisual();
        }
        protected override void OnPointerExited(PointerEventArgs e) { Ui.Input(_list.RaiseMouseLeave); InvalidateVisual(); }
        protected override void OnPointerWheelChanged(PointerWheelEventArgs e)
        {
            int visible = Math.Max(1, (int)(Bounds.Height / WinForms.ListView.RowHeight));
            _top = Math.Max(0, Math.Min(Math.Max(0, _list.Items.Count - visible), _top - (int)Math.Round(e.Delta.Y * 3)));
            InvalidateVisual();
            e.Handled = true;
        }
    }
}
