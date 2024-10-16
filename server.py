import socketserver
# Example used at https://docs.python.org/3/library/socketserver.html

import threading
# Threads is used to run multiple I/O-bound tasks simultaneously, here, requests
# https://docs.python.org/3/library/threading.html 
import re

# Global dic to track connected and their socket
# Needs to be refactored, Explore the Reactor Pattern in the future
connected_clients = {}


# Override class socketserver.BaseRequestHandler : https://docs.python.org/3/library/socketserver.html#socketserver.BaseRequestHandler
class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """
    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the client.
    """

    def setup(self) :
        print(f'New client connection : {self.client_address}')
        connected_clients[self.client_address] = self.request

        print(f'Threads alive : {threading.active_count()}')


    def handle(self):
        if (self.client_address[0] not in WHITE_LIST) :
            print('IP not in the WhiteList')
            return
        try :
            while True : # Keep the connection Open, delete the loop when only the server will send commands 
                self.data = self.request.recv(1024).strip() # buff size 1024
                print(f'{self.client_address} > ' + self.data.decode('utf-8'))

                # send back data
                self.request.sendall(b'Alive ping back received')
                
        except ConnectionAbortedError :
            print('Connection was aborted by the local system')
        except ConnectionResetError :
            pass # Connection was forcibly closed by the remote host
    

    def finish(self) :
        print(f'Connection closed for: {self.client_address}')
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

    except KeyboardInterrupt:
        print('Central commands terminated')


def list_commands_available():
    print('\nhelp : List all the commands available')
    print('list : To list clients connected to the server')
    print('send_echo [clientIP@port] ["message"]')
    print('get_SC [clientIP@port] : Get a ScreenShot of the client Desktop')
    print('shell [clientIP@port] [\'Shell Command\'] : Send a Shell/Powershell command to the client and get the result')


def print_clients():
    if len(connected_clients) == 0: 
        print('No clients connected')
    else :
        print('Clients : ')
        for client in connected_clients:
            print(f'{client[0]}@{client[1]}')
        

# Verify that the socket is not closed, share the method from client
def send_echo(msg: str):
    client_ip, client_port = msg.split(' ')[1].split("@")
    client_port = int(client_port)
    echo_msg = msg.split('\"')[1].replace('\"', "")
    # print(f'Client : {client_ip} @ {client_port} and msg : {echo_msg}')

    for client in connected_clients:
        if client[0] == client_ip and client[1] == client_port:
            client_socket = connected_clients.get(client)
            command = f"echo {echo_msg}"
            print(f'echo {echo_msg} sent')
            client_socket.sendall(command.encode('utf-8'))
        else :
            print(f'Client {client_ip}@{client_port} is not is the list of connected client')


def get_SC(client):
    pass

# Replacing the send_echo test
# Do some verification on the user input
# PRINT EXEMPLES
# shell 127.0.0.1@57693 powershell ls -n

# self.request.sendall(b'powershell start brave www.google.ca') 
# self.request.sendall(b'powershell ls -n')
def send_shell(msg: str):
    client_ip, client_port = msg.split(' ')[1].split("@")
    client_port = int(client_port)
    command = re.split('@\d+ ', msg)[1] # Do some join if there's more than 1 @

    for client in connected_clients:
        if client[0] == client_ip and client[1] == client_port:
            client_socket = connected_clients.get(client)
            print(f'Command : {command} sent')

            client_socket.sendall(command.encode('utf-8')) 
            # The Data back should be caught by the open loop Handler

        else :
            print(f'Client {client_ip}@{client_port} is not is the list of connected client')




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