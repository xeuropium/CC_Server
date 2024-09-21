import socketserver
# https://docs.python.org/3/library/socketserver.html

# Override class socketserver.BaseRequestHandler : https://docs.python.org/3/library/socketserver.html#socketserver.BaseRequestHandler
class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def setup(self) :
        print(f'New client connected : {self.client_address}')

    def handle(self):
        try :
            while True : # Keep the connection Open
                self.data = self.request.recv(1024).strip() # buff size 1024
                # print(f'Received from {self.client_address[0]}')
                print(self.data.decode('utf-8'))

                # send back data
                # self.request.sendall(b'powershell start brave www.google.ca') 
                self.request.sendall(b'powershell echo shellMsg')
        except ConnectionAbortedError :
            print('Client disconnected')
    
    def finish(self) :
        pass

def white_listing():
    pass


if __name__ == '__main__':
    HOST, PORT = 'localhost', 5000
    
    try :
        with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server : 
            print(f'Server Hosting @ : {HOST}:{PORT}')
            server.serve_forever() # 'Handle one request at a time until shutdown. (CTL+C)' 
            
    except KeyboardInterrupt:
        print('Server terminated')