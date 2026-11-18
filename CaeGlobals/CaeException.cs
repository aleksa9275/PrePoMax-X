// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
// Source code: https://github.com/PrePoMax/PrePoMax
// Author: Matej Borovinšek
// Contributors: PrePoMax-X (separate the existing exception from Windows presentation)

using System;

namespace CaeGlobals
{
    public class CaeException : Exception
    {
        public CaeException()
        {
        }
        public CaeException(string message)
            : base(message)
        {
        }
        public CaeException(string message, Exception inner)
            : base(message, inner)
        {
        }
    }
}
