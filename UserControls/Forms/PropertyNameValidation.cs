// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
// Licensed under the terms defined in the root LICENSE file.
using System;
using System.Collections.Generic;
using System.Linq;
using CaeGlobals;
namespace UserControls
{
    public static class PropertyNameValidation
    {
        public static void CheckName(string nameToEdit, string newName, ICollection<string> existingNames, string messageName)
        {
            // Named to existing name
            if ((nameToEdit == null && existingNames.Contains(newName, StringComparer.OrdinalIgnoreCase)) ||
            // Renamed to existing name
            ((nameToEdit != null && newName.ToLower() != nameToEdit.ToLower()) &&
             newName != nameToEdit && existingNames.Contains(newName, StringComparer.OrdinalIgnoreCase)))
            // Exception
            throw new CaeException("The selected "+ messageName + " name already exists. " +
                "Uppercase and lowercase letters are regarded as equal.");
        }
    }
}
