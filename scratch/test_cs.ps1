$code = @"
using System;
using System.IO;
using System.Runtime.InteropServices;

public class AudioChecker {
    public static void Check() {
        Console.WriteLine("C# compiler works in powershell");
    }
}
"@
Add-Type -TypeDefinition $code
[AudioChecker]::Check()
