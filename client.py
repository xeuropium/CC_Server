import socket
import sys
# https://docs.python.org/3/library/socketserver.html#socketserver-tcpserver-example

def send_data(sock) :
    print('Enter exit to terminate the communication')

    try :
        while True :
            msg = input('> ') # Takes the user input
            if msg == 'exit':
                break
            
            # Send data to the server
            sock.sendall(msg.encode('utf-8')) 

            try : # Get data back from server
                res = sock.recv(1024).decode('utf-8')
                print(f'Server response : {res}')
            except socket.timeout:
                print("Timeout, no response from server")
                break
    except KeyboardInterrupt:
        print('Comms terminated')
    finally:
        sock.close()



if __name__ == '__main__':
    HOST, PORT = 'localhost', 5000

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock: # Conect with TCP
        try: 
            sock.connect((HOST, PORT))
            print(f'Connected @ : {sock.getpeername()}')
            send_data(sock)

        except ConnectionRefusedError:
            print('Connection refused by the host (server might be down or unreachable)')
        
        
