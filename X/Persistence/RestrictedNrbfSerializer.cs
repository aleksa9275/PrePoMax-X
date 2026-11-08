using System.Collections;
using System.Formats.Nrbf;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using System.Runtime.Serialization;
using System.Text;
using CaeGlobals;

namespace PrePoMaxX.Persistence;

public sealed class RestrictedNrbfSerializer : IBinaryObjectSerializer
{
    readonly NrbfTypePolicy policy;
    public const long MaximumBytes=512L*1024*1024;
    const int MaximumRecords=2000000,MaximumArrayElements=32000000,MaximumDepth=256;
    static readonly StreamingContext context = new(StreamingContextStates.All);
    public RestrictedNrbfSerializer(NrbfTypePolicy policy) {this.policy=policy;}
    public void Serialize(Stream stream,object value) => new Writer(stream,policy).Write(value);
    public object Deserialize(Stream stream)
    {
        if(!stream.CanSeek || stream.Length-stream.Position>MaximumBytes)throw new SerializationException("NRBF byte limit exceeded or input is not seekable.");
        SerializationRecord root=NrbfDecoder.Decode(stream,out var records,leaveOpen:true);
        if(stream.Position!=stream.Length)throw new SerializationException("Trailing bytes after NRBF MessageEnd.");
        if(records.Count>MaximumRecords)throw new SerializationException("NRBF record limit exceeded.");
        return new Reader(policy,records.Values).Read(root);
    }
    static FieldInfo[] Fields(Type type) => FormatterServices.GetSerializableMembers(type,context).Cast<FieldInfo>().ToArray();
    static void Callbacks(object value,Type attribute)
    {
        for(Type t=value.GetType();t!=null && t!=typeof(object);t=t.BaseType)
            foreach(var method in t.GetMethods(BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.DeclaredOnly).Where(m=>m.IsDefined(attribute,false)))
                method.Invoke(value,new object[]{context});
    }
    sealed class Reader
    {
        readonly NrbfTypePolicy policy;
        readonly Dictionary<SerializationRecordId,object> objects=new();
        readonly Dictionary<SerializationRecordId,Type> types=new();
        readonly HashSet<SerializationRecordId> filling=new(),filled=new(),legacyUiMetadata=new();
        readonly SerializationRecord[] records;
        int depth;
        public Reader(NrbfTypePolicy policy,IEnumerable<SerializationRecord> records) {this.policy=policy;this.records=records.Where(r=>r is ClassRecord or ArrayRecord or PrimitiveTypeRecord).ToArray();}
        Type Resolve(SerializationRecord record)=>policy.Resolve(record.TypeName.AssemblyQualifiedName);
        public object Read(SerializationRecord root)
        {
            // Old Windows PMX files persisted a UI undo/redo event. Its delegate
            // metadata is inert: the live Controller always reattaches this event.
            // Only this known event slot may reference such metadata; no delegate
            // or method named by the input is ever resolved or activated.
            foreach(var owner in records.OfType<ClassRecord>().Where(c=>c.TypeName.FullName=="PrePoMax.Commands.CommandsCollection" && c.HasMember("EnableDisableUndoRedo")))
                MarkLegacyUiMetadata(owner.GetRawValue("EnableDisableUndoRedo"));
            // Validate every type and shape before allocating application instances.
            long total=0;
            foreach(var record in records)
            {
                if(legacyUiMetadata.Contains(record.Id))continue;
                string name=record.TypeName.FullName;
                if(name is "System.OrdinalComparer" or "System.OrdinalIgnoreCaseComparer" or "System.OrdinalCaseSensitiveComparer" or "System.UnitySerializationHolder")
                {
                    string identity=record.TypeName.AssemblyQualifiedName;
                    if(!identity.Contains(", mscorlib,") && !identity.Contains(", System.Private.CoreLib,"))throw new SerializationException("Unexpected assembly for framework metadata.");
                    continue;
                }
                Type type=Resolve(record); types[record.Id]=type;
                if(record is ArrayRecord array)
                {
                    long count=1;foreach(int n in array.Lengths)count=checked(count*n);
                    total=checked(total+count);if(total>MaximumArrayElements)throw new SerializationException("NRBF array allocation limit exceeded.");
                }
            }
            object result=Convert(root);
            foreach(var record in records)if(!legacyUiMetadata.Contains(record.Id))Convert(record);
            foreach(var pair in objects)if(pair.Value!=null && types.TryGetValue(pair.Key,out var type) && IsApplication(type))Callbacks(pair.Value,typeof(OnDeserializedAttribute));
            foreach(var value in objects.Values.OfType<IDeserializationCallback>())value.OnDeserialization(null);
            return result;
        }
        void MarkLegacyUiMetadata(object raw)
        {
            if(raw==null)return;
            if(raw is not ClassRecord root || root.TypeName.FullName!="System.DelegateSerializationHolder")throw new SerializationException("Invalid legacy undo/redo event metadata.");
            var pending=new Stack<ClassRecord>();pending.Push(root);
            while(pending.TryPop(out var record))
            {
                string name=record.TypeName.FullName;
                if(name is not ("System.DelegateSerializationHolder" or "System.DelegateSerializationHolder+DelegateEntry" or "System.Reflection.MemberInfoSerializationHolder"))continue;
                if(!record.TypeName.AssemblyQualifiedName.Contains(", mscorlib,"))throw new SerializationException("Unexpected assembly for legacy event metadata.");
                if(!legacyUiMetadata.Add(record.Id))continue;
                foreach(string field in record.MemberNames)if(record.GetRawValue(field) is ClassRecord child)pending.Push(child);
            }
        }
        static bool IsApplication(Type type) => type.Assembly!=typeof(object).Assembly && type.Assembly!=typeof(System.Drawing.Color).Assembly;
        object Convert(object raw)
        {
            if(raw is not SerializationRecord record)return raw;
            if(filled.Contains(record.Id))return objects[record.Id];
            if(filling.Contains(record.Id))return objects[record.Id];
            if(++depth>MaximumDepth)throw new SerializationException("NRBF graph depth limit exceeded.");
            try
            {
                if(record is PrimitiveTypeRecord primitive) {objects[record.Id]=primitive.Value;filled.Add(record.Id);return primitive.Value;}
                if(record is ClassRecord special)
                {
                    if(special.TypeName.FullName is "System.OrdinalComparer" or "System.OrdinalIgnoreCaseComparer" or "System.OrdinalCaseSensitiveComparer")
                    {
                        bool ignore=special.TypeName.FullName.Contains("IgnoreCase") || (special.HasMember("_ignoreCase") && special.GetBoolean("_ignoreCase"));
                        object comparer=ignore?StringComparer.OrdinalIgnoreCase:StringComparer.Ordinal;objects[record.Id]=comparer;filled.Add(record.Id);return comparer;
                    }
                    if(special.TypeName.FullName=="System.UnitySerializationHolder")
                    {
                        if(special.GetInt32("UnityType")!=4)throw new SerializationException("Only allowlisted Type metadata may use UnitySerializationHolder.");
                        object type=policy.ResolveMetadata(special.GetString("Data")+", "+special.GetString("AssemblyName"));objects[record.Id]=type;filled.Add(record.Id);return type;
                    }
                }
                Type runtimeType=types[record.Id];
                if(record is ArrayRecord array)
                {
                    int[] lengths=array.Lengths.ToArray();
                    Array target=Array.CreateInstance(runtimeType.GetElementType(),lengths);
                    objects[record.Id]=target;filling.Add(record.Id);
                    Array source=array.GetArray(runtimeType);
                    int[] index=new int[lengths.Length];
                    foreach(object item in source)
                    {
                        target.SetValue(Coerce(Convert(item),runtimeType.GetElementType()),index);
                        for(int d=index.Length-1;d>=0;d--) {if(++index[d]<lengths[d])break;index[d]=0;}
                    }
                    filling.Remove(record.Id);filled.Add(record.Id);return target;
                }
                if(record is not ClassRecord cls)throw new SerializationException("Unsupported NRBF record: "+record.RecordType);
                object instance=RuntimeHelpers.GetUninitializedObject(runtimeType);objects[record.Id]=instance;filling.Add(record.Id);
                if(IsApplication(runtimeType))Callbacks(instance,typeof(OnDeserializingAttribute));
                if(typeof(ISerializable).IsAssignableFrom(runtimeType))
                {
                    var info=new SerializationInfo(runtimeType,new FormatterConverter());
                    foreach(string name in cls.MemberNames)info.AddValue(name,Convert(cls.GetRawValue(name)));
                    ConstructorInfo ctor=runtimeType.GetConstructor(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance,null,new[]{typeof(SerializationInfo),typeof(StreamingContext)},null) ?? throw new SerializationException("Missing serialization constructor: "+runtimeType.FullName);
                    // Invoke the reviewed constructor on the allocated object so cyclic
                    // references and identities are retained rather than copied afterward.
                    var init=new DynamicMethod("InitializeAllowedData",null,new[]{typeof(object),typeof(SerializationInfo),typeof(StreamingContext)},typeof(RestrictedNrbfSerializer).Module,true);
                    var il=init.GetILGenerator();il.Emit(OpCodes.Ldarg_0);il.Emit(runtimeType.IsValueType?OpCodes.Unbox:OpCodes.Castclass,runtimeType);il.Emit(OpCodes.Ldarg_1);il.Emit(OpCodes.Ldarg_2);il.Emit(OpCodes.Call,ctor);il.Emit(OpCodes.Ret);
                    ((Action<object,SerializationInfo,StreamingContext>)init.CreateDelegate(typeof(Action<object,SerializationInfo,StreamingContext>)))(instance,info,context);
                }
                else
                {
                    var fields=Fields(runtimeType).ToDictionary(f=>f.Name,StringComparer.Ordinal);
                    foreach(string name in cls.MemberNames)
                    {
                        if(runtimeType.FullName=="PrePoMax.Commands.CommandsCollection" && name=="EnableDisableUndoRedo")continue;
                        if(cls.GetRawValue(name) is SerializationRecord target && legacyUiMetadata.Contains(target.Id))throw new SerializationException("Legacy UI event metadata is referenced outside its event slot.");
                        if(!fields.TryGetValue(name,out var field))throw new SerializationException("Unknown member "+runtimeType.FullName+"."+name);
                        field.SetValue(instance,Coerce(Convert(cls.GetRawValue(name)),field.FieldType));
                    }
                    foreach(var field in fields.Values)
                        if(!cls.HasMember(field.Name) && !field.IsDefined(typeof(OptionalFieldAttribute),false))throw new SerializationException("Missing required member "+runtimeType.FullName+"."+field.Name);
                }
                filling.Remove(record.Id);filled.Add(record.Id);return instance;
            }
            finally {depth--;}
        }
        static object Coerce(object value,Type type)
        {
            if(value==null || type.IsInstanceOfType(value))return value;
            if(type.IsEnum)return Enum.ToObject(type,value);
            throw new SerializationException("Member type mismatch for "+type.FullName);
        }
    }
    sealed class Writer
    {
        readonly BinaryWriter writer;
        readonly NrbfTypePolicy policy;
        readonly Dictionary<object,int> ids=new(ReferenceEqualityComparer.Instance);
        readonly Queue<object> queue=new();
        readonly Dictionary<string,int> libraries=new(StringComparer.Ordinal);
        int nextId=1, nextValueId=-1;
        long start;
        public Writer(Stream stream,NrbfTypePolicy policy) {writer=new BinaryWriter(stream,new UTF8Encoding(false,true),leaveOpen:true);this.policy=policy;start=stream.Position;}
        public void Write(object value)
        {
            if(value==null)throw new SerializationException("NRBF root cannot be null.");
            int root=Id(value);writer.Write((byte)0);writer.Write(root);writer.Write(-1);writer.Write(1);writer.Write(0);
            while(queue.TryDequeue(out object item))
            {
                if(writer.BaseStream.Position-start>MaximumBytes || ids.Count>MaximumRecords)throw new SerializationException("NRBF output limit exceeded.");
                Object(item,ids[item]);
            }
            writer.Write((byte)11);writer.Flush();
        }
        int Id(object value) {if(ids.TryGetValue(value,out int id))return id;id=nextId++;ids.Add(value,id);queue.Enqueue(value);return id;}
        int Library(Type type)
        {
            string identity=NrbfTypePolicy.AssemblyIdentity(type);
            if(libraries.TryGetValue(identity,out int id))return id;
            id=nextId++;libraries.Add(identity,id);writer.Write((byte)12);writer.Write(id);writer.Write(identity);return id;
        }
        void Value(object value,Type type)
        {
            if(Primitive(type)!=0) {PrimitiveValue(value,type);return;}
            if(value==null) {writer.Write((byte)10);return;}
            Type actual=value.GetType();
            if(Primitive(actual)!=0) {writer.Write((byte)8);writer.Write(Primitive(actual));PrimitiveValue(value,actual);return;}
            // NRBF value-type members are inline records. Keeping them as queued
            // references loses the legacy ObjectManager's nested value fixups.
            if(type.IsValueType && actual.IsValueType) {Object(value,nextValueId--);return;}
            writer.Write((byte)9);writer.Write(Id(value));
        }
        void Object(object value,int id)
        {
            Type type=value.GetType();
            if(value is string text) {writer.Write((byte)6);writer.Write(id);writer.Write(text);return;}
            if(value is Type represented)
            {
                policy.RequireMetadata(represented);
                Class(id,"System.UnitySerializationHolder",null,new[]{("Data",typeof(string),(object)NrbfTypePolicy.TypeName(represented)),("UnityType",typeof(int),(object)4),("AssemblyName",typeof(string),(object)NrbfTypePolicy.AssemblyIdentity(represented))});return;
            }
            if(ReferenceEquals(value,EqualityComparer<string>.Default))
            {
                Type compatible=typeof(object).Assembly.GetType("System.Collections.Generic.GenericEqualityComparer`1",true).MakeGenericType(typeof(string));
                Class(id,NrbfTypePolicy.TypeName(compatible),null,System.Array.Empty<(string,Type,object)>());return;
            }
            if(value is StringComparer comparer)
            {
                if(comparer!=StringComparer.Ordinal && comparer!=StringComparer.OrdinalIgnoreCase)throw new SerializationException("Only ordinal string comparers are supported.");
                Class(id,"System.OrdinalComparer",null,new[]{("_ignoreCase",typeof(bool),(object)(comparer==StringComparer.OrdinalIgnoreCase))});return;
            }
            policy.Require(type);
            if(value is Array array) {Array(array,id,type);return;}
            Callbacks(value,typeof(OnSerializingAttribute));
            var fields=new List<(string Name,Type Type,object Value)>();
            if(value is ISerializable serializable)
            {
                var info=new SerializationInfo(type,new FormatterConverter());serializable.GetObjectData(info,context);
                if(info.ObjectType!=type)throw new SerializationException("Serialization type replacement is not allowed: "+type.FullName);
                foreach(SerializationEntry entry in info)fields.Add((entry.Name,entry.ObjectType,entry.Value));
            }
            else foreach(var field in Fields(type))fields.Add((field.Name,field.FieldType,field.GetValue(value)));
            Class(id,NrbfTypePolicy.TypeName(type),type,fields.ToArray());
            Callbacks(value,typeof(OnSerializedAttribute));
        }
        void Class(int id,string name,Type type,(string Name,Type Type,object Value)[] fields)
        {
            bool system=type==null || NrbfTypePolicy.IsSystemClass(type);
            int library=system?0:Library(type);
            foreach(var field in fields)if(BinaryType(field.Type)==4)Library(field.Type);
            writer.Write((byte)(system?4:5));writer.Write(id);writer.Write(name);writer.Write(fields.Length);
            foreach(var field in fields)writer.Write(field.Name);
            foreach(var field in fields)writer.Write(BinaryType(field.Type));
            foreach(var field in fields)TypeInformation(field.Type);
            if(!system)writer.Write(library);
            foreach(var field in fields)Value(field.Value,field.Type);
        }
        byte BinaryType(Type type)
        {
            if(Primitive(type)!=0)return 0;
            if(type==typeof(string))return 1;
            if(type==typeof(object))return 2;
            if(type==typeof(object[]))return 5;
            if(type==typeof(string[]))return 6;
            if(type.IsSZArray && Primitive(type.GetElementType())!=0)return 7;
            return (byte)(NrbfTypePolicy.IsSystemClass(type)?3:4);
        }
        void TypeInformation(Type type)
        {
            switch(BinaryType(type))
            {
                case 0:writer.Write(Primitive(type));break;
                case 3:writer.Write(NrbfTypePolicy.TypeName(type));break;
                case 4:writer.Write(NrbfTypePolicy.TypeName(type));writer.Write(libraries[NrbfTypePolicy.AssemblyIdentity(type)]);break;
                case 7:writer.Write(Primitive(type.GetElementType()));break;
            }
        }
        void Array(Array array,int id,Type type)
        {
            if(array.LongLength>MaximumArrayElements)throw new SerializationException("NRBF array length limit exceeded.");
            if(Enumerable.Range(0,array.Rank).Any(d=>array.GetLowerBound(d)!=0))throw new SerializationException("Nonzero array lower bounds are not supported.");
            Type element=type.GetElementType();byte primitive=Primitive(element);
            if(array.Rank==1 && primitive!=0)
            {
                writer.Write((byte)15);writer.Write(id);writer.Write(array.Length);writer.Write(primitive);
                foreach(object item in array)PrimitiveValue(item,element);return;
            }
            bool system=NrbfTypePolicy.IsSystemClass(element);
            int library=primitive!=0 || element==typeof(object) || element==typeof(string) || system?0:Library(element);
            writer.Write((byte)7);writer.Write(id);writer.Write((byte)(array.Rank>1?2:element.IsArray?1:0));writer.Write(array.Rank);
            for(int d=0;d<array.Rank;d++)writer.Write(array.GetLength(d));
            if(primitive!=0) {writer.Write((byte)0);writer.Write(primitive);}
            else if(element==typeof(string))writer.Write((byte)1);
            else if(element==typeof(object))writer.Write((byte)2);
            else {writer.Write((byte)(system?3:4));writer.Write(NrbfTypePolicy.TypeName(element));if(!system)writer.Write(library);}
            foreach(object item in array)Value(item,element);
        }
        static byte Primitive(Type type)=>Type.GetTypeCode(type) switch
        {
            TypeCode.Boolean when !type.IsEnum=>1,TypeCode.Byte when !type.IsEnum=>2,TypeCode.Char=>3,TypeCode.Decimal=>5,TypeCode.Double=>6,TypeCode.Int16 when !type.IsEnum=>7,TypeCode.Int32 when !type.IsEnum=>8,TypeCode.Int64 when !type.IsEnum=>9,TypeCode.SByte when !type.IsEnum=>10,TypeCode.Single=>11,TypeCode.DateTime=>13,TypeCode.UInt16 when !type.IsEnum=>14,TypeCode.UInt32 when !type.IsEnum=>15,TypeCode.UInt64 when !type.IsEnum=>16,_=>type==typeof(TimeSpan)?(byte)12:(byte)0
        };
        void PrimitiveValue(object value,Type type)
        {
            switch(Primitive(type))
            {
                case 1:writer.Write((bool)value);break;case 2:writer.Write((byte)value);break;case 3:writer.Write((char)value);break;
                case 5:writer.Write(((decimal)value).ToString(System.Globalization.CultureInfo.InvariantCulture));break;
                case 6:writer.Write((double)value);break;case 7:writer.Write((short)value);break;case 8:writer.Write((int)value);break;case 9:writer.Write((long)value);break;case 10:writer.Write((sbyte)value);break;case 11:writer.Write((float)value);break;case 12:writer.Write(((TimeSpan)value).Ticks);break;case 13:writer.Write(((DateTime)value).ToBinary());break;case 14:writer.Write((ushort)value);break;case 15:writer.Write((uint)value);break;case 16:writer.Write((ulong)value);break;
                default:throw new SerializationException("Unsupported primitive: "+type.FullName);
            }
        }
    }
}
