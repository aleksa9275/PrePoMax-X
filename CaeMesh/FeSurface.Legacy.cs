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
using DynamicTypeDescriptor;
using CaeGlobals;

namespace CaeMesh
{
    public partial class FeSurface
    {
        public FeSurface(FeSurface surface)
            : base(surface)
        {
            _type = surface._type;
            _createdFrom = surface._createdFrom;
            _nodeSetName = surface._nodeSetName;
            _createdFromNodeSetName = surface._createdFromNodeSetName;
            _faceIds = surface._faceIds?.ToArray();
            _area = surface._area;
            _elementFaces = surface._elementFaces != null ? new Dictionary<FeFaceName, string>(surface._elementFaces) : null;
            _creationData = surface._creationData?.DeepCopy(true, false);
            _surfaceFaceTypes = surface._surfaceFaceTypes;
            _temporarySurface = surface._temporarySurface;
        }


    }
}
