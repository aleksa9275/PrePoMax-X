// PrePoMax-X modern process boundary. The original net48 implementation stays
// in ExecutableJob.Legacy.cs; no engineering algorithm or solver is selected here.
using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace CaeJob
{
    public partial class ExecutableJob
    {
        // Original Controller operations reuse their work directory and job
        // names during history replay. Hosts can allocate separate log folders
        // without changing native-tool working paths or overwriting evidence.
        public static Func<string,string,string> ProcessLogDirectoryFactory { get; set; }
        private static readonly ConcurrentDictionary<string,SemaphoreSlim> _executableSlots =
            new ConcurrentDictionary<string,SemaphoreSlim>(OperatingSystem.IsWindows() ? StringComparer.OrdinalIgnoreCase : StringComparer.Ordinal);
        [NonSerialized] private readonly object _processLock = new object();
        [NonSerialized] private readonly StringBuilder _capturedOutput = new StringBuilder();
        [NonSerialized] private readonly StringBuilder _capturedError = new StringBuilder();
        [NonSerialized] private bool _stopRequested;
        [NonSerialized] private int _submitted;
        [field: NonSerialized] public IReadOnlyList<string> ProcessArguments { get; set; }
        [field: NonSerialized] public IReadOnlyDictionary<string,string> ProcessEnvironment { get; set; }
        [field: NonSerialized] public bool ProcessStarted { get; private set; }
        [field: NonSerialized] public int? ExitCode { get; private set; }
        [field: NonSerialized] public string FailureReason { get; private set; }
        public string CapturedStandardOutput { get { lock (_capturedOutput) return _capturedOutput.ToString(); } }
        public string CapturedStandardError { get { lock (_capturedError) return _capturedError.ToString(); } }

        // One-shot asynchronous platform entry; original Submit/AppendOutput/status
        // semantics remain available. ArgumentList avoids shell quoting entirely.
        public Task SubmitAsync(CancellationToken cancellationToken = default)
        {
            if (Interlocked.Exchange(ref _submitted, 1) != 0)
                throw new InvalidOperationException("A portable job instance can be submitted once.");
            return Task.Run(() => {
                using (cancellationToken.Register(() => Kill("Cancellation requested."))) Submit();
            });
        }
        private void Run()
        {
            bool started = false;
            bool drained = false;
            SemaphoreSlim slot = null;
            bool ownsSlot = false;
            try
            {
                if (!Regex.IsMatch(Name, @"\A[A-Za-z0-9_-]{1,80}\z")) throw new ArgumentException("Simple job name required.");
                if (!Path.IsPathFullyQualified(_executable) || !File.Exists(_executable)) throw new FileNotFoundException("Absolute executable path required.");
                if (!Directory.Exists(_workDirectory)) throw new DirectoryNotFoundException("Working directory does not exist.");
                if (_timeLimit.TotalMilliseconds < 1 || _timeLimit.TotalMilliseconds > int.MaxValue)
                    throw new ArgumentException("Time limit must be between 1 ms and Int32.MaxValue ms.");
                if (!_allowConcurrentRuns)
                {
                    slot = _executableSlots.GetOrAdd(_executable, _ => new SemaphoreSlim(1,1));
                    double stopAt = Math.Min(5000, _timeLimit.TotalMilliseconds);
                    while (!(ownsSlot = slot.Wait(0)))
                    {
                        if (Volatile.Read(ref _stopRequested)) { _jobStatus = JobStatus.Killed; return; }
                        if (_watch.Elapsed.TotalMilliseconds >= stopAt) throw new IOException("The executable is busy in this host.");
                        Thread.Sleep(10);
                    }
                }
                string logDirectory = ProcessLogDirectoryFactory?.Invoke(_workDirectory, Name) ?? _workDirectory;
                if (!Path.IsPathFullyQualified(logDirectory)) throw new ArgumentException("Absolute process log directory required.");
                Directory.CreateDirectory(logDirectory);
                string outputPath = Path.Combine(logDirectory, "_output_" + Name + ".txt");
                string errorPath = Path.Combine(logDirectory, "_error_" + Name + ".txt");
                // Never overwrite evidence from an earlier run. Callers allocate a fresh run directory.
                using (new FileStream(outputPath, FileMode.CreateNew)) { }
                using (new FileStream(errorPath, FileMode.CreateNew)) { }
                _outputFileName = outputPath; _errorFileName = errorPath;
                var info = new ProcessStartInfo(_executable) {
                    WorkingDirectory = _workDirectory, UseShellExecute = false,
                    CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true,
                    RedirectStandardInput = true
                };
                if (ProcessArguments != null)
                    foreach (string value in ProcessArguments) info.ArgumentList.Add(value ?? throw new ArgumentException("Null argument."));
                else info.Arguments = _argument ?? "";
                if (ProcessEnvironment != null)
                    foreach (var value in ProcessEnvironment) info.Environment[value.Key] = value.Value;
                _outputWaitHandle = new AutoResetEvent(false); _errorWaitHandle = new AutoResetEvent(false);
                _exe = new Process { StartInfo = info };
                _exe.OutputDataReceived += (sender,e) => {
                    if (e.Data != null) lock (_capturedOutput) _capturedOutput.AppendLine(e.Data);
                    _exe_OutputDataReceived(sender,e);
                };
                _exe.ErrorDataReceived += (sender,e) => {
                    if (e.Data != null) lock (_capturedError) _capturedError.AppendLine(e.Data);
                    _exe_ErrorDataReceived(sender,e);
                };
                lock (_processLock)
                {
                    if (_stopRequested) { _jobStatus = JobStatus.Killed; return; }
                    _exe.Start(); started = true; ProcessStarted = true;
                    _exe.StandardInput.Close();
                    _exe.BeginOutputReadLine(); _exe.BeginErrorReadLine();
                }
                int Remaining() => Math.Max(0, (int)(_timeLimit.TotalMilliseconds - _watch.Elapsed.TotalMilliseconds));
                bool complete = _exe.WaitForExit(Remaining());
                if (complete) complete = _outputWaitHandle.WaitOne(Remaining()) && _errorWaitHandle.WaitOne(Remaining());
                drained = complete;
                if (!complete)
                {
                    lock (_processLock)
                    {
                        if (_jobStatus != JobStatus.Killed) _jobStatus = JobStatus.TimedOut;
                        StopProcess();
                    }
                    AddDataToOutput("Process/output deadline exceeded.");
                }
                if (_exe.WaitForExit(5000)) ExitCode = _exe.ExitCode;
                else throw new IOException("Process did not terminate after stop request.");
                lock (_processLock)
                    if (_jobStatus == JobStatus.Running) _jobStatus = ExitCode == 0 ? JobStatus.OK : JobStatus.Failed;
            }
            catch (Exception error) when (error is IOException || error is System.ComponentModel.Win32Exception ||
                error is ArgumentException || error is InvalidOperationException || error is UnauthorizedAccessException)
            {
                FailureReason = error.Message;
                lock (_processLock) { if (_jobStatus != JobStatus.Killed) _jobStatus = JobStatus.Failed; if (started) StopProcess(); }
                AddDataToOutput(error.Message);
            }
            finally
            {
                if (started)
                {
                    // Bounded drain after kill; never wait forever on inherited child pipes.
                    if (!drained) { _outputWaitHandle?.WaitOne(1000); _errorWaitHandle?.WaitOne(1000); }
                    try { _exe.CancelOutputRead(); } catch (InvalidOperationException) { }
                    try { _exe.CancelErrorRead(); } catch (InvalidOperationException) { }
                }
                _exe?.Dispose();
                // Event handlers may still finish; handles are small per-run resources and
                // are disposed only after Process has stopped delivering callbacks.
                _outputWaitHandle?.Dispose(); _errorWaitHandle?.Dispose();
                if (ownsSlot) slot.Release();
            }
        }
        public void Kill(string message)
        {
            lock (_processLock)
            {
                _stopRequested = true;
                if (_jobStatus == JobStatus.OK || _jobStatus == JobStatus.Failed || _jobStatus == JobStatus.TimedOut) return;
                _jobStatus = JobStatus.Killed;
                StopProcess();
            }
        }
        private void StopProcess()
        {
            try { if (_exe != null && !_exe.HasExited) _exe.Kill(entireProcessTree: true); }
            catch (InvalidOperationException) { }
            catch (System.ComponentModel.Win32Exception error) { FailureReason = error.Message; }
        }
    }
}
