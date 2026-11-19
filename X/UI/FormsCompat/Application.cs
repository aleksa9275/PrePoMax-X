// WinForms Application for the headless control model (M2: the original Program runs FrmMain). With a renderer
// attached (RunHandler, the Qt main window) Run hands it the main form; without one - the original command line with
// -g No - Run is a message loop of its own: posted calls (BeginInvoke, SynchronizationContext.Post), the enabled
// timers and Idle, until the main form closes or Exit is called. Exceptions of the loop go to ThreadException, as
// in WinForms.
using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

namespace System.Windows.Forms
{
    public static class Application
    {
        /// <summary>The renderer's event processing (Qt processEvents); the headless loop runs its queue instead.</summary>
        public static Action DoEventsHandler;
        /// <summary>The renderer's main loop for the main form (shows it, returns when it closes).</summary>
        public static Action<Form> RunHandler;
        public static string StartupPath => AppContext.BaseDirectory.TrimEnd(System.IO.Path.DirectorySeparatorChar);
        public static string ExecutablePath => Environment.ProcessPath;
        public static string ProductVersion => System.Reflection.Assembly.GetEntryAssembly()?.GetName().Version?.ToString() ?? "3.0.1.0";
        public static string ProductName => "PrePoMax";
        public static bool MessageLoop => DoEventsHandler != null || s_loop != null;
        public static void DoEvents()
        {
            if (DoEventsHandler != null) DoEventsHandler();
            else s_loop?.RunPending();
        }
        // Message filters and the idle event: a filter sees no Win32 message here; Idle is raised after the pending
        // events are processed
        static readonly List<IMessageFilter> filters = new List<IMessageFilter>();
        public static event EventHandler Idle;
        public static void AddMessageFilter(IMessageFilter filter) { lock (filters) filters.Add(filter); }
        public static void RemoveMessageFilter(IMessageFilter filter) { lock (filters) filters.Remove(filter); }
        public static void RaiseIdle() => Idle?.Invoke(null, EventArgs.Empty);
        public static FormCollection OpenForms => new FormCollection(Form.OpenForms);
        public static event ThreadExceptionEventHandler ThreadException;
        public static event EventHandler ApplicationExit;
        public static void EnableVisualStyles() { }
        public static void SetCompatibleTextRenderingDefault(bool defaultValue) { }
        public static void SetUnhandledExceptionMode(UnhandledExceptionMode mode) { }
        /// <summary>An exception of an event handler: ThreadException when handled there, else it propagates.</summary>
        public static bool RaiseThreadException(Exception exception)
        {
            ThreadExceptionEventHandler handler = ThreadException;
            if (handler == null) return false;
            handler(Thread.CurrentThread, new ThreadExceptionEventArgs(exception));
            return true;
        }
        static HeadlessMessageLoop s_loop;
        public static void Run(Form mainForm)
        {
            if (mainForm == null) throw new ArgumentNullException(nameof(mainForm));
            try
            {
                if (RunHandler != null) RunHandler(mainForm);
                else RunHeadless(mainForm);
            }
            finally
            {
                s_loop = null;
                ApplicationExit?.Invoke(null, EventArgs.Empty);
            }
        }
        /// <summary>The message loop of a run without a renderer (the original command line with -g No).</summary>
        public static void RunHeadless(Form mainForm)
        {
            s_loop = new HeadlessMessageLoop();
            s_loop.Run(mainForm);
        }
        /// <summary>Closes the open forms (FormClosing may not cancel an exit) and ends Run.</summary>
        public static void Exit()
        {
            foreach (Form form in Form.OpenForms.ToArray()) form.CloseForExit();
            s_loop?.Stop();
            ExitHandler?.Invoke();
        }
        public static void ExitThread() => Exit();
        /// <summary>The renderer's end of its main loop.</summary>
        public static Action ExitHandler;
    }
    public enum UnhandledExceptionMode { Automatic, ThrowException, CatchException }

    /// <summary>The open forms (Application.OpenForms), by index or name.</summary>
    public class FormCollection : ReadOnlyCollectionBase
    {
        internal FormCollection(IEnumerable<Form> forms) { foreach (Form form in forms) InnerList.Add(form); }
        public virtual Form this[int index] => (Form)InnerList[index];
        public virtual Form this[string name] => InnerList.Cast<Form>().FirstOrDefault(f => string.Equals(f.Name, name, StringComparison.OrdinalIgnoreCase));
    }

    /// <summary>The message loop of a run without a renderer: one thread, posted calls in order, timers by their
    /// interval.</summary>
    sealed class HeadlessMessageLoop : SynchronizationContext
    {
        readonly BlockingCollection<(SendOrPostCallback Callback, object State)> _queue = new BlockingCollection<(SendOrPostCallback, object)>();
        readonly Dictionary<Timer, DateTime> _timers = new Dictionary<Timer, DateTime>();
        readonly int _thread = Environment.CurrentManagedThreadId;
        volatile bool _stopped;

        public override void Post(SendOrPostCallback d, object state) { if (!_queue.IsAddingCompleted) _queue.Add((d, state)); }
        public override void Send(SendOrPostCallback d, object state)
        {
            if (Environment.CurrentManagedThreadId == _thread) { d(state); return; }
            using (var done = new ManualResetEventSlim())
            {
                Exception error = null;
                Post(_ => { try { d(state); } catch (Exception e) { error = e; } finally { done.Set(); } }, null);
                done.Wait();
                if (error != null) System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(error).Throw();
            }
        }
        public override SynchronizationContext CreateCopy() => this;
        public void Stop() { _stopped = true; Post(_ => { }, null); }

        void TimerChanged(Timer timer)
        {
            lock (_timers)
            {
                if (timer.Enabled) _timers[timer] = DateTime.UtcNow.AddMilliseconds(timer.Interval);
                else _timers.Remove(timer);
            }
        }
        public void Run(Form mainForm)
        {
            SynchronizationContext previous = Current;
            SetSynchronizationContext(this);
            Control.SetUiThreadContext(this);
            Timer.StateChanged += TimerChanged;
            Form.CreateControlsOnShow = true;
            mainForm.FormClosed += (s, e) => Stop();
            try
            {
                Dispatch(_ => mainForm.Show(), null);
                while (!_stopped)
                {
                    TimeSpan wait = NextTimer();
                    if (_queue.TryTake(out var item, wait)) Dispatch(item.Callback, item.State);
                    RunDueTimers();
                    if (_queue.Count == 0) Dispatch(_ => Application.RaiseIdle(), null);
                }
            }
            finally
            {
                Timer.StateChanged -= TimerChanged;
                SetSynchronizationContext(previous);
            }
        }
        /// <summary>Application.DoEvents: the calls posted so far and the due timers.</summary>
        public void RunPending()
        {
            int count = _queue.Count;
            for (int i = 0; i < count && _queue.TryTake(out var item); i++) Dispatch(item.Callback, item.State);
            RunDueTimers();
        }
        TimeSpan NextTimer()
        {
            lock (_timers)
            {
                if (_timers.Count == 0) return TimeSpan.FromMilliseconds(250);
                TimeSpan wait = _timers.Values.Min() - DateTime.UtcNow;
                return wait < TimeSpan.Zero ? TimeSpan.Zero : wait;
            }
        }
        void RunDueTimers()
        {
            Timer[] due;
            DateTime now = DateTime.UtcNow;
            lock (_timers)
            {
                due = _timers.Where(t => t.Value <= now).Select(t => t.Key).ToArray();
                foreach (Timer timer in due) _timers[timer] = now.AddMilliseconds(timer.Interval);
            }
            foreach (Timer timer in due) Dispatch(_ => timer.RaiseTick(), null);
        }
        static void Dispatch(SendOrPostCallback callback, object state)
        {
            try { callback(state); }
            catch (Exception error) when (Application.RaiseThreadException(error)) { }
        }
    }
}


namespace System.Windows.Forms
{
    /// <summary>The WindowsFormsSynchronizationContext of a renderer's user-interface thread (the WinForms message
    /// queue). Posted and sent calls wait in this queue until the renderer's event loop runs Drain on that thread; the
    /// calling threads never enter the renderer. Installed, it also brings the control model's callbacks to the
    /// renderer (notifications, dialogs, timers, measuring) onto that thread: the renderer (Python, with its global
    /// interpreter lock) is entered by one thread only, as WinForms windows are used by one thread only.</summary>
    public sealed class ToolkitSynchronizationContext : SynchronizationContext
    {
        readonly ConcurrentQueue<Action> _queue = new ConcurrentQueue<Action>();
        readonly int _thread = Environment.CurrentManagedThreadId;
        /// <summary>The context of the renderer's user-interface thread (null without a renderer of this kind).</summary>
        public static ToolkitSynchronizationContext Installed { get; private set; }
        /// <summary>Creates the context on the user-interface thread and installs it (Control.Invoke/BeginInvoke too).</summary>
        public static ToolkitSynchronizationContext Install()
        {
            var context = new ToolkitSynchronizationContext();
            Installed = context;
            Control.SetUiThreadContext(context);
            return context;
        }
        public bool IsUiThread => Environment.CurrentManagedThreadId == _thread;
        public void Run(Action action)
        {
            SynchronizationContext previous = Current;
            SetSynchronizationContext(this);
            try { action(); }
            finally { SetSynchronizationContext(previous); }
        }
        public override void Post(SendOrPostCallback d, object state) => _queue.Enqueue(() => Run(() => d(state)));
        public void PostAction(Action action) => _queue.Enqueue(() => Run(action));
        public override void Send(SendOrPostCallback d, object state)
        {
            if (IsUiThread) { d(state); return; }
            using (var done = new ManualResetEventSlim())
            {
                Exception error = null;
                _queue.Enqueue(() => { try { Run(() => d(state)); } catch (Exception e) { error = e; } finally { done.Set(); } });
                done.Wait();
                if (error != null) System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(error).Throw();
            }
        }
        public override SynchronizationContext CreateCopy() => this;
        /// <summary>The renderer's event loop: runs the calls queued so far (on the user-interface thread). An
        /// exception goes to Application.ThreadException, else to the returned list for the renderer to report.</summary>
        public Exception[] Drain()
        {
            if (!IsUiThread) throw new InvalidOperationException("Drain runs on the user-interface thread.");
            var errors = new List<Exception>();
            int count = _queue.Count;
            for (int i = 0; i < count && _queue.TryDequeue(out Action action); i++)
            {
                try { action(); }
                catch (Exception error) { if (!Application.RaiseThreadException(error)) errors.Add(error); }
            }
            return errors.ToArray();
        }
        /// <summary>Runs function on the user-interface thread of the installed context (directly when there is none
        /// or on that thread) and returns its result.</summary>
        public static T OnUiThread<T>(Func<T> function)
        {
            ToolkitSynchronizationContext ui = Installed;
            if (ui == null || ui.IsUiThread) return function();
            T result = default(T);
            ui.Send(_ => result = function(), null);
            return result;
        }
        /// <summary>CaeGlobals.MessageBoxes.UiDispatcher: the original Form.Invoke hop of the message boxes.</summary>
        public Func<Func<object>, object> Dispatcher => function => OnUiThread(function);
        /// <summary>A callback raised on another thread reaches the renderer later on its thread.</summary>
        internal static bool Defer(Action callback)
        {
            ToolkitSynchronizationContext ui = Installed;
            if (ui == null || ui.IsUiThread) return false;
            ui.PostAction(callback);
            return true;
        }
    }
}
