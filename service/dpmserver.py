#      dpmserver.py
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


import socket
import threading
from SocketServer import BaseRequestHandler, TCPServer, ThreadingMixIn

class ThreadedTCPRequestHandler(BaseRequestHandler):
    def handle(self):
        self.data =  self.request.recv(1024)
        cur_thread = threading.current_thread()
        res = self.server.rpcserver.proc(self.data)
        self.request.sendall(res)

class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    def set_server(self, rpcserver):
        self.rpcserver = rpcserver

class DPMServer(object):
        
    def run(self, rpcserver):
        self.server = ThreadedTCPServer((rpcserver.addr, rpcserver.port), ThreadedTCPRequestHandler)
        self.server.set_server(rpcserver) 
        self.server.serve_forever()
        
    