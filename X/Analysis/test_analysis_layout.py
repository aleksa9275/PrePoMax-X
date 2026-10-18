import unittest
from unittest.mock import patch
from pathlib import Path
import xml.etree.ElementTree as ET
import analysis_layout as layout


class SourceContracts(unittest.TestCase):
    def test_current_closure(self):
        self.assertEqual(len(layout.source_rows()), 146)

    def test_equation_algorithm_edit_rejected(self):
        original = layout.original
        def changed(revision, path):
            value = original(revision, path)
            return value.replace(b'GetValueFromEquation(_equation)', b'0') if path.endswith('EquationContainer.cs') else value
        with patch.object(layout, 'original', changed), self.assertRaises(ValueError):
            layout.source_rows()

    def test_original_formatter_edit_rejected(self):
        original = layout.original
        def changed(revision, path):
            value = original(revision, path)
            return value.replace(b'value.ToString("E8")', b'value.ToString("E6")') if path == layout.EXTENSIONS else value
        with patch.object(layout, 'original', changed), self.assertRaises(ValueError):
            layout.source_rows()

    def test_boundary_hash_edit_rejected(self):
        read = Path.read_bytes
        def changed(path):
            value = read(path)
            return value + b'changed' if path == layout.ROOT / layout.BOUNDARY else value
        with patch.object(Path, 'read_bytes', changed), self.assertRaises(ValueError):
            layout.source_rows()

    def test_type_owner_edit_rejected(self):
        parse = ET.parse
        def changed(path):
            tree = parse(path)
            if path == layout.HERE / 'CaeModel/CaeModel.csproj':
                item = next(i for i in tree.findall('.//Compile') if i.attrib['Include'].endswith('Materials/Material.cs'))
                item.attrib['Include'] = item.attrib['Include'].replace('CaeModel/', 'CaeGlobals/')
            return tree
        with patch.object(ET, 'parse', changed), self.assertRaises(ValueError):
            layout.source_rows()

    def test_dependency_version_edit_rejected(self):
        parse = ET.parse
        def changed(path):
            tree = parse(path)
            if path == layout.HERE / 'CaeGlobals/CaeGlobals.csproj':
                tree.findall('.//PackageReference')[0].attrib['Version'] = '[99.0.0]'
            return tree
        with patch.object(ET, 'parse', changed), self.assertRaises(ValueError):
            layout.source_rows()

    def test_coupled_legacy_member_edit_rejected(self):
        read = Path.read_bytes
        def changed(path):
            value = read(path)
            return value+b'changed' if path==layout.ROOT/'CaeModel/Steps/Step.Legacy.cs' else value
        with patch.object(Path,'read_bytes',changed), self.assertRaises(ValueError):
            layout.source_rows()

    def test_legacy_project_missing_partial_rejected(self):
        parse = ET.parse
        def changed(path):
            tree = parse(path)
            if path==layout.ROOT/'CaeModel/CaeModel.csproj':
                ns={'m':'http://schemas.microsoft.com/developer/msbuild/2003'}
                for group in tree.findall('.//m:ItemGroup',ns):
                    for child in list(group):
                        if child.attrib.get('Include')=='Steps\\Step.Legacy.cs':group.remove(child)
            return tree
        with patch.object(ET,'parse',changed), self.assertRaises(ValueError):
            layout.source_rows()

    def test_unreviewed_upstream_change_rejected(self):
        original = layout.original
        pin = '912fb3d08014f246d48bef14d62a2cba0fdf5bb0'
        def changed(revision, path):
            value = original(revision, path)
            return value + b'changed' if revision == pin and path.endswith('Materials/Material.cs') else value
        with patch.object(layout, 'original', changed), self.assertRaises(ValueError):
            layout.source_rows(pin)


if __name__ == '__main__': unittest.main()
