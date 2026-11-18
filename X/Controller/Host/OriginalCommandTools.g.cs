// Generated; original FrmEditCommands SHA256 094b49069119f11aee6864cd3f93ed1e7684eaab62efb421a948eb15e603885d
using System;using System.Collections.Generic;using System.Linq;using PrePoMax.Commands;
namespace PrePoMax {public static class OriginalCommandTools {public static List<Command> Reorganize(List<Command> commands)
        {
            List<Command> importCommands = new List<Command>();
            List<Command> meshSetupCommands = new List<Command>();
            List<CCreateMesh> meshCommands = new List<CCreateMesh>();
            //
            int count = 0;
            int index = -1;

            foreach (var command in commands)
            {
                if (command is CSetNewModelProperties)
                {
                    index = count;
                }
                else if (command is CImportFile)
                {
                    importCommands.Add(command);
                }
                else if (command is CAddMeshSetupItem || command is CReplaceMeshSetupItem || command is CDuplicateMeshSetupItems ||
                         command is CRemoveMeshSetupItems)
                {
                    meshSetupCommands.Add(command);
                }
                else if (command is CActivateDeactivate ad && ad.ContainsMeshSetupItem())
                {
                    meshSetupCommands.Add(command);
                }
                else if (command is CActivateDeactivateMultiple adm && adm.ContainsMeshSetupItem())
                {
                    meshSetupCommands.Add(command);
                }
                else if (command is CCreateMesh cm)
                {
                    meshCommands.Add(cm);
                }
                //
                count++;
            }
            //
            foreach (var command in importCommands) commands.Remove(command);
            foreach (var command in meshSetupCommands) commands.Remove(command);
            foreach (var command in meshCommands) commands.Remove(command);
            //
            index++;
            HashSet<string> meshedPartNames = new HashSet<string>();
            foreach (var command in importCommands) commands.Insert(index++, command);
            foreach (var command in meshSetupCommands) commands.Insert(index++, command);
            foreach (var command in meshCommands)
            {
                string[] newPartNames = command.PartNames.Where(name => meshedPartNames.Add(name)).ToArray();
                if (newPartNames.Length == command.PartNames.Length) commands.Insert(index++, command);
                else if (newPartNames.Length > 0) commands.Insert(index++, new CCreateMesh(newPartNames));
            }
            //
            return commands;
        }}}
