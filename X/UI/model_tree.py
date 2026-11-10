"""Original UserControls/ModelTree: Geometry / FE Model / Results tabs, search box,
static node layout, node images and the tree context menu.

Layout, texts, images and menu items come from original_model_tree.json
(generate-model-tree.py). Item state and menu fields come from the C# port of the
ModelTree rules (Workbench/OriginalModelTree.cs). This module ports
PrepareToolStripItem, FilterTree, the tab events and the menu actions; each action
runs the same FrmMain helper as the original main menu item (main_menu.apply_target),
so confirmations and Controller commands are shared.
"""
import json
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
from System import Array, String
from PrePoMax import ViewGeometryModelResults

from main_menu import MENU, leaves
from main_toolbars import original_icon

TREE = json.loads(Path(__file__).with_name('original_model_tree.json').read_text(encoding='utf-8'))
ROLE = QtCore.Qt.ItemDataRole.UserRole
KEY = QtCore.Qt.ItemDataRole.UserRole + 1
VIEWS = {'tpGeometry': 'Geometry', 'tpModel': 'Model', 'tpResults': 'Results'}
# Original static node -> session family, per tree.
FAMILIES = {
    'Geometry': {'Parts': 'Geometry parts', 'Mesh Setup': 'Mesh setup'},
    'Model': {'Parts': 'Parts', 'Node Sets': 'Node sets', 'Element Sets': 'Element sets', 'Surfaces': 'Surfaces',
              'Reference Points': 'Reference points', 'Coordinate Systems': 'Coordinate systems', 'Materials': 'Materials',
              'Sections': 'Sections', 'Constraints': 'Constraints', 'Surface Interactions': 'Surface interactions',
              'Contact Pairs': 'Contact pairs', 'Distributions': 'Distributions', 'Amplitudes': 'Amplitudes',
              'Initial Conditions': 'Initial conditions', 'Steps': 'Steps', 'Analyses': 'Jobs'},
    'Results': {'Parts': 'Result parts', 'Node Sets': 'Result node sets', 'Element Sets': 'Result element sets',
                'Surfaces': 'Result surfaces', 'Reference Points': 'Result reference points',
                'Coordinate Systems': 'Result coordinate systems', 'Field Outputs': 'Result fields',
                'History Outputs': 'Result histories'},
}
STEP_FAMILIES = {'History Outputs': 'History outputs', 'Field Outputs': 'Field outputs', 'BCs': 'Boundary conditions',
                 'Loads': 'Loads', 'Defined Fields': 'Defined fields'}
# FrmMain helper suffix per family (HideModelParts, DeleteNodeSets, ...).
SUFFIX = {'Geometry parts': 'GeometryParts', 'Parts': 'ModelParts', 'Result parts': 'ResultParts', 'Node sets': 'NodeSets',
          'Element sets': 'ElementSets', 'Surfaces': 'Surfaces', 'Reference points': 'ModelReferencePoints',
          'Coordinate systems': 'ModelCoordinateSystems', 'Result reference points': 'ResultReferencePoints',
          'Result coordinate systems': 'ResultCoordinateSystems', 'Materials': 'Materials', 'Sections': 'Sections',
          'Constraints': 'Constraints', 'Surface interactions': 'SurfaceInteractions', 'Contact pairs': 'ContactPairs',
          'Distributions': 'Distributions', 'Amplitudes': 'Amplitudes', 'Initial conditions': 'InitialConditions',
          'Steps': 'Steps', 'History outputs': 'HistoryOutputs', 'Field outputs': 'FieldOutputs',
          'Boundary conditions': 'BoundaryConditions', 'Loads': 'Loads', 'Defined fields': 'DefinedFields',
          'Jobs': 'Analyses', 'Mesh setup': 'MeshSetupItems', 'Result fields': 'ResultFieldOutputs',
          'Result histories': 'ResultHistoryOutputs'}
SINGULAR = {'Boundary conditions': 'BoundaryCondition', 'Loads': 'Load', 'Defined fields': 'DefinedField',
            'History outputs': 'HistoryOutput', 'Field outputs': 'FieldOutput', 'Initial conditions': 'InitialCondition'}


class Folder:
    """A static original node without a session collection (Model, Mesh, Features, Contacts, Results)."""
    Family = 'Original folder'
    Group = True
    Step = None
    FolderId = None
    Type = 'Folder'
    Item = None
    Children = ()
    Text = None
    Icon = None
    Menu = ()
    Gray = False
    Invalid = False

    def __init__(self, name):
        self.Name = name


def item_count(entry):
    """CountOrderedDictionaryItemNodes: items, counted through folders."""
    return sum(item_count(c) if c.Group and c.FolderId else 1 for c in entry.Children)


def tree_icon(key):
    return original_icon(TREE['icons'].get(key)) if key else QtGui.QIcon()


def select_specs():
    specs = {}
    for top in MENU['menus']:
        for node in leaves(top):
            select = node.get('select')
            if select:
                select = select.get('inStep', select)
                specs.setdefault(select['target'], select)
    return specs


class OriginalModelTreeWorkbench:
    # ------------------------------------------------------------------ build
    def build_original_tree(self):
        """Replace the single tree header by the original tab control with a search box per tab."""
        self.tree_specs = select_specs()
        splitter = self.tree.parentWidget()
        index = splitter.indexOf(self.tree)
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.tree_tabs = QtWidgets.QTabBar()
        for tab in TREE['tabs']:
            self.tree_tabs.addTab(tab['text'])
        self.tree_tabs.currentChanged.connect(lambda index: self.guard(lambda: self.tree_tab_changed(index)))
        self.tree_search = QtWidgets.QLineEdit()
        self.tree_search.setPlaceholderText('Search')
        self.tree_search.setClearButtonEnabled(True)
        self.tree_search_text = {}
        self.tree_search.textChanged.connect(lambda text: self.guard(lambda: self.filter_tree(text)))
        layout.addWidget(self.tree_tabs)
        layout.addWidget(self.tree_search)
        layout.addWidget(self.tree)
        splitter.insertWidget(index, panel)
        self.tree.setHeaderHidden(True)
        self.tree.setIconSize(QtCore.QSize(16, 16))
        self.tree.itemExpanded.connect(self._update_dots)
        self.tree.itemCollapsed.connect(self._update_dots)
        try:
            self.tree.customContextMenuRequested.disconnect()
            self.tree.itemDoubleClicked.disconnect()
        except TypeError:
            pass
        self.tree.customContextMenuRequested.connect(lambda position: self.guard(lambda: self.original_tree_menu(position)))
        self.tree.itemDoubleClicked.connect(lambda item, column: self.guard(lambda: self.original_double_click(item)))

    def current_tree_view(self):
        return str(self.controller.CurrentView)

    def tree_tab_changed(self, index):
        """ModelTree tcGeometryModelResults_SelectedIndexChanged -> FrmMain.ModelTree_ViewEvent."""
        view = VIEWS[TREE['tabs'][index]['id']]
        if view == self.current_tree_view():
            return
        if self.active_editor is not None:  # tcGeometryModelResults_Deselecting: cancelled while a form is open
            self.sync_tree_tab()
            return
        from CaeGlobals import vtkSelectBy
        self.controller.SelectBy = vtkSelectBy.Default
        self.view.setCurrentText(view)

    def sync_tree_tab(self):
        if not hasattr(self, 'tree_tabs'):
            return
        view = self.current_tree_view()
        index = next(i for i, t in enumerate(TREE['tabs']) if VIEWS[t['id']] == view)
        self.tree_tabs.blockSignals(True)
        self.tree_tabs.setCurrentIndex(index)
        self.tree_tabs.blockSignals(False)
        self.tree_search.blockSignals(True)
        self.tree_search.setText(self.tree_search_text.get(view, ''))
        self.tree_search.blockSignals(False)

    # -------------------------------------------------------------- populate
    def original_tree_entries(self):
        c = self.controller
        if c.CurrentView == ViewGeometryModelResults.Geometry:
            return {e.Family: e for e in self.geometry.Tree}
        if c.CurrentView == ViewGeometryModelResults.Results:
            return {e.Family: e for e in self.results.Tree}
        entries = {e.Family: e for e in self.authoring.Tree}
        entries['Jobs'] = self.results.Jobs
        return entries

    def populate_original_tree(self, expanded, selected_keys):
        view = self.current_tree_view()
        entries = self.original_tree_entries()
        tree_id = next(t['tree'] for t in TREE['tabs'] if VIEWS[t['id']] == view)
        self.tree_view_name = view

        def add_entry(parent, entry, text=None, icon=None):
            item = QtWidgets.QTreeWidgetItem(parent, [text or entry.Text or entry.Name])
            key = (entry.Family, entry.Step or '', entry.FolderId or entry.Name)
            item.setData(0, ROLE, entry)
            item.setData(0, KEY, key)
            item.setToolTip(0, str(entry.Type or entry.Family))
            item.setIcon(0, tree_icon(icon or entry.Icon))
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole + 2, icon or entry.Icon)
            if getattr(entry, 'Gray', False):
                item.setForeground(0, QtGui.QBrush(QtGui.QColor('gray')))
            if getattr(entry, 'Invalid', False):
                item.setForeground(0, QtGui.QBrush(QtGui.QColor(200, 0, 0)))
            if entry.Family == 'Steps' and not entry.Group:
                self._add_step_children(item, entry, add_entry)
            else:
                for child in entry.Children:
                    add_entry(item, child)
            item.setExpanded(expanded.get(key, bool(entry.Group)))
            item.setSelected(key in selected_keys)
            return item

        def add_static(parent, node):
            family = FAMILIES[view].get(node['name'])
            entry = entries.get(family) if family else None
            if node['name'] == 'Model' and view == 'Model':
                entry = entries.get('Model properties')
            if entry is None:
                entry = Folder(node['text'])
            text = node['text']
            if family and entry.Group:
                n = item_count(entry)
                if n > 0:
                    text += ' (' + str(n) + ')'
            item = add_entry(parent, entry, text, node.get('image'))
            if node['name'] == 'Model' and view == 'Model':
                item.setData(0, QtCore.Qt.ItemDataRole.UserRole + 3, 'Model')
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole + 4, node['name'])
            for child in node.get('children', []):
                add_static(item, child)
            if isinstance(entry, Folder) or node['name'] == 'Model':
                item.setExpanded(expanded.get(item.data(0, KEY), True))
            return item

        for node in TREE['trees'][tree_id]:
            add_static(self.tree, node)
        for item in self.walk_tree():
            self._update_dots(item)
        text = getattr(self, 'tree_search_text', {}).get(view, '')
        if text:
            self._apply_filter(text)

    def _add_step_children(self, item, entry, add_entry):
        """AddStep: History Outputs, Field Outputs, BCs, Loads, Defined Fields (with counts)."""
        by_family = {c.Family: c for c in entry.Children}
        for node in TREE['stepNodes']:
            child = by_family.get(STEP_FAMILIES[node['name']])
            if child is None:
                continue
            n = item_count(child)
            text = node['name'] + (' (' + str(n) + ')' if n > 0 else '')
            sub = add_entry(item, child, text, node['image'])
            sub.setData(0, QtCore.Qt.ItemDataRole.UserRole + 4, node['name'])

    def _update_dots(self, item):
        """SetAllNodesStatusIcons: Dots.ico / Dots_t.ico by expansion."""
        key = item.data(0, QtCore.Qt.ItemDataRole.UserRole + 2)
        if key in ('Dots.ico', 'Dots_t.ico'):
            item.setIcon(0, tree_icon('Dots_t.ico' if item.childCount() and item.isExpanded() else 'Dots.ico'))

    # ---------------------------------------------------------------- filter
    def filter_tree(self, text):
        self.tree_search_text[self.current_tree_view()] = text
        self.refresh()

    def _apply_filter(self, text):
        """ModelTree.FilterTree/FilterNodes: leaves whose text contains none of the words are removed."""
        words = text.upper().split()

        def prune(parent):
            for index in reversed(range(parent.childCount())):
                child = parent.child(index)
                prune(child)
                if child.childCount() == 0 and not any(w in child.text(0).strip().upper() for w in words):
                    parent.removeChild(child)
        prune(self.tree.invisibleRootItem())
        self.tree.expandAll()

    # ---------------------------------------------------------- double click
    def original_double_click(self, item):
        """cltv_MouseDoubleClick: a static node creates (CanCreate) or toggles; an item is edited."""
        entry = item.data(0, ROLE)
        if entry is None or len(self.tree.selectedItems()) != 1:
            return
        if item.data(0, QtCore.Qt.ItemDataRole.UserRole + 3) == 'Model':
            return self.tree_action('tsmiEdit', [item])
        if entry.Group and not entry.FolderId:
            fields = self.node_fields(item)
            if 'Create' in fields:
                return self.tree_action('tsmiCreate', [item])
        if entry.Group:
            item.setExpanded(not item.isExpanded())
            return
        self.tree_action('tsmiEdit', [item])

    # ----------------------------------------------------------- menu rules
    def node_fields(self, item):
        from PrePoMaxX.UI import OriginalModelTree
        entry = item.data(0, ROLE)
        if item.data(0, QtCore.Qt.ItemDataRole.UserRole + 3) == 'Model':
            return list(OriginalModelTree.GroupFields('Model', 'Model'))
        if entry is None:
            return []
        if entry.Group and not entry.FolderId:
            name = item.data(0, QtCore.Qt.ItemDataRole.UserRole + 4) or ''
            return list(OriginalModelTree.GroupFields(name, self.current_tree_view())) if name else []
        return list(entry.Menu) if hasattr(entry, 'Menu') else []

    def action_items(self, items):
        """GetSelectedNodesIncludingGroupItems: folder (group) nodes act on their items."""
        result = []
        for item in items:
            entry = item.data(0, ROLE)
            if entry is not None and entry.Group and entry.FolderId:
                stack = [item.child(i) for i in range(item.childCount())]
                while stack:
                    child = stack.pop(0)
                    e = child.data(0, ROLE)
                    if e is not None and e.Group and e.FolderId:
                        stack += [child.child(i) for i in range(child.childCount())]
                    elif child not in result:
                        result.append(child)
            elif item not in result:
                result.append(item)
        return result

    def prepare_tree_menu(self, items):
        """ModelTree.PrepareToolStripItem: visible and enabled original items for the selection."""
        nodes = self.action_items(items)
        n = len(nodes)
        has = n > 0
        fields = {}
        types = set()
        for node in nodes:
            for f in self.node_fields(node):
                fields[f] = fields.get(f, 0) + 1
            entry = node.data(0, ROLE)
            if getattr(entry, 'Item', None) is not None:
                types.add(type(entry.Item).__name__)
        F = lambda name: fields.get(name, 0)
        visible = {}
        visible['tsmiCreate'] = has and F('Create') == n
        visible['tsmiEdit'] = has and F('Edit') == n
        visible['tsmiEditStepControls'] = has and F('EditStepControls') == n
        visible['tsmiQuery'] = F('Query') > 0
        visible['tsmiDuplicate'] = has and F('Duplicate') == n
        visible['tsmiPropagate'] = has and F('Propagate') == n
        visible['tsmiPreview'] = has and F('Preview') == n
        visible['tsmiAddToPlot'] = visible['tsmiAddToNewPlot'] = has and F('AddToPlot') == n
        visible['tsmiCompoundPart'] = F('CompoundPart') == n and n > 1
        visible['tsmiSwapPartGeometries'] = F('SwapParts') == n and n == 2
        # TryGetSplitCellsToGroup / TryGetBodiesToFuse are not ported yet: these items stay hidden.
        visible['tsmiGroupSplitCells'] = visible['tsmiFuseBodies'] = False
        visible['tsmiPreviewEdgeMesh'] = has and F('MeshingParameters') == n
        visible['tsmiCreateMesh'] = has and F('CreateMesh') == n
        visible['tsmiCopyGeometryToResults'] = visible['tsmiPreviewEdgeMesh']
        visible['tsmiEditCalculiXKeywords'] = F('EditCalculixKeywords') == n and n > 0
        visible['tsmiMergeParts'] = F('MergePart') == n and n > 1
        visible['tsmiConvertToPart'] = has and F('ConvertToPart') == n
        visible['tsmiMaterialLibrary'] = F('MaterialLibrary') == n and n > 0
        visible['tsmiSearchContactPairs'] = F('SearchContactPairs') == n and n > 0
        visible['tsmiSwapMasterSlave'] = F('SwapMergeMasterSlave') == n and n > 0
        visible['tsmiMergeByMasterSlave'] = visible['tsmiSwapMasterSlave'] and n > 1
        visible['tsmiHide'] = visible['tsmiShow'] = visible['tsmiShowOnly'] = has and F('Hide') + F('Show') == n
        visible['tsmiSetColor'] = visible['tsmiResetColor'] = visible['tsmiSetTransparency'] = has and F('ColorTransparency') == n
        visible['tsmiColorContoursOff'] = visible['tsmiColorContoursOn'] = \
            F('ResultRepresentationOn') + F('ResultRepresentationOff') == n and n > 0
        for key in ('tsmiRun', 'tsmiCheckModel', 'tsmiMonitor', 'tsmiResults', 'tsmiKill'):
            visible[key] = has and F('Run') == n
        visible['tsmiActivate'] = visible['tsmiDeactivate'] = has and F('Activate') + F('Deactivate') == n
        visible['tsmiCreateGroup'] = self.can_create_group(items)
        visible['tsmiExpandAll'] = visible['tsmiCollapseAll'] = True
        groups = [i for i in items if i.data(0, ROLE) is not None and i.data(0, ROLE).Group and i.data(0, ROLE).FolderId]
        compatible = bool(groups) and len({(g.data(0, ROLE).Family, g.data(0, ROLE).Step) for g in groups}) == 1
        if groups and len(groups) == len(items):
            visible['tsmiDelete'] = compatible
        elif groups:
            visible['tsmiDelete'] = compatible and has and F('Delete') == n
        else:
            visible['tsmiDelete'] = has and F('Delete') == n
        enabled = {k: True for k in visible}
        enabled['tsmiCreate'] = F('Create') == 1
        if types == {'GeometryPart'} or types == {'GeometryPart', 'CompoundGeometryPart'}:
            enabled['tsmiEdit'] = True
        else:
            enabled['tsmiEdit'] = F('Edit') == 1
        enabled['tsmiColorContoursOff'] = F('ResultRepresentationOn') > 0
        enabled['tsmiColorContoursOn'] = F('ResultRepresentationOff') > 0
        for key in ('tsmiRun', 'tsmiMonitor', 'tsmiResults', 'tsmiKill'):
            enabled[key] = F('Run') == 1
        return visible, enabled

    def can_create_group(self, items):
        """CanCreateOrderedDictionaryGroup: items of one organisable collection (or its root node)."""
        entries = [i.data(0, ROLE) for i in items]
        if not entries or any(e is None or isinstance(e, Folder) for e in entries):
            return False
        keys = {(e.Family, e.Step) for e in entries}
        if len(keys) != 1:
            return False
        family, step = next(iter(keys))
        if family not in SUFFIX or family.startswith('Result') or family in ('Mesh setup', 'Geometry parts'):
            return False
        return bool(self.authoring.CanOrganize(family, step))

    def original_tree_menu(self, position):
        item = self.tree.itemAt(position)
        if item is None:
            return
        if not item.isSelected():
            self.tree.clearSelection()
            item.setSelected(True)
        items = self.tree.selectedItems()
        visible, enabled = self.prepare_tree_menu(items)
        menu = QtWidgets.QMenu(self)
        self.tree_menu_actions = {}
        pending_separator = False
        for spec in TREE['contextMenu']:
            if spec.get('separator'):
                pending_separator = True
                continue
            if not visible.get(spec['id']):
                continue
            if pending_separator and menu.actions():
                menu.addSeparator()
            pending_separator = False
            action = menu.addAction(original_icon(spec.get('image')), spec['text'])
            action.setEnabled(enabled.get(spec['id'], True))
            self.tree_menu_actions[spec['id']] = action
            action.triggered.connect(lambda checked=False, key=spec['id']: self.guard(lambda: self.tree_action(key, items)))
        if menu.actions():
            menu.exec(self.tree.viewport().mapToGlobal(position))

    # --------------------------------------------------------------- actions
    def tree_action(self, key, items):
        nodes = self.action_items(items)
        entries = [n.data(0, ROLE) for n in nodes]
        first, entry = (nodes[0], entries[0]) if nodes else (None, None)
        c = self.controller
        menu = lambda handler: self.run_original_item(self.original_menu_nodes[handler])

        def grouped():
            groups = {}
            for e in entries:
                if e is not None and not e.Group:
                    groups.setdefault((e.Family, e.Step), []).append(str(e.Name))
            return groups

        def target(prefix, family, names, step):
            spec = self.tree_specs.get(prefix + SUFFIX.get(family, ''))
            if spec is None:
                raise ValueError('The original tree action is not available for ' + family + '.')
            return self.apply_target(spec, names, step)

        if key == 'tsmiCreate':
            if first.data(0, QtCore.Qt.ItemDataRole.UserRole + 4) == 'Mesh Setup':
                return self.edit_geometry('Mesh setup')
            if entry.Family == 'Jobs':
                return None if c.Model.Mesh is None else self.edit_results('Jobs')
            if entry.Family in ('Result fields', 'Result histories'):
                return self.edit_results(entry.Family)
            if entry.Family in self.NEEDS_MESH and c.Model.Mesh is None:
                return
            return self.edit_definition(entry.Family, entry.Step, None)
        if key == 'tsmiEdit':
            if first.data(0, QtCore.Qt.ItemDataRole.UserRole + 3) == 'Model':
                return self.edit_model()
            if entry.Family in ('Result node sets', 'Result element sets', 'Result surfaces'):
                return
            return self.edit_item(first)
        if key == 'tsmiEditStepControls':
            return self.edit_definition('Solution controls', str(entry.Name), None)
        if key == 'tsmiQuery':
            return self.query_dialog()
        if key == 'tsmiEditCalculiXKeywords':
            return menu('tsmiEditCalculiXKeywords_Click')
        if key == 'tsmiMaterialLibrary':
            return menu('tsmiMaterialLibrary_Click')
        if key == 'tsmiSearchContactPairs':
            return menu('tsmiSearchContactPairs_Click')
        if key in ('tsmiExpandAll', 'tsmiCollapseAll'):
            for item in items:
                stack = [item]
                while stack:
                    node = stack.pop()
                    node.setExpanded(key == 'tsmiExpandAll')
                    stack += [node.child(i) for i in range(node.childCount())]
            return
        if key in ('tsmiAddToPlot', 'tsmiAddToNewPlot'):
            if key == 'tsmiAddToNewPlot' or self.plot_panel.current() < 0:
                self.plot_panel.add()
            for e in entries:
                if e.Family == 'Amplitudes':
                    self.plot_panel.session.AddAmplitude(self.plot_panel.current(), e.Name)
                else:
                    self.plot_panel.session.AddHistory(self.plot_panel.current(), e.Item)
            self.plot_panel.rebuild()
            self.plot_dock.show()
            return
        if key == 'tsmiCreateGroup':
            text, ok = QtWidgets.QInputDialog.getText(self, 'Create group', 'Name')
            if ok:
                e = entries[0]
                names = [] if e.Group else [str(x.Name) for x in entries if not x.Group]
                self.authoring.CreateFolder(e.Family, e.Step, text, Array[String](names), e.FolderId if e.Group else None)
                self.refresh()
            return
        if key == 'tsmiDelete':
            folders = [i.data(0, ROLE) for i in items if i.data(0, ROLE).Group and i.data(0, ROLE).FolderId]
            for folder in folders:
                self.authoring.RemoveFolder(folder.Family, folder.Step, folder.FolderId)
            for (family, step), names in grouped().items():
                if family in ('Result field components', 'Result history fields', 'Result history components'):
                    for e in [x for x in entries if x.Family == family]:
                        self.remove_result_leaf(e)
                    continue
                target('Delete', family, names, step)
            return self.refresh()
        if key in ('tsmiActivate', 'tsmiDeactivate'):
            for (family, step), names in grouped().items():
                if family == 'Mesh setup':
                    self.geometry.SetActive(Array[String](names), key == 'tsmiActivate')
                else:
                    self.authoring.Activate(family, step, Array[String](names), key == 'tsmiActivate')
            return self.refresh()
        if key in ('tsmiPropagate', 'tsmiPreview'):
            prefix = 'Propagate' if key == 'tsmiPropagate' else 'Preview'
            for e in entries:
                spec = self.tree_specs[prefix + SINGULAR[e.Family]]
                self.apply_target(spec, str(e.Name), e.Step)
            return
        if key in ('tsmiRun', 'tsmiCheckModel', 'tsmiMonitor', 'tsmiResults', 'tsmiKill'):
            name = {'tsmiRun': 'RunAnalysis', 'tsmiCheckModel': 'CheckModel', 'tsmiMonitor': 'MonitorAnalysis',
                    'tsmiResults': 'ResultsAnalysis', 'tsmiKill': 'KillAnalysis'}[key]
            return self.custom_targets()[name](str(entry.Name), None)
        simple = {'tsmiCompoundPart': 'CreateAndImportCompoundPart', 'tsmiSwapPartGeometries': 'SwapPartGeometries',
                  'tsmiPreviewEdgeMesh': 'PreviewEdgeMesh', 'tsmiCopyGeometryToResults': 'CopyGeometryPartsToResults',
                  'tsmiConvertToPart': 'ConvertElementSetsToMeshParts',
                  'tsmiColorContoursOff': 'ResultRepresentationOffResultPart', 'tsmiColorContoursOn': 'ResultRepresentationOnResultPart'}
        if key in simple:
            names = [str(e.Name) for e in entries]
            spec = self.tree_specs.get(simple[key])
            custom = self.custom_targets().get(simple[key])
            if custom is not None:
                custom(names, None)
                return self.refresh()
            return self.apply_target(spec, names, None)
        if key == 'tsmiCreateMesh':
            parts = [str(e.Name) for e in entries if e.Family == 'Geometry parts']
            setups = [str(e.Name) for e in entries if e.Family == 'Mesh setup']
            if setups:
                for name in c.GetPartNamesToMeshFromMeshSetupItems(Array[String](setups)) or []:
                    if str(name) not in parts:
                        parts.append(str(name))
            if parts:
                self.custom_targets()['CreatePartMeshes'](parts, None)
            return
        prefixes = {'tsmiDuplicate': 'Duplicate', 'tsmiHide': 'Hide', 'tsmiShow': 'Show', 'tsmiShowOnly': 'ShowOnly',
                    'tsmiSetColor': 'SetColorFor', 'tsmiResetColor': 'ResetColorFor',
                    'tsmiSetTransparency': 'SetTransparencyFor', 'tsmiMergeParts': 'Merge',
                    'tsmiSwapMasterSlave': 'SwapMasterSlave', 'tsmiMergeByMasterSlave': 'MergeByMasterSlave'}
        if key in prefixes:
            for (family, step), names in grouped().items():
                target(prefixes[key], family, names, step)
            return self.refresh()
        raise ValueError('Unmapped original tree action ' + key)
