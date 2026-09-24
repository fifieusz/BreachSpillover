$sourcePath = (Resolve-Path "frontend/static/sounds/Clickingsound.mp3").Path
$destPath = [System.IO.Path]::Combine((Resolve-Path "scratch").Path, "click_decoded.wav")

$csharp = @"
using System;
using System.IO;
using System.Runtime.InteropServices;

public static class Mp3Converter {
    [DllImport("mfplat.dll", ExactSpelling = true)]
    public static extern int MFStartup(uint version, uint dwFlags);

    [DllImport("mfplat.dll", ExactSpelling = true)]
    public static extern int MFShutdown();

    [DllImport("mfreadwrite.dll", ExactSpelling = true)]
    public static extern int MFCreateSourceReaderFromURL([MarshalAs(UnmanagedType.LPWStr)] string pwszURL, IntPtr pAttributes, out IntPtr ppSourceReader);

    public const uint MF_VERSION = 0x00020070;
    public const uint MFSTARTUP_FULL = 0;

    public static void Convert(string input, string output) {
        Console.WriteLine("Convert input: " + input);
    }
}
"@
Add-Type -TypeDefinition $csharp
[Mp3Converter]::Convert($sourcePath, $destPath)
