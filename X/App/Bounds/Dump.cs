// The per-form bounds comparison (M3-1a): every original form class is constructed as the application constructs
// it (InitializeComponent; reference arguments null), laid out, and the bounds of every control are written as JSON.
// The same source runs twice: on .NET Framework 4.8 with WinForms and the original 3.0.1 (Windows, or CrossOver as
// evidence), and on .NET 10 with the FormsCompat control model and X/App. compare.py compares the two files.
// C# 7.3: it is compiled by the net48 project too.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Windows.Forms;

namespace PrePoMaxX.Bounds
{
    public static class Dump
    {
        public static int Run(Assembly[] assemblies, string output, string platform)
        {
            var text = new StringBuilder();
            text.Append("{\"platform\":").Append(Quote(platform)).Append(",\"forms\":[");
            bool firstForm = true;
            var types = assemblies.SelectMany(Types)
                                  .Where(t => typeof(Form).IsAssignableFrom(t) && !t.IsAbstract && !t.ContainsGenericParameters)
                                  .OrderBy(t => t.FullName, StringComparer.Ordinal).ToList();
            foreach (Type type in types)
            {
                if (!firstForm) text.Append(',');
                firstForm = false;
                text.Append("\n{\"type\":").Append(Quote(type.FullName));
                Form form = null;
                try
                {
                    form = Construct(type);
                    // The layouts WinForms runs before the form appears (a pending one per container), top down
                    PerformLayouts(form);
                    text.Append(",\"autoScale\":").Append(Quote(AutoScale(form)));
                    text.Append(",\"client\":").Append(Size(form.ClientSize));
                    text.Append(",\"controls\":[");
                    bool first = true;
                    Write(text, form, "", ref first);
                    text.Append(']');
                }
                catch (Exception error)
                {
                    Exception inner = error is TargetInvocationException && error.InnerException != null ? error.InnerException : error;
                    text.Append(",\"error\":").Append(Quote(inner.GetType().Name + ": " + inner.Message));
                }
                finally
                {
                    try { if (form != null) form.Dispose(); } catch { }
                }
                text.Append('}');
            }
            text.Append("\n]}\n");
            File.WriteAllText(output, text.ToString());
            Console.WriteLine(types.Count + " forms written to " + output);
            return 0;
        }

        static IEnumerable<Type> Types(Assembly assembly)
        {
            try { return assembly.GetTypes(); }
            catch (ReflectionTypeLoadException error) { return error.Types.Where(t => t != null); }
        }

        static Form Construct(Type type)
        {
            ConstructorInfo constructor = type.GetConstructors().OrderBy(c => c.GetParameters().Length).FirstOrDefault();
            if (constructor == null) throw new MissingMethodException("No public constructor.");
            object[] arguments = constructor.GetParameters()
                .Select(p => p.HasDefaultValue ? p.DefaultValue : p.ParameterType.IsValueType ? Activator.CreateInstance(p.ParameterType) : null)
                .ToArray();
            return (Form)constructor.Invoke(arguments);
        }

        static void PerformLayouts(Control control)
        {
            control.PerformLayout();
            foreach (Control child in control.Controls) PerformLayouts(child);
        }

        static string AutoScale(Form form)
        {
            // The designer's and the current font dimensions: when they differ, WinForms scales the form
            PropertyInfo current = typeof(ContainerControl).GetProperty("CurrentAutoScaleDimensions");
            string value = form.AutoScaleDimensions.Width.ToString(CultureInfo.InvariantCulture) + "x" +
                           form.AutoScaleDimensions.Height.ToString(CultureInfo.InvariantCulture);
            if (current != null)
            {
                var size = (System.Drawing.SizeF)current.GetValue(form, null);
                value += " current " + size.Width.ToString(CultureInfo.InvariantCulture) + "x" + size.Height.ToString(CultureInfo.InvariantCulture);
            }
            return value + " " + form.AutoScaleMode;
        }

        static void Write(StringBuilder text, Control parent, string path, ref bool first)
        {
            int index = 0;
            foreach (Control control in parent.Controls)
            {
                string name = string.IsNullOrEmpty(control.Name) ? "#" + index : control.Name;
                string childPath = path.Length == 0 ? name : path + "/" + name;
                if (!first) text.Append(',');
                first = false;
                text.Append("\n {\"path\":").Append(Quote(childPath))
                    .Append(",\"type\":").Append(Quote(control.GetType().Name))
                    .Append(",\"bounds\":[").Append(control.Left).Append(',').Append(control.Top).Append(',')
                    .Append(control.Width).Append(',').Append(control.Height).Append("]}");
                Write(text, control, childPath, ref first);
                index++;
            }
        }

        static string Size(System.Drawing.Size size) => "[" + size.Width + "," + size.Height + "]";

        static string Quote(string value)
        {
            if (value == null) return "null";
            var text = new StringBuilder("\"");
            foreach (char c in value)
            {
                if (c == '"' || c == '\\') text.Append('\\').Append(c);
                else if (c < 32) text.Append("\\u").Append(((int)c).ToString("x4"));
                else text.Append(c);
            }
            return text.Append('"').ToString();
        }
    }
}
