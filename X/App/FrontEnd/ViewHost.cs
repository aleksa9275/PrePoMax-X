// The original vtkControl in a native child window of the Avalonia window (the successor of X/UI/original_viewport.py):
// VTK creates its OpenGL view in the host's native window (VtkNativeHost.AttachNativeWindow, an NSView on macOS, an
// X11 window on Linux); Avalonia's pointer, wheel and key events go to the interaction style in device pixels.
using System;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Platform;
using Avalonia.Threading;
using vtkControl.Native;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEnd
{
    internal sealed class ViewHost : NativeControlHost, Avalonia.Rendering.ICustomHitTest
    {
        // Avalonia hit-tests what it draws; the native view draws nothing in Avalonia's scene
        public bool HitTest(Point point) => new Rect(Bounds.Size).Contains(point);
        internal readonly vtkControl.vtkControl Control;
        bool _attached;
        int _wheel;
        DispatcherTimer _events;
        internal int Inputs;
        static readonly bool TraceInput = Environment.GetEnvironmentVariable("PREPOMAXX_TRACE_VIEW_INPUT") == "1";

        public ViewHost(vtkControl.vtkControl control)
        {
            Control = control;
            Focusable = true;
        }

        internal bool Attached => _attached;

        protected override IPlatformHandle CreateNativeControlCore(IPlatformHandle parent)
        {
            IPlatformHandle handle = base.CreateNativeControlCore(parent);
            if (OperatingSystem.IsMacOS())
            {
                // Avalonia's native host view keeps the mouse to itself; transparent to hit testing, the clicks over the
                // view reach Avalonia's window and this control (VtkNativeHost makes VTK's own view transparent). The
                // view renders in device pixels, pinned to the host, its overlays scaled (D066)
                CocoaPassThrough.ApplyToView(handle.Handle);
                VtkNativeHost.DeviceScale = TopLevel.GetTopLevel(this)?.RenderScaling ?? 1;
                VtkNativeHost.FitViewToHost = true;
            }
            Dispatcher.UIThread.Post(() => Attach(handle.Handle), DispatcherPriority.Loaded);
            return handle;
        }

        /// <summary>WinForms creates the window of the control when it is first shown: OnHandleCreated, then Load.
        /// FrmMain loaded the control when it created it; the control sends its scene to the native view now.</summary>
        void Attach(IntPtr window)
        {
            if (_attached) return;
            _attached = true;
            Ui.Guard(() =>
            {
                Control.NativeHost.AttachNativeWindow(window);
                Control.RaiseLoad();
                Control.EnableNativeMirror(true);
                if (TraceInput && Control.NativeMirror != null)
                    Control.NativeMirror.NativeEvent += (s, e) => Console.WriteLine("[view event] " + (int)e.Event + " " + string.Join(",", e.Values ?? new double[0]));
            });
            if (OperatingSystem.IsLinux())
            {
                // X11: the view's exposure, size and the interaction style's timers come from its own display connection
                _events = new DispatcherTimer(TimeSpan.FromMilliseconds(10), DispatcherPriority.Background, (s, e) => Control.NativeHost.ProcessEvents());
                _events.Start();
            }
            Ui.RequestSync();
        }

        protected override void OnSizeChanged(SizeChangedEventArgs e)
        {
            base.OnSizeChanged(e);
            if (Environment.GetEnvironmentVariable("PREPOMAXX_TRACE_VIEW_SIZE") == "1")
                Console.WriteLine("[view size] host " + e.NewSize + " model " + Control.Width + "x" + Control.Height + " attached " + _attached);
            // Avalonia gives the native host view its new frame after this layout pass; the model's control has
            // fitted VTK's view to its size before, inside the old frame. Fit it again once the frame is placed
            if (_attached) Dispatcher.UIThread.Post(() => { if (_attached) Ui.Guard(() => Control.NativeHost.FitView()); }, DispatcherPriority.Background);
        }

        protected override void DestroyNativeControlCore(IPlatformHandle control)
        {
            // Before Avalonia destroys the native window: the view is released while its window still exists
            _events?.Stop();
            if (_attached) { _attached = false; Ui.Guard(() => Control.NativeHost.DetachNativeWindow()); }
            base.DestroyNativeControlCore(control);
        }

        // Input. A Win32 window delivers the mouse and the keys to VTK's interactor itself; VTK's Cocoa and X11 views
        // inside a parent leave them to the parent, which hands them to the interaction style (vtkn_view_handle_input)
        // in display pixels, origin bottom left
        bool Send(VtkNativeInput input, Point position, KeyModifiers modifiers, int keyCode = 0, string symbol = null)
        {
            VtkNativeView view = _attached ? Control.NativeMirror : null;
            Inputs++;
            if (TraceInput && input != VtkNativeInput.MouseMove) Console.WriteLine("[view input] " + input + " at " + (int)position.X + "," + (int)position.Y + (view == null ? " (no view)" : ""));
            if (view == null) return false;
            double ratio = VtkNativeHost.DeviceScale;
            // Cocoa's interactor reports the Command key as control, as PrePoMax's Ctrl
            bool control = (modifiers & (KeyModifiers.Control | KeyModifiers.Meta)) != 0, shift = (modifiers & KeyModifiers.Shift) != 0;
            Keyboard.SetModifiers(modifiers);
            Ui.Guard(() => view.HandleInput(input, (int)Math.Round(position.X * ratio), (int)Math.Round((Bounds.Height - position.Y) * ratio),
                                            control, shift, keyCode, symbol));
            Ui.RequestSync();
            return true;
        }
        internal bool SendForProbe(VtkNativeInput input, Point position) => Send(input, position, KeyModifiers.None);

        protected override void OnPointerPressed(PointerPressedEventArgs e)
        {
            Focus();
            var kind = e.GetCurrentPoint(this).Properties.PointerUpdateKind;
            VtkNativeInput? input = kind == PointerUpdateKind.LeftButtonPressed ? VtkNativeInput.LeftButtonDown :
                kind == PointerUpdateKind.MiddleButtonPressed ? VtkNativeInput.MiddleButtonDown :
                kind == PointerUpdateKind.RightButtonPressed ? VtkNativeInput.RightButtonDown : (VtkNativeInput?)null;
            if (input.HasValue && Send(input.Value, e.GetPosition(this), e.KeyModifiers))
            {
                e.Pointer.Capture(this);
                e.Handled = true;
            }
        }

        protected override void OnPointerReleased(PointerReleasedEventArgs e)
        {
            var kind = e.GetCurrentPoint(this).Properties.PointerUpdateKind;
            VtkNativeInput? input = kind == PointerUpdateKind.LeftButtonReleased ? VtkNativeInput.LeftButtonUp :
                kind == PointerUpdateKind.MiddleButtonReleased ? VtkNativeInput.MiddleButtonUp :
                kind == PointerUpdateKind.RightButtonReleased ? VtkNativeInput.RightButtonUp : (VtkNativeInput?)null;
            if (input.HasValue && Send(input.Value, e.GetPosition(this), e.KeyModifiers)) e.Handled = true;
            if (!e.GetCurrentPoint(this).Properties.IsLeftButtonPressed && !e.GetCurrentPoint(this).Properties.IsMiddleButtonPressed &&
                !e.GetCurrentPoint(this).Properties.IsRightButtonPressed) e.Pointer.Capture(null);
        }

        protected override void OnPointerMoved(PointerEventArgs e) { _pointer = e.GetPosition(this); if (Send(VtkNativeInput.MouseMove, e.GetPosition(this), e.KeyModifiers)) e.Handled = true; }
        protected override void OnPointerExited(PointerEventArgs e) => Send(VtkNativeInput.Leave, default, e.KeyModifiers);

        protected override void OnPointerWheelChanged(PointerWheelEventArgs e)
        {
            // One wheel event per notch (WHEEL_DELTA 120), as Win32 and Cocoa wheels give them; trackpads add up
            _wheel += (int)Math.Round(e.Delta.Y * 120);
            while (Math.Abs(_wheel) >= 120)
            {
                int step = _wheel > 0 ? 120 : -120;
                _wheel -= step;
                Send(step > 0 ? VtkNativeInput.WheelForward : VtkNativeInput.WheelBackward, e.GetPosition(this), e.KeyModifiers);
            }
            e.Handled = true;
        }

        Point _pointer;
        protected override void OnPointerEntered(PointerEventArgs e) { _pointer = e.GetPosition(this); base.OnPointerEntered(e); }

        // The VTK key symbols the interaction style compares (vtkNativeInteractorStyle GetLegacyKeyCode)
        static string Symbol(KeyEventArgs e)
        {
            switch (e.Key)
            {
                case Key.Left: return "Left";
                case Key.Up: return "Up";
                case Key.Right: return "Right";
                case Key.Down: return "Down";
                case Key.Escape: return "Escape";
                case Key.Return: return "Return";
                case Key.Space: return "space";
                case Key.Delete: return "Delete";
                case Key.LeftShift: case Key.RightShift: return "Shift_L";
                case Key.LeftCtrl: case Key.RightCtrl: case Key.LWin: case Key.RWin: return "Control_L";
                case Key.LeftAlt: case Key.RightAlt: return "Alt_L";
            }
            return e.KeySymbol is { Length: 1 } s && !char.IsControl(s[0]) ? s : null;
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            int code = e.KeySymbol is { Length: 1 } s && s[0] < 256 ? s[0] : 0;
            if (Send(VtkNativeInput.KeyPress, _pointer, e.KeyModifiers, code, Symbol(e))) e.Handled = true;
        }

        protected override void OnKeyUp(KeyEventArgs e)
        {
            int code = e.KeySymbol is { Length: 1 } s && s[0] < 256 ? s[0] : 0;
            if (Send(VtkNativeInput.KeyRelease, _pointer, e.KeyModifiers, code, Symbol(e))) e.Handled = true;
        }

        internal void Capture(string path) => Ui.Guard(() => Control.NativeMirror?.WritePng(path, 1));
    }
}
