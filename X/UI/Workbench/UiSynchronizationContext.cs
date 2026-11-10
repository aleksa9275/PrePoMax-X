// WindowsFormsSynchronizationContext equivalent for the toolkit thread: the original forms' async handlers
// (await OnApplyAsync, await Task.Run(...)) resume on the user-interface thread, as under WinForms.
using System.Threading;

namespace PrePoMaxX.UI;

public sealed class UiSynchronizationContext : SynchronizationContext
{
    readonly Action<Action> post;
    readonly int uiThread;
    UiSynchronizationContext(Action<Action> post, int uiThread) { this.post = post; this.uiThread = uiThread; }
    /// <summary>Creates the context for the calling (user-interface) thread; post must be thread-safe and run
    /// the action later on that thread. It is current only while original form code runs (Run), as the
    /// WinForms context is during message dispatch, so synchronous waits elsewhere are not affected.</summary>
    public static UiSynchronizationContext Create(Action<Action> post) => new(post, Environment.CurrentManagedThreadId);
    public void Run(Action action)
    {
        var previous = Current;
        SetSynchronizationContext(this);
        try { action(); }
        finally { SetSynchronizationContext(previous); }
    }
    public override void Post(SendOrPostCallback d, object state) => post(() => Run(() => d(state)));
    public override void Send(SendOrPostCallback d, object state)
    {
        if (Environment.CurrentManagedThreadId == uiThread) { d(state); return; }
        using var done = new ManualResetEventSlim();
        Exception error = null;
        post(() => { try { d(state); } catch (Exception e) { error = e; } finally { done.Set(); } });
        done.Wait();
        if (error != null) System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(error).Throw();
    }
    public override SynchronizationContext CreateCopy() => this;
}
