"""Mechanical ownership check for original point transformation algorithms."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
PIN='82e955da9afc6f5442212f9b581caf58e3a7340a'
PATH='CaeMesh/FeMesh.cs'
def render():
    text=subprocess.check_output(['git','show',PIN+':'+PATH],cwd=ROOT).decode('utf-8-sig')
    bodies=[]
    for start,end in [('        public static void TranslatePoint(', '        //\n        public string[] RotateParts('),('        public static void RotatePoint(', '        //\n        public string[] MirrorParts('),('        public static void ScalePoint(', '        // Tools')]:
        a=text.index(start);b=text.index(end,a);bodies.append(text[a:b]);text=text[:a]+text[b:]
    text=text.replace('public class FeMesh : ISerializable','public partial class FeMesh : ISerializable',1)
    shared='// Original PrePoMax point transformations; see root LICENSE and Matej Borovinšek attribution.\nusing System;\nusing System.Linq;\nusing CaeGlobals;\nnamespace CaeMesh\n{\n    public partial class FeMesh\n    {\n'+''.join(bodies)+'    }\n}\n'
    return {PATH:text,'CaeMesh/FeMesh.Transformations.cs':shared}
def verify():
    for name,text in render().items():
        if (ROOT/name).read_text(encoding='utf-8-sig')!=text:raise ValueError('Original point transformation extraction changed: '+name)
if __name__=='__main__':verify()
