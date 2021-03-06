#!/usr/bin/env python3

import socket
import struct
import utilities as util
import json
import os
import os.path as op
from threading import Thread

def sendFile(fname, conn, mypath, udpAddr = None):
    fpath = op.join(mypath, fname)
    if op.exists(fpath):
        size = op.getsize(fpath)
    else:
        size = -1
    size = struct.pack('i', size)
    if udpAddr:
        conn.sendto(size, udpAddr)
    else:
        conn.send(size)
    if not op.exists(fpath):
        return
    perm = os.stat(fpath).st_mode
    perm = struct.pack('I', perm)
    if udpAddr:
        conn.sendto(perm, udpAddr)
    else:
        conn.send(perm)
    f = open(fpath, 'rb')
    l = f.read(1024)
    while (l):
        if udpAddr:
            conn.sendto(l, udpAddr)
        else:
            conn.send(l)
        l = f.read(1024)
    f.close()


def sendIndex(flag, args, conn, mypath):
    table = util.listFiles(flag, args, mypath)
    tosend = json.dumps(table)
    conn.send(tosend.encode())


def sendHash(flag, args, conn, mypath):
    table = util.listHash(flag, args, mypath)
    tosend = json.dumps(table)
    conn.send(tosend.encode())


def recvCommand(conn, mypath, sudp = None):
    data = conn.recv(struct.calcsize('II'))
    cmd, argSize = struct.unpack('II', data)
    # print(cmd, argSize)
    if cmd == 4:
        return 'exit'
    if cmd == 1:   # index
        arg = conn.recv(argSize).decode().split(' ')
        flag = arg[0]
        args = arg[1:]
        # print(cmd, flag, args)
        sendIndex(flag, args, conn, mypath)
    elif cmd == 2: # hash
        arg = conn.recv(argSize).decode().split(' ', 1)
        flag = arg[0]
        try:
            args = arg[1]
        except:
            args = None
        # print(cmd, flag, args)
        sendHash(flag, args, conn, mypath)
    elif cmd == 3: # download
        arg = conn.recv(argSize).decode().split(' ', 1)
        flag = arg[0]
        fname = arg[1]
        # print(cmd, arg.decode())
        if flag == 'UDP':
            data, addr = sudp.recvfrom(1024)
            sendFile(fname, sudp, mypath, addr)
        else:
            sendFile(fname, conn, mypath)

class Server(Thread):
    def __init__(self, mypath = './files_server/', port = 60000):
        # , mypath = './files_server', port = 60000
        Thread.__init__(self)
        self.mypath = mypath
        host = os.environ.get('host') or ""
        self.s = socket.socket()
        self.s.bind((host, port))
        self.s.listen(5)
        self.sudp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sudp.bind((host, port))

    def run(self):
        while True:
            conn, addr = self.s.accept()
            # print('Got connection from', addr)
            if recvCommand(conn, self.mypath, self.sudp) == 'exit':
                break
            # print('Done sending')
            conn.close()
        self.s.close()
        self.sudp.close()
