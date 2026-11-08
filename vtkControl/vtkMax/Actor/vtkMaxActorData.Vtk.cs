// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://gitlab.com/MatejB/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

// PrePoMax-X: rendering-dependent method, moved verbatim from vtkMaxActorData.cs
// so the data class builds without ActiViz (D062).

namespace vtkControl
{
    public partial class vtkMaxActorData
    {
        public double[][][] GetStlTriangles()
        {
            vtkMaxActor actor = new vtkMaxActor(this);
            return actor.GetStlTriangles();
        }
    }
}
