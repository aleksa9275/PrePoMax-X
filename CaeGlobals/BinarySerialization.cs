using System;
using System.IO;
using System.Runtime.Serialization.Formatters.Binary;

namespace CaeGlobals
{
    public interface IBinaryObjectSerializer
    {
        void Serialize(Stream stream, object value);
        object Deserialize(Stream stream);
    }

    // The original Windows build retains its formatter. Portable hosts must
    // install the restricted NRBF implementation before persistence or cloning.
    public static class BinarySerialization
    {
        public static Func<IBinaryObjectSerializer> Factory { get; set; }
        public static IBinaryObjectSerializer Create()
        {
            if (Factory != null) return Factory();
            if (Environment.Version.Major >= 5)
                throw new NotSupportedException("A restricted binary serializer must be installed by the host.");
            return new LegacySerializer();
        }
        private sealed class LegacySerializer : IBinaryObjectSerializer
        {
            public void Serialize(Stream stream, object value)
            {
                new BinaryFormatter().Serialize(stream, value);
            }
            public object Deserialize(Stream stream)
            {
                return new BinaryFormatter { Binder = RenamedTypeSerializationBinder.Instance }.Deserialize(stream);
            }
        }
    }
}
