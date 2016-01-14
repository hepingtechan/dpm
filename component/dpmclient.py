#      dpmclient.py
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
import socket
from threading import Lock
from lib.stream import Stream

class DPMClient():   
    def __init__(self, uid=None, key=None):
        self._lock = Lock()
        self._uid = uid
        self._key = None
        if key:
            self._key = rsa.PublicKey.load_pkcs1(key)
      
    def request(self, addr, port, buf):
        self._lock.acquire()
        try:
            return self._request(addr, port, buf)
        finally:
            self._lock.release()
    
    def _request(self, addr, port, buf):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((addr, port))
        try:
            if self._key:
                stream = Stream(sock, uid=self._uid, key=self._key)
            else:
                stream = Stream(sock)
            stream.write( buf)
            if self._key:
                stream = Stream(sock)
            _, _, res = stream.readall()
            return res
        finally:
            sock.close()
