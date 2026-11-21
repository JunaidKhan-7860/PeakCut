using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Threading;

namespace PeakCutLauncher
{
    class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            string peakcutDir = @"C:\peakcut";
            string ollamaPath = @"C:\Users\jarhj\AppData\Local\Programs\Ollama\ollama.exe";
            string pythonPath = @"C:\peakcut\.venv\Scripts\python.exe";

            // 1. Ensure Ollama is running
            bool ollamaRunning = false;
            try
            {
                using (var client = new HttpClient { Timeout = TimeSpan.FromSeconds(1) })
                {
                    var res = client.GetAsync("http://127.0.0.1:11434/api/tags").Result;
                    if (res.IsSuccessStatusCode) ollamaRunning = true;
                }
            }
            catch {}

            if (!ollamaRunning && File.Exists(ollamaPath))
            {
                var psi = new ProcessStartInfo(ollamaPath, "serve")
                {
                    CreateNoWindow = true,
                    UseShellExecute = false,
                    WindowStyle = ProcessWindowStyle.Hidden
                };
                Process.Start(psi);
            }

            // 2. Ensure PeakCut Studio Server is running
            bool peakcutRunning = false;
            try
            {
                using (var client = new HttpClient { Timeout = TimeSpan.FromSeconds(1) })
                {
                    var res = client.GetAsync("http://127.0.0.1:8765/healthz").Result;
                    if (res.IsSuccessStatusCode) peakcutRunning = true;
                }
            }
            catch {}

            if (!peakcutRunning && File.Exists(pythonPath))
            {
                var psi = new ProcessStartInfo(pythonPath, "-m studio.server")
                {
                    WorkingDirectory = peakcutDir,
                    CreateNoWindow = true,
                    UseShellExecute = false,
                    WindowStyle = ProcessWindowStyle.Hidden
                };
                Process.Start(psi);
            }

            // 3. Wait for PeakCut to respond
            for (int i = 0; i < 30; i++)
            {
                Thread.Sleep(500);
                try
                {
                    using (var client = new HttpClient { Timeout = TimeSpan.FromSeconds(1) })
                    {
                        var res = client.GetAsync("http://127.0.0.1:8765/healthz").Result;
                        if (res.IsSuccessStatusCode) break;
                    }
                }
                catch {}
            }

            // 4. Open default web browser to PeakCut Studio
            try
            {
                Process.Start(new ProcessStartInfo("http://127.0.0.1:8765/app") { UseShellExecute = true });
            }
            catch {}
        }
    }
}
