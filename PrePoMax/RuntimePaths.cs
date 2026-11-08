using System;
using System.Windows.Forms;
namespace PrePoMax
{
    // Windows keeps its original installed layout. Native/headless hosts resolve
    // the same tool identities through their explicit runtime manifest.
    public static class RuntimePaths
    {
        public static Func<string,string> ToolResolver { get; set; }
        public static Func<string,bool> ExecutableValidator { get; set; }
        public static string Tool(string originalRelativePath)
        {
            return ToolResolver == null ? Application.StartupPath + originalRelativePath : ToolResolver(originalRelativePath);
        }
        // Gmsh carries this optional helper directory even for algorithms which
        // never invoke it. Required execution still goes through Tool().
        public static string OptionalTool(string originalRelativePath)
        {
            try { return Tool(originalRelativePath); }
            catch (System.IO.FileNotFoundException) { return null; }
        }
        public static bool IsExecutable(string path)
        {
            if (ExecutableValidator != null) return ExecutableValidator(path);
            string extension = System.IO.Path.GetExtension(path);
            return extension == ".exe" || extension == ".bat" || extension == ".cmd";
        }
    }
}
