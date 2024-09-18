import socketserver
# https://docs.python.org/3/library/socketserver.html


class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def handle(self):
        
            self.data = self.request.recv(1024).strip()
            print(f'Received from {self.client_address[0]}')
            print(self.data)

            # send back data
            self.request.sendall('status : received') 

if __name__ == '__main__':
    HOST, PORT = 'localhost', 5000
    
    try :
        with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server : 
            print(f'Server Hosting @ : {HOST}:{PORT}')
            server.serve_forever() # 'Handle one request at a time until shutdown. (CTL+C)' 
            # server.get_request()
            
    except KeyboardInterrupt:
        print('Server terminated')