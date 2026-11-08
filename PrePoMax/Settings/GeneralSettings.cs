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
using System.ComponentModel;
using CaeGlobals;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.IO.Compression;
using DynamicTypeDescriptor;

namespace PrePoMax
{
    [Serializable]
    public enum RunPostProcessingEnum
    {
        [StandardValue("Yes", DisplayName = "Yes")]
        Yes,
        //
        [StandardValue("No", DisplayName = "No")]
        No,
        //
        [StandardValue("Ask", DisplayName = "Ask")]
        Ask,
    }
    [Serializable]
    public partial class GeneralSettings : ISettings
    {
        // Variables                                                                                                                
        private bool _openLastFile;
        private string _lastFileName;
        private bool _saveResultsInPmx;
        private CompressionLevel _compressionLevel;
        private UnitSystemType _unitSystemType;
        // CAD periodic surface split of older files when their history is regenerated
        private int _numOfSplitFaces;
        // Mesh edge angle
        private double _edgeAngle;
        // Post-processing
        private RunPostProcessingEnum _runHistoryPostprocessing;
        // Property editor
        private bool _showAllProperties;
        //
        private LinkedList<string> _recentFiles;
        private List<string> _materialLibraryFiles;
        // Form size and position
        private FormWindowState _formWindowState;
        private Size _formSize;
        private double _formRelativeXLocation;
        private double _formRelativeYLocation;


        // Properties                                                                                                               
        public bool OpenLastFile { get { return _openLastFile; } set { _openLastFile = value; } }
        public string LastFileName { get { return _lastFileName; } set { _lastFileName = value; } }
        public bool SaveResultsInPmx { get { return _saveResultsInPmx; } set { _saveResultsInPmx = value; } }
        public CompressionLevel CompressionLevel { get { return _compressionLevel; } set { _compressionLevel = value; } }
        public UnitSystemType UnitSystemType { get { return _unitSystemType; } set { _unitSystemType = value; } }
        public int NumOfSplitFaces
        {
            get { return _numOfSplitFaces; }
            set
            {
                _numOfSplitFaces = value;
                if (_numOfSplitFaces < 1) _numOfSplitFaces = 1;
            }
        }
        public double EdgeAngle
        {
            get { return _edgeAngle; }
            set
            {
                _edgeAngle = value;
                if (_edgeAngle < 0) _edgeAngle = 0;
                else if (_edgeAngle > 90) _edgeAngle = 90;
            }
        }
        public RunPostProcessingEnum RunHistoryPostprocessing
        {
            get { return _runHistoryPostprocessing; }
            set { _runHistoryPostprocessing = value; }
        }
        public bool ShowAllProperties { get { return _showAllProperties; } set { _showAllProperties = value; } }


        // Constructors                                                                                                             
        public GeneralSettings()
        {
            Reset();
        }


        // Methods                                                                                                                  
        public void CheckValues()
        {
        }
        public void Reset()
        {
            _openLastFile = false;
            _lastFileName = null;
            _saveResultsInPmx = true;
            _compressionLevel = CompressionLevel.Fastest;
            _unitSystemType = UnitSystemType.MM_TON_S_C;
            _numOfSplitFaces = 2;
            _edgeAngle = 30;
            _runHistoryPostprocessing = RunPostProcessingEnum.Ask;
            _showAllProperties = true;
            //
            ResetFormSize();
        }
        // Recent files
        public string[] GetRecentFiles()
        {
            if (_recentFiles != null) return _recentFiles.ToArray();
            else return null;
        }
        public void AddRecentFile(string fileNameWithPath)
        {
            if (_recentFiles == null) _recentFiles = new LinkedList<string>();
            //
            if (_recentFiles.Count == 0) _recentFiles.AddFirst(fileNameWithPath);
            else
            {
                if (!_recentFiles.Contains(fileNameWithPath))
                {
                    int _maxRecentFiles = 15;
                    while (_recentFiles.Count >= _maxRecentFiles) _recentFiles.RemoveLast();
                    _recentFiles.AddFirst(fileNameWithPath);
                }
                else
                {
                    _recentFiles.Remove(fileNameWithPath);
                    _recentFiles.AddFirst(fileNameWithPath);
                }
            }
        }
        public void RemoveRecentFile(string fileNameWithPath)
        {
            if (_recentFiles == null) _recentFiles = new LinkedList<string>();
            if (_recentFiles.Count > 0) _recentFiles.Remove(fileNameWithPath);
        }

        public void ClearRecentFiles()
        {
            _recentFiles.Clear();
        }
        // Material library files
        public string[] GetMaterialLibraryFiles()
        {
            if (_materialLibraryFiles != null) return _materialLibraryFiles.ToArray();
            else return new string[0];
        }
        public void AddMaterialLibraryFile(string fileNameWithPath)
        {
            if (_materialLibraryFiles == null) _materialLibraryFiles = new List<string>();
            if (!_materialLibraryFiles.Contains(fileNameWithPath)) _materialLibraryFiles.Add(fileNameWithPath);
        }
        public void RemoveMaterialLibraryFile(string fileNameWithPath)
        {
            if (_materialLibraryFiles != null && _materialLibraryFiles.Contains(fileNameWithPath))
                _materialLibraryFiles.Remove(fileNameWithPath);
        }
        public void ClearMaterialLibraryFiles()
        {
            _materialLibraryFiles = null;
        }
        // Form size
        private void ResetFormSize()
        {
            _formWindowState = FormWindowState.Normal;
            _formSize = new Size(1280, 720);
            _formRelativeXLocation = 0.5;
            _formRelativeYLocation = 0.5;
        }
    }
}
