// PrePoMax-X: the window a native view renders into, for the headless WinForms model of X/UI/FormsCompat.
// The original VtkNativeHost (Native/VtkNativeHost.cs) is the same control on Win32: its view follows the window
// handle and the size, and paints on Paint. Here the renderer (X/UI) gives the host the native window of a Qt widget
// (an NSView on macOS, an X11 window on Linux) through AttachNativeWindow; VTK creates its OpenGL view inside it.
// VTK's Cocoa and X11 views leave the mouse and the keys to the parent, which hands them to the view
// (VtkNativeView.HandleInput); on X11 the host also pumps the view's own events (ProcessEvents). The focus messages of the original (WM_PARENTNOTIFY, the child
// window) are Win32 only: Qt passes the focus to the native child itself.
using System;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace vtkControl.Native
{
    public class VtkNativeHost : Control
    {
        // Variables
        private VtkNativeView _view;


        // Events
        public event EventHandler ViewCreated;


        // Properties
        public VtkNativeView View { get { return _view; } }
        // The original returns the Win32 child window of VTK to give it the keyboard; Qt does that on these platforms
        public IntPtr ViewWindow { get { return IntPtr.Zero; } }


        // Constructors
        // Invalidate and Refresh of the control model raise a "Refresh" notification instead of WM_PAINT; the view
        // paints on it, as the original host paints on WM_PAINT
        /// <summary>Device pixels per control unit of a front end whose native window VTK's Cocoa view sizes in points
        /// (VTK divides the size it is given by the backing scale): with 2 on a Retina display the view covers the host
        /// and renders at device resolution. 1 (the default) keeps the size as given.</summary>
        public static double DeviceScale = 1;
        /// <summary>macOS: VTK's view is pinned to the host view's bounds (and follows them) and the host clips it. A
        /// front end whose host view is not flipped (Avalonia) needs it: VTK places its view from its parent's height
        /// and keeps its bottom-left corner when it resizes it.</summary>
        public static bool FitViewToHost;
        private static int Device(int size) => OperatingSystem.IsMacOS() ? Math.Max(1, (int)Math.Round(size * DeviceScale)) : size;
        public VtkNativeHost()
        {
            ControlNotifications.Changed += OnControlChanged;
        }


        // Methods
        private void OnControlChanged(Control control, string property)
        {
            if (control == this && property == "Refresh") OnPaint(null);
        }
        protected override void Dispose(bool disposing)
        {
            if (disposing) ControlNotifications.Changed -= OnControlChanged;
            base.Dispose(disposing);
        }
        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            //
            if (Handle == IntPtr.Zero)
            {
                // A run without a user interface (-g No, CreateOffScreenHandle): the original's hidden window still
                // draws on Windows; here the view draws off screen
                _view = VtkNativeView.CreateOffScreen(Math.Max(1, ClientSize.Width), Math.Max(1, ClientSize.Height));
                ViewCreated?.Invoke(this, EventArgs.Empty);
                return;
            }
            _view = VtkNativeView.CreateEmbedded(Handle, Device(Math.Max(1, ClientSize.Width)), Device(Math.Max(1, ClientSize.Height)));
            if (OperatingSystem.IsMacOS())
            {
                _view.Render();     // VTK creates its NSView at the first render
                CocoaPassThrough.Apply(Handle);
                if (FitViewToHost) { CocoaPassThrough.FitSubviews(Handle); _view.Render(); }
            }
            ViewCreated?.Invoke(this, EventArgs.Empty);
        }
        /// <summary>X11: dispatches the exposure, size and timer events of the view (selection and smooth zoom
        /// timers of the interaction style); the host calls it from its event loop. Nothing to do on macOS.</summary>
        public void ProcessEvents()
        {
            if (_view != null && OperatingSystem.IsLinux())
                VtkNativeLibrary.Check(vtkn_view_process_events(_view.Handle()));
        }
        [DllImport(VtkNativeMethods.LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern VtkNativeStatus vtkn_view_process_events(IntPtr view);
        protected override void OnHandleDestroyed(EventArgs e)
        {
            if (_view != null)
            {
                _view.Dispose();
                _view = null;
            }
            base.OnHandleDestroyed(e);
        }
        protected override void OnResize(EventArgs e)
        {
            base.OnResize(e);
            if (_view != null && ClientSize.Width > 0 && ClientSize.Height > 0)
            {
                _view.SetSize(Device(ClientSize.Width), Device(ClientSize.Height));
                if (FitViewToHost && OperatingSystem.IsMacOS() && Handle != IntPtr.Zero) CocoaPassThrough.FitSubviews(Handle);
                _view.Render();
            }
        }
        protected override void OnPaint(PaintEventArgs e)
        {
            if (_view != null) _view.Render();
        }
    }

    // VTK's Cocoa window inside a parent is a plain NSView that leaves the input to the parent ("the superview
    // handles the events"). A plain NSView does not take the first click of a window that is not key, so a click
    // on the view while a form window is active would only activate the main window; Win32 passes that click on.
    // The NSView of VTK is made transparent to hit testing (hitTest: returns nil), so every click, the first one
    // too, reaches the parent - the Qt view, which accepts first clicks - and through it the interaction style.
    public static class CocoaPassThrough
    {
        [StructLayout(LayoutKind.Sequential)]
        private struct NSPoint { public double X; public double Y; }
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate IntPtr HitTest(IntPtr self, IntPtr selector, NSPoint point);
        private const string ObjC = "/usr/lib/libobjc.A.dylib";
        [DllImport(ObjC)] private static extern IntPtr objc_getClass(string name);
        [DllImport(ObjC)] private static extern IntPtr sel_registerName(string name);
        [DllImport(ObjC)] private static extern IntPtr objc_allocateClassPair(IntPtr superclass, string name, IntPtr extraBytes);
        [DllImport(ObjC)] private static extern void objc_registerClassPair(IntPtr cls);
        [DllImport(ObjC)] private static extern bool class_addMethod(IntPtr cls, IntPtr selector, IntPtr imp, string types);
        [DllImport(ObjC)] private static extern IntPtr object_getClass(IntPtr obj);
        [DllImport(ObjC)] private static extern IntPtr object_setClass(IntPtr obj, IntPtr cls);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] private static extern IntPtr Send(IntPtr receiver, IntPtr selector);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] private static extern IntPtr Send(IntPtr receiver, IntPtr selector, IntPtr argument);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] private static extern ulong SendCount(IntPtr receiver, IntPtr selector);
        private static readonly HitTest NoHit = (self, selector, point) => IntPtr.Zero;
        private static IntPtr _class;

        /// <summary>Makes one view transparent to hit testing, whatever its class (a front end's native host view): a
        /// subclass of its class answers hitTest: with nil.</summary>
        public static void ApplyToView(IntPtr view)
        {
            IntPtr cls = object_getClass(view);
            string name = "PrePoMaxXPassThrough_" + Marshal.PtrToStringAnsi(class_getName(cls));
            IntPtr pass = objc_getClass(name);
            if (pass == IntPtr.Zero)
            {
                pass = objc_allocateClassPair(cls, name, IntPtr.Zero);
                class_addMethod(pass, sel_registerName("hitTest:"), Marshal.GetFunctionPointerForDelegate(NoHit), "@@:{CGPoint=dd}");
                objc_registerClassPair(pass);
            }
            object_setClass(view, pass);
        }
        [DllImport(ObjC)] private static extern IntPtr class_getName(IntPtr cls);
        [StructLayout(LayoutKind.Sequential)]
        private struct NSRect { public double X; public double Y; public double Width; public double Height; }
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] private static extern NSRect SendRect(IntPtr receiver, IntPtr selector);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] private static extern void SendRect(IntPtr receiver, IntPtr selector, NSRect rect);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] private static extern void SendBool(IntPtr receiver, IntPtr selector, bool value);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] private static extern void SendULong(IntPtr receiver, IntPtr selector, ulong value);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] private static extern bool SendRespondsTo(IntPtr receiver, IntPtr selector, IntPtr query);
        /// <summary>Pins every subview (VTK's view) to the bounds of the host view, sizes them with it, and makes the
        /// host clip them (macOS 14 and later no longer clip subviews by default).</summary>
        public static void FitSubviews(IntPtr hostView)
        {
            NSRect bounds = SendRect(hostView, sel_registerName("bounds"));
            IntPtr clips = sel_registerName("setClipsToBounds:");
            if (SendRespondsTo(hostView, sel_registerName("respondsToSelector:"), clips)) SendBool(hostView, clips, true);
            IntPtr subviews = Send(hostView, sel_registerName("subviews"));
            ulong count = SendCount(subviews, sel_registerName("count"));
            for (ulong i = 0; i < count; i++)
            {
                IntPtr view = Send(subviews, sel_registerName("objectAtIndex:"), (IntPtr)(long)i);
                SendRect(view, sel_registerName("setFrame:"), bounds);
                SendULong(view, sel_registerName("setAutoresizingMask:"), 18);  // NSViewWidthSizable | NSViewHeightSizable
            }
        }
        public static void Apply(IntPtr parentView)
        {
            IntPtr nsView = objc_getClass("NSView");
            if (_class == IntPtr.Zero)
            {
                _class = objc_allocateClassPair(nsView, "PrePoMaxXPassThroughView", IntPtr.Zero);
                class_addMethod(_class, sel_registerName("hitTest:"), Marshal.GetFunctionPointerForDelegate(NoHit), "@@:{CGPoint=dd}");
                objc_registerClassPair(_class);
            }
            IntPtr subviews = Send(parentView, sel_registerName("subviews"));
            ulong count = SendCount(subviews, sel_registerName("count"));
            for (ulong i = 0; i < count; i++)
            {
                IntPtr view = Send(subviews, sel_registerName("objectAtIndex:"), (IntPtr)(long)i);
                // Only the plain NSView VTK made (Qt's own child views keep their class)
                if (object_getClass(view) == nsView) object_setClass(view, _class);
            }
        }
    }
}
