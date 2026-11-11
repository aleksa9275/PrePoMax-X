"""Executed UI evidence for the code editor forms compiled whole (C12), run as a step of forms_gui_probe.py on the
imported public deck: FrmCalculixKeywordEditor (the original CalculixInpTextBox on the FastColoredTextBox model) and
FrmEditCommands (the original PythonEditorTextBox, its grid and FrmViewObjectProperties). Text is typed with Qt key
events into the editor widgets; the original handlers and the editor model do the rest."""
from PyQt6 import QtCore, QtTest

from forms_gui_probe_child import ChildFormsProbe


class EditorFormsProbe(ChildFormsProbe):
    def editor_widget(self, form, text_box):
        """The Qt editor drawing the FastColoredTextBox inside an original text box control."""
        from FastColoredTextBoxNS import FastColoredTextBox
        inner = next(x for x in self.walk(text_box) if isinstance(x, FastColoredTextBox))
        _, widget = self.widget(form, inner)
        return inner, widget

    def type_keys(self, widget, text):
        widget.setFocus()
        QtTest.QTest.keyClicks(widget, text)
        self.renderer.flush()
        self.app.processEvents()

    def key(self, widget, key, modifier=QtCore.Qt.KeyboardModifier.NoModifier):
        QtTest.QTest.keyClick(widget, key, modifier)
        self.renderer.flush()
        self.app.processEvents()

    def keyword_editor(self):
        """FrmCalculixKeywordEditor: the keyword tree, the .inp preview with the original CalculiX styles, a user
        keyword added under the selected keyword and typed into the keyword text box, OK -> the editor state command."""
        c = self.c
        report = self.report['forms'].setdefault('FrmCalculixKeywordEditor', {})
        user_before = c.GetCalculixUserKeywords()
        count_before = 0 if user_before is None else user_before.Count

        def operate(form):
            self.check('Edit CalculiX keywords opens the original modal FrmCalculixKeywordEditor',
                       type(form).__name__ == 'FrmCalculixKeywordEditor' and form.Modal)
            tree = self.by_name(form, 'cltvKeywordsTree')
            inp = self.by_name(form, 'citbInpFile')
            keyword_box = self.by_name(form, 'citbKeyword')
            roots = [str(n.Text) for n in tree.Nodes]
            report['treeRoots'] = roots
            report['inpLines'] = int(inp.LineCount)
            self.check('the keyword tree holds the model keywords (PrepareForm)', len(roots) > 0 and tree.Nodes[0].Nodes.Count > 0)
            self.check('the .inp preview holds the whole input file', inp.LineCount > 10 and '*NODE' in str(inp.Text).upper())
            inner, inp_widget = self.editor_widget(form, inp)
            inner.FlushDelayedEvents()
            styled = {}
            for i in range(min(int(inner.LinesCount), 400)):
                line = str(inner.GetLineText(i))
                runs = list(inner.GetLineRuns(i))
                if runs and runs[2] and line[:1] == '*':
                    styled[line[:2] == '**'] = runs[2] & 0xffffff
            report['styles'] = {('comment' if k else 'keyword'): hex(v) for k, v in styled.items()}
            self.check('CalculixInpTextBox colours keyword lines blue (ApplyCalculixStyles)', styled.get(False) == 0x0000ff)
            self.check('and comment lines green (the first text style of a character draws)', styled.get(True) == 0x008000)
            self.check('the preview is drawn by the code editor widget', inp_widget is not None and inp_widget.isVisible())
            # Select the step keyword node with a Qt click at its label (CodersLabTreeView)
            node = None
            for root in tree.Nodes:
                for child in root.Nodes:
                    if str(child.Text).strip('* ').upper().startswith('STEP'):
                        node = child
            if node is None:
                node = tree.Nodes[0].Nodes[0]
            node.EnsureVisible()
            self.renderer.flush()
            _, tree_widget = self.widget(form, tree)
            self.tree_click(tree_widget, node)
            report['selected'] = str(node.Text)
            report['keywordText'] = str(keyword_box.Text)[:200]
            self.check('a Qt click on a keyword node shows its text (cltvKeywordsTree_AfterSelect)',
                       tree.SelectedNode == node and str(node.Text).strip('* ').upper() in str(keyword_box.Text).upper())
            nodes_before = node.Nodes.Count
            self.click(form, 'btnAddKeyword')
            added = tree.SelectedNode
            self.check('Add keyword adds a user keyword under the selected keyword (btnAddKeyword_Click)',
                       node.Nodes.Count == nodes_before + 1 and added is not None and str(added.Text) == 'User keyword')
            kinner, kwidget = self.editor_widget(form, keyword_box)
            # Typed: select all, then the user keyword text with an Enter (Qt key events through the model)
            # The user clicks into the keyword text first (focus moves from the tree to the editor)
            QtTest.QTest.mouseClick(kwidget.viewport(), QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.NoModifier, QtCore.QPoint(60, 5))
            kwidget.setFocus()
            self.renderer.flush()
            self.app.processEvents()
            self.key(kwidget, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
            report['afterSelectAll'] = [str(kinner.Selection.Start), str(kinner.Selection.End), kwidget.hasFocus(), str(kinner.Text)[:40]]
            self.type_keys(kwidget, '*Node print, nset=Nall')
            self.key(kwidget, QtCore.Qt.Key.Key_Return)
            self.type_keys(kwidget, 'U')
            typed = str(keyword_box.Text).replace('\r\n', '\n')
            report['typed'] = typed
            self.check('Qt typing edits the keyword through FastColoredTextBox (select all, insert, Enter)',
                       typed == '*Node print, nset=Nall\nU')
            self.key(kwidget, QtCore.Qt.Key.Key_Z, QtCore.Qt.KeyboardModifier.ControlModifier)
            self.check('Ctrl+Z undoes the last typed character (FCTB undo)', str(keyword_box.Text).replace('\r\n', '\n') == '*Node print, nset=Nall\n')
            self.type_keys(kwidget, 'U')
            QtTest.QTest.qWait(700)   # tUpdate (500 ms) writes the keyword into the .inp preview
            self.renderer.flush()
            self.check('the preview shows the typed user keyword (tUpdate_Tick)', '*NODE PRINT, NSET=NALL' in str(inp.Text).upper())
            self.click(form, 'btnOK')
        self.modal('tsmiEditCalculiXKeywords_Click', operate)
        user = c.GetCalculixUserKeywords()
        texts = [] if user is None else [str(k.Data) for k in user.Values]
        report['userKeywords'] = texts
        self.check('OK stores the user keyword (SetCalculixKeywordEditorStateCommand)',
                   user is not None and user.Count == count_before + 1 and any('*Node print' in t for t in texts))

    def edit_commands(self):
        """FrmEditCommands: the history grid, the Python view (PythonEditorTextBox with the original highlighter),
        the selected command's lines, FrmViewObjectProperties on a double click, Delete and Cancel."""
        c = self.c
        report = self.report['forms'].setdefault('FrmEditCommands', {})
        commands = c.GetCommands().Count
        self.entry('tsmiEditHistory_Click')
        form = next((f for f in self.open_forms() if type(f).__name__ == 'FrmEditCommands'), None)
        self.check('Edit history opens the original FrmEditCommands', form is not None)
        grid = self.by_name(form, 'dgvCommands')
        report['rows'] = int(grid.Rows.Count)
        self.check('the history grid lists every command (PrepareForm)', grid.Rows.Count == commands)
        split = self.by_name(form, 'splMain')
        report['pythonCollapsed'] = bool(split.Panel2Collapsed)
        if split.Panel2Collapsed:
            show = next(i for i in self.by_name(form, 'msMain').Items[1].DropDownItems if str(i.Name) == 'tsmiShowPython')
            self.renderer.guard(show.PerformClick)
            self.renderer.flush()
        python = self.by_name(form, 'petbPython')
        inner, widget = self.editor_widget(form, python)
        inner.FlushDelayedEvents()
        script = str(python.ScriptText)
        report['pythonLines'] = int(inner.LinesCount)
        self.check('View > Python shows the history as a Python script (UpdatePythonScript)',
                   not split.Panel2Collapsed and 'import' in script and widget is not None and widget.isVisible())
        import re
        keyword_re = re.compile(r'\b(False|None|True|and|as|assert|break|class|continue|def|del|elif|else|except|finally|for|from|'
                                r'global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b')
        comment_ok, keyword_seen, keyword_ok = None, 0, True
        for i in range(int(inner.LinesCount)):
            line = str(inner.GetLineText(i))
            runs = list(inner.GetLineRuns(i))
            spans = [(runs[k], runs[k] + runs[k + 1], runs[k + 2] & 0xffffff, runs[k + 4]) for k in range(0, len(runs), 6)]
            if line.startswith('#') and comment_ok is None:
                comment_ok = all(fore == 0x008000 and style & 2 for _, _, fore, style in spans)
            if '#' in line or '"' in line or "'" in line:
                continue
            for m in keyword_re.finditer(line):
                keyword_seen += 1
                fore = next((f for a, b, f, _ in spans if a <= m.start() < b), None)
                keyword_ok &= fore == 0x0000ff
        report['comments'] = comment_ok
        report['keywordsChecked'] = keyword_seen
        self.check('Python comments are green italic (PythonTextBoxSyntaxHighlighter)', comment_ok is True)
        self.check('Python keywords outside strings and comments are blue', keyword_ok)
        self.check('the script is read-only in the history editor', bool(python.ReadOnly))
        # Select the last command: its Python lines are selected (HighlightSelectedCommandInPythonScript)
        _, table = self.widget(form, grid)
        last = grid.Rows.Count - 1
        index = table.model().index(last, 0)
        QtTest.QTest.mouseClick(table.viewport(), QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.NoModifier, table.visualRect(index).center())
        self.renderer.flush()
        self.app.processEvents()
        selection = inner.Selection
        report['selectedLines'] = [int(selection.Start.iLine), int(selection.End.iLine)]
        self.check('selecting a command selects its Python lines', grid.CurrentRow is not None and grid.CurrentRow.Index == last
                   and not selection.IsEmpty)
        # A double click on the first command opens FrmViewObjectProperties (modal)
        from System.Windows.Forms import Form
        seen = {}

        def later():
            dialog = next((f for f in Form.OpenForms if f.Visible and f.Modal), None)
            if dialog is None:
                QtCore.QTimer.singleShot(50, later)
                return
            seen['form'] = type(dialog).__name__
            seen['title'] = str(dialog.Text)
            self.renderer.guard(dialog.CloseByUser)
            self.renderer.flush()
        QtCore.QTimer.singleShot(50, later)
        index = table.model().index(0, 0)
        QtTest.QTest.mouseDClick(table.viewport(), QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.NoModifier, table.visualRect(index).center())
        QtTest.QTest.qWait(400)
        report['properties'] = seen
        self.check('a double click shows the command in the original FrmViewObjectProperties', seen.get('form') == 'FrmViewObjectProperties'
                   and seen.get('title') == 'Command Properties')
        # Delete the last row (a Qt click on its row header selects the row, then the Delete key), then Cancel
        header = table.verticalHeader()
        y = header.sectionViewportPosition(last) + header.sectionSize(last) // 2
        QtTest.QTest.mouseClick(header.viewport(), QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.NoModifier, QtCore.QPoint(header.width() // 2, y))
        self.renderer.flush()
        self.app.processEvents()
        report['selectedRows'] = [int(r.Index) for r in grid.SelectedRows]
        table.setFocus()
        QtTest.QTest.keyClick(table, QtCore.Qt.Key.Key_Delete)
        self.renderer.flush()
        self.app.processEvents()
        report['rowsAfterDelete'] = int(grid.Rows.Count)
        self.check('Delete removes the selected command row', grid.Rows.Count == commands - 1)
        self.click(form, 'btnCancel')
        self.check('Cancel hides the form and keeps the history', not form.Visible and c.GetCommands().Count == commands)
