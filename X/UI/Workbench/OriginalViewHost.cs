// The view half of the original FrmMain (M1). OriginalViewHost.g.cs holds the original FrmMain members that drive
// vtkControl, copied unchanged; this part gives them what FrmMain gives them: the vtkControl of the viewport and
// the marshalling to the user-interface thread (Control.Invoke), and keeps the view statements of the members
// whose original bodies also change FrmMain's own controls (the toolkit mirrors those controls).
// The headless FrmMain (X/Controller/Host) routes the controller's calls here by name while a viewport exists.
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.ExceptionServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace PrePoMax
{
    public sealed partial class OriginalViewHost
    {
        // Variables
        private readonly vtkControl.vtkControl _vtk;
        // The two FrmMain tool strip buttons the view members check (section view, follower view); the toolkit
        // mirrors their Checked state
        private readonly ToolStripButton tsbSectionView = new ToolStripButton();
        private readonly ToolStripButton tsbFollowerView = new ToolStripButton();
        private readonly Action<Action> _post;
        private readonly int _uiThread;
        private readonly Dictionary<string, MethodInfo[]> _members;
        private double _selectionPrecision;
        // The marshalled calls waiting for the user-interface thread (run by the posted Drain or by WaitFor)
        private readonly ConcurrentQueue<Action> _pending = new ConcurrentQueue<Action>();
        private static OriginalViewHost _current;


        // Properties
        public vtkControl.vtkControl Control { get { return _vtk; } }
        public bool SectionViewChecked { get { return tsbSectionView.Checked; } }
        public bool FollowerViewChecked { get { return tsbFollowerView.Checked; } }
        // Control.InvokeRequired of the original form
        public bool InvokeRequired { get { return Environment.CurrentManagedThreadId != _uiThread; } }


        // Constructors
        /// <summary>Created on the user-interface thread; post runs an action later on that thread (thread-safe).</summary>
        public OriginalViewHost(vtkControl.vtkControl vtk, Action<Action> post)
        {
            _vtk = vtk;
            _post = post;
            _uiThread = Environment.CurrentManagedThreadId;
            _current = this;
            _members = typeof(OriginalViewHost).GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly)
                .Where(m => !m.IsSpecialName && m.Name != nameof(InvokeIfRequired) && m.Name != nameof(TryInvoke) &&
                            m.Name != nameof(Handles) && m.Name != nameof(Invoke))
                .GroupBy(m => m.Name).ToDictionary(g => g.Key, g => g.ToArray(), StringComparer.Ordinal);
        }


        // Methods
        /// <summary>The headless FrmMain sends the view calls here from now on, and the view asks the controller.</summary>
        public void Attach(FrmMain presentation)
        {
            presentation.ViewHost = TryInvoke;
            WireController(presentation.Controller);
        }
        public bool Handles(string name) => _members.ContainsKey(name);
        /// <summary>Calls the original member of this name whose parameters take the arguments; out parameters are
        /// written back into the array, as the generated controller host reads them.</summary>
        public bool TryInvoke(string name, object[] arguments, out object result)
        {
            result = null;
            if (!_members.TryGetValue(name, out MethodInfo[] candidates)) return false;
            // The controller asks for the selection precision from its background work too, while the user-interface
            // thread may wait for that work: it gets the value of the last view call on that thread instead of a
            // marshalled call (FrmMain marshals it; WinForms keeps pumping messages while it waits)
            if (name == "GetSelectionPrecision")
            {
                if (InvokeRequired) { result = _selectionPrecision; return true; }
                result = _selectionPrecision = _vtk.GetSelectionPrecision();
                return true;
            }
            MethodInfo method = candidates.FirstOrDefault(m => Accepts(m, arguments));
            if (method == null)
                throw new MissingMethodException("OriginalViewHost." + name + " takes no such arguments (" +
                                                 string.Join(", ", arguments.Select(a => a?.GetType().Name ?? "null")) + ")");
            try { result = method.Invoke(this, arguments); }
            catch (TargetInvocationException error) when (error.InnerException != null)
            {
                ExceptionDispatchInfo.Capture(error.InnerException).Throw();
            }
            return true;
        }
        private static bool Accepts(MethodInfo method, object[] arguments)
        {
            ParameterInfo[] parameters = method.GetParameters();
            if (parameters.Length != arguments.Length) return false;
            for (int i = 0; i < parameters.Length; i++)
            {
                Type type = parameters[i].ParameterType;
                if (type.IsByRef) { if (parameters[i].IsOut) continue; type = type.GetElementType(); }
                if (arguments[i] == null) { if (type.IsValueType && Nullable.GetUnderlyingType(type) == null) return false; }
                else if (!type.IsInstanceOfType(arguments[i])) return false;
            }
            return true;
        }
        // Control.Invoke of the original form
        public object Invoke(Delegate method)
        {
            object result = null;
            InvokeMarshaled(() => result = method.DynamicInvoke());
            return result;
        }
        // FrmMain.InvokeMarshaled: Control.Invoke with the stack trace of the failure kept
        private void InvokeMarshaled(System.Windows.Forms.MethodInvoker method)
        {
            if (!InvokeRequired) { method(); return; }
            ExceptionDispatchInfo captured = null;
            using (var done = new ManualResetEventSlim())
            {
                _pending.Enqueue(() =>
                {
                    try { method(); }
                    catch (Exception ex) { captured = ExceptionDispatchInfo.Capture(ex); }
                    finally { done.Set(); }
                });
                // The post enters the toolkit (Python), which the user-interface thread may hold while it waits in
                // WaitFor: a pool thread posts, this thread only waits for the call itself
                ThreadPool.QueueUserWorkItem(_ => _post(Drain));
                done.Wait();
            }
            if (captured != null) captured.Throw();
        }
        private void Drain()
        {
            while (_pending.TryDequeue(out Action action)) action();
        }
        /// <summary>Waits on the user-interface thread for a controller task whose work calls the view. The original
        /// forms await these tasks (the message loop keeps running); a synchronous wait runs the marshalled view calls
        /// itself, or the task and this thread would wait for each other.</summary>
        public static void WaitFor(Task task)
        {
            OriginalViewHost host = _current;
            if (host != null && !host.InvokeRequired)
            {
                IAsyncResult result = task;
                while (!task.IsCompleted)
                {
                    host.Drain();
                    result.AsyncWaitHandle.WaitOne(5);
                }
                host.Drain();
            }
            task.GetAwaiter().GetResult();
        }

        // The "Vtk" block of the FrmMain constructor: the view asks the controller for its data. The handlers that
        // belong to FrmMain's tree and forms (selection, part picks, widget menus and settings) are the toolkit's;
        // it subscribes to OnMouseLeftButtonUpSelection and sets Controller_ActorsPicked and the Form_ callbacks.
        public void WireController(Controller _controller)
        {
            _vtk.RotationPointChanged += _controller.RotationPointChanged;       // FrmMain._vtk_RotationPointChanged
            _vtk.Controller_GetAnnotationText += _controller.GetAnnotationText;
            _vtk.Controller_GetSectionViewHatchGroup = _controller.GetSectionViewHatchGroup;
            _vtk.Controller_AnimationFrameChanged = _controller.AnimationFrameChanged;
            _vtk.Controller_GetAnimationLocatorNodes = _controller.GetAnimationLocatorNodes;
            _vtk.Controller_GetVolumeGridData = _controller.GetVolumeGridData;
            _vtk.Controller_GetAnimationNodes = _controller.GetAnimationNodes;
            _vtk.Controller_GetNodeActorData = _controller.GetNodeActorData;
            _vtk.Controller_GetCellActorData = _controller.GetCellActorData;
            _vtk.Controller_GetCellFaceActorData = _controller.GetCellFaceActorData;
            _vtk.Controller_GetEdgeActorData = _controller.GetEdgeActorData;
            _vtk.Controller_GetSurfaceEdgesActorDataFromElementId = _controller.GetSurfaceEdgesActorDataFromElementId;
            _vtk.Controller_GetSurfaceEdgesActorDataFromNodeAndElementIds =
                _controller.GetSurfaceEdgesActorDataFromNodeAndElementIds;
            _vtk.Controller_GetPartActorData = _controller.GetPartActorData;
            _vtk.Controller_GetGeometryActorData = _controller.GetGeometryActorData;
            _vtk.Controller_GetGeometryVertexActorData = _controller.GetGeometryVertexActorData;
        }

        // The view statements of the MIXED members of generate-view-host.py
        // FrmMain.ClearControls: the tree, the output and the result controls are the toolkit's
        public void ClearControls()
        {
            InvokeIfRequired(() =>
            {
                _vtk.Clear();
                _vtk.RemoveAllArrowWidgets();
            });
        }
        // FrmMain.Clear3D: the viewport text editor is not ported (pending), so nothing is committed first
        public void Clear3D()
        {
            InvokeIfRequired(_vtk.Clear);
        }
        // FrmMain.SetAnimationFrame: as Clear3D
        public void SetAnimationFrame(int frameNum, bool scalarRangeFromAllFrames)
        {
            InvokeIfRequired(_vtk.SetAnimationFrame, frameNum, scalarRangeFromAllFrames);
        }
        // FrmMain.SetCurrentEdgesVisibilities: the toolkit checks the edge buttons and updates the highlight
        public void SetCurrentEdgesVisibilities(vtkControl.vtkEdgesVisibility edgesVisibility)
        {
            InvokeIfRequired(() => _vtk.EdgesVisibility = edgesVisibility);
        }
    }
}
