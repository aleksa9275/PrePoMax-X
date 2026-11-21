// Diagnostics: images of the application's own windows as the screen shows them, the native VTK view included
// (Avalonia's RenderTargetBitmap draws only Avalonia's scene). macOS lets an application capture its own windows
// without the screen recording permission a screenshot tool needs.
//   PREPOMAXX_WINDOW_CAPTURE=<path prefix>  PREPOMAXX_WINDOW_CAPTURE_AT=<seconds after start, comma separated>
// writes <prefix>-<seconds>s-<n>.png for every visible window.
using System;
using System.Linq;
using System.Runtime.InteropServices;
using Avalonia.Threading;

namespace PrePoMaxX.FrontEnd
{
    internal static class WindowCapture
    {
        [StructLayout(LayoutKind.Sequential)]
        struct CGRect { public double X, Y, Width, Height; }
        const string CoreGraphics = "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics";
        const string ObjC = "/usr/lib/libobjc.A.dylib";
        [DllImport(CoreGraphics)] static extern IntPtr CGWindowListCreateImage(CGRect bounds, uint listOption, uint windowId, uint imageOption);
        [DllImport(CoreGraphics)] static extern void CGImageRelease(IntPtr image);
        [DllImport(ObjC)] static extern IntPtr objc_getClass(string name);
        [DllImport(ObjC)] static extern IntPtr sel_registerName(string name);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] static extern IntPtr Send(IntPtr receiver, IntPtr selector);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] static extern IntPtr Send(IntPtr receiver, IntPtr selector, IntPtr a);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] static extern IntPtr Send(IntPtr receiver, IntPtr selector, ulong a, IntPtr b);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] static extern bool SendWrite(IntPtr receiver, IntPtr selector, IntPtr path, bool atomically);
        [DllImport(ObjC, EntryPoint = "objc_msgSend")] static extern long SendLong(IntPtr receiver, IntPtr selector);

        internal static void Start()
        {
            string prefix = Environment.GetEnvironmentVariable("PREPOMAXX_WINDOW_CAPTURE");
            if (string.IsNullOrEmpty(prefix) || !OperatingSystem.IsMacOS()) return;
            string at = Environment.GetEnvironmentVariable("PREPOMAXX_WINDOW_CAPTURE_AT") ?? "20";
            foreach (string text in at.Split(',', StringSplitOptions.RemoveEmptyEntries))
            {
                if (!double.TryParse(text, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double seconds)) continue;
                DispatcherTimer.RunOnce(() => CaptureAll(prefix + "-" + text.Trim() + "s"), TimeSpan.FromSeconds(seconds));
            }
            StartResize(prefix);
        }

        /// <summary>PREPOMAXX_WINDOW_CAPTURE_RESIZE=<seconds>: from then on the main window is resized in steps and each
        /// step captured right after the resize and once the loop has run (the frames of a live resize).</summary>
        static void StartResize(string prefix)
        {
            string at = Environment.GetEnvironmentVariable("PREPOMAXX_WINDOW_CAPTURE_RESIZE");
            if (string.IsNullOrEmpty(at) || !double.TryParse(at, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double seconds)) return;
            DispatcherTimer.RunOnce(() =>
            {
                var window = Ui.Windows.Values.FirstOrDefault(w => w.IsVisible);
                Console.WriteLine("[window capture] resize from " + window?.ClientSize);
                if (window == null) return;
                int step = 0;
                double width = window.ClientSize.Width, height = window.ClientSize.Height;
                DispatcherTimer timer = null;
                timer = new DispatcherTimer(TimeSpan.FromMilliseconds(120), DispatcherPriority.Normal, (s, e) =>
                {
                    try
                    {
                        if (step >= 6) { timer.Stop(); return; }
                        int n = step++;
                        window.Width = width - 60 * (n + 1);
                        window.Height = height - 40 * (n + 1);
                        CaptureAll(prefix + "-resize" + n + "a");
                        Dispatcher.UIThread.Post(() => CaptureAll(prefix + "-resize" + n + "b"), DispatcherPriority.Background);
                    }
                    catch (Exception error) { Console.Error.WriteLine("[window capture] " + error); timer.Stop(); }
                });
                timer.Start();
            }, TimeSpan.FromSeconds(seconds));
        }

        static void CaptureAll(string prefix)
        {
            int n = 0;
            foreach (var window in Ui.Windows.Values.Where(w => w.IsVisible).ToList())
            {
                try
                {
                    IntPtr nsWindow = window.TryGetPlatformHandle()?.Handle ?? IntPtr.Zero;
                    if (nsWindow == IntPtr.Zero) continue;
                    uint number = (uint)SendLong(nsWindow, sel_registerName("windowNumber"));
                    Save(number, prefix + "-" + (n++) + ".png");
                }
                catch (Exception e) { Console.Error.WriteLine("[window capture] " + e.Message); }
            }
        }

        static void Save(uint windowNumber, string path)
        {
            // CGRectNull, kCGWindowListOptionIncludingWindow, kCGWindowImageBoundsIgnoreFraming | BestResolution
            var nullRect = new CGRect { X = double.PositiveInfinity, Y = double.PositiveInfinity };
            IntPtr image = CGWindowListCreateImage(nullRect, 8, windowNumber, 1 | 8);
            if (image == IntPtr.Zero) { Console.Error.WriteLine("[window capture] no image of window " + windowNumber); return; }
            try
            {
                IntPtr rep = Send(Send(objc_getClass("NSBitmapImageRep"), sel_registerName("alloc")), sel_registerName("initWithCGImage:"), image);
                IntPtr data = Send(rep, sel_registerName("representationUsingType:properties:"), 4 /* NSBitmapImageFileTypePNG */,
                                   Send(objc_getClass("NSDictionary"), sel_registerName("dictionary")));
                IntPtr nsPath = Send(objc_getClass("NSString"), sel_registerName("stringWithUTF8String:"), Marshal.StringToCoTaskMemUTF8(path));
                bool written = SendWrite(data, sel_registerName("writeToFile:atomically:"), nsPath, true);
                Send(rep, sel_registerName("release"));
                Console.WriteLine("[window capture] " + (written ? path : "not written: " + path));
            }
            finally { CGImageRelease(image); }
        }
    }
}
