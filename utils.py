import socket
import select

# See the select section : https://docs.python.org/3/howto/sockets.html#socket-howto 
def is_socket_closed(sock: socket.socket) -> bool:
    try:
        # Check if the socket is still open by looking at the file descriptor
        if sock.fileno() == -1:
            return True
        readable, _, _ = select.select([sock], [], [], 0)
        return readable
    except (ValueError, OSError):
            return True
