// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://gitlab.com/MatejB/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Management;
using System.ComponentModel;
using CaeGlobals;

namespace CaeJob
{
    public partial class ExecutableJob
    {
        private void Run()
        {
            if (!File.Exists(_executable)) throw new Exception("The file '" + _executable + "' does not exist.");
            if (!_allowConcurrentRuns && !Tools.WaitForFileToUnlock(_executable, 5000))
                throw new Exception("The mesher is busy.");
            //
            string tmpName = Path.GetFileName(Name);
            _outputFileName = Path.Combine(_workDirectory, "_output_" + tmpName + ".txt");
            _errorFileName = Path.Combine(_workDirectory, "_error_" + tmpName + ".txt");
            //
            if (File.Exists(_outputFileName)) File.Delete(_outputFileName);
            if (File.Exists(_errorFileName)) File.Delete(_errorFileName);
            //
            ProcessStartInfo psi = new ProcessStartInfo();
            psi.CreateNoWindow = true;
            psi.FileName = _executable;
            psi.Arguments = _argument;
            psi.WorkingDirectory = _workDirectory;
            psi.WindowStyle = ProcessWindowStyle.Normal;
            psi.UseShellExecute = false;
            psi.RedirectStandardOutput = true;
            psi.RedirectStandardInput = true;   // sometimes needed
            psi.RedirectStandardError = true;
            //
            Debug.WriteLine(DateTime.Now + "   Start proces: " + tmpName + " in: " + _workDirectory);
            //
            _exe = new Process();
            _exe.StartInfo = psi;
            //
            _outputWaitHandle = new AutoResetEvent(false);
            _errorWaitHandle = new AutoResetEvent(false);
            {
                _exe.OutputDataReceived += _exe_OutputDataReceived;
                _exe.ErrorDataReceived += _exe_ErrorDataReceived;
                //
                _exe.Start();
                ChildProcessJob.Add(_exe);
                _exe.BeginOutputReadLine();
                _exe.BeginErrorReadLine();
                //
                int ms = (int)Math.Min(int.MaxValue, _timeLimit.TotalMilliseconds);
                //
                if (_exe.WaitForExit(ms) && _outputWaitHandle.WaitOne(ms) && _errorWaitHandle.WaitOne(ms))
                {
                    // Process completed. Check process. ExitCode here. After Kill() _jobStatus is Killed
                    if (_jobStatus == JobStatus.Running)
                    {
                        _jobStatus = JobStatus.OK;
                        if (_exe.ExitCode != 0) _jobStatus = JobStatus.Failed;
                    }
                }
                else
                {
                    Kill("The run was stopped after the time limit of " + _timeLimit.TotalMinutes + " min.");
                    _jobStatus = JobStatus.TimedOut;
                }
                _exe.Close();
            }
        }
        private void RunCompatible()
        {
            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = _executable;
            psi.Arguments = _argument;
            psi.WorkingDirectory = _workDirectory;
            psi.UseShellExecute = false;
            //
            //SetEnvironmentVariables(psi);
            //
            _exe = new Process();
            _exe.StartInfo = psi;
            _exe.Start();
            ChildProcessJob.Add(_exe);
            //
            int ms = 1000 * 3600 * 24 * 7 * 3; // 3 weeks
            if (_exe.WaitForExit(ms))
            {
                // Process completed. Check process.ExitCode here.

                // after Kill() _jobStatus is Killed
                _jobStatus = JobStatus.OK;
            }
            else
            {
                // Timed out.
                Kill("Time out.");
                //Debug.WriteLine(DateTime.Now + "   Timeout proces: " + Name + " in: " + _workDirectory);
                _jobStatus = JobStatus.TimedOut;
            }
            _exe.Close();
        }
        public void Kill(string message)
        {
            try
            {
                if (_exe != null)
                {
                    AddDataToOutput(message);
                    //
                    _watch.Stop();
                    _updateWatch.Stop();
                    //
                    _jobStatus = JobStatus.Killed;  // this has to be here before _exe.Kill, to return the correct status
                    //
                    KillAllProcessesSpawnedBy((UInt32)_exe.Id);
                    //
                    _exe.Kill();
                }
            }
            catch
            { }
            finally
            {
                // Dereference the link to other objects
                AppendOutput = null;
            }
        }
        private static void KillAllProcessesSpawnedBy(UInt32 parentProcessId)
        {
            // NOTE: Process Ids are reused!
            ManagementObjectSearcher searcher = new ManagementObjectSearcher(
                "SELECT * " +
                "FROM Win32_Process " +
                "WHERE ParentProcessId=" + parentProcessId);
            ManagementObjectCollection collection = searcher.Get();
            if (collection.Count > 0)
            {
                foreach (var item in collection)
                {
                    UInt32 childProcessId = (UInt32)item["ProcessId"];
                    if ((int)childProcessId != Process.GetCurrentProcess().Id)
                    {

                        KillAllProcessesSpawnedBy(childProcessId);

                        try
                        {
                            Process childProcess = Process.GetProcessById((int)childProcessId);
                            childProcess.Kill();
                            childProcess.WaitForExit(5000);
                        }
                        catch
                        {
                        }
                    }
                }
            }
        }
    }
}
