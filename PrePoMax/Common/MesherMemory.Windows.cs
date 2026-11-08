namespace PrePoMax
{
    internal static class MesherMemory
    {
        public static float AvailableMegabytes
        {
            get
            {
                using (var counter = new System.Diagnostics.PerformanceCounter("Memory", "Available MBytes"))
                    return counter.NextValue();
            }
        }
    }
}
