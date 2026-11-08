namespace PrePoMax
{
    public static class RuntimeInitialization
    {
        public static void SetCultureAndLanguage()
        {
            System.Globalization.CultureInfo ci =
                (System.Globalization.CultureInfo)System.Globalization.CultureInfo.InvariantCulture.Clone();
            ci.NumberFormat.NumberGroupSeparator = "";
            //
            System.Threading.Thread.CurrentThread.CurrentCulture = ci;           // This thread
            System.Globalization.CultureInfo.DefaultThreadCurrentCulture = ci;   // All feature threads
            //
            System.Threading.Thread.CurrentThread.CurrentUICulture = ci;
            System.Globalization.CultureInfo.DefaultThreadCurrentUICulture = ci;

        }
    }
}
