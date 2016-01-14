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

import rsa
import struct
import socket
import threading
from lib.stream import Stream
from conf.config import SHOW_TIME
from lib.util import show_class, show_error
from lib.stream import UID_LEN, FLG_LEN, FLG_SEC
from SocketServer import BaseRequestHandler, TCPServer, ThreadingMixIn

if SHOW_TIME:
    from datetime import datetime

PRINT = False
CACHE_MAX = 4096

class DPMRequestHandler(BaseRequestHandler):
    def _print(self, text):
        if PRINT:
            show_class(self, text)
    
    def handle(self):
        if SHOW_TIME:
            start_time = datetime.utcnow()
        uid = self.request.recv(UID_LEN)
        if len(uid) != UID_LEN:
            show_error(self, 'failed to handle, invalid head')
            return
        buf = self.request.recv(FLG_LEN)
        if len(buf) != FLG_LEN:
            show_error(self, 'failed to handle, invalid head')
            return
        flg, = struct.unpack('I', buf)
        if flg == FLG_SEC:
            if not self.server.rpcserver.user:
                show_error(self, 'user is not initialized')
                raise Exception('user is not initialized')
            key = self.server.cache_get(uid)
            if not key:
                key = self.server.rpcserver.user.get_private_key(uid)
                if not key:
                    show_error(self, 'failed to handle, invalid private key')
                    return
                key = rsa.PrivateKey.load_pkcs1(key)
                self.server.cache_update(uid, key)
            stream = Stream(self.request, uid=uid, key=key)
        else:
            stream = Stream(self.request)
        buf = stream.read()
        if buf:
            res = self.server.rpcserver.proc(buf)
            if flg == FLG_SEC:
                stream = Stream(self.request)
            stream.write(res)
        if SHOW_TIME:
            self._print('handle, time=%d sec' % (datetime.utcnow() - start_time).seconds)

class DPMTCPServer(ThreadingMixIn, TCPServer):
    def set_server(self, rpcserver):
        self._cache = {}
        self.rpcserver = rpcserver
    
    def cache_get(self, uid):
        return self._cache.get(uid)
    
    def cache_update(self, uid, key):
        if len(self._cache) >= CACHE_MAX:
            self._cache.popitem()
        self._cache.update({uid:key})
    
class DPMServer(object):
    def run(self, rpcserver):
        self.server = DPMTCPServer((rpcserver.addr, rpcserver.port), DPMRequestHandler)
        self.server.set_server(rpcserver) 
        self.server.serve_forever()
