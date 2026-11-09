using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
var root=Path.GetFullPath(args[0]);
if(args.Length>1 && args[1]=="--audit")
{
 var audit=Directory.GetFiles(Path.Combine(root,"PrePoMax/Forms"),"Frm*.cs",SearchOption.AllDirectories)
  .OrderBy(f=>f,StringComparer.Ordinal).Select(f=>new {file=Path.GetRelativePath(root,f).Replace(Path.DirectorySeparatorChar,'/'),
   classes=CSharpSyntaxTree.ParseText(File.ReadAllText(f)).GetRoot().DescendantNodes().OfType<ClassDeclarationSyntax>()
    .Where(c=>c.Identifier.Text.StartsWith("Frm",StringComparison.Ordinal)).Select(c=>new {name=c.Identifier.Text,
     controls=c.Members.OfType<FieldDeclarationSyntax>().SelectMany(d=>d.Declaration.Variables.Select(v=>new {name=v.Identifier.Text,type=d.Declaration.Type.ToString()})).ToArray(),
     methods=c.Members.OfType<MethodDeclarationSyntax>().Select(m=>new{name=m.Identifier.Text,calls=m.DescendantNodes().OfType<InvocationExpressionSyntax>().Select(i=>i.Expression.ToString()).Distinct().ToArray()}).ToArray(),
     events=c.DescendantNodes().OfType<AssignmentExpressionSyntax>().Where(n=>n.IsKind(SyntaxKind.AddAssignmentExpression) && n.Right.DescendantNodesAndSelf().OfType<IdentifierNameSyntax>().Any(i=>i.Identifier.Text.Contains("_")))
      .Select(n=>new {source=n.Left.ToString(),handler=n.Right.ToString()}).ToArray(),
     text=c.DescendantNodes().OfType<AssignmentExpressionSyntax>().Where(n=>n.Left.ToString().EndsWith(".Text",StringComparison.Ordinal) && n.Right is LiteralExpressionSyntax)
      .Select(n=>new {control=n.Left.ToString(),text=n.Right.ToString()}).ToArray()}).ToArray()});
 Console.Write(JsonSerializer.Serialize(audit));return;
}
var forms=Directory.GetFiles(Path.Combine(root,"PrePoMax/Forms"),"Frm*.cs",SearchOption.AllDirectories)
 .Where(f=>!f.EndsWith(".Designer.cs")).SelectMany(f=>CSharpSyntaxTree.ParseText(File.ReadAllText(f)).GetRoot().DescendantNodes().OfType<ClassDeclarationSyntax>()
 .Select(c=>new {file=Path.GetRelativePath(root,f).Replace(Path.DirectorySeparatorChar,'/'),name=c.Identifier.Text,fields=c.Members.OfType<FieldDeclarationSyntax>().Select(m=>m.ToString()).ToArray(),
 properties=c.Members.OfType<PropertyDeclarationSyntax>().Select(m=>new {name=m.Identifier.Text,code=m.ToString()}).ToArray(),
 methods=c.Members.OfType<MethodDeclarationSyntax>().Select(m=>new {name=m.Identifier.Text,code=m.ToString(),body=m.Body?.ToString(),tryBody=m.Body?.Statements.OfType<TryStatementSyntax>().FirstOrDefault()?.Block.ToString(),locals=(m.Body?.Statements.OfType<LocalDeclarationStatementSyntax>()??Enumerable.Empty<LocalDeclarationStatementSyntax>()).Where(d=>d.Declaration.Type.ToString()=="string[]").Select(d=>new {code=d.ToString(), names=d.Declaration.Variables.Select(v=>v.Identifier.Text).ToArray()}).ToArray(),
 variables=m.DescendantNodes().OfType<VariableDeclarationSyntax>().SelectMany(d=>d.Variables.Select(v=>new {type=d.Type.ToString(),name=v.Identifier.Text})).ToArray(),
 calls=m.DescendantNodes().OfType<InvocationExpressionSyntax>().Select(i=>new {expression=i.Expression.ToString(),arguments=i.ArgumentList.Arguments.Select(v=>v.ToString()).ToArray(),code=i.ToString()}).ToArray(),parameters=m.ParameterList.Parameters.Select(p=>new {name=p.Identifier.Text,type=p.Type.ToString()}).ToArray()}).ToArray()}));
Console.Write(JsonSerializer.Serialize(forms));
