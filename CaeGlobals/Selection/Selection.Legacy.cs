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
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices.WindowsRuntime;
using System.Runtime.Serialization;
using System.Security.Policy;
using System.Text;
using System.Threading.Tasks;

namespace CaeGlobals
{
    public partial class Selection
    {
        public Selection(Selection selection, bool copyNodes, bool copyNodeHashes)
        {
            SelectionNode selectionNode;
            _nodes = new List<SelectionNode>();
            if (copyNodes)
            {
                foreach (var node in selection._nodes)
                {
                    selectionNode = node.DeepClone();
                    if (copyNodeHashes) selectionNode.Hash = node.Hash;
                    _nodes.Add(selectionNode);
                }
            }
            _selectItem = selection._selectItem;
            _currentView = selection._currentView;
            _maxNumberOfGeometryIds = selection._maxNumberOfGeometryIds;
            _maxNumberOfItemIds = selection._maxNumberOfItemIds;
            _limitSelectionToFirstPart = selection._limitSelectionToFirstPart;
            _limitSelectionToFirstGeometryType = selection._limitSelectionToFirstGeometryType;
            _limitSelectionToFirstMesherType = selection._limitSelectionToFirstMesherType;
            _limitSelectionToShellEdges = selection._limitSelectionToShellEdges;
            _enableShellEdgeFaceSelection = selection._enableShellEdgeFaceSelection;
        }
        public Selection DeepCopy(bool copyNodes, bool copyNodeHashes)
        {
            return new Selection(this, copyNodes, copyNodeHashes);
        }
    }
}
