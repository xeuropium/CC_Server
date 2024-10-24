The goal of this project is to simulate a Command and Control Server with Clients.  
Along the way, I'll try to learn more about how to use sockets, threads, and protocols.    
In the end, it would be interesting to capture the traffic exchanged between the beacon (client) and the Remote using tools like Wireshark.

# Concepts used  :

## Client server Architecture
inc

## Threads and Threading 
inc

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