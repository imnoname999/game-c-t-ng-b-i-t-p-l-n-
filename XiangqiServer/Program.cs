using System;
using System.Net;
using System.Net.Sockets;
using System.IO;
using System.Threading;

class Program
{
    static void Main()
    {
        TcpListener server = new TcpListener(IPAddress.Any, 5000);
        server.Start();
        Console.WriteLine("Server started on port 5000...");

        while (true)
        {
            TcpClient client = server.AcceptTcpClient();
            Console.WriteLine("Client connected!");
            Thread t = new Thread(HandleClient);
            t.Start(client);
        }
    }

    static void HandleClient(object obj)
    {
        TcpClient client = (TcpClient)obj;
        using (StreamReader reader = new StreamReader(client.GetStream()))
        using (StreamWriter writer = new StreamWriter(client.GetStream()) { AutoFlush = true })
        {
            writer.WriteLine("Welcome to the Xiangqi Server!");
            while (true)
            {
                try
                {
                    string msg = reader.ReadLine();
                    if (msg == null) break;
                    Console.WriteLine($"Client: {msg}");
                    writer.WriteLine("Server received: " + msg);
                }
                catch { break; }
            }
        }
        client.Close();
        Console.WriteLine("Client disconnected!");
    }
}
