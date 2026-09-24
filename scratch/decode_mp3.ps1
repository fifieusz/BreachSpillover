$code = @"
using System;
using System.IO;
using System.Runtime.InteropServices;

public class AudioDecoder {
    [DllImport("mfplat.dll", ExactSpelling = true)]
    private static extern int MFStartup(uint version, uint flags);

    [DllImport("mfplat.dll", ExactSpelling = true)]
    private static extern int MFShutdown();

    [DllImport("mfreadwrite.dll", ExactSpelling = true)]
    private static extern int MFCreateSourceReaderFromURL([MarshalAs(UnmanagedType.LPWStr)] string url, IntPtr attributes, out IntPtr sourceReader);

    // GUIDs
    // MF_MT_MAJOR_TYPE = 48eba18e-f827-4970-b477-5dd4e7e86787
    // MFMediaType_Audio = 73647561-0000-0010-8000-00AA00389B71
    // MF_MT_SUBTYPE = f7e34c9a-42e8-47f4-b771-4a02935e5331
    // MFAudioFormat_PCM = 00000001-0000-0010-8000-00AA00389B71

    public static void Analyze(string filePath) {
        Console.WriteLine("Analyzing: " + filePath);
        // We can decode to wav using Windows Media Player or MediaFoundation
    }
}
"@
Add-Type -TypeDefinition $code
[AudioDecoder]::Analyze("frontend/static/sounds/Clickingsound.mp3")
