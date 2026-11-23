// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using System;
using System.IO;
using System.Runtime.Serialization;

namespace PrePoMax.LegacyImport
{
    // The entry to the files PrePoMax wrote with the binary formatter before the storage payloads: the model data of a
    // .pmx file, a .pmh history, the settings and the material library. The application hands it to
    // CaeGlobals.ObjectSerializer.LegacyReader, which receives every stream that is not a storage payload.
    public static class LegacyReader
    {
        // PrePoMax-X: a host that sets this binder restricts the types a file may name to the ones it binds (an allowlist);
        // a name it does not bind is read as a type that no longer exists, and the binder throws for a refused one
        public static SerializationBinder RestrictingBinder;

        // Methods                                                                                                                  
        public static object Read(Stream stream)
        {
            if (RestrictingBinder != null) return new LegacyObjectReader(RestrictingBinder, true).Read(stream);
            return new LegacyObjectReader(RenamedTypeSerializationBinder.Instance).Read(stream);
        }
    }
}
