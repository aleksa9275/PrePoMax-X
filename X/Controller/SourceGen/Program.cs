using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

var root = Path.GetFullPath(args[0]);
var files = Directory.GetFiles(Path.Combine(root, "PrePoMax"), "*.cs", SearchOption.AllDirectories);
var names = new HashSet<string>();
var sourceNames = System.Xml.Linq.XDocument.Load(Path.Combine(root,"X/Domain/PrePoMax/Sources.g.props")).Descendants("Compile").Select(e=>e.Attribute("Include").Value.Replace("$(RepositoryRoot)",root+"/")).ToHashSet();
foreach (var f in files.Where(f => sourceNames.Contains(f)))
 foreach (var n in CSharpSyntaxTree.ParseText(File.ReadAllText(f)).GetRoot().DescendantNodes().OfType<MemberAccessExpressionSyntax>())
  if(n.Expression.ToString() is "_form" or "Form" or "form" || (n.Expression.ToString().EndsWith(".Form") || n.Expression.ToString().EndsWith(".Host")) || n.Expression.ToString().EndsWith("Form()")) names.Add(n.Name.Identifier.Text);
// RPC talks directly to FrmMain. These four methods have typed native implementations
// in AutomationHost.cs; emitting presentation forwarding methods would duplicate them.
var nativeAutomationMembers=new HashSet<string>{"PrepareAutomationPythonEngine","EchoAutomationExecution","GetAutomationBusyReason","RequestAutomationExit","AutomationModelFileName"};
var output = new System.Text.StringBuilder("// Generated presentation contract from original FrmMain signatures.\nusing CaeGlobals; using CaeJob; using CaeMesh; using CaeModel; using CaeResults; using FileInOut.Output; using PrePoMax.Commands; using PrePoMax.Forms; using PrePoMax.Python; using System; using System.Collections.Generic; using System.Drawing; using System.Threading.Tasks; using System.Windows.Forms; using UserControls; using vtkControl;\nnamespace PrePoMax { public partial class FrmMain {\n");
foreach(var f in files.Where(f=>Path.GetFileName(f).StartsWith("FrmMain.") || Path.GetFileName(f)=="FrmMain.cs"))
{
 var tree=CSharpSyntaxTree.ParseText(File.ReadAllText(f)).GetRoot();
 foreach(var c in tree.DescendantNodes().OfType<ClassDeclarationSyntax>().Where(c=>c.Identifier.Text=="FrmMain"))
 foreach(var m in c.Members)
 {
  if(m is MethodDeclarationSyntax method && names.Contains(method.Identifier.Text) && method.Identifier.Text != "InvokeIfRequired" && !nativeAutomationMembers.Contains(method.Identifier.Text) && method.Modifiers.Any(SyntaxKind.PublicKeyword))
  {
   var values=method.ParameterList.Parameters.Select(p=>p.Modifiers.Any(SyntaxKind.OutKeyword)?"null":p.Identifier.Text);
   string argsExpr="new object[] {"+string.Join(",",values)+"}";
   string body="var args = "+argsExpr+";";
   bool isVoid=method.ReturnType.ToString()=="void";
   body+=(isVoid?(method.ParameterList.Parameters.Any(p=>p.Modifiers.Any(SyntaxKind.OutKeyword))?"QueryPresentation<object>(":"InvokePresentation("):"var result = QueryPresentation<"+method.ReturnType+">(")+"\""+method.Identifier.Text+"\", args);";
   int i=0;
   foreach(var p in method.ParameterList.Parameters) { if(p.Modifiers.Any(SyntaxKind.OutKeyword)||p.Modifiers.Any(SyntaxKind.RefKeyword)) body+=p.Identifier.Text+" = ("+p.Type+")args["+i+"];"; i++; }
   if(!isVoid)body+="return result;";
   var sig=method.WithAttributeLists(default).WithModifiers(SyntaxFactory.TokenList(SyntaxFactory.Token(SyntaxKind.PublicKeyword))).WithBody(SyntaxFactory.ParseStatement("{"+body+"}") as BlockSyntax).WithExpressionBody(null).WithSemicolonToken(default);
   output.AppendLine(sig.NormalizeWhitespace().ToFullString());
  }
  if(m is PropertyDeclarationSyntax prop && names.Contains(prop.Identifier.Text) && !nativeAutomationMembers.Contains(prop.Identifier.Text) && prop.Modifiers.Any(SyntaxKind.PublicKeyword))
   output.AppendLine("public "+prop.Type+" "+prop.Identifier.Text+" {get; set;}");
 }
}
output.AppendLine("}}");
Write(Path.Combine(root,"X/Controller/Host/FrmMain.Contract.g.cs"),output.ToString());
var contractTree = CSharpSyntaxTree.ParseText(output.ToString()).GetRoot();
var declaration = contractTree.DescendantNodes().OfType<ClassDeclarationSyntax>().Single(c=>c.Identifier.Text=="FrmMain");
var contract = new System.Text.StringBuilder("// Generated from original FrmMain signatures by X/Controller/SourceGen.\n"+string.Join("\n",contractTree.ChildNodes().OfType<UsingDirectiveSyntax>().Select(u=>u.ToString()))+"\nnamespace PrePoMax { public interface IControllerHost : System.Windows.Forms.IWin32Window {\n");
foreach(var member in declaration.Members)
{
 if(member is MethodDeclarationSyntax method) contract.AppendLine(method.WithModifiers(default).WithBody(null).WithSemicolonToken(SyntaxFactory.Token(SyntaxKind.SemicolonToken)).NormalizeWhitespace().ToFullString());
 if(member is PropertyDeclarationSyntax prop)
 {
   var original = files.Where(f=>Path.GetFileName(f)=="FrmMain.cs").SelectMany(f=>CSharpSyntaxTree.ParseText(File.ReadAllText(f)).GetRoot().DescendantNodes().OfType<PropertyDeclarationSyntax>()).First(p=>p.Identifier.Text==prop.Identifier.Text);
   var accessors = original.AccessorList.Accessors.Where(a=>!a.Modifiers.Any(SyntaxKind.PrivateKeyword) && !a.Modifiers.Any(SyntaxKind.ProtectedKeyword)).Select(a=>SyntaxFactory.AccessorDeclaration(a.Kind()).WithSemicolonToken(SyntaxFactory.Token(SyntaxKind.SemicolonToken)));
   contract.AppendLine(prop.WithModifiers(default).WithAccessorList(SyntaxFactory.AccessorList(SyntaxFactory.List(accessors))).NormalizeWhitespace().ToFullString());
 }
}
contract.AppendLine("void Invalidate(); void InvokeIfRequired(Action action); T InvokeIfRequired<T>(Func<T> action);\n}}");
Write(Path.Combine(root,"PrePoMax/IControllerHost.cs"),contract.ToString());
void Write(string path,string value)
{
 value=value.Replace("\r\n","\n");
 if(args.Skip(1).Contains("--check"))
 {
  if(!File.Exists(path) || File.ReadAllText(path).Replace("\r\n","\n")!=value)throw new InvalidOperationException("Stale host contract: "+path);
 }
 else File.WriteAllText(path,value);
}
