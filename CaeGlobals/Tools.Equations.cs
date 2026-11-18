// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using System;

namespace CaeGlobals
{
    [Serializable]
    public static partial class Tools
    {
        public static double GetPhase360(double phase)
        {
            return (phase % 360 + 360) % 360;
        }
    }
}
