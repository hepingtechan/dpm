#      frontend.py
#      
#      Copyright (C) 2015 Xiao-Fang Huang <huangxfbnu@163.com>
#      
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#      
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#      
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#      MA 02110-1301, USA.

import struct
import socket
from random import randint
from lib.stream import Stream
from lib.stream import UID_LEN, HEAD_LEN
from lib.util import localhost, show_info, show_error
from SocketServer import BaseRequestHandler, TCPServer, ThreadingMixIn
from conf.config import FRONTEND_PORT, BACKEND_PORT, BACKEND_SERVERS, PKG_MAX

PRINT = False
BODY_MAX = 64

class FrontendHandler(BaseRequestHandler):
    def _get_backend(self, uid):
        n = randint(0, len(BACKEND_SERVERS) - 1)
        return BACKEND_SERVERS[n]
    
    def _print(self, text):
        if PRINT:
            show_info(self, text)
    
    def _forward(self, uid, src, dest):
        self._print('start to forward, uid=%s' % str(uid))
        dest.sendall(uid)
        buf = src.recv(HEAD_LEN - UID_LEN)
        if len(buf) != HEAD_LEN - UID_LEN:
            show_error(self, 'failed to forward, invalid head, len=%d' % len(buf))
            return
        dest.sendall(buf)
        total, = struct.unpack('I', buf[-4:])
        if not total or total >=  PKG_MAX / BODY_MAX:
            show_error(self, 'failed to forward, invalid head, total=%d' % total)
            return
        cnt = 0
        while cnt < total:
            head = src.recv(2)
            if len(head) != 2:
                show_error(self, 'failed to forward, invalid packet')
                return
            dest.sendall(head)
            length, = struct.unpack('H', head)
            if length > BODY_MAX:
                show_error(self, 'failed to forward, invalid length')
                return
            body = ''
            while len(body) < length:
                buf = src.recv(length - len(body))
                if not buf:
                    show_error(self, 'failed to forward')
                    return
                body += buf
            if len(body) != length:
                show_error(self, 'failed to forward')
                return
            dest.sendall(body)
            cnt += 1
        dest.recv(1)
        src.sendall('0')
    
    def handle(self):
        uid = self.request.recv(UID_LEN)
        if len(uid) != UID_LEN:
            show_error(self, 'failed to handle, invalid head')
            return
        addr = self._get_backend(uid)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((addr, BACKEND_PORT))
        try:
            self._forward(uid, self.request, sock)
            stream = Stream(sock)
            _, _, res = stream.readall()
            stream = Stream(self.request)
            stream.write(res)
        finally:
            sock.close()

class FrontendServer(ThreadingMixIn, TCPServer):
    pass

class Frontend(object):
    def run(self, addr, port):
        self._server = FrontendServer((addr, port), FrontendHandler)
        self._server.serve_forever()

def main():
    frontend = Frontend()
    frontend.run(localhost(), FRONTEND_PORT)
