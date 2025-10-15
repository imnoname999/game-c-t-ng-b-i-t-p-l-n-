using System;
using System.IO;
using System.Net.Sockets;
using System.Threading;

class Program
{
    static void Main()
    {
        Console.Write("Enter server IP (default 127.0.0.1): ");
        string ip = Console.ReadLine();
        if (string.IsNullOrEmpty(ip)) ip = "127.0.0.1";

        TcpClient client = new TcpClient(ip, 5000);
        Console.WriteLine("Connected to server!");

        NetworkStream stream = client.GetStream();
        StreamReader reader = new StreamReader(stream);
        StreamWriter writer = new StreamWriter(stream) { AutoFlush = true };

        // Thread để đọc dữ liệu từ server
        new Thread(() =>
        {
            while (true)
            {
                try
                {
                    string response = reader.ReadLine();
                    if (response == null) break;
                    Console.WriteLine("Server: " + response);
                }
                catch { break; }
            }
        }).Start();

        // Gửi dữ liệu tới server
        while (true)
        {
            string message = Console.ReadLine();
            if (message == "exit") break;
            writer.WriteLine(message);
        }

        client.Close();
        Console.WriteLine("Disconnected!");
    }
}
