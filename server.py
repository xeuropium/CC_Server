import socketserver
# https://docs.python.org/3/library/socketserver.html

# Override class socketserver.BaseRequestHandler : https://docs.python.org/3/library/socketserver.html#socketserver.BaseRequestHandler
class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """
    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def setup(self) :
        print(f'New client connection : {self.client_address}')


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
    pass

def read_white_list():
    with open('white_list.txt', 'r') as file:
        whitelist = {line.strip() for line in file if line.strip()}
    return whitelist


if __name__ == '__main__':
    HOST, PORT = 'localhost', 5000
    WHITE_LIST = read_white_list()
    
    try :
        with ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler) as server : 
            print(f'Server Hosting @ : {HOST}:{PORT}')
            server.serve_forever() # 'Handle one request at a time until shutdown. (CTL+C)' 
            
    except KeyboardInterrupt:
        print('Server terminated')