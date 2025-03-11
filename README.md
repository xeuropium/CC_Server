The goal of this project is to simulate a Command and Control Server with Clients.  
Along the way, I'll try to learn more about how to use sockets, threads, and protocols.    
In the end, it would be interesting to capture the traffic exchanged between the beacon (client) and the Remote using tools like Wireshark.

# Concepts used  :

## Client server Architecture
The server is hosted in the cloud. It waits for incoming client connections. Once a connection is made, it can send commands.

The client (or beacon) sends an initial message to the server. If it receives the correct response, it maintains a TCP connection. At that point, it simply waits for commands, executes them, and sends the response.

## Threads and Threading 
### Server 
1. Handling Multiple Client Connections

The `handle(self)` method in the server class is called every time a new client connects. However, because `ThreadingMixIn` is used, each call to `handle(self)` is executed in a new thread.

2. Threading of the `ThreadedTCPServer`

The `socketserver` runs in a separate thread.  
The main Python thread is used for listening to operator commands.  

# Stream-based Protocol (TCP) vs Datagram-based Protocol (UDP)
## TCP :
Tcp is connection-oriented and reliable stream-based protocol.  
It uses a <ins>three-way handshake</ins> for establishing and maintaining a connection.  
Uses <ins>error checking</ins> for a reliable data transmission.  
Data is send as a **Stream of bytes**, no concept of message boundaries.
-> I'll implement my own using this : https://stackoverflow.com/a/3420392 

## UDP :
No need to establish a connection before sending data.  
A Datagram is an independent, self-contained packet with <ins>no concept of session</ins>  
While UDP enforces **explicit message boundaries** there is no guarantee that Datagrams will be delivered in the correct order. 

### Buffer size consideration
From what I've read, it is preferable not to send data larger than 8192 bytes.
The best way to send an image is to split it into multiple smaller packets and then reconstruct the final image.

The header indicating the length is 4 byte (32 bits) = a max 2^32−1=4,294,967,295 Integer  
A packet sending 1024 bytes can send a max 1024 char with utf-8. 

## Wireshark investigation
[Wireshark doc](./doc/wireshark.md)