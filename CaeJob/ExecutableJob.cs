// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
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
using CaeGlobals;

namespace CaeJob
{
    //[Serializable]
    //public enum JobStatus
    //{
    //    None,
    //    InQueue,
    //    Running,
    //    OK,
    //    Killed,
    //    TimedOut,
    //    Failed
    //}

    [PmxType(6004)]
    public partial class ExecutableJob : NamedClass
    {
        // Variables                                                                                                                
        [PmxKey(0)] protected string _workDirectory;
        [PmxKey(1)] protected string _executable;
        [PmxKey(2)] protected string _argument;
        [PmxKey(3)] protected JobStatus _jobStatus;
        //
        [NonSerialized] protected Stopwatch _watch;
        [NonSerialized] protected Stopwatch _updateWatch;   // timer does not tick - use update watch
        [NonSerialized] private Process _exe;
        [NonSerialized] AutoResetEvent _outputWaitHandle;
        [NonSerialized] AutoResetEvent _errorWaitHandle;
        [NonSerialized] private StringBuilder _sbOutput;
        [NonSerialized] private string _outputFileName;
        [NonSerialized] private string _errorFileName;
        [NonSerialized] private object _myLock;
        [NonSerialized] private bool _allowConcurrentRuns;
        [NonSerialized] private TimeSpan _timeLimit;


        // Properties
        public override string Name
        {
            get { return base.Name; }
            set
            {
                base.Name = value;
                _argument = Name;
            }
        }
        public string WorkDirectory
        {
            get { return _workDirectory; }
            set { _workDirectory = value; }
        }
        public string Executable
        {
            get { return _executable; }
            set { _executable = value; }
        }
        public string Argument
        {
            get { return _argument; }
            set { _argument = value; }
        }
        public JobStatus JobStatus { get { return _jobStatus; } }
        /// <summary>
        /// Runs the executable while another process runs it, instead of waiting for that one to end.
        /// </summary>
        public bool AllowConcurrentRuns { get { return _allowConcurrentRuns; } set { _allowConcurrentRuns = value; } }
        /// <summary>
        /// How long the executable may run before it is stopped and the job ends as timed out.
        /// </summary>
        public TimeSpan TimeLimit { get { return _timeLimit; } set { _timeLimit = value; } }
        public string OutputData
        {
            get
            {
                try
                {
                    if (_sbOutput != null)
                    {
                        if (_myLock == null) _myLock = new object();
                        lock (_myLock) return _sbOutput.ToString();
                    }
                    else return null;
                }
                catch
                {
                    return null;
                }
            }
        }
        /// <summary>
        /// What the executable wrote to its standard error, which is where an executable of this solution
        /// writes the reason it failed.
        /// </summary>
        public string ErrorData
        {
            get
            {
                try
                {
                    if (_errorFileName != null && File.Exists(_errorFileName)) return File.ReadAllText(_errorFileName);
                    else return null;
                }
                catch
                {
                    return null;
                }
            }
        }


        // Events                                                                                                                           
        public event Action<string> AppendOutput;


        // Constructor                                                                                                              
        public ExecutableJob(string name, string executable, string argument, string workDirectory)
            : base(name)
        {
            _executable = executable;
            _argument = argument;
            _workDirectory = workDirectory;
            //
            _exe = null;
            _jobStatus = JobStatus.None;
            _watch = null;
            _updateWatch = null;
            _sbOutput = null;
            _allowConcurrentRuns = false;
            _timeLimit = TimeSpan.FromDays(21);
        }


        // Methods                                                                                                                  
        public void Submit()
        {
            if (_myLock == null) _myLock = new object();
            lock (_myLock)
            {
                if (_sbOutput == null) _sbOutput = new StringBuilder();
                _sbOutput.Clear();
            }
            //
            AddDataToOutput("Running command: " + _executable + " " + _argument);
            //
            _watch = new Stopwatch();
            _updateWatch = new Stopwatch();
            //
            _jobStatus = JobStatus.Running;
            //
            _watch.Start();
            _updateWatch.Start();
            //
            Run();
            //
            RunCompleted();
        }
        private void _exe_ErrorDataReceived(object sender, DataReceivedEventArgs e)
        {
            if (e.Data == null)
            {
                // The safe wait handle closes on kill
                if (!_errorWaitHandle.SafeWaitHandle.IsClosed) _errorWaitHandle.Set();
            }
            else
            {
                File.AppendAllText(_errorFileName, e.Data + Environment.NewLine);
                AddDataToOutput(e.Data);
            }
        }
        private void _exe_OutputDataReceived(object sender, DataReceivedEventArgs e)
        {
            if (e.Data == null)
            {
                // The safe wait handle closes on kill
                if (!_outputWaitHandle.SafeWaitHandle.IsClosed) _outputWaitHandle.Set();
            }
            else
            {
                AddDataToOutput(e.Data);
            }
        }
        void RunCompleted()
        {
            _watch.Stop();
            _updateWatch.Stop();
            //
            AddDataToOutput("");
            AddDataToOutput("Elapsed time [s]: " + _watch.Elapsed.TotalSeconds.ToString());
            //
            UpdateOutput();
            // Dereference the link to otheh objects
            AppendOutput = null;
        }
        //
        private void AddDataToOutput(string data)
        {
            if (_myLock == null) _myLock = new object();
            lock (_myLock) _sbOutput.AppendLine(data);
            //
            if (_updateWatch != null && _updateWatch.ElapsedMilliseconds > 1000)
            {
                UpdateOutput();
                _updateWatch.Restart();
            }
        }
        void UpdateOutput()
        {
            try
            {
                AppendOutput?.Invoke(OutputData);
                //
                if (_myLock == null) _myLock = new object();
                lock (_myLock)
                {
                    //if (Tools.WaitForFileToUnlock(_outputFileName, 5000))
                    if (_outputFileName != null)
                    {
                        File.AppendAllText(_outputFileName, OutputData);
                        _sbOutput.Clear();
                    }
                }
            }
            catch { }
        }
    }
}
