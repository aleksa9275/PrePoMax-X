// PrePoMax-X portable counterpart of CaeJob/AnalysisJob.Windows.cs (D062).
// The original enumerates child processes through WMI, which only exists on
// Windows; there the exception was swallowed by Kill() before the solver process
// itself was killed. Here the descendants are terminated with the .NET process-
// tree kill, keeping the original contract that the caller then kills the parent.
using System;
using System.Diagnostics;

namespace CaeJob
{
    public partial class AnalysisJob
    {
        public static void KillAllProcessesSpawnedBy(UInt32 parentProcessId)
        {
            Process parent;
            try { parent = Process.GetProcessById((int)parentProcessId); }
            catch (ArgumentException) { return; }   // already exited
            if (parent.Id == Process.GetCurrentProcess().Id) return;
            // Kills the parent together with all descendants; the original caller kills the parent next anyway.
            parent.Kill(entireProcessTree: true);
        }
    }
}
