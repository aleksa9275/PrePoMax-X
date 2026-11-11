// Headless model of FastColoredTextBox 2.16.24 (FCTB, Pavel Torgashov, LGPLv3), the code editor control the
// original UserControls text boxes (CalculixInpTextBox, PythonEditorTextBox, PythonConsoleTextBox,
// OutputTextBox) derive from or host (D062). Written from FCTB's documented behaviour, not copied from its
// source: text lines with per-character style layers, places and ranges, undo commands with auto-undo groups,
// the TextChanging/TextChanged/TextChangedDelayed and SelectionChanged events, the default hotkey actions,
// typed characters (auto indent, auto-completed brackets), bookmarks, the autocomplete menu and the find and
// replace forms. The renderer (X/UI/original_controls.py) draws the lines from GetLineRuns and feeds keys,
// characters and mouse places back. Only what the original text boxes use is modelled.
using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;
using KEYS = System.Windows.Forms.Keys;

namespace FastColoredTextBoxNS
{
    /// <summary>A position: character iChar of line iLine.</summary>
    public struct Place : IEquatable<Place>
    {
        public int iChar;
        public int iLine;
        public Place(int iChar, int iLine) { this.iChar = iChar; this.iLine = iLine; }
        public void Offset(int dx, int dy) { iChar += dx; iLine += dy; }
        public bool Equals(Place other) => iChar == other.iChar && iLine == other.iLine;
        public override bool Equals(object obj) => obj is Place p && Equals(p);
        public override int GetHashCode() => iChar.GetHashCode() ^ iLine.GetHashCode();
        public static bool operator ==(Place p1, Place p2) => p1.Equals(p2);
        public static bool operator !=(Place p1, Place p2) => !p1.Equals(p2);
        public static bool operator <(Place p1, Place p2) => p1.iLine < p2.iLine || (p1.iLine == p2.iLine && p1.iChar < p2.iChar);
        public static bool operator <=(Place p1, Place p2) => p1.Equals(p2) || p1 < p2;
        public static bool operator >(Place p1, Place p2) => p1.iLine > p2.iLine || (p1.iLine == p2.iLine && p1.iChar > p2.iChar);
        public static bool operator >=(Place p1, Place p2) => p1.Equals(p2) || p1 > p2;
        public static Place operator +(Place p1, Place p2) => new Place(p1.iChar + p2.iChar, p1.iLine + p2.iLine);
        public static Place Empty => new Place();
        public override string ToString() => "(" + iChar + "," + iLine + ")";
    }

    /// <summary>Style layers of a character (one bit per entry of FastColoredTextBox.Styles).</summary>
    [Flags]
    public enum StyleIndex : ushort
    {
        None = 0, Style0 = 0x1, Style1 = 0x2, Style2 = 0x4, Style3 = 0x8, Style4 = 0x10, Style5 = 0x20, Style6 = 0x40,
        Style7 = 0x80, Style8 = 0x100, Style9 = 0x200, Style10 = 0x400, Style11 = 0x800, Style12 = 0x1000,
        Style13 = 0x2000, Style14 = 0x4000, Style15 = 0x8000, All = 0xffff
    }

    public struct Char
    {
        public char c;
        public StyleIndex style;
        public Char(char c) { this.c = c; style = StyleIndex.None; }
    }

    /// <summary>A text line: its characters with their style layers.</summary>
    public class Line : List<Char>
    {
        public bool IsChanged { get; set; }
        public int AutoIndentSpacesNeededCount { get; internal set; }
        public string Text
        {
            get
            {
                var sb = new StringBuilder(Count);
                foreach (Char c in this) sb.Append(c.c);
                return sb.ToString();
            }
        }
        public int StartSpacesCount
        {
            get
            {
                int spaces = 0;
                for (int i = 0; i < Count; i++)
                {
                    if (this[i].c == ' ') spaces++;
                    else break;
                }
                return spaces;
            }
        }
        public void ClearStyle(StyleIndex styleIndex)
        {
            for (int i = 0; i < Count; i++)
            {
                Char c = this[i];
                c.style &= ~styleIndex;
                this[i] = c;
            }
        }
    }

    /// <summary>System.Drawing.Brush stand-in (SolidBrush needs GDI+, which .NET 10 provides only on Windows):
    /// a solid colour the renderer paints with.</summary>
    public sealed class StyleBrush : IDisposable
    {
        public Color Color { get; set; }
        public StyleBrush(Color color) { Color = color; }
        public void Dispose() { }
    }

    public abstract class Style : IDisposable
    {
        public bool IsExportable { get; set; } = true;
        public virtual void Dispose() { }
    }

    /// <summary>Text colour, background and font style of the characters of a layer.</summary>
    public class TextStyle : Style
    {
        public StyleBrush ForeBrush { get; set; }
        public StyleBrush BackgroundBrush { get; set; }
        public FontStyle FontStyle { get; set; }
        public TextStyle(StyleBrush foreBrush, StyleBrush backgroundBrush, FontStyle fontStyle)
        {
            ForeBrush = foreBrush;
            BackgroundBrush = backgroundBrush;
            FontStyle = fontStyle;
        }
    }

    /// <summary>A rounded background marker behind the characters of a layer.</summary>
    public class MarkerStyle : Style
    {
        public StyleBrush BackgroundBrush { get; set; }
        public MarkerStyle(StyleBrush backgroundBrush) { BackgroundBrush = backgroundBrush; }
    }

    public class SelectionStyle : Style
    {
        public StyleBrush BackgroundBrush { get; set; }
        public SelectionStyle(StyleBrush backgroundBrush) { BackgroundBrush = backgroundBrush; }
    }

    public enum Language { Custom, CSharp, VB, HTML, XML, SQL, PHP, JS, Lua, JSON }
    public enum WordWrapMode { WordWrapControlWidth, WordWrapPreferredWidth, CharWrapControlWidth, CharWrapPreferredWidth, Custom }
    public enum BracketsHighlightStrategy { Strategy1, Strategy2 }

    public enum FCTBAction
    {
        None, AutocompleteMenu, AutoIndentChars, BookmarkLine, ClearWordLeft, ClearWordRight, CommentSelected, Copy, Cut,
        DeleteCharRight, FindChar, FindDialog, FindNext, GoDown, GoDownWithSelection, GoDown_ColumnSelectionMode, GoEnd,
        GoEndWithSelection, GoFirstLine, GoFirstLineWithSelection, GoHome, GoHomeWithSelection, GoLastLine,
        GoLastLineWithSelection, GoLeft, GoLeftWithSelection, GoLeft_ColumnSelectionMode, GoPageDown,
        GoPageDownWithSelection, GoPageUp, GoPageUpWithSelection, GoRight, GoRightWithSelection,
        GoRight_ColumnSelectionMode, GoToDialog, GoNextBookmark, GoPrevBookmark, GoUp, GoUpWithSelection,
        GoUp_ColumnSelectionMode, GoWordLeft, GoWordLeftWithSelection, GoWordRight, GoWordRightWithSelection,
        IndentIncrease, IndentDecrease, LowerCase, MacroExecute, MacroRecord, MoveSelectedLinesDown,
        MoveSelectedLinesUp, NavigateBackward, NavigateForward, Paste, Redo, ReplaceDialog, ReplaceMode, ScrollDown,
        ScrollUp, SelectAll, UnbookmarkLine, Undo, UpperCase, ZoomIn, ZoomNormal, ZoomOut, ClearHints,
        CustomAction1, CustomAction2, CustomAction3, CustomAction4, CustomAction5, CustomAction6, CustomAction7,
        CustomAction8, CustomAction9, CustomAction10, CustomAction11, CustomAction12, CustomAction13, CustomAction14,
        CustomAction15, CustomAction16, CustomAction17, CustomAction18, CustomAction19, CustomAction20
    }

    /// <summary>Shortcuts of the control and their actions (FCTB's default mapping).</summary>
    public class HotkeysMapping : SortedDictionary<Keys, FCTBAction>
    {
        public virtual void InitDefault()
        {
            this[KEYS.Control | KEYS.G] = FCTBAction.GoToDialog;
            this[KEYS.Control | KEYS.F] = FCTBAction.FindDialog;
            this[KEYS.Alt | KEYS.F] = FCTBAction.FindChar;
            this[KEYS.F3] = FCTBAction.FindNext;
            this[KEYS.Control | KEYS.H] = FCTBAction.ReplaceDialog;
            this[KEYS.Control | KEYS.C] = FCTBAction.Copy;
            this[KEYS.Control | KEYS.Shift | KEYS.C] = FCTBAction.CommentSelected;
            this[KEYS.Control | KEYS.X] = FCTBAction.Cut;
            this[KEYS.Control | KEYS.V] = FCTBAction.Paste;
            this[KEYS.Control | KEYS.A] = FCTBAction.SelectAll;
            this[KEYS.Control | KEYS.Z] = FCTBAction.Undo;
            this[KEYS.Control | KEYS.R] = FCTBAction.Redo;
            this[KEYS.Control | KEYS.U] = FCTBAction.UpperCase;
            this[KEYS.Shift | KEYS.Control | KEYS.U] = FCTBAction.LowerCase;
            this[KEYS.Control | KEYS.OemMinus] = FCTBAction.NavigateBackward;
            this[KEYS.Control | KEYS.Shift | KEYS.OemMinus] = FCTBAction.NavigateForward;
            this[KEYS.Control | KEYS.B] = FCTBAction.BookmarkLine;
            this[KEYS.Control | KEYS.Shift | KEYS.B] = FCTBAction.UnbookmarkLine;
            this[KEYS.Control | KEYS.N] = FCTBAction.GoNextBookmark;
            this[KEYS.Control | KEYS.Shift | KEYS.N] = FCTBAction.GoPrevBookmark;
            this[KEYS.Alt | KEYS.Back] = FCTBAction.Undo;
            this[KEYS.Control | KEYS.Back] = FCTBAction.ClearWordLeft;
            this[KEYS.Insert] = FCTBAction.ReplaceMode;
            this[KEYS.Control | KEYS.Insert] = FCTBAction.Copy;
            this[KEYS.Shift | KEYS.Insert] = FCTBAction.Paste;
            this[KEYS.Delete] = FCTBAction.DeleteCharRight;
            this[KEYS.Control | KEYS.Delete] = FCTBAction.ClearWordRight;
            this[KEYS.Shift | KEYS.Delete] = FCTBAction.Cut;
            this[KEYS.Left] = FCTBAction.GoLeft;
            this[KEYS.Shift | KEYS.Left] = FCTBAction.GoLeftWithSelection;
            this[KEYS.Control | KEYS.Left] = FCTBAction.GoWordLeft;
            this[KEYS.Control | KEYS.Shift | KEYS.Left] = FCTBAction.GoWordLeftWithSelection;
            this[KEYS.Alt | KEYS.Shift | KEYS.Left] = FCTBAction.GoLeft_ColumnSelectionMode;
            this[KEYS.Right] = FCTBAction.GoRight;
            this[KEYS.Shift | KEYS.Right] = FCTBAction.GoRightWithSelection;
            this[KEYS.Control | KEYS.Right] = FCTBAction.GoWordRight;
            this[KEYS.Control | KEYS.Shift | KEYS.Right] = FCTBAction.GoWordRightWithSelection;
            this[KEYS.Alt | KEYS.Shift | KEYS.Right] = FCTBAction.GoRight_ColumnSelectionMode;
            this[KEYS.Up] = FCTBAction.GoUp;
            this[KEYS.Shift | KEYS.Up] = FCTBAction.GoUpWithSelection;
            this[KEYS.Alt | KEYS.Shift | KEYS.Up] = FCTBAction.GoUp_ColumnSelectionMode;
            this[KEYS.Alt | KEYS.Up] = FCTBAction.MoveSelectedLinesUp;
            this[KEYS.Control | KEYS.Up] = FCTBAction.ScrollUp;
            this[KEYS.Down] = FCTBAction.GoDown;
            this[KEYS.Shift | KEYS.Down] = FCTBAction.GoDownWithSelection;
            this[KEYS.Alt | KEYS.Shift | KEYS.Down] = FCTBAction.GoDown_ColumnSelectionMode;
            this[KEYS.Alt | KEYS.Down] = FCTBAction.MoveSelectedLinesDown;
            this[KEYS.Control | KEYS.Down] = FCTBAction.ScrollDown;
            this[KEYS.PageUp] = FCTBAction.GoPageUp;
            this[KEYS.Shift | KEYS.PageUp] = FCTBAction.GoPageUpWithSelection;
            this[KEYS.PageDown] = FCTBAction.GoPageDown;
            this[KEYS.Shift | KEYS.PageDown] = FCTBAction.GoPageDownWithSelection;
            this[KEYS.Home] = FCTBAction.GoHome;
            this[KEYS.Shift | KEYS.Home] = FCTBAction.GoHomeWithSelection;
            this[KEYS.Control | KEYS.Home] = FCTBAction.GoFirstLine;
            this[KEYS.Control | KEYS.Shift | KEYS.Home] = FCTBAction.GoFirstLineWithSelection;
            this[KEYS.End] = FCTBAction.GoEnd;
            this[KEYS.Shift | KEYS.End] = FCTBAction.GoEndWithSelection;
            this[KEYS.Control | KEYS.End] = FCTBAction.GoLastLine;
            this[KEYS.Control | KEYS.Shift | KEYS.End] = FCTBAction.GoLastLineWithSelection;
            this[KEYS.Escape] = FCTBAction.ClearHints;
            this[KEYS.Control | KEYS.M] = FCTBAction.MacroRecord;
            this[KEYS.Control | KEYS.E] = FCTBAction.MacroExecute;
            this[KEYS.Control | KEYS.Space] = FCTBAction.AutocompleteMenu;
            this[KEYS.Tab] = FCTBAction.IndentIncrease;
            this[KEYS.Shift | KEYS.Tab] = FCTBAction.IndentDecrease;
            this[KEYS.Control | KEYS.Subtract] = FCTBAction.ZoomOut;
            this[KEYS.Control | KEYS.Add] = FCTBAction.ZoomIn;
            this[KEYS.Control | KEYS.D0] = FCTBAction.ZoomNormal;
            this[KEYS.Control | KEYS.I] = FCTBAction.AutoIndentChars;
        }
    }

    public class TextChangedEventArgs : EventArgs
    {
        public Range ChangedRange { get; set; }
        public TextChangedEventArgs(Range changedRange) { ChangedRange = changedRange; }
    }

    public class TextChangingEventArgs : EventArgs
    {
        public string InsertingText { get; set; }
        public bool Cancel { get; set; }
    }

    /// <summary>A text range between Start (the caret end) and End.</summary>
    public class Range : IEnumerable<Place>
    {
        Place start, end;
        public readonly FastColoredTextBox tb;
        int preferedPos = -1;
        int updating;

        public Range(FastColoredTextBox tb) { this.tb = tb; }
        public Range(FastColoredTextBox tb, int iStartChar, int iStartLine, int iEndChar, int iEndLine) : this(tb)
        {
            start = new Place(iStartChar, iStartLine);
            end = new Place(iEndChar, iEndLine);
        }
        public Range(FastColoredTextBox tb, Place start, Place end) : this(tb) { this.start = start; this.end = end; }
        public Range(FastColoredTextBox tb, int iLine) : this(tb)
        {
            start = new Place(0, iLine);
            end = new Place(tb[iLine].Count, iLine);
        }

        public bool ColumnSelectionMode { get; set; }
        public Place Start { get => start; set { end = start = value; preferedPos = -1; OnSelectionChanged(); } }
        public Place End { get => end; set { end = value; OnSelectionChanged(); } }
        public bool IsEmpty => Start == End;
        public bool ReadOnly => tb.ReadOnly;
        public int FromX
        {
            get
            {
                if (end.iLine < start.iLine) return end.iChar;
                if (end.iLine > start.iLine) return start.iChar;
                return Math.Min(end.iChar, start.iChar);
            }
        }
        public int ToX
        {
            get
            {
                if (end.iLine < start.iLine) return start.iChar;
                if (end.iLine > start.iLine) return end.iChar;
                return Math.Max(end.iChar, start.iChar);
            }
        }
        public int FromLine => Math.Min(Start.iLine, End.iLine);
        public int ToLine => Math.Max(Start.iLine, End.iLine);
        public string Text { get { GetText(out string text, out _); return text; } }
        public int Length => Text.Length;
        public char CharAfterStart
        {
            get
            {
                if (Start.iLine < 0 || Start.iLine >= tb.LinesCount) return '\n';
                if (Start.iChar >= tb[Start.iLine].Count) return '\n';
                return tb[Start.iLine][Start.iChar].c;
            }
        }
        public char CharBeforeStart
        {
            get
            {
                if (Start.iLine < 0 || Start.iLine >= tb.LinesCount) return '\n';
                if (Start.iChar > tb[Start.iLine].Count || Start.iChar <= 0) return '\n';
                return tb[Start.iLine][Start.iChar - 1].c;
            }
        }

        internal void GetText(out string text, out List<Place> charIndexToPlace)
        {
            int fromLine = Math.Min(end.iLine, start.iLine);
            int toLine = Math.Max(end.iLine, start.iLine);
            int fromChar = FromX;
            int toChar = ToX;
            var sb = new StringBuilder();
            charIndexToPlace = new List<Place>();
            if (fromLine >= 0)
            {
                for (int y = fromLine; y <= toLine && y < tb.LinesCount; y++)
                {
                    int fromX = y == fromLine ? fromChar : 0;
                    int toX = y == toLine ? Math.Min(toChar - 1, tb[y].Count - 1) : tb[y].Count - 1;
                    for (int x = fromX; x <= toX; x++)
                    {
                        sb.Append(tb[y][x].c);
                        charIndexToPlace.Add(new Place(x, y));
                    }
                    if (y != toLine && fromLine != toLine)
                        foreach (char c in Environment.NewLine)
                        {
                            sb.Append(c);
                            charIndexToPlace.Add(new Place(tb[y].Count, y));
                        }
                }
            }
            text = sb.ToString();
            charIndexToPlace.Add(End > Start ? End : Start);
        }

        public Range Clone() => new Range(tb, start, end) { ColumnSelectionMode = ColumnSelectionMode, preferedPos = preferedPos };
        public void Normalize() { if (Start > End) Inverse(); }
        public void Inverse() { var temp = start; start = end; end = temp; }
        public void SelectAll()
        {
            ColumnSelectionMode = false;
            Start = new Place(0, 0);
            if (tb.LinesCount > 0)
            {
                end = new Place(0, 0);
                start = new Place(tb[tb.LinesCount - 1].Count, tb.LinesCount - 1);
            }
            if (this == tb.Selection) tb.Invalidate();
        }
        public void Expand()
        {
            Normalize();
            start = new Place(0, start.iLine);
            end = new Place(tb.GetLineLength(end.iLine), end.iLine);
        }
        public bool Contains(Place place)
        {
            if (place.iLine < Math.Min(start.iLine, end.iLine)) return false;
            if (place.iLine > Math.Max(start.iLine, end.iLine)) return false;
            Place s = start, e = end;
            if (s > e) { var t = s; s = e; e = t; }
            if (place.iLine == s.iLine && place.iChar < s.iChar) return false;
            if (place.iLine == e.iLine && place.iChar > e.iChar) return false;
            return true;
        }
        public Range GetIntersectionWith(Range range)
        {
            Range r1 = Clone(), r2 = range.Clone();
            r1.Normalize();
            r2.Normalize();
            Place newStart = r1.Start > r2.Start ? r1.Start : r2.Start;
            Place newEnd = r1.End < r2.End ? r1.End : r2.End;
            if (newEnd < newStart) return new Range(tb, start, start);
            return tb.GetRange(newStart, newEnd);
        }

        public void BeginUpdate() => updating++;
        public void EndUpdate()
        {
            updating--;
            if (updating == 0) OnSelectionChanged();
        }
        void OnSelectionChanged()
        {
            if (tb.Selection == this && updating == 0) tb.OnSelectionChanged();
        }

        // Styles
        public void SetStyle(Style style) => SetStyle(ToStyleIndex(tb.GetOrSetStyleLayerIndex(style)));
        public void SetStyle(Style style, string regexPattern) => SetStyle(style, regexPattern, RegexOptions.None);
        public void SetStyle(Style style, string regexPattern, RegexOptions options)
        {
            StyleIndex layer = ToStyleIndex(tb.GetOrSetStyleLayerIndex(style));
            foreach (Range range in GetRanges(regexPattern, options).ToList()) range.SetStyle(layer);
            tb.Invalidate();
        }
        public void SetStyle(StyleIndex styleLayer)
        {
            int fromLine = Math.Min(End.iLine, Start.iLine), toLine = Math.Max(End.iLine, Start.iLine);
            int fromChar = FromX, toChar = ToX;
            if (fromLine < 0) return;
            for (int y = fromLine; y <= toLine && y < tb.LinesCount; y++)
            {
                int fromX = y == fromLine ? fromChar : 0;
                int toX = y == toLine ? Math.Min(toChar - 1, tb[y].Count - 1) : tb[y].Count - 1;
                for (int x = fromX; x <= toX; x++)
                {
                    Char c = tb[y][x];
                    c.style |= styleLayer;
                    tb[y][x] = c;
                }
            }
        }
        public void ClearStyle(params Style[] styles)
        {
            try { ClearStyle(tb.GetStyleIndexMask(styles)); }
            catch { }
        }
        public void ClearStyle(StyleIndex styleIndex)
        {
            int fromLine = Math.Min(End.iLine, Start.iLine), toLine = Math.Max(End.iLine, Start.iLine);
            int fromChar = FromX, toChar = ToX;
            if (fromLine < 0) return;
            for (int y = fromLine; y <= toLine && y < tb.LinesCount; y++)
            {
                int fromX = y == fromLine ? fromChar : 0;
                int toX = y == toLine ? Math.Min(toChar - 1, tb[y].Count - 1) : tb[y].Count - 1;
                for (int x = fromX; x <= toX; x++)
                {
                    Char c = tb[y][x];
                    c.style &= ~styleIndex;
                    tb[y][x] = c;
                }
            }
            tb.Invalidate();
        }
        public static StyleIndex ToStyleIndex(int i) => (StyleIndex)(1 << i);

        public IEnumerable<Range> GetRanges(string regexPattern) => GetRanges(regexPattern, RegexOptions.None);
        public IEnumerable<Range> GetRanges(string regexPattern, RegexOptions options)
        {
            GetText(out string text, out List<Place> charIndexToPlace);
            var regex = new Regex(regexPattern, options);
            foreach (Match m in regex.Matches(text))
            {
                var r = new Range(tb);
                Group group = m.Groups["range"];
                if (!group.Success) group = m.Groups[0];
                r.Start = charIndexToPlace[group.Index];
                r.End = charIndexToPlace[group.Index + group.Length];
                yield return r;
            }
        }
        public Range GetFragment(string allowedSymbolsPattern) => GetFragment(allowedSymbolsPattern, RegexOptions.None);
        public Range GetFragment(string allowedSymbolsPattern, RegexOptions options)
        {
            var r = new Range(tb) { Start = Start };
            var regex = new Regex(allowedSymbolsPattern, options);
            while (r.GoLeftThroughFolded())
            {
                if (!regex.IsMatch(r.CharAfterStart.ToString()))
                {
                    r.GoRightThroughFolded();
                    break;
                }
            }
            Place startFragment = r.Start;
            r.Start = Start;
            do
            {
                if (!regex.IsMatch(r.CharAfterStart.ToString())) break;
            } while (r.GoRightThroughFolded());
            return new Range(tb, startFragment, r.Start);
        }

        // Caret movement (FCTB Range.Go*)
        internal bool GoLeftThroughFolded()
        {
            if (start.iChar == 0 && start.iLine == 0) return false;
            Start = start.iChar > 0 ? new Place(start.iChar - 1, start.iLine) : new Place(tb[start.iLine - 1].Count, start.iLine - 1);
            return true;
        }
        internal bool GoRightThroughFolded()
        {
            int last = tb.LinesCount - 1;
            if (start.iLine >= last && start.iChar >= tb[last].Count) return false;
            Start = start.iChar < tb[start.iLine].Count ? new Place(start.iChar + 1, start.iLine) : new Place(0, start.iLine + 1);
            return true;
        }
        public void GoLeft() => GoLeft(false);
        public void GoLeft(bool shift)
        {
            ColumnSelectionMode = false;
            if (!shift && start > end) { Start = End; return; }
            if (start.iChar != 0 || start.iLine != 0)
                start = start.iChar > 0 ? new Place(start.iChar - 1, start.iLine) : new Place(tb[start.iLine - 1].Count, start.iLine - 1);
            if (!shift) end = start;
            OnSelectionChanged();
            preferedPos = -1;
        }
        public void GoRight() => GoRight(false);
        public void GoRight(bool shift)
        {
            ColumnSelectionMode = false;
            if (!shift && start < end) { Start = End; return; }
            if (start.iLine < tb.LinesCount - 1 || start.iChar < tb[tb.LinesCount - 1].Count)
                start = start.iChar < tb[start.iLine].Count ? new Place(start.iChar + 1, start.iLine) : new Place(0, start.iLine + 1);
            if (!shift) end = start;
            OnSelectionChanged();
            preferedPos = -1;
        }
        internal void GoUp(bool shift)
        {
            ColumnSelectionMode = false;
            if (!shift && start.iLine > end.iLine) { Start = End; return; }
            if (preferedPos < 0) preferedPos = start.iChar;
            if (start.iLine > 0) start = new Place(Math.Min(preferedPos, tb[start.iLine - 1].Count), start.iLine - 1);
            else start = new Place(0, 0);
            if (!shift) end = start;
            OnSelectionChanged();
        }
        internal void GoDown(bool shift)
        {
            ColumnSelectionMode = false;
            if (!shift && start.iLine < end.iLine) { Start = End; return; }
            if (preferedPos < 0) preferedPos = start.iChar;
            if (start.iLine < tb.LinesCount - 1) start = new Place(Math.Min(preferedPos, tb[start.iLine + 1].Count), start.iLine + 1);
            else start = new Place(tb[start.iLine].Count, start.iLine);
            if (!shift) end = start;
            OnSelectionChanged();
        }
        internal void GoPageUp(bool shift)
        {
            ColumnSelectionMode = false;
            if (preferedPos < 0) preferedPos = start.iChar;
            int iLine = Math.Max(0, start.iLine - tb.VisibleLinesCount);
            start = new Place(Math.Min(preferedPos, tb[iLine].Count), iLine);
            if (!shift) end = start;
            OnSelectionChanged();
        }
        internal void GoPageDown(bool shift)
        {
            ColumnSelectionMode = false;
            if (preferedPos < 0) preferedPos = start.iChar;
            int iLine = Math.Min(tb.LinesCount - 1, start.iLine + tb.VisibleLinesCount);
            start = new Place(Math.Min(preferedPos, tb[iLine].Count), iLine);
            if (!shift) end = start;
            OnSelectionChanged();
        }
        internal void GoHome(bool shift)
        {
            ColumnSelectionMode = false;
            if (start.iLine < 0) return;
            start = new Place(0, start.iLine);
            if (!shift) end = start;
            OnSelectionChanged();
            preferedPos = -1;
        }
        internal void GoEnd(bool shift)
        {
            ColumnSelectionMode = false;
            if (start.iLine < 0) return;
            start = new Place(tb[start.iLine].Count, start.iLine);
            if (!shift) end = start;
            OnSelectionChanged();
            preferedPos = -1;
        }
        internal void GoFirst(bool shift)
        {
            ColumnSelectionMode = false;
            start = new Place(0, 0);
            if (!shift) end = start;
            OnSelectionChanged();
        }
        internal void GoLast(bool shift)
        {
            ColumnSelectionMode = false;
            start = new Place(tb[tb.LinesCount - 1].Count, tb.LinesCount - 1);
            if (!shift) end = start;
            OnSelectionChanged();
        }
        static bool IsSpaceChar(char c) => c == ' ' || c == '\t';
        static bool IsIdentifierChar(char c) => char.IsLetterOrDigit(c) || c == '_';
        public void GoWordLeft(bool shift)
        {
            ColumnSelectionMode = false;
            if (!shift && start > end) { Start = End; return; }
            Range range = Clone();
            bool wasSpace = false;
            while (IsSpaceChar(range.CharBeforeStart)) { wasSpace = true; range.GoLeft(shift); }
            bool wasIdentifier = false;
            while (IsIdentifierChar(range.CharBeforeStart)) { wasIdentifier = true; range.GoLeft(shift); }
            if (!wasIdentifier && (!wasSpace || range.CharBeforeStart != '\n')) range.GoLeft(shift);
            Start = range.Start;
            End = range.End;
        }
        public void GoWordRight(bool shift)
        {
            ColumnSelectionMode = false;
            if (!shift && start < end) { Start = End; return; }
            Range range = Clone();
            if (range.CharAfterStart == '\n') range.GoRight(shift);
            while (IsSpaceChar(range.CharAfterStart)) range.GoRight(shift);
            bool wasIdentifier = false;
            while (IsIdentifierChar(range.CharAfterStart)) { wasIdentifier = true; range.GoRight(shift); }
            if (!wasIdentifier) range.GoRight(shift);
            Start = range.Start;
            End = range.End;
        }

        public IEnumerator<Place> GetEnumerator()
        {
            int fromLine = Math.Min(end.iLine, start.iLine), toLine = Math.Max(end.iLine, start.iLine);
            int fromChar = FromX, toChar = ToX;
            if (fromLine < 0) yield break;
            for (int y = fromLine; y <= toLine; y++)
            {
                int fromX = y == fromLine ? fromChar : 0;
                int toX = y == toLine ? Math.Min(toChar - 1, tb[y].Count - 1) : tb[y].Count - 1;
                for (int x = fromX; x <= toX; x++) yield return new Place(x, y);
            }
        }
        IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
        public override string ToString() => "Start: " + Start + " End: " + End;
    }

    public class Bookmark
    {
        public FastColoredTextBox TB { get; }
        public string Name { get; set; }
        public int LineIndex { get; set; }
        public Color Color { get; set; }
        public Bookmark(FastColoredTextBox tb, string name, int lineIndex) { TB = tb; Name = name; LineIndex = lineIndex; Color = tb.BookmarkColor; }
    }

    public class Bookmarks : ICollection<Bookmark>, IDisposable
    {
        readonly FastColoredTextBox tb;
        readonly List<Bookmark> items = new List<Bookmark>();
        public Bookmarks(FastColoredTextBox tb) { this.tb = tb; }
        public int Count => items.Count;
        public bool IsReadOnly => false;
        public void Add(int lineIndex) => Add(lineIndex, "Bookmark " + items.Count);
        public void Add(int lineIndex, string bookmarkName)
        {
            if (Contains(lineIndex)) return;
            Add(new Bookmark(tb, bookmarkName, lineIndex));
        }
        public void Add(Bookmark item) { if (!items.Contains(item)) items.Add(item); tb.Invalidate(); }
        public void Clear() { items.Clear(); tb.Invalidate(); }
        public bool Contains(Bookmark item) => items.Contains(item);
        public bool Contains(int lineIndex) => items.Any(b => b.LineIndex == lineIndex);
        public bool Remove(int lineIndex)
        {
            bool removed = items.RemoveAll(b => b.LineIndex == lineIndex) > 0;
            tb.Invalidate();
            return removed;
        }
        public bool Remove(Bookmark item) { bool removed = items.Remove(item); tb.Invalidate(); return removed; }
        public Bookmark GetBookmark(int i) => items[i];
        public void CopyTo(Bookmark[] array, int arrayIndex) => items.CopyTo(array, arrayIndex);
        public IEnumerator<Bookmark> GetEnumerator() => items.GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
        public void Dispose() { }
        internal void LinesInserted(int index, int count) { foreach (var b in items) if (b.LineIndex >= index) b.LineIndex += count; }
        internal void LinesRemoved(int index, int count)
        {
            items.RemoveAll(b => b.LineIndex >= index && b.LineIndex < index + count);
            foreach (var b in items) if (b.LineIndex >= index + count) b.LineIndex -= count;
        }
    }

    /// <summary>The code editor control.</summary>
    [ToolboxItem(true)]
    public class FastColoredTextBox : UserControl
    {
        readonly List<Line> lines = new List<Line>();
        readonly CommandHistory history;
        Range selection;
        Range delayedTextChangedRange;
        readonly System.Windows.Forms.Timer delayedTextChangedTimer = new System.Windows.Forms.Timer();
        readonly System.Windows.Forms.Timer delayedSelectionTimer = new System.Windows.Forms.Timer();
        bool isChanged;
        bool handledChar;
        Keys lastModifiers;
        int updating;
        Range updatingRange;
        FindForm findForm;
        ReplaceForm replaceForm;
        char[] autoCompleteBracketsList = { '(', ')', '{', '}', '[', ']', '"', '"', '\'', '\'' };

        public FastColoredTextBox()
        {
            history = new CommandHistory(this);
            lines.Add(new Line());
            selection = new Range(this) { Start = new Place(0, 0) };
            Bookmarks = new Bookmarks(this);
            HotkeysMapping = new HotkeysMapping();
            HotkeysMapping.InitDefault();
            Styles = new Style[sizeof(ushort) * 8];
            Font = new FontSpec("Courier New", 9.75f);
            BackColor = Color.White;
            ForeColor = Color.Black;
            delayedTextChangedTimer.Interval = DelayedTextChangedInterval;
            delayedTextChangedTimer.Tick += (s, e) => { delayedTextChangedTimer.Stop(); RaiseDelayedTextChanged(); };
            delayedSelectionTimer.Interval = DelayedEventsInterval;
            delayedSelectionTimer.Tick += (s, e) => { delayedSelectionTimer.Stop(); OnSelectionChangedDelayed(); };
        }

        // Events
        public new event EventHandler<TextChangedEventArgs> TextChanged;
        public event EventHandler<TextChangingEventArgs> TextChanging;
        public event EventHandler<TextChangedEventArgs> TextChangedDelayed;
        public event EventHandler SelectionChanged;
        public event EventHandler SelectionChangedDelayed;
        public event KeyPressEventHandler KeyPressing;
        public event KeyPressEventHandler KeyPressed;
        public event EventHandler UndoRedoStateChanged;
        public event ScrollEventHandler Scroll;
        public event EventHandler ZoomChanged;

        // Properties
        public Style[] Styles { get; }
        public HotkeysMapping HotkeysMapping { get; set; }
        public Bookmarks Bookmarks { get; }
        public Language Language { get; set; }
        public bool ShowLineNumbers { get; set; } = true;
        public int ReservedCountOfLineNumberChars { get; set; } = 1;
        public Color LineNumberColor { get; set; } = Color.Teal;
        public Color BookmarkColor { get; set; } = Color.PowderBlue;
        public Color CurrentLineColor { get; set; } = Color.Transparent;
        public Color SelectionColor { get; set; } = Color.Blue;
        public Color DisabledColor { get; set; } = Color.FromArgb(100, 180, 180, 180);
        public Color ServiceLinesColor { get; set; } = Color.Silver;
        public Color IndentBackColor { get; set; } = Color.WhiteSmoke;
        public Color CaretColor { get; set; } = Color.Black;
        public Color FoldingIndicatorColor { get; set; } = Color.Green;
        public StyleBrush BackBrush { get; set; }
        public Padding Paddings { get; set; } = new Padding(0);
        public int LeftPadding { get; set; }
        public bool WordWrap { get; set; }
        public WordWrapMode WordWrapMode { get; set; } = WordWrapMode.WordWrapControlWidth;
        public bool AcceptsTab { get; set; } = true;
        public bool AcceptsReturn { get; set; } = true;
        public int TabLength { get; set; } = 4;
        public bool AutoIndent { get; set; } = true;
        public bool AutoIndentExistingLines { get; set; } = true;
        public bool AutoIndentChars { get; set; }
        public bool AutoCompleteBrackets { get; set; }
        public char[] AutoCompleteBracketsList { get => autoCompleteBracketsList; set => autoCompleteBracketsList = value; }
        public string CommentPrefix { get; set; } = "//";
        public bool ReadOnly { get; set; }
        public bool IsReplaceMode { get; set; }
        public bool VirtualSpace { get; set; }
        public bool ShowFoldingLines { get; set; }
        public bool HighlightFoldingIndicator { get; set; } = true;
        public bool CaretVisible { get; set; } = true;
        public int DelayedTextChangedInterval { get; set; } = 100;
        public int DelayedEventsInterval { get; set; } = 100;
        public BracketsHighlightStrategy BracketsHighlightStrategy { get; set; }
        public char LeftBracket { get; set; }
        public char RightBracket { get; set; }
        public char LeftBracket2 { get; set; }
        public char RightBracket2 { get; set; }
        public int LineInterval { get; set; }
        public bool AllowSeveralTextStyleDrawing { get; set; }
        public new BorderStyle BorderStyle { get; set; }
        int zoom = 100;
        public int Zoom { get => zoom; set { zoom = value; ZoomChanged?.Invoke(this, EventArgs.Empty); Invalidate(); } }
        public int TextVersion { get; private set; }
        public bool IsChanged
        {
            get => isChanged;
            set
            {
                if (!value) foreach (Line line in lines) line.IsChanged = false;
                isChanged = value;
            }
        }
        public int LinesCount => lines.Count;
        public Line this[int iLine] => lines[iLine];
        public Char this[Place place] { get => lines[place.iLine][place.iChar]; set => lines[place.iLine][place.iChar] = value; }
        public IList<string> Lines => lines.Select(l => l.Text).ToList();
        public override string Text
        {
            get
            {
                if (LinesCount == 0) return "";
                var sel = new Range(this);
                sel.SelectAll();
                return sel.Text;
            }
            set
            {
                if (value == Text && value != "") return;
                Selection.ColumnSelectionMode = false;
                Selection.BeginUpdate();
                try
                {
                    Selection.SelectAll();
                    InsertText(value);
                    GoHome();
                }
                finally { Selection.EndUpdate(); }
            }
        }
        public int TextLength
        {
            get
            {
                if (LinesCount == 0) return 0;
                var sel = new Range(this);
                sel.SelectAll();
                return sel.Length;
            }
        }
        public Range Range => new Range(this, new Place(0, 0), new Place(lines[lines.Count - 1].Count, lines.Count - 1));
        public Range Selection
        {
            get => selection;
            set
            {
                if (value == selection) return;
                selection.BeginUpdate();
                selection.Start = value.Start;
                selection.End = value.End;
                selection.EndUpdate();
                Invalidate();
            }
        }
        public string SelectedText { get => Selection.Text; set => InsertText(value); }
        public int SelectionStart
        {
            get => Math.Min(PlaceToPosition(Selection.Start), PlaceToPosition(Selection.End));
            set => Selection.Start = PositionToPlace(value);
        }
        public int SelectionLength
        {
            get => Selection.Length;
            set { if (value > 0) Selection.End = PositionToPlace(SelectionStart + value); }
        }
        public bool UndoEnabled => history.UndoEnabled;
        public bool RedoEnabled => history.RedoEnabled;

        // Geometry the renderer reports (pixels of the drawn text area) for mouse places and page moves
        public int CharWidth { get; set; } = 8;
        public int CharHeight { get; set; } = 15;
        public int LeftIndent { get; set; }
        public int VerticalScrollValue { get; set; }
        public int HorizontalScrollValue { get; set; }
        internal int VisibleLinesCount => Math.Max(1, ClientSize.Height / Math.Max(1, CharHeight + LineInterval));

        public int GetLineLength(int iLine) => iLine < 0 || iLine >= lines.Count ? 0 : lines[iLine].Count;
        public Range GetRange(Place fromPlace, Place toPlace) => new Range(this, fromPlace, toPlace);
        public Range GetRange(int fromPos, int toPos) => new Range(this, PositionToPlace(fromPos), PositionToPlace(toPos));
        public Range GetLine(int iLine) => new Range(this, new Place(0, iLine), new Place(lines[iLine].Count, iLine));
        public string GetLineText(int iLine) => lines[iLine].Text;
        public int PlaceToPosition(Place point)
        {
            if (point.iLine < 0 || point.iLine >= lines.Count || point.iChar >= lines[point.iLine].Count + Environment.NewLine.Length) return -1;
            int result = 0;
            for (int i = 0; i < point.iLine; i++) result += lines[i].Count + Environment.NewLine.Length;
            return result + point.iChar;
        }
        public Place PositionToPlace(int pos)
        {
            if (pos < 0) return new Place(0, 0);
            for (int i = 0; i < lines.Count; i++)
            {
                int lineLength = lines[i].Count + Environment.NewLine.Length;
                if (pos < lines[i].Count) return new Place(pos, i);
                if (pos < lineLength) return new Place(lines[i].Count, i);
                pos -= lineLength;
            }
            return lines.Count > 0 ? new Place(lines[lines.Count - 1].Count, lines.Count - 1) : new Place(0, 0);
        }
        public Place PointToPlace(Point point)
        {
            int iLine = Math.Max(0, Math.Min(lines.Count - 1, (point.Y + VerticalScrollValue) / Math.Max(1, CharHeight + LineInterval)));
            int x = point.X + HorizontalScrollValue - LeftIndent - Paddings.Left;
            int iChar = Math.Max(0, Math.Min(lines[iLine].Count, (int)Math.Round(x / (double)Math.Max(1, CharWidth))));
            return new Place(iChar, iLine);
        }
        public Point PlaceToPoint(Place place)
        {
            return new Point(LeftIndent + Paddings.Left + place.iChar * CharWidth - HorizontalScrollValue,
                             place.iLine * (CharHeight + LineInterval) - VerticalScrollValue);
        }

        // Styles
        public int GetStyleIndex(Style style) => Array.IndexOf(Styles, style);
        public StyleIndex GetStyleIndexMask(Style[] styles)
        {
            StyleIndex mask = StyleIndex.None;
            foreach (Style style in styles)
            {
                int i = GetStyleIndex(style);
                if (i >= 0) mask |= Range.ToStyleIndex(i);
            }
            return mask;
        }
        public int GetOrSetStyleLayerIndex(Style style)
        {
            int i = GetStyleIndex(style);
            if (i < 0) i = AddStyle(style);
            return i;
        }
        public int AddStyle(Style style)
        {
            if (style == null) return -1;
            int i = GetStyleIndex(style);
            if (i >= 0) return i;
            for (i = Styles.Length - 1; i >= 0; i--)
                if (Styles[i] != null) break;
            i++;
            if (i >= Styles.Length) throw new Exception("Maximum count of Styles is exceeded.");
            Styles[i] = style;
            return i;
        }
        public void ClearStylesBuffer() { for (int i = 0; i < Styles.Length; i++) Styles[i] = null; }
        public void ClearStyle(StyleIndex styleIndex) { foreach (Line line in lines) line.ClearStyle(styleIndex); Invalidate(); }

        // Text editing (undoable commands)
        public virtual void InsertText(string text) => InsertText(text, true);
        public virtual void InsertText(string text, bool jumpToCaret)
        {
            if (text == null) return;
            if (text == "\r") text = "\n";
            history.BeginAutoUndo();
            try
            {
                if (!Selection.IsEmpty) history.Execute(new ClearSelectedCommand(this));
                history.Execute(new InsertTextCommand(this, text));
                if (updating <= 0 && jumpToCaret) DoCaretVisible();
            }
            finally { history.EndAutoUndo(); }
            Invalidate();
        }
        public virtual Range InsertText(string text, Style style) => InsertText(text, style, true);
        public virtual Range InsertText(string text, Style style, bool jumpToCaret)
        {
            if (text == null) return null;
            Place last = Selection.Start > Selection.End ? Selection.End : Selection.Start;
            InsertText(text, jumpToCaret);
            Range range = new Range(this, last, Selection.Start).GetIntersectionWith(Range);
            if (style != null) range.SetStyle(style);
            return range;
        }
        public virtual void AppendText(string text) => AppendText(text, null);
        public virtual void AppendText(string text, Style style)
        {
            if (text == null) return;
            Selection.ColumnSelectionMode = false;
            Place oldStart = Selection.Start, oldEnd = Selection.End;
            Selection.BeginUpdate();
            history.BeginAutoUndo();
            try
            {
                Selection.Start = new Place(lines[lines.Count - 1].Count, lines.Count - 1);
                Place last = Selection.Start;
                history.Execute(new InsertTextCommand(this, text));
                if (style != null) new Range(this, last, Selection.Start).SetStyle(style);
            }
            finally
            {
                history.EndAutoUndo();
                Selection.Start = oldStart;
                Selection.End = oldEnd;
                Selection.EndUpdate();
            }
            Invalidate();
        }
        public virtual void ClearSelected()
        {
            if (Selection.IsEmpty) return;
            history.Execute(new ClearSelectedCommand(this));
            Invalidate();
        }
        public void Clear()
        {
            Selection.BeginUpdate();
            try
            {
                Selection.SelectAll();
                ClearSelected();
                history.Clear();
                Invalidate();
            }
            finally { Selection.EndUpdate(); }
        }
        public void SelectAll() => Selection.SelectAll();
        public virtual void Copy()
        {
            if (Selection.IsEmpty) Selection.Expand();
            if (!Selection.IsEmpty)
            {
                var data = new DataObject();
                OnCreateClipboardData(data);
                Clipboard.SetDataObject(data, true);
            }
        }
        protected virtual void OnCreateClipboardData(DataObject data) => data.SetData(DataFormats.UnicodeText, Selection.Text);
        public virtual void Cut()
        {
            if (!Selection.IsEmpty)
            {
                Copy();
                ClearSelected();
            }
            else if (LinesCount == 1)
            {
                Selection.SelectAll();
                Copy();
                ClearSelected();
            }
            else
            {
                Copy();
                if (Selection.Start.iLine >= 0 && Selection.Start.iLine < LinesCount)
                {
                    int iLine = Selection.Start.iLine;
                    Selection = iLine < LinesCount - 1 ? new Range(this, 0, iLine, 0, iLine + 1)
                                                        : new Range(this, lines[iLine - 1].Count, iLine - 1, lines[iLine].Count, iLine);
                    ClearSelected();
                }
            }
        }
        public virtual void Paste()
        {
            string text = Clipboard.ContainsText() ? Clipboard.GetText() : null;
            if (!string.IsNullOrEmpty(text)) InsertText(text);
        }
        public void Undo() { history.Undo(); Invalidate(); }
        public void Redo() { history.Redo(); Invalidate(); }
        public void ClearUndo() => history.Clear();
        public void BeginAutoUndo() => history.BeginAutoUndo();
        public void EndAutoUndo() => history.EndAutoUndo();
        public void BeginUpdate()
        {
            if (updating == 0) updatingRange = null;
            updating++;
        }
        public void EndUpdate()
        {
            updating--;
            if (updating == 0 && updatingRange != null)
            {
                updatingRange.Expand();
                OnTextChanged(updatingRange);
            }
        }

        // Primitive changes (the commands use these; they do not record undo)
        internal Place InsertRaw(Place place, string text)
        {
            var current = place;
            for (int i = 0; i < text.Length; i++)
            {
                char c = text[i];
                if (c == '\r')
                {
                    if (i < text.Length - 1 && text[i + 1] == '\n') continue;
                    c = '\n';
                }
                if (c == '\n')
                {
                    Line line = lines[current.iLine];
                    var rest = new Line();
                    rest.AddRange(line.GetRange(current.iChar, line.Count - current.iChar));
                    line.RemoveRange(current.iChar, line.Count - current.iChar);
                    lines.Insert(current.iLine + 1, rest);
                    Bookmarks.LinesInserted(current.iLine + 1, 1);
                    line.IsChanged = rest.IsChanged = true;
                    current = new Place(0, current.iLine + 1);
                }
                else if (c == '\t')
                {
                    int spaces = TabLength - current.iChar % TabLength;
                    for (int s = 0; s < spaces; s++) lines[current.iLine].Insert(current.iChar++, new Char(' '));
                    lines[current.iLine].IsChanged = true;
                }
                else
                {
                    lines[current.iLine].Insert(current.iChar, new Char(c));
                    lines[current.iLine].IsChanged = true;
                    current.iChar++;
                }
            }
            return current;
        }
        internal string RemoveRaw(Place from, Place to)
        {
            if (to < from) { var t = from; from = to; to = t; }
            string removed = new Range(this, from, to).Text;
            if (from.iLine == to.iLine)
                lines[from.iLine].RemoveRange(from.iChar, to.iChar - from.iChar);
            else
            {
                Line first = lines[from.iLine];
                first.RemoveRange(from.iChar, first.Count - from.iChar);
                Line last = lines[to.iLine];
                first.AddRange(last.GetRange(to.iChar, last.Count - to.iChar));
                lines.RemoveRange(from.iLine + 1, to.iLine - from.iLine);
                Bookmarks.LinesRemoved(from.iLine + 1, to.iLine - from.iLine);
            }
            lines[from.iLine].IsChanged = true;
            return removed;
        }

        // Change notifications
        public virtual void OnTextChanging(ref string text)
        {
            if (TextChanging != null)
            {
                var args = new TextChangingEventArgs { InsertingText = text };
                TextChanging(this, args);
                text = args.InsertingText;
                if (args.Cancel) text = string.Empty;
            }
        }
        public virtual void OnTextChanging()
        {
            string temp = null;
            OnTextChanging(ref temp);
        }
        public virtual void OnTextChanged() { var r = new Range(this); r.SelectAll(); OnTextChanged(new TextChangedEventArgs(r)); }
        public virtual void OnTextChanged(int fromLine, int toLine)
        {
            fromLine = Math.Max(0, Math.Min(fromLine, LinesCount - 1));
            toLine = Math.Max(0, Math.Min(toLine, LinesCount - 1));
            var r = new Range(this);
            r.Start = new Place(0, Math.Min(fromLine, toLine));
            r.End = new Place(lines[Math.Max(fromLine, toLine)].Count, Math.Max(fromLine, toLine));
            OnTextChanged(new TextChangedEventArgs(r));
        }
        public virtual void OnTextChanged(Range r) => OnTextChanged(new TextChangedEventArgs(r));
        protected virtual void OnTextChanged(TextChangedEventArgs args)
        {
            args.ChangedRange.Normalize();
            if (updating > 0)
            {
                updatingRange = updatingRange == null ? args.ChangedRange.Clone()
                    : new Range(this, updatingRange.Start < args.ChangedRange.Start ? updatingRange.Start : args.ChangedRange.Start,
                                updatingRange.End > args.ChangedRange.End ? updatingRange.End : args.ChangedRange.End);
                return;
            }
            IsChanged = true;
            TextVersion++;
            base.OnTextChanged(EventArgs.Empty);
            TextChanged?.Invoke(this, args);
            Notify("Text");
            delayedTextChangedRange = delayedTextChangedRange == null ? args.ChangedRange.Clone()
                : new Range(this, new Place(0, Math.Min(delayedTextChangedRange.FromLine, args.ChangedRange.FromLine)),
                            new Place(0, Math.Max(delayedTextChangedRange.ToLine, args.ChangedRange.ToLine)));
            delayedTextChangedTimer.Stop();
            delayedTextChangedTimer.Start();
        }
        void RaiseDelayedTextChanged()
        {
            if (delayedTextChangedRange == null) return;
            Range range = delayedTextChangedRange;
            delayedTextChangedRange = null;
            int from = Math.Min(range.FromLine, LinesCount - 1), to = Math.Min(range.ToLine, LinesCount - 1);
            OnTextChangedDelayed(new Range(this, 0, from, lines[to].Count, to));
        }
        public virtual void OnTextChangedDelayed(Range changedRange) => TextChangedDelayed?.Invoke(this, new TextChangedEventArgs(changedRange));
        /// <summary>Raises a pending TextChangedDelayed now (the renderer's idle flush and tests).</summary>
        public void FlushDelayedEvents()
        {
            if (delayedTextChangedTimer.Enabled) { delayedTextChangedTimer.Stop(); RaiseDelayedTextChanged(); }
            if (delayedSelectionTimer.Enabled) { delayedSelectionTimer.Stop(); OnSelectionChangedDelayed(); }
        }
        public virtual void OnSelectionChanged()
        {
            SelectionChanged?.Invoke(this, EventArgs.Empty);
            Notify("Selection");
            delayedSelectionTimer.Stop();
            delayedSelectionTimer.Start();
        }
        public virtual void OnSelectionChangedDelayed() => SelectionChangedDelayed?.Invoke(this, EventArgs.Empty);
        public virtual void OnUndoRedoStateChanged() => UndoRedoStateChanged?.Invoke(this, EventArgs.Empty);

        // View
        public void DoCaretVisible() => Notify("ScrollToCaret");
        public void DoSelectionVisible() => Notify("ScrollToCaret");
        public void DoRangeVisible(Range range) => DoRangeVisible(range, false);
        public void DoRangeVisible(Range range, bool tryToCentre) => Notify("ScrollToCaret");
        public void Navigate(int iLine)
        {
            if (iLine >= LinesCount) return;
            Selection.Start = new Place(0, iLine);
            DoSelectionVisible();
        }
        public void BookmarkLine(int iLine) => Bookmarks.Add(iLine);
        public void UnbookmarkLine(int iLine) => Bookmarks.Remove(iLine);
        public void GoHome()
        {
            Selection.Start = new Place(0, 0);
            DoCaretVisible();
        }
        public void GoEnd()
        {
            if (lines.Count > 0) Selection.Start = new Place(lines[lines.Count - 1].Count, lines.Count - 1);
            DoCaretVisible();
        }
        public virtual void GoHome(bool shift)
        {
            Selection.BeginUpdate();
            try
            {
                int iLine = Selection.Start.iLine;
                int spaces = this[iLine].StartSpacesCount;
                if (Selection.Start.iChar <= spaces) Selection.GoHome(shift);
                else
                {
                    Selection.GoHome(shift);
                    for (int i = 0; i < spaces; i++) Selection.GoRight(shift);
                }
            }
            finally { Selection.EndUpdate(); }
        }
        public void ShowFindDialog() => ShowFindDialog(null);
        public virtual void ShowFindDialog(string findText)
        {
            if (findForm == null) findForm = new FindForm(this);
            if (findText != null) findForm.tbFind.Text = findText;
            else if (!Selection.IsEmpty && Selection.Start.iLine == Selection.End.iLine) findForm.tbFind.Text = Selection.Text;
            findForm.Show();
            findForm.Focus();
        }
        public void ShowReplaceDialog() => ShowReplaceDialog(null);
        public virtual void ShowReplaceDialog(string findText)
        {
            if (ReadOnly) return;
            if (replaceForm == null) replaceForm = new ReplaceForm(this);
            if (findText != null) replaceForm.tbFind.Text = findText;
            else if (!Selection.IsEmpty && Selection.Start.iLine == Selection.End.iLine) replaceForm.tbFind.Text = Selection.Text;
            replaceForm.Show();
            replaceForm.Focus();
        }

        // Style runs of a line for the renderer: start, length, fore ARGB (0 = default), back ARGB (0 = none),
        // font style, marker ARGB (0 = none); the first text style of a character draws, markers always.
        public int[] GetLineRuns(int iLine)
        {
            var result = new List<int>();
            Line line = lines[iLine];
            int i = 0;
            while (i < line.Count)
            {
                StyleIndex style = line[i].style;
                int j = i + 1;
                while (j < line.Count && line[j].style == style) j++;
                int fore = 0, back = 0, font = 0, marker = 0;
                bool hasTextStyle = false;
                for (int k = 0; k < Styles.Length; k++)
                {
                    if (((int)style & (1 << k)) == 0 || Styles[k] == null) continue;
                    switch (Styles[k])
                    {
                        case TextStyle t:
                            // FCTB FlushRendering: only the first text style of a character draws (unless
                            // AllowSeveralTextStyleDrawing); other style kinds always draw
                            if (hasTextStyle && !AllowSeveralTextStyleDrawing) break;
                            if (t.ForeBrush != null) fore = t.ForeBrush.Color.ToArgb();
                            if (t.BackgroundBrush != null) back = t.BackgroundBrush.Color.ToArgb();
                            font = (int)t.FontStyle;
                            hasTextStyle = true;
                            break;
                        case MarkerStyle m:
                            if (m.BackgroundBrush != null) marker = m.BackgroundBrush.Color.ToArgb();
                            break;
                    }
                }
                result.AddRange(new[] { i, j - i, fore, back, font, marker });
                i = j;
            }
            return result.ToArray();
        }

        // Keyboard (FCTB OnKeyDown/ProcessKey and WM_CHAR processing)
        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            if (Focused) lastModifiers = e.Modifiers;
            handledChar = false;
            if (e.Handled)
            {
                handledChar = true;
                return;
            }
            if (ProcessKey(e.KeyData)) return;
            e.Handled = true;
            DoCaretVisible();
            Invalidate();
        }
        protected override void ProcessCharInput(char c, Keys modifiers)
        {
            ProcessKey(c, modifiers);
            base.ProcessCharInput(c, modifiers);
        }
        public virtual bool ProcessKey(Keys keyData)
        {
            var a = new KeyEventArgs(keyData);
            if (a.KeyCode == Keys.Tab && !AcceptsTab) return false;
            if (HotkeysMapping.TryGetValue(keyData, out FCTBAction act))
            {
                DoAction(act);
                if (act == FCTBAction.ScrollDown || act == FCTBAction.ScrollUp || act == FCTBAction.ZoomIn || act == FCTBAction.ZoomOut || act == FCTBAction.ZoomNormal) return true;
                if (keyData == Keys.Tab || keyData == (Keys.Tab | Keys.Shift))
                {
                    handledChar = true;
                    return true;
                }
            }
            else
            {
                if (a.KeyCode == Keys.Alt) return true;
                if ((a.Modifiers & Keys.Control) != 0) return true;
                if ((a.Modifiers & Keys.Alt) != 0) return true;
                if (a.KeyCode == Keys.ShiftKey) return true;
            }
            return false;
        }
        void DoAction(FCTBAction action)
        {
            switch (action)
            {
                case FCTBAction.ZoomIn: Zoom += 10; break;
                case FCTBAction.ZoomOut: Zoom = Math.Max(10, Zoom - 10); break;
                case FCTBAction.ZoomNormal: Zoom = 100; break;
                case FCTBAction.FindDialog: ShowFindDialog(); break;
                case FCTBAction.FindNext:
                    if (findForm == null || findForm.tbFind.Text == "") ShowFindDialog();
                    else findForm.FindNext(findForm.tbFind.Text);
                    break;
                case FCTBAction.ReplaceDialog: ShowReplaceDialog(); break;
                case FCTBAction.Copy: Copy(); break;
                case FCTBAction.CommentSelected: CommentSelected(); break;
                case FCTBAction.Cut: if (!Selection.ReadOnly) Cut(); break;
                case FCTBAction.Paste: if (!Selection.ReadOnly) Paste(); break;
                case FCTBAction.SelectAll: Selection.SelectAll(); break;
                case FCTBAction.Undo: if (!ReadOnly) Undo(); break;
                case FCTBAction.Redo: if (!ReadOnly) Redo(); break;
                case FCTBAction.LowerCase: if (!Selection.ReadOnly) ReplaceSelected(Selection.Text.ToLower()); break;
                case FCTBAction.UpperCase: if (!Selection.ReadOnly) ReplaceSelected(Selection.Text.ToUpper()); break;
                case FCTBAction.IndentDecrease: if (!Selection.ReadOnly) DecreaseIndent(); break;
                case FCTBAction.IndentIncrease: if (!Selection.ReadOnly) IncreaseIndent(); break;
                case FCTBAction.BookmarkLine: BookmarkLine(Selection.Start.iLine); break;
                case FCTBAction.UnbookmarkLine: UnbookmarkLine(Selection.Start.iLine); break;
                case FCTBAction.ClearWordLeft:
                    if (OnKeyPressing('\b')) break;
                    if (!Selection.ReadOnly)
                    {
                        if (!Selection.IsEmpty) ClearSelected();
                        Selection.GoWordLeft(true);
                        if (!Selection.ReadOnly) ClearSelected();
                    }
                    OnKeyPressed('\b');
                    break;
                case FCTBAction.ClearWordRight:
                    if (OnKeyPressing((char)0xff)) break;
                    if (!Selection.ReadOnly)
                    {
                        if (!Selection.IsEmpty) ClearSelected();
                        Selection.GoWordRight(true);
                        if (!Selection.ReadOnly) ClearSelected();
                    }
                    OnKeyPressed((char)0xff);
                    break;
                case FCTBAction.DeleteCharRight:
                    if (OnKeyPressing((char)0xff)) break;
                    if (!Selection.ReadOnly)
                    {
                        if (!Selection.IsEmpty) ClearSelected();
                        else if (Selection.Start.iChar < lines[Selection.Start.iLine].Count || Selection.Start.iLine < LinesCount - 1)
                            history.Execute(new InsertCharCommand(this, (char)0xff));
                    }
                    OnKeyPressed((char)0xff);
                    break;
                case FCTBAction.GoLeft: Selection.GoLeft(false); break;
                case FCTBAction.GoLeftWithSelection: Selection.GoLeft(true); break;
                case FCTBAction.GoRight: Selection.GoRight(false); break;
                case FCTBAction.GoRightWithSelection: Selection.GoRight(true); break;
                case FCTBAction.GoUp: Selection.GoUp(false); break;
                case FCTBAction.GoUpWithSelection: Selection.GoUp(true); break;
                case FCTBAction.GoDown: Selection.GoDown(false); break;
                case FCTBAction.GoDownWithSelection: Selection.GoDown(true); break;
                case FCTBAction.GoPageUp: Selection.GoPageUp(false); break;
                case FCTBAction.GoPageUpWithSelection: Selection.GoPageUp(true); break;
                case FCTBAction.GoPageDown: Selection.GoPageDown(false); break;
                case FCTBAction.GoPageDownWithSelection: Selection.GoPageDown(true); break;
                case FCTBAction.GoFirstLine: Selection.GoFirst(false); break;
                case FCTBAction.GoFirstLineWithSelection: Selection.GoFirst(true); break;
                case FCTBAction.GoLastLine: Selection.GoLast(false); break;
                case FCTBAction.GoLastLineWithSelection: Selection.GoLast(true); break;
                case FCTBAction.GoHome: GoHome(false); break;
                case FCTBAction.GoHomeWithSelection: GoHome(true); break;
                case FCTBAction.GoEnd: Selection.GoEnd(false); break;
                case FCTBAction.GoEndWithSelection: Selection.GoEnd(true); break;
                case FCTBAction.GoWordLeft: Selection.GoWordLeft(false); break;
                case FCTBAction.GoWordLeftWithSelection: Selection.GoWordLeft(true); break;
                case FCTBAction.GoWordRight: Selection.GoWordRight(false); break;
                case FCTBAction.GoWordRightWithSelection: Selection.GoWordRight(true); break;
                case FCTBAction.ReplaceMode: if (!ReadOnly) IsReplaceMode = !IsReplaceMode; break;
                case FCTBAction.ScrollDown: Notify("ScrollDown"); break;
                case FCTBAction.ScrollUp: Notify("ScrollUp"); break;
                case FCTBAction.ClearHints: break;
            }
        }
        void ReplaceSelected(string text)
        {
            Place start = Selection.Start, end = Selection.End;
            InsertText(text);
            Selection.Start = start;
            Selection.End = end;
        }
        public void CommentSelected() => CommentSelected(CommentPrefix);
        public virtual void CommentSelected(string commentPrefix)
        {
            if (string.IsNullOrEmpty(commentPrefix)) return;
            Selection.Normalize();
            bool isCommented = lines[Selection.Start.iLine].Text.TrimStart().StartsWith(commentPrefix);
            if (isCommented) RemoveLinePrefix(commentPrefix);
            else InsertLinePrefix(commentPrefix);
        }
        public void InsertLinePrefix(string prefix)
        {
            Range old = Selection.Clone();
            int from = Math.Min(Selection.Start.iLine, Selection.End.iLine);
            int to = Math.Max(Selection.Start.iLine, Selection.End.iLine);
            BeginUpdate();
            Selection.BeginUpdate();
            history.BeginAutoUndo();
            try
            {
                int spaces = Enumerable.Range(from, to - from + 1).Where(i => lines[i].Text.Trim().Length > 0)
                    .Select(i => lines[i].StartSpacesCount).DefaultIfEmpty(0).Min();
                for (int i = from; i <= to; i++)
                {
                    Selection.Start = new Place(Math.Min(spaces, lines[i].Count), i);
                    history.Execute(new InsertTextCommand(this, prefix));
                }
                Selection.Start = new Place(0, from);
                Selection.End = new Place(lines[to].Count, to);
            }
            finally
            {
                history.EndAutoUndo();
                Selection.EndUpdate();
                EndUpdate();
            }
            Invalidate();
        }
        public void RemoveLinePrefix(string prefix)
        {
            int from = Math.Min(Selection.Start.iLine, Selection.End.iLine);
            int to = Math.Max(Selection.Start.iLine, Selection.End.iLine);
            BeginUpdate();
            Selection.BeginUpdate();
            history.BeginAutoUndo();
            try
            {
                for (int i = from; i <= to; i++)
                {
                    string text = lines[i].Text;
                    string trimmedText = text.TrimStart();
                    if (!trimmedText.StartsWith(prefix)) continue;
                    int spaces = text.Length - trimmedText.Length;
                    Selection.Start = new Place(spaces, i);
                    Selection.End = new Place(spaces + prefix.Length, i);
                    ClearSelected();
                }
                Selection.Start = new Place(0, from);
                Selection.End = new Place(lines[to].Count, to);
            }
            finally
            {
                history.EndAutoUndo();
                Selection.EndUpdate();
                EndUpdate();
            }
            Invalidate();
        }
        public virtual void IncreaseIndent()
        {
            if (Selection.Start == Selection.End)
            {
                if (!Selection.ReadOnly)
                {
                    Selection.Start = new Place(this[Selection.Start.iLine].StartSpacesCount, Selection.Start.iLine);
                    int spaces = TabLength - Selection.Start.iChar % TabLength;
                    InsertText(new string(' ', spaces));
                }
                return;
            }
            InsertLinePrefixForIndent(new string(' ', TabLength));
        }
        void InsertLinePrefixForIndent(string prefix)
        {
            Range old = Selection.Clone();
            old.Normalize();
            int from = old.Start.iLine, to = old.End.iLine;
            if (old.End.iChar == 0 && to > from) to--;
            BeginUpdate();
            Selection.BeginUpdate();
            history.BeginAutoUndo();
            try
            {
                for (int i = from; i <= to; i++)
                {
                    if (lines[i].Count == 0) continue;
                    Selection.Start = new Place(0, i);
                    history.Execute(new InsertTextCommand(this, prefix));
                }
                Selection.Start = new Place(0, from);
                Selection.End = new Place(lines[to].Count, to);
            }
            finally
            {
                history.EndAutoUndo();
                Selection.EndUpdate();
                EndUpdate();
            }
        }
        public virtual void DecreaseIndent()
        {
            Range old = Selection.Clone();
            old.Normalize();
            int from = old.Start.iLine, to = old.End.iLine;
            if (!old.IsEmpty && old.End.iChar == 0 && to > from) to--;
            BeginUpdate();
            Selection.BeginUpdate();
            history.BeginAutoUndo();
            try
            {
                for (int i = from; i <= to; i++)
                {
                    int spaces = Math.Min(lines[i].StartSpacesCount, TabLength);
                    if (spaces == 0) continue;
                    Selection.Start = new Place(0, i);
                    Selection.End = new Place(spaces, i);
                    history.Execute(new ClearSelectedCommand(this));
                }
                if (old.IsEmpty) Selection.Start = new Place(Math.Min(old.Start.iChar, lines[from].Count), from);
                else
                {
                    Selection.Start = new Place(0, from);
                    Selection.End = new Place(lines[to].Count, to);
                }
            }
            finally
            {
                history.EndAutoUndo();
                Selection.EndUpdate();
                EndUpdate();
            }
        }
        public void OnKeyPressing(KeyPressEventArgs args) => KeyPressing?.Invoke(this, args);
        bool OnKeyPressing(char c)
        {
            var args = new KeyPressEventArgs(c);
            OnKeyPressing(args);
            return args.Handled;
        }
        public void OnKeyPressed(char c) => KeyPressed?.Invoke(this, new KeyPressEventArgs(c));
        /// <summary>A typed character (FCTB ProcessKey(char, Keys)).</summary>
        public virtual bool ProcessKey(char c, Keys modifiers)
        {
            if (handledChar) return true;
            if (c == '\b' && (modifiers == Keys.None || modifiers == Keys.Shift || (modifiers & Keys.Alt) != 0))
            {
                if (ReadOnly || !Enabled) return false;
                if (OnKeyPressing(c)) return true;
                if (!Selection.IsEmpty) ClearSelected();
                else if (Selection.Start.iChar > 0 || Selection.Start.iLine > 0) InsertChar('\b');
                OnKeyPressed('\b');
                return true;
            }
            if (char.IsControl(c) && c != '\r' && c != '\t') return false;
            if (ReadOnly || !Enabled) return false;
            if (modifiers != Keys.None && modifiers != Keys.Shift && modifiers != (Keys.Control | Keys.Alt) &&
                modifiers != (Keys.Shift | Keys.Control | Keys.Alt) && (modifiers != Keys.Alt || char.IsLetterOrDigit(c)))
                return false;
            char sourceC = c;
            if (OnKeyPressing(sourceC)) return true;
            if (c == '\r' && !AcceptsReturn) return false;
            if (c == '\r') c = '\n';
            if (IsReplaceMode)
            {
                Selection.GoRight(true);
                Selection.Inverse();
            }
            if (!DoAutocompleteBrackets(c)) InsertChar(c);
            if (c == '\n' && AutoIndent) DoAutoIndent(Selection.Start.iLine);
            DoCaretVisible();
            Invalidate();
            OnKeyPressed(sourceC);
            return true;
        }
        /// <summary>FCTB InsertChar: a selection is cleared first, in one undo group with the character.</summary>
        void InsertChar(char c)
        {
            history.BeginAutoUndo();
            try
            {
                if (!Selection.IsEmpty) history.Execute(new ClearSelectedCommand(this));
                history.Execute(new InsertCharCommand(this, c));
            }
            finally { history.EndAutoUndo(); }
            Invalidate();
        }
        bool DoAutocompleteBrackets(char c)
        {
            if (!AutoCompleteBrackets) return false;
            for (int i = 1; i < autoCompleteBracketsList.Length; i += 2)
                if (c == autoCompleteBracketsList[i] && c == Selection.CharAfterStart)
                {
                    Selection.GoRight();
                    return true;
                }
            for (int i = 0; i < autoCompleteBracketsList.Length; i += 2)
                if (c == autoCompleteBracketsList[i])
                {
                    InsertBrackets(autoCompleteBracketsList[i], autoCompleteBracketsList[i + 1]);
                    return true;
                }
            return false;
        }
        void InsertBrackets(char left, char right)
        {
            Range original = Selection.Clone();
            original.Normalize();
            string text = Selection.Text;
            Selection.BeginUpdate();
            history.BeginAutoUndo();
            try
            {
                InsertText(left + text + right);
                Selection.Start = new Place(original.Start.iChar + 1, original.Start.iLine);
                if (text.Length > 0) Selection.End = new Place(original.End.iChar + (original.Start.iLine == original.End.iLine ? 1 : 0), original.End.iLine);
            }
            finally
            {
                history.EndAutoUndo();
                Selection.EndUpdate();
            }
        }
        /// <summary>FCTB auto indent: a new line takes the indent of the nearest non-empty line above it.</summary>
        void DoAutoIndent(int iLine)
        {
            if (iLine <= 0 || iLine >= LinesCount) return;
            int needSpaces = 0;
            for (int i = iLine - 1; i >= 0; i--)
                if (lines[i].Text.Trim().Length > 0) { needSpaces = lines[i].StartSpacesCount; break; }
            int spaces = lines[iLine].StartSpacesCount;
            if (needSpaces == spaces) { if (Selection.Start.iChar < spaces) Selection.Start = new Place(spaces, iLine); return; }
            Place caret = Selection.Start;
            Selection.BeginUpdate();
            history.BeginAutoUndo();
            try
            {
                Selection.Start = new Place(0, iLine);
                Selection.End = new Place(spaces, iLine);
                InsertText(new string(' ', needSpaces));
                Selection.Start = new Place(Math.Max(needSpaces, caret.iChar - spaces + needSpaces), iLine);
            }
            finally
            {
                history.EndAutoUndo();
                Selection.EndUpdate();
            }
        }

        // Mouse (renderer places)
        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Button == MouseButtons.Left)
            {
                Place place = PointToPlace(e.Location);
                if ((ModifierKeys & Keys.Shift) != 0) Selection.End = place;
                else Selection.Start = place;
                Invalidate();
            }
        }
        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            if (e.Button == MouseButtons.Left)
            {
                Place place = PointToPlace(e.Location);
                Selection.BeginUpdate();
                Place start = Selection.Start;
                Selection.Start = place;
                Selection.End = start;
                Selection.Inverse();
                Selection.Start = place;
                Selection.End = start;
                Selection.EndUpdate();
                Invalidate();
            }
        }
        protected override void OnMouseDoubleClick(MouseEventArgs e)
        {
            base.OnMouseDoubleClick(e);
            Place place = PointToPlace(e.Location);
            var fragment = new Range(this, place, place).GetFragment(@"[\w]");
            Selection.BeginUpdate();
            Selection.Start = fragment.Start;
            Selection.End = fragment.End;
            Selection.Inverse();
            Selection.EndUpdate();
            Invalidate();
        }
        protected virtual void CheckAndChangeSelectionType() { }
        protected virtual void OnScroll(ScrollEventArgs se) => Scroll?.Invoke(this, se);
        public void RaiseScroll() => OnScroll(new ScrollEventArgs(ScrollEventType.ThumbPosition, VerticalScrollValue));
        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                delayedTextChangedTimer.Dispose();
                delayedSelectionTimer.Dispose();
                findForm?.Dispose();
                replaceForm?.Dispose();
            }
            base.Dispose(disposing);
        }

        // Undo history: FCTB CommandManager (each command undoable; commands executed inside an auto-undo group are
        // undone together with the command before them)
        internal abstract class UndoableCommand
        {
            protected readonly FastColoredTextBox tb;
            protected Place sel, selEnd, lastSel, lastSelEnd;
            internal bool autoUndo;
            protected UndoableCommand(FastColoredTextBox tb)
            {
                this.tb = tb;
                sel = tb.Selection.Start;
                selEnd = tb.Selection.End;
            }
            public abstract void Execute();
            public abstract void Undo();
            public virtual void Redo()
            {
                tb.Selection.Start = sel;
                tb.Selection.End = selEnd;
                Execute();
            }
            protected void Remember() { lastSel = tb.Selection.Start; lastSelEnd = tb.Selection.End; }
        }
        sealed class InsertTextCommand : UndoableCommand
        {
            string text;
            Place insertStart, insertEnd;
            public InsertTextCommand(FastColoredTextBox tb, string text) : base(tb) { this.text = text; }
            public override void Execute()
            {
                tb.OnTextChanging(ref text);
                insertStart = tb.Selection.Start;
                insertEnd = tb.InsertRaw(insertStart, text);
                tb.Selection.Start = insertEnd;
                Remember();
                tb.OnTextChanged(insertStart.iLine, insertEnd.iLine);
            }
            public override void Undo()
            {
                tb.OnTextChanging();
                tb.RemoveRaw(insertStart, insertEnd);
                tb.Selection.Start = sel;
                tb.Selection.End = selEnd;
                tb.OnTextChanged(insertStart.iLine, insertStart.iLine);
            }
        }
        sealed class ClearSelectedCommand : UndoableCommand
        {
            string deletedText;
            Place from;
            public ClearSelectedCommand(FastColoredTextBox tb) : base(tb) { }
            public override void Execute()
            {
                string temp = null;
                tb.OnTextChanging(ref temp);
                if (temp == "") throw new ArgumentOutOfRangeException();
                Range s = tb.Selection.Clone();
                s.Normalize();
                from = s.Start;
                deletedText = tb.RemoveRaw(s.Start, s.End);
                tb.Selection.Start = from;
                Remember();
                tb.OnTextChanged(from.iLine, from.iLine);
            }
            public override void Undo()
            {
                tb.OnTextChanging();
                Place end = tb.InsertRaw(from, deletedText);
                tb.Selection.Start = sel;
                tb.Selection.End = selEnd;
                tb.OnTextChanged(from.iLine, end.iLine);
            }
        }
        sealed class InsertCharCommand : UndoableCommand
        {
            readonly char c;
            string deleted = "";
            Place place, after;
            public InsertCharCommand(FastColoredTextBox tb, char c) : base(tb) { this.c = c; }
            public override void Execute()
            {
                string text = c.ToString();
                tb.OnTextChanging(ref text);
                place = tb.Selection.Start;
                if (c == '\b')
                {
                    Place before = place.iChar > 0 ? new Place(place.iChar - 1, place.iLine) : new Place(tb[place.iLine - 1].Count, place.iLine - 1);
                    deleted = tb.RemoveRaw(before, place);
                    after = before;
                }
                else if (c == (char)0xff)
                {
                    Place next = place.iChar < tb[place.iLine].Count ? new Place(place.iChar + 1, place.iLine) : new Place(0, place.iLine + 1);
                    deleted = tb.RemoveRaw(place, next);
                    after = place;
                }
                else after = tb.InsertRaw(place, text);
                tb.Selection.Start = after;
                Remember();
                tb.OnTextChanged(Math.Min(place.iLine, after.iLine), Math.Max(place.iLine, after.iLine));
            }
            public override void Undo()
            {
                tb.OnTextChanging();
                if (c == '\b' || c == (char)0xff) tb.InsertRaw(after, deleted);
                else tb.RemoveRaw(place, after);
                tb.Selection.Start = sel;
                tb.Selection.End = selEnd;
                tb.OnTextChanged(Math.Min(place.iLine, after.iLine), Math.Max(place.iLine, after.iLine));
            }
        }
        sealed class CommandHistory
        {
            const int MaxHistoryLength = 200;
            readonly FastColoredTextBox tb;
            readonly LinkedList<UndoableCommand> history = new LinkedList<UndoableCommand>();
            readonly Stack<UndoableCommand> redoStack = new Stack<UndoableCommand>();
            int autoUndoCommands, disabledCommands;
            public CommandHistory(FastColoredTextBox tb) { this.tb = tb; }
            public bool UndoEnabled => history.Count > 0;
            public bool RedoEnabled => redoStack.Count > 0;
            public void Execute(UndoableCommand cmd)
            {
                if (disabledCommands > 0) return;
                cmd.autoUndo = autoUndoCommands > 0;
                history.AddLast(cmd);
                if (history.Count > MaxHistoryLength) history.RemoveFirst();
                try { cmd.Execute(); }
                catch (ArgumentOutOfRangeException) { history.RemoveLast(); }
                redoStack.Clear();
                tb.OnUndoRedoStateChanged();
            }
            public void Undo()
            {
                if (history.Count > 0)
                {
                    UndoableCommand cmd = history.Last.Value;
                    history.RemoveLast();
                    disabledCommands++;
                    try { cmd.Undo(); }
                    finally { disabledCommands--; }
                    redoStack.Push(cmd);
                }
                if (history.Count > 0 && history.Last.Value.autoUndo) Undo();
                tb.OnUndoRedoStateChanged();
            }
            public void Redo()
            {
                if (redoStack.Count == 0) return;
                UndoableCommand cmd = redoStack.Pop();
                disabledCommands++;
                try { cmd.Redo(); }
                finally { disabledCommands--; }
                history.AddLast(cmd);
                if (cmd.autoUndo) Redo();
                tb.OnUndoRedoStateChanged();
            }
            public void BeginAutoUndo() => autoUndoCommands++;
            public void EndAutoUndo()
            {
                autoUndoCommands--;
                if (autoUndoCommands == 0 && history.Count > 0) history.Last.Value.autoUndo = false;
            }
            public void Clear()
            {
                history.Clear();
                redoStack.Clear();
                tb.OnUndoRedoStateChanged();
            }
        }
    }

    // Autocomplete menu (FCTB AutocompleteMenu / AutocompleteListView)
    public enum CompareResult { Hidden, Visible, VisibleAndSelected }

    public class AutocompleteItem
    {
        public object Tag;
        string toolTipTitle, toolTipText, menuText;
        public AutocompleteMenu Parent { get; internal set; }
        public string Text { get; set; }
        public int ImageIndex { get; set; } = -1;
        public AutocompleteItem() { }
        public AutocompleteItem(string text) { Text = text; }
        public AutocompleteItem(string text, int imageIndex) : this(text) { ImageIndex = imageIndex; }
        public AutocompleteItem(string text, int imageIndex, string menuText) : this(text, imageIndex) { this.menuText = menuText; }
        public AutocompleteItem(string text, int imageIndex, string menuText, string toolTipTitle, string toolTipText) : this(text, imageIndex, menuText)
        {
            this.toolTipTitle = toolTipTitle;
            this.toolTipText = toolTipText;
        }
        public virtual string GetTextForReplace() => Text;
        public virtual CompareResult Compare(string fragmentText)
        {
            if (Text.StartsWith(fragmentText, StringComparison.InvariantCultureIgnoreCase) && Text != fragmentText)
                return CompareResult.VisibleAndSelected;
            return CompareResult.Hidden;
        }
        public override string ToString() => menuText ?? Text;
        public virtual void OnSelected(AutocompleteMenu popupMenu, SelectedEventArgs e) { }
        public virtual string ToolTipTitle { get => toolTipTitle; set => toolTipTitle = value; }
        public virtual string ToolTipText { get => toolTipText; set => toolTipText = value; }
        public virtual string MenuText { get => menuText; set => menuText = value; }
        public virtual Color ForeColor { get => Color.Transparent; set => throw new NotImplementedException("Override this property to change color"); }
        public virtual Color BackColor { get => Color.Transparent; set => throw new NotImplementedException("Override this property to change color"); }
    }

    public class SelectingEventArgs : EventArgs
    {
        public AutocompleteItem Item { get; internal set; }
        public bool Cancel { get; set; }
        public int SelectedIndex { get; set; }
        public bool Handled { get; set; }
    }

    public class SelectedEventArgs : EventArgs
    {
        public AutocompleteItem Item { get; internal set; }
        public FastColoredTextBox Tb { get; set; }
    }

    /// <summary>The popup list of an AutocompleteMenu; the renderer draws its visible items under the fragment.</summary>
    public class AutocompleteListView
    {
        readonly FastColoredTextBox tb;
        internal AutocompleteMenu Menu;
        readonly List<AutocompleteItem> visibleItems = new List<AutocompleteItem>();
        IEnumerable<AutocompleteItem> sourceItems = new List<AutocompleteItem>();
        readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer();
        int focussedItemIndex;
        public event EventHandler FocussedItemIndexChanged;
        public Color SelectedColor { get; set; } = Color.Orange;
        public Color HoveredColor { get; set; } = Color.Red;
        public bool AllowTabKey { get; set; }
        public int AppearInterval { get => timer.Interval; set => timer.Interval = value; }
        public int ToolTipDuration { get; set; } = 3000;
        public Size MaxToolTipSize { get; set; }
        public bool AlwaysShowTooltip { get; set; }
        public ImageList ImageList { get; set; }
        public Size MinimumSize { get; set; }
        public Size MaximumSize { get; set; } = new Size(180, 180);
        public FontSpec Font { get; set; } = new FontSpec("Microsoft Sans Serif", 9);
        public int ItemHeight => Math.Max(18, (int)Math.Ceiling((Font?.Size ?? 9) * 96 / 72) + 4);
        public int Count => visibleItems.Count;
        public IReadOnlyList<AutocompleteItem> VisibleItems => visibleItems;
        public int FocussedItemIndex
        {
            get => focussedItemIndex;
            set
            {
                if (focussedItemIndex == value) return;
                focussedItemIndex = value;
                FocussedItemIndexChanged?.Invoke(this, EventArgs.Empty);
            }
        }
        public AutocompleteItem FocussedItem
        {
            get => focussedItemIndex >= 0 && focussedItemIndex < visibleItems.Count ? visibleItems[focussedItemIndex] : null;
            set => FocussedItemIndex = visibleItems.IndexOf(value);
        }

        internal AutocompleteListView(FastColoredTextBox tb)
        {
            this.tb = tb;
            AppearInterval = 500;
            timer.Tick += (s, e) => { timer.Stop(); DoAutocomplete(false); };
            tb.KeyDown += tb_KeyDown;
            tb.SelectionChanged += tb_SelectionChanged;
            tb.KeyPressed += tb_KeyPressed;
            tb.LostFocus += (s, e) => { if (Menu != null && !Menu.IsDisposed) Menu.Close(); };
            tb.Scroll += (s, e) => { if (Menu != null && !Menu.IsDisposed) Menu.Close(); };
        }
        public void Invalidate() => Menu?.RaiseChanged();
        void tb_KeyPressed(object sender, KeyPressEventArgs e)
        {
            bool backspaceORdel = e.KeyChar == '\b' || e.KeyChar == 0xff;
            if (Menu.Visible && !backspaceORdel) DoAutocomplete(false);
            else { timer.Stop(); timer.Start(); }
        }
        internal void DoAutocomplete(bool forced)
        {
            if (!Menu.Enabled) { Menu.Close(); return; }
            visibleItems.Clear();
            FocussedItemIndex = 0;
            Range fragment = tb.Selection.GetFragment(Menu.SearchPattern);
            string text = fragment.Text;
            if (forced || (text.Length >= Menu.MinFragmentLength && tb.Selection.IsEmpty && (tb.Selection.Start > fragment.Start || text.Length == 0)))
            {
                Menu.Fragment = fragment;
                bool foundSelected = false;
                foreach (AutocompleteItem item in sourceItems)
                {
                    item.Parent = Menu;
                    CompareResult res = item.Compare(text);
                    if (res != CompareResult.Hidden) visibleItems.Add(item);
                    if (res == CompareResult.VisibleAndSelected && !foundSelected)
                    {
                        foundSelected = true;
                        FocussedItemIndex = visibleItems.Count - 1;
                    }
                }
            }
            if (Count > 0)
            {
                if (!Menu.Visible)
                {
                    var args = new CancelEventArgs();
                    Menu.OnOpening(args);
                    if (!args.Cancel) Menu.ShowAt(tb.PlaceToPoint(fragment.End));
                }
                Invalidate();
            }
            else Menu.Close();
        }
        void tb_SelectionChanged(object sender, EventArgs e)
        {
            if (!Menu.Visible) return;
            bool needClose = false;
            if (!tb.Selection.IsEmpty) needClose = true;
            else if (!Menu.Fragment.Contains(tb.Selection.Start))
            {
                if (tb.Selection.Start.iLine == Menu.Fragment.End.iLine && tb.Selection.Start.iChar == Menu.Fragment.End.iChar + 1)
                {
                    char c = tb.Selection.CharBeforeStart;
                    if (!Regex.IsMatch(c.ToString(), Menu.SearchPattern)) needClose = true;
                }
                else needClose = true;
            }
            if (needClose) Menu.Close();
        }
        void tb_KeyDown(object sender, KeyEventArgs e)
        {
            if (Menu.Visible && ProcessKey(e.KeyCode, e.Modifiers)) e.Handled = true;
            if (!Menu.Visible)
            {
                if (tb.HotkeysMapping.TryGetValue(e.KeyData, out FCTBAction action) && action == FCTBAction.AutocompleteMenu)
                {
                    DoAutocomplete(false);
                    e.Handled = true;
                }
                else if (e.KeyCode == Keys.Escape && timer.Enabled) timer.Stop();
            }
        }
        bool ProcessKey(Keys keyData, Keys keyModifiers)
        {
            if (keyModifiers == Keys.None)
                switch (keyData)
                {
                    case Keys.Down: SelectNext(+1); return true;
                    case Keys.PageDown: SelectNext(+10); return true;
                    case Keys.Up: SelectNext(-1); return true;
                    case Keys.PageUp: SelectNext(-10); return true;
                    case Keys.Enter: OnSelecting(); return true;
                    case Keys.Tab:
                        if (!AllowTabKey) break;
                        OnSelecting();
                        return true;
                    case Keys.Escape: Menu.Close(); return true;
                }
            return false;
        }
        public void SelectNext(int shift)
        {
            FocussedItemIndex = Math.Max(0, Math.Min(FocussedItemIndex + shift, visibleItems.Count - 1));
            Invalidate();
        }
        internal virtual void OnSelecting()
        {
            if (FocussedItemIndex < 0 || FocussedItemIndex >= visibleItems.Count) return;
            tb.BeginAutoUndo();
            try
            {
                AutocompleteItem item = FocussedItem;
                var args = new SelectingEventArgs { Item = item, SelectedIndex = FocussedItemIndex };
                Menu.OnSelecting(args);
                if (args.Cancel)
                {
                    FocussedItemIndex = args.SelectedIndex;
                    Invalidate();
                    return;
                }
                if (!args.Handled) DoAutocomplete(item, Menu.Fragment);
                Menu.Close();
                var args2 = new SelectedEventArgs { Item = item, Tb = Menu.Fragment.tb };
                item.OnSelected(Menu, args2);
                Menu.OnSelected(args2);
            }
            finally { tb.EndAutoUndo(); }
        }
        void DoAutocomplete(AutocompleteItem item, Range fragment)
        {
            string newText = item.GetTextForReplace();
            FastColoredTextBox t = fragment.tb;
            t.BeginAutoUndo();
            t.Selection.Start = fragment.Start;
            t.Selection.End = fragment.End;
            t.InsertText(newText);
            t.EndAutoUndo();
            t.Focus();
        }
        /// <summary>A click on visible item index (renderer input).</summary>
        public void UserClickItem(int index, bool doubleClick)
        {
            FocussedItemIndex = index;
            Invalidate();
            if (doubleClick) OnSelecting();
        }
        public void SetAutocompleteItems(ICollection<string> items) => SetAutocompleteItems(items.Select(i => new AutocompleteItem(i)).ToList());
        public void SetAutocompleteItems(IEnumerable<AutocompleteItem> items) => sourceItems = items;
        internal void Dispose() => timer.Dispose();
    }

    /// <summary>Popup autocomplete menu of a FastColoredTextBox (a ToolStripDropDown in FCTB; here a model the
    /// renderer shows as a popup list below the fragment).</summary>
    public class AutocompleteMenu : IDisposable
    {
        readonly AutocompleteListView listView;
        bool visible;
        public static event Action<AutocompleteMenu, string> Changed;
        public FastColoredTextBox TextBox { get; }
        public Range Fragment { get; internal set; }
        public string SearchPattern { get; set; } = @"[\w\.]";
        public int MinFragmentLength { get; set; } = 2;
        public bool Enabled { get; set; } = true;
        public bool Visible => visible;
        public bool IsDisposed { get; private set; }
        public Point Location { get; private set; }
        public event EventHandler<SelectingEventArgs> Selecting;
        public event EventHandler<SelectedEventArgs> Selected;
        public event EventHandler<CancelEventArgs> Opening;
        public bool AllowTabKey { get => listView.AllowTabKey; set => listView.AllowTabKey = value; }
        public int AppearInterval { get => listView.AppearInterval; set => listView.AppearInterval = value; }
        public Size MaxTooltipSize { get => listView.MaxToolTipSize; set => listView.MaxToolTipSize = value; }
        public bool AlwaysShowTooltip { get => listView.AlwaysShowTooltip; set => listView.AlwaysShowTooltip = value; }
        public Color SelectedColor { get => listView.SelectedColor; set => listView.SelectedColor = value; }
        public Color HoveredColor { get => listView.HoveredColor; set => listView.HoveredColor = value; }
        public FontSpec Font { get => listView.Font; set => listView.Font = value; }
        public Size MinimumSize { get => listView.MinimumSize; set => listView.MinimumSize = value; }
        public Size MaximumSize { get => listView.MaximumSize; set => listView.MaximumSize = value; }
        public ImageList ImageList { get => listView.ImageList; set => listView.ImageList = value; }
        public int ToolTipDuration { get => listView.ToolTipDuration; set => listView.ToolTipDuration = value; }
        public AutocompleteListView Items => listView;

        public AutocompleteMenu(FastColoredTextBox tb)
        {
            TextBox = tb;
            listView = new AutocompleteListView(tb) { Menu = this };
        }
        internal void OnOpening(CancelEventArgs args) => Opening?.Invoke(this, args);
        internal void ShowAt(Point location)
        {
            Location = location;
            visible = true;
            Changed?.Invoke(this, "Show");
        }
        internal void RaiseChanged() { if (visible) Changed?.Invoke(this, "Items"); }
        public void Close()
        {
            if (!visible) return;
            visible = false;
            Changed?.Invoke(this, "Close");
        }
        public virtual void OnSelecting() => listView.OnSelecting();
        public void SelectNext(int shift) => listView.SelectNext(shift);
        internal void OnSelecting(SelectingEventArgs args) => Selecting?.Invoke(this, args);
        public void OnSelected(SelectedEventArgs args) => Selected?.Invoke(this, args);
        public void Show(bool forced) => listView.DoAutocomplete(forced);
        public void Dispose()
        {
            Close();
            IsDisposed = true;
            listView.Dispose();
        }
    }

    /// <summary>FCTB's Find form (FindForm.cs): pattern, match case, whole word, regex; Find next.</summary>
    public class FindForm : Form
    {
        internal readonly TextBox tbFind = new TextBox();
        internal readonly CheckBox cbMatchCase = new CheckBox(), cbWholeWord = new CheckBox(), cbRegex = new CheckBox();
        readonly Button btFindNext = new Button(), btClose = new Button();
        protected readonly FastColoredTextBox tb;
        Place startPlace;
        bool firstSearch = true;

        public FindForm(FastColoredTextBox tb)
        {
            this.tb = tb;
            Text = "Find";
            FormBorderStyle = FormBorderStyle.FixedToolWindow;
            StartPosition = FormStartPosition.CenterScreen;
            ShowInTaskbar = false;
            TopMost = true;
            ClientSize = new Size(360, 103);
            var label = new Label { Text = "Find: ", AutoSize = true, Location = new Point(23, 14) };
            tbFind.Location = new Point(62, 12);
            tbFind.Size = new Size(286, 20);
            cbMatchCase.Text = "Match case"; cbMatchCase.AutoSize = true; cbMatchCase.Location = new Point(66, 38);
            cbWholeWord.Text = "Match whole word"; cbWholeWord.AutoSize = true; cbWholeWord.Location = new Point(154, 38);
            cbRegex.Text = "Regex"; cbRegex.AutoSize = true; cbRegex.Location = new Point(273, 38);
            btFindNext.Text = "Find next"; btFindNext.Location = new Point(192, 68); btFindNext.Size = new Size(75, 23);
            btClose.Text = "Close"; btClose.Location = new Point(273, 68); btClose.Size = new Size(75, 23);
            btFindNext.Click += (s, e) => FindNext(tbFind.Text);
            btClose.Click += (s, e) => Close();
            tbFind.TextChanged += (s, e) => ResetSerach();
            cbMatchCase.CheckedChanged += (s, e) => ResetSerach();
            cbWholeWord.CheckedChanged += (s, e) => ResetSerach();
            cbRegex.CheckedChanged += (s, e) => ResetSerach();
            Controls.AddRange(new Control[] { label, tbFind, cbMatchCase, cbWholeWord, cbRegex, btFindNext, btClose });
            AcceptButton = btFindNext;
            CancelButton = btClose;
        }
        void ResetSerach() => firstSearch = true;
        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (e.CloseReason == CloseReason.UserClosing)
            {
                e.Cancel = true;
                Hide();
            }
            tb.Focus();
            base.OnFormClosing(e);
        }
        protected string Pattern(string pattern)
        {
            if (!cbRegex.Checked) pattern = Regex.Escape(pattern);
            if (cbWholeWord.Checked) pattern = "\\b" + pattern + "\\b";
            return pattern;
        }
        protected RegexOptions Options => cbMatchCase.Checked ? RegexOptions.None : RegexOptions.IgnoreCase;
        public virtual void FindNext(string pattern)
        {
            try
            {
                RegexOptions opt = Options;
                pattern = Pattern(pattern);
                Range range = tb.Selection.Clone();
                range.Normalize();
                if (firstSearch)
                {
                    startPlace = range.Start;
                    firstSearch = false;
                }
                range.Start = range.End;
                if (range.Start >= startPlace) range.End = new Place(tb.GetLineLength(tb.LinesCount - 1), tb.LinesCount - 1);
                else range.End = startPlace;
                foreach (Range r in range.GetRanges(pattern, opt))
                {
                    tb.Selection = r;
                    tb.DoSelectionVisible();
                    tb.Invalidate();
                    return;
                }
                if (range.Start >= startPlace && startPlace > Place.Empty)
                {
                    tb.Selection.Start = new Place(0, 0);
                    FindNext(pattern);
                    return;
                }
                MessageBox.Show("Not found");
            }
            catch (Exception ex) { MessageBox.Show(ex.Message); }
        }
    }

    /// <summary>FCTB's Replace form (ReplaceForm.cs): find next, replace, replace all.</summary>
    public class ReplaceForm : FindForm
    {
        internal readonly TextBox tbReplace = new TextBox();
        readonly Button btReplace = new Button(), btReplaceAll = new Button();

        public ReplaceForm(FastColoredTextBox tb) : base(tb)
        {
            Text = "Find and replace";
            ClientSize = new Size(360, 155);
            var label = new Label { Text = "Replace: ", AutoSize = true, Location = new Point(8, 68) };
            tbReplace.Location = new Point(62, 66);
            tbReplace.Size = new Size(286, 20);
            btReplace.Text = "Replace"; btReplace.Location = new Point(111, 120); btReplace.Size = new Size(75, 23);
            btReplaceAll.Text = "Replace all"; btReplaceAll.Location = new Point(30, 120); btReplaceAll.Size = new Size(75, 23);
            foreach (Control c in Controls) if (c is Button b) b.Top = 120;
            btReplace.Click += (s, e) => Replace();
            btReplaceAll.Click += (s, e) => ReplaceAll();
            Controls.AddRange(new Control[] { label, tbReplace, btReplace, btReplaceAll });
        }
        void Replace()
        {
            if (tb.SelectionLength != 0 && !tb.Selection.ReadOnly) tb.InsertText(tbReplace.Text);
            FindNext(tbFind.Text);
        }
        void ReplaceAll()
        {
            try
            {
                tb.Selection.BeginUpdate();
                var ranges = tb.Range.GetRanges(Pattern(tbFind.Text), Options).ToList();
                if (ranges.Count > 0)
                {
                    tb.BeginAutoUndo();
                    try
                    {
                        for (int i = ranges.Count - 1; i >= 0; i--)
                        {
                            tb.Selection.Start = ranges[i].Start;
                            tb.Selection.End = ranges[i].End;
                            tb.InsertText(tbReplace.Text);
                        }
                    }
                    finally { tb.EndAutoUndo(); }
                }
                tb.Selection.EndUpdate();
                tb.Invalidate();
                MessageBox.Show(ranges.Count + " occurrence(s) replaced");
            }
            catch (Exception ex)
            {
                tb.Selection.EndUpdate();
                MessageBox.Show(ex.Message);
            }
        }
    }
}
