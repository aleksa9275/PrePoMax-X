"""Original UserControls/ModelTree: Geometry / FE Model / Results tabs, search box,
static node layout, node images and the tree context menu.

Layout, texts, images and menu items come from original_model_tree.json
(generate-model-tree.py). Item state and menu fields come from the C# port of the
ModelTree rules (Workbench/OriginalModelTree.cs). This module ports
PrepareToolStripItem, FilterTree, the tab events and the menu actions; each action
runs the same FrmMain helper as the original main menu item (main_menu.apply_target),
so confirmations and Controller commands are shared. In-place rename (CanRename,
CheckNodeName, cltv_AfterLabelEdit), drag and drop of items, groups and steps
(cltv_ItemDrag/DragOver/DragDrop), tree groups (tsmiCreateGroup_Click) and the
keyboard keys (cltv_KeyDown) use the C# ports in Workbench/OriginalTreeLayout.cs.
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


def entry_of(item):
    return item.data(0, ROLE) if item is not None else None


def is_folder(entry):
    return entry is not None and bool(entry.Group) and bool(entry.FolderId)


def is_collection(entry):
    """A static collection node (the OrderedDictionaryTreeContext root)."""
    return entry is not None and bool(entry.Group) and not entry.FolderId and entry.Family not in ('Split sub parts', 'Original folder')


def single_split_compound(entry):
    item = getattr(entry, 'Item', None)
    if item is not None and type(item).__name__ == 'CompoundGeometryPart':
        name = item.GetSingleSplitSubPartName()
        return str(name) if name is not None else None
    return None


class TreeRenameDelegate(QtWidgets.QStyledItemDelegate):
    """Native label edit of CodersLabTreeView: IsNodeRenameable before, CheckNodeName and the rename event after."""

    def __init__(self, owner):
        super().__init__(owner.tree)
        self.owner = owner

    def createEditor(self, parent, option, index):
        if not self.owner.can_rename(self.owner.tree.itemFromIndex(index)):
            return None
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        editor.setText(self.owner.rename_text(self.owner.tree.itemFromIndex(index)))

    def setModelData(self, editor, model, index):
        item = self.owner.tree.itemFromIndex(index)
        entry, text = entry_of(item), editor.text()
        # The rename rebuilds the tree, which waits until the editor has closed (BeginInvoke in the original).
        QtCore.QTimer.singleShot(0, lambda: self.owner.guard(lambda: self.owner.rename_node(entry, text)))


class TreeDragFilter(QtCore.QObject):
    """cltv_DragEnter/DragOver/DragDrop on the tree viewport (drags start with the tree's own item drag)."""

    def __init__(self, owner):
        super().__init__(owner.tree)
        self.owner = owner

    def eventFilter(self, watched, event):
        kind = event.type()
        T = QtCore.QEvent.Type
        if kind == T.Leave:
            self.owner.tree_mouse_over(None)
            return False
        if kind not in (T.DragEnter, T.DragMove, T.Drop, T.DragLeave):
            return False
        owner = self.owner
        if kind == T.DragLeave:
            owner.tree_drop_hint(None)
            return True
        if event.source() is not owner.tree:
            event.ignore()
            return True
        if kind == T.DragEnter:
            owner.tree_drag = owner.drag_data(owner.tree.selectedItems())
            if owner.tree_drag is None:
                event.ignore()
            else:
                event.acceptProposedAction()
            return True
        target = owner.drop_target(event.position().toPoint()) if owner.tree_drag else None
        owner.tree_drop_hint(target)
        if target is None:
            event.ignore()
            return True
        # Copy: the view must not remove the dragged rows; the tree is rebuilt from the model.
        event.setDropAction(QtCore.Qt.DropAction.CopyAction)
        event.accept()
        if kind == T.Drop:
            data, owner.tree_drag = owner.tree_drag, None
            owner.tree_drop_hint(None)
            QtCore.QTimer.singleShot(0, lambda: owner.guard(lambda: owner.drop(data, target)))
        return True


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
        # In-place rename: a click on the selected node or F2 (CodersLabTreeView label edit).
        try:
            self.tree.itemChanged.disconnect()
        except TypeError:
            pass
        self.tree_rename_delegate = TreeRenameDelegate(self)
        self.tree.setItemDelegate(self.tree_rename_delegate)
        self.tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.SelectedClicked |
                                  QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed)
        # Drag and drop of ordered-dictionary items, groups and steps.
        self.tree_drag = None
        self.tree_drop_item = None
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(False)
        self.tree.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragDrop)
        self.tree_drag_filter = TreeDragFilter(self)
        self.tree.viewport().installEventFilter(self.tree_drag_filter)
        # Mouse over highlight (MouseOverNodeChangedEvent -> timerMouseMove -> SelectEvent(items, true)).
        self.tree.setMouseTracking(True)
        self.tree_hover_item = None
        self.tree_hover_timer = QtCore.QTimer(self)
        self.tree_hover_timer.setSingleShot(True)
        self.tree_hover_timer.setInterval(100)
        self.tree_hover_timer.timeout.connect(lambda: self.guard(self.tree_hover_highlight))
        self.tree.itemEntered.connect(self.tree_mouse_over)
        # cltv_KeyDown: Space inverts hide/show or activate/deactivate, Enter creates or edits.
        for key, callback in (('Space', self.invert_hide_show_or_activate), ('Return', self.tree_enter_key),
                              ('Enter', self.tree_enter_key)):
            shortcut = QtGui.QShortcut(QtGui.QKeySequence(key), self.tree)
            shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(lambda cb=callback: self.guard(cb))
            self.tree_shortcuts = getattr(self, 'tree_shortcuts', [])
            self.tree_shortcuts.append(shortcut)

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
            if self.can_rename_entry(entry):
                item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
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
            if node['name'] == 'Model' and view == 'Model':
                text = self.model_node_text(text)
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
            if is_folder(entry) or (entry is not None and entry.Family == 'Split sub parts'):
                stack = [item.child(i) for i in range(item.childCount())]
                while stack:
                    child = stack.pop(0)
                    e = child.data(0, ROLE)
                    if is_folder(e):
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
        visible['tsmiGroupSplitCells'] = self.split_cells_to_group(nodes) is not None
        visible['tsmiFuseBodies'] = self.bodies_to_fuse(nodes) is not None
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

    def can_organize(self, family, step):
        from PrePoMaxX.UI import OriginalTreeLayout
        return bool(OriginalTreeLayout.CanOrganize(self.controller, family, step))

    def can_create_group(self, items):
        """CanCreateOrderedDictionaryGroup: one collection or group node, or items of one organisable collection."""
        entries = [entry_of(i) for i in items]
        if not entries or any(e is None or isinstance(e, Folder) for e in entries):
            return False
        if len(entries) == 1 and (is_folder(entries[0]) or is_collection(entries[0])):
            return self.can_organize(entries[0].Family, entries[0].Step)
        if any(e.Group or self.compound_of(i) is not None for i, e in zip(items, entries)):
            return False
        keys = {(e.Family, e.Step) for e in entries}
        return len(keys) == 1 and self.can_organize(*next(iter(keys)))

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
            return self.create_tree_group(items)
        if key == 'tsmiDelete':
            return self.delete_tree_nodes(items)
        if key in ('tsmiGroupSplitCells', 'tsmiFuseBodies'):
            found = self.split_cells_to_group(nodes) if key == 'tsmiGroupSplitCells' else self.bodies_to_fuse(nodes)
            if found is not None:
                (self.group_split_cells_and_select if key == 'tsmiGroupSplitCells' else self.fuse_bodies_and_select)(found[0], found[1:])
            return
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

    # ---------------------------------------------------------------- groups
    def create_tree_group(self, items):
        """tsmiCreateGroup_Click: the group gets the next free name (GetNextGroupName/GetNextPartGroupName)."""
        from PrePoMaxX.UI import OriginalTreeLayout
        if not self.can_create_group(items):
            return
        entries = [entry_of(i) for i in items]
        e = entries[0]
        single = len(entries) == 1 and (is_folder(e) or is_collection(e))
        names = [] if single else [str(x.Name) for x in entries]
        OriginalTreeLayout.CreateGroup(self.controller, e.Family, e.Step, single, e.FolderId if single else None,
                                       Array[String](names))
        self.refresh()

    def delete_tree_nodes(self, items):
        """tsmiDelete_Click: only groups -> RemoveSelectedGroups (their items stay); otherwise the selected items
        (split sub parts as their cells) are deleted and the selected groups removed afterwards."""
        from PrePoMaxX.UI import OriginalTreeLayout
        entries = [entry_of(i) for i in items]
        folders = [e for e in entries if is_folder(e)]

        def remove_groups():
            if folders and len({(f.Family, f.Step) for f in folders}) == 1:
                OriginalTreeLayout.RemoveGroups(self.controller, folders[0].Family, folders[0].Step,
                                                Array[String]([str(f.FolderId) for f in folders]))
        if folders and len(folders) == len(entries):
            remove_groups()
            return self.refresh()
        direct = []
        for item, e in zip(items, entries):
            if e is not None and e.Family == 'Split sub parts':
                direct += [item.child(i) for i in range(item.childCount())]
            elif e is not None and not e.Group:
                direct.append(item)
        groups = {}
        for e in [entry_of(i) for i in direct]:
            if e is not None and not e.Group:
                groups.setdefault((e.Family, e.Step), []).append(e)
        for (family, step), group in groups.items():
            if family in ('Result field components', 'Result history fields', 'Result history components'):
                for e in group:
                    self.remove_result_leaf(e)
                continue
            spec = self.tree_specs.get('Delete' + SUFFIX.get(family, ''))
            if spec is None:
                raise ValueError('The original tree action is not available for ' + family + '.')
            self.apply_target(spec, [str(e.Name) for e in group], step)
        if folders:
            remove_groups()
        self.refresh()

    # ------------------------------------------------------- compound cells
    def compound_of(self, item):
        """IsCompoundGeometrySubPartNode: the compound a node hangs under, directly or through a split sub part."""
        parent = item.parent() if item is not None else None
        parent_entry = entry_of(parent)
        if parent_entry is None:
            return None
        if parent_entry.Family == 'Split sub parts':
            return str(parent_entry.Step)
        if type(getattr(parent_entry, 'Item', None)).__name__ == 'CompoundGeometryPart':
            return str(parent_entry.Name)
        return None

    def _compound_arguments(self, nodes):
        compounds = [self.compound_of(n) for n in nodes]
        cells = [str(entry_of(n).Name) if entry_of(n) is not None else '' for n in nodes]
        return Array[String](compounds), Array[String](cells)

    def split_cells_to_group(self, nodes):
        from PrePoMaxX.UI import OriginalModelTree
        if self.current_tree_view() != 'Geometry' or not nodes:
            return None
        found = OriginalModelTree.SplitCellsToGroup(self.controller, *self._compound_arguments(nodes))
        return [str(x) for x in found] if found is not None else None

    def bodies_to_fuse(self, nodes):
        from PrePoMaxX.UI import OriginalModelTree
        if self.current_tree_view() != 'Geometry' or not nodes:
            return None
        single = single_split_compound(entry_of(nodes[0])) if len(nodes) == 1 else None
        single = str(entry_of(nodes[0]).Name) if single else None
        found = OriginalModelTree.BodiesToFuse(self.controller, single, *self._compound_arguments(nodes))
        return [str(x) for x in found] if found is not None else None

    def select_tree_node(self, predicate, clear=True):
        if clear:
            self.tree.clearSelection()
        for item in self.walk_tree():
            if predicate(entry_of(item)):
                self.tree.clearSelection()
                item.setSelected(True)
                parent = item.parent()
                while parent is not None:
                    parent.setExpanded(True)
                    parent = parent.parent()
                self.tree.scrollToItem(item)
                return item
        return None

    def select_split_sub_part(self, compound, sub_part):
        """ModelTree.SelectSplitSubPart: the sub part node, or the compound when it reads as that part."""
        def sub_part_node(e):
            return e is not None and e.Family == 'Split sub parts' and str(e.Step) == compound and str(e.Name) == sub_part

        def cell_node(e):
            return (e is not None and not e.Group and e.Family == 'Geometry parts' and str(e.Name) == sub_part and
                    type(getattr(e, 'Item', None)).__name__ == 'GeometryPart')

        def compound_node(e):
            return e is not None and str(e.Name) == compound and single_split_compound(e) == sub_part
        for match in (sub_part_node, cell_node, compound_node):
            if self.select_tree_node(match, clear=False) is not None:
                return True
        return False

    def group_split_cells_and_select(self, compound, cells):
        """FrmMain.GroupSplitCellsAndSelect."""
        sub_part = self.controller.GroupSplitCellsCommand(compound, Array[String](cells), None)
        self.refresh()
        self.select_split_sub_part(compound, str(sub_part))

    def fuse_bodies_and_select(self, compound, cells):
        """FrmMain.FuseBodiesAndSelect: the fused cell's sub part, or the fused part itself."""
        c = self.controller
        fused = c.FuseBodiesCommand(compound, Array[String](cells))
        self.refresh()
        sub_part = c.GetSplitSubPartNameOfCell(fused) if fused is not None else None
        if sub_part is not None:
            self.select_split_sub_part(str(c.GetCompoundPartNameOfBody(fused)), str(sub_part))
        elif fused is not None:
            self.select_tree_node(lambda e: e is not None and not e.Group and e.Family == 'Geometry parts' and str(e.Name) == str(fused))

    # ---------------------------------------------------------------- rename
    def can_rename_entry(self, entry):
        """ModelTree.CanRename."""
        from PrePoMaxX.UI import OriginalModelTree
        if entry is None or isinstance(entry, Folder):
            return False
        if is_folder(entry) or entry.Family == 'Split sub parts':
            return True
        item = getattr(entry, 'Item', None)
        return item is not None and not entry.Group and bool(OriginalModelTree.CanRename(item))

    def can_rename(self, item):
        if item is None or len(self.tree.selectedItems()) > 1:
            return False
        if getattr(self, 'operation_task', None) is not None or self.active_editor is not None:
            return False
        return self.can_rename_entry(entry_of(item))

    def rename_text(self, item):
        entry = entry_of(item)
        return single_split_compound(entry) or str(entry.Name)

    def rename_selected(self):
        items = self.tree.selectedItems()
        if len(items) == 1 and self.can_rename(items[0]):
            self.tree.editItem(items[0], 0)

    def rename_tree_item(self, item, column):
        """Superseded by TreeRenameDelegate (original label edit)."""

    def rename_node(self, entry, text):
        """CodersLabTreeView.OnAfterLabelEdit + ModelTree.CheckNodeName + cltv_AfterLabelEdit."""
        from PrePoMaxX.UI import OriginalTreeLayout
        new_name = text.strip()
        if new_name == self.rename_text_of(entry):
            return
        if not new_name:
            raise ValueError('Name cannot be an empty string.')
        c = self.controller
        if is_folder(entry):
            if OriginalTreeLayout.CheckGroupName(c, entry.Family, entry.Step, entry.FolderId, new_name):
                OriginalTreeLayout.RenameGroup(c, entry.Family, entry.Step, entry.FolderId, new_name)
        elif entry.Family == 'Split sub parts':
            c.RenameSplitSubPartCommand(str(entry.Step), str(entry.Name), new_name)
        elif single_split_compound(entry):
            c.RenameSplitSubPartCommand(str(entry.Name), single_split_compound(entry), new_name)
        elif c.CheckItemName(entry.Item, new_name, entry.Step):
            c.RenameCommand(entry.Item, new_name, entry.Step)
        self.refresh()

    def rename_text_of(self, entry):
        return single_split_compound(entry) or str(entry.Name)

    # ---------------------------------------------------------- drag & drop
    def drag_data(self, items):
        """cltv_ItemDrag: steps, one group, or items of one ordered-dictionary collection."""
        from PrePoMaxX.UI import OriginalTreeLayout
        entries = [entry_of(i) for i in items]
        if not entries or any(e is None for e in entries) or any(self.compound_of(i) is not None for i in items):
            return None
        if all(e.Family == 'Steps' and not e.Group for e in entries):
            return {'steps': [str(e.Name) for e in entries]}
        if len(entries) == 1 and is_folder(entries[0]):
            e = entries[0]
            return {'family': e.Family, 'step': e.Step, 'group': str(e.FolderId), 'names': []} \
                if self.can_organize(e.Family, e.Step) else None
        if any(e.Group for e in entries) or len({(e.Family, e.Step) for e in entries}) != 1:
            return None
        e = entries[0]
        if not self.can_organize(e.Family, e.Step):
            return None
        names = OriginalTreeLayout.ItemNames(self.controller, e.Family, e.Step, Array[String]([str(x.Name) for x in entries]))
        return {'family': e.Family, 'step': e.Step, 'group': None, 'names': [str(n) for n in names]}

    def drop_target(self, point):
        """TryGetStepDropTarget / TryGetOrderedDictionaryDropTarget for the row under the pointer."""
        from PrePoMaxX.UI import OriginalTreeLayout
        item = self.tree.itemAt(point)
        e = entry_of(item)
        data = self.tree_drag
        if e is None or isinstance(e, Folder):
            return None
        rect = self.tree.visualItemRect(item)
        fraction = (point.y() - rect.top()) / max(1, rect.height())
        if 'steps' in data:
            if e.Family != 'Steps' or is_folder(e):
                return None
            index = OriginalTreeLayout.StepDropIndex(self.controller, Array[String](data['steps']),
                                                     None if e.Group else str(e.Name), fraction)
            return (item, index) if index >= 0 else None
        if (e.Family, e.Step) != (data['family'], data['step']):
            return None
        # Compound geometry parts are fixed presentation subtrees.
        if e.Family == 'Geometry parts' and (type(getattr(e, 'Item', None)).__name__ == 'CompoundGeometryPart'
                                             or self.compound_of(item) is not None):
            return None
        kind, key = ('Group', str(e.FolderId)) if is_folder(e) else ('Root', None) if e.Group else ('Item', str(e.Name))
        found = OriginalTreeLayout.DropTarget(self.controller, data['family'], data['step'], Array[String](data['names']),
                                              data['group'], kind, key, fraction)
        return (item, found) if found is not None else None

    def tree_drop_hint(self, target):
        """ShowDropIndicator / HideDropIndicator: the target row is marked while dragging."""
        previous, self.tree_drop_item = self.tree_drop_item, None
        try:
            if previous is not None:
                previous.setBackground(0, QtGui.QBrush())
        except RuntimeError:
            pass
        if target is not None:
            self.tree_drop_item = target[0]
            self.tree_drop_item.setBackground(0, QtGui.QBrush(self.palette().highlight().color().lighter(160)))

    def drop(self, data, target):
        """cltv_DragDrop: MoveStepsCommand or the ordered-dictionary layout change."""
        from PrePoMaxX.UI import OriginalTreeLayout
        if 'steps' in data:
            self.controller.MoveStepsCommand(Array[String](data['steps']), target[1])
        else:
            OriginalTreeLayout.Drop(self.controller, data['family'], data['step'], Array[String](data['names']),
                                    data['group'], target[1])
        self.refresh()

    # ------------------------------------------------------------ mouse over
    def tree_mouse_over(self, item):
        if item is self.tree_hover_item:
            return
        self.tree_hover_item = item
        self.tree_hover_timer.start()

    def node_items(self, item):
        """The NamedClass items of a node (a split sub part stands for its cells)."""
        e = entry_of(item)
        if e is None:
            return []
        if e.Family == 'Split sub parts':
            return [entry_of(item.child(i)).Item for i in range(item.childCount())
                    if entry_of(item.child(i)) is not None and entry_of(item.child(i)).Item is not None]
        return [e.Item] if getattr(e, 'Item', None) is not None else []

    def tree_hover_highlight(self):
        """timerMouseMove_Tick: selected items plus the item under the mouse, highlighted as mouse over."""
        if getattr(self, 'operation_task', None) is not None or self.active_editor is not None:
            return
        from System import Object
        items = []
        for selected in self.tree.selectedItems():
            items += self.node_items(selected)
        try:
            hover = self.tree_hover_item
            if hover is not None:
                items += self.node_items(hover)
        except RuntimeError:
            self.tree_hover_item = None
        self.controller.Highlight3DObjects(Array[Object](items), True)
        self.scene.show_selection(self.session.Presentation.SelectionActors)
        self.render()

    def tree_selection_changed(self):
        """cltv_SelectionsChanged: a single field data node selects that field; otherwise the selected items
        (split sub parts as their cells) are highlighted."""
        if getattr(self, 'operation_task', None) is not None or self.active_editor is not None:
            return
        from System import Object
        selected = self.tree.selectedItems()
        if len(selected) == 1 and entry_of(selected[0]) is not None and entry_of(selected[0]).Family == 'Result field components':
            self.controller.Highlight3DObjects(None)
            return self.open_result_leaf(entry_of(selected[0]))
        items = []
        for item in selected:
            items += self.node_items(item)
        if items:
            self.controller.Highlight3DObjects(Array[Object](items))
        else:
            self.controller.ClearAllSelection()
        self.scene.show_selection(self.session.Presentation.SelectionActors)
        self.render()

    # -------------------------------------------------------------- keyboard
    def remove_selected(self):
        """cltv_KeyDown Delete -> tsmiDelete_Click (when the menu item would be offered)."""
        items = self.tree.selectedItems()
        if items and self.prepare_tree_menu(items)[0].get('tsmiDelete'):
            self.tree_action('tsmiDelete', items)

    def tree_enter_key(self):
        """cltv_KeyDown Enter: a single static node creates, otherwise edit."""
        items = self.tree.selectedItems()
        if not items:
            return
        visible, enabled = self.prepare_tree_menu(items)
        if len(items) == 1 and is_collection(entry_of(items[0])) and visible.get('tsmiCreate'):
            return self.tree_action('tsmiCreate', items)
        if visible.get('tsmiEdit') and enabled.get('tsmiEdit'):
            self.tree_action('tsmiEdit', items)

    def invert_hide_show_or_activate(self):
        """InvertHideShowOrActivateDeactivate: hideable items swap visibility, the others activity."""
        from PrePoMaxX.UI import OriginalModelTree
        groups = {'tsmiHide': [], 'tsmiShow': [], 'tsmiDeactivate': [], 'tsmiActivate': []}
        for node in self.action_items(self.tree.selectedItems()):
            e = entry_of(node)
            item = getattr(e, 'Item', None)
            if item is None:
                continue
            if OriginalModelTree.CanHide(item):
                groups['tsmiHide' if item.Visible else 'tsmiShow'].append(node)
            elif 'Activate' in self.node_fields(node) or 'Deactivate' in self.node_fields(node):
                groups['tsmiDeactivate' if item.Active else 'tsmiActivate'].append(node)
        actions = [(key, nodes) for key, nodes in groups.items() if nodes]
        # Each action rebuilds the tree, so the nodes are resolved by entry before the first one.
        plans = [(key, [entry_of(n) for n in nodes]) for key, nodes in actions]
        for key, entries in plans:
            current = [i for i in self.walk_tree() if entry_of(i) is not None and any(
                not entry_of(i).Group and entry_of(i).Family == x.Family and entry_of(i).Step == x.Step and
                str(entry_of(i).Name) == str(x.Name) for x in entries)]
            if current:
                self.tree_action(key, current)

    # ------------------------------------------------------------ Model node
    def model_node_text(self, text):
        """UpdateNumberOfKeywords: '(User Keywords: n; Modified Keywords: m)'."""
        model = self.controller.Model
        counts = []
        if model is not None and model.CalculixUserKeywords is not None and model.CalculixUserKeywords.Count > 0:
            counts.append('User Keywords: ' + str(model.CalculixUserKeywords.Count))
        if model is not None and model.CalculixKeywordOverrides is not None:
            modified = model.GetNumberOfUnsuppressedKeywordOverrides()
            if modified > 0:
                counts.append('Modified Keywords: ' + str(modified))
        return text + (' (' + '; '.join(counts) + ')' if counts else '')
