import socket
import subprocess
import select
# https://docs.python.org/3/library/socketserver.html#socketserver-tcpserver-example


def is_socket_closed(sock: socket.socket) -> bool:
    readable, _, _ = select.select([sock], [], [], 0)
    return readable


def send_data(sock: socket.socket):
    if is_socket_closed(sock):
        print('Connection aborted (not in the whitelist)')
        return
    
    try:
        while True:
            print('Enter exit to terminate the communication')
            msg = input('> ') # Takes the user input
            if msg == 'exit':
                break
            
            # Send data to the server
            sock.sendall(msg.encode('utf-8')) 

            # Get data back from server
            get_data(sock)

    except KeyboardInterrupt:
        print('Comms terminated')
    except ConnectionResetError:
        print('The server closed the connection')
    finally:
        sock.close()


def get_data(sock: socket.socket):
    try: 
        res = sock.recv(1024).decode('utf-8')
        print(f'Server response : {res}')
        if 'ls' in res:
            command = res.split(' ')
            exec_command(command)
        else:
            print(res)
    except socket.timeout:
        print("Timeout, no response from server")
    except ConnectionAbortedError :
        print('Connection aborted from server')


# example : command = ['powershell', 'start', 'brave', 'www.google.ca']
def exec_command(command):
    # Shell=True : features such as shell pipes, filename wildcards, environment variable expansion
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)


if __name__ == '__main__':
    HOST, PORT = 'localhost', 5000

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock: # Conect with TCP
        try: 
            sock.connect((HOST, PORT))
            print(f'Connected @ : {sock.getpeername()}')
            send_data(sock)

        except ConnectionRefusedError:
            print('Connection refused by the host (server might be down or unreachable)')
        
        
