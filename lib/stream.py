#      stream.py
#      
#      Copyright (C) 2015  Xu Tian <tianxu@iscas.ac.cn>
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
from log import log_err

FLG_LEN = 4
UID_LEN = 32
HEAD_LEN = 40
PACKET_LEN = 50
FLG_SEC = 0x00000001
ANON = '0' * UID_LEN

class Stream(object):
    def __init__(self, sock, uid=ANON, key=None):
        self._sock = sock
        self._uid = uid
        self._key = key
    
    def write(self, buf):
        if len(self._uid) != UID_LEN:
            log_err('Stream',  'invalid uid')
            return
        if self._key:
            flg = FLG_SEC
        else:
            flg = 0
        cnt = 0
        length = len(buf)
        total = (length + PACKET_LEN - 1) / PACKET_LEN
        head = self._uid + struct.pack('I', flg) + struct.pack('I', total)
        self._sock.sendall(head)
        while cnt < total:
            start = cnt * PACKET_LEN
            end = min(start + PACKET_LEN, length)
            if self._key:
                body = rsa.encrypt(buf[start:end], self._key)
            else:
                body = buf[start:end]
            head = struct.pack('H', len(body))
            self._sock.sendall(head)
            self._sock.sendall(body)
            cnt += 1
        self._sock.recv(1)
    
    def _recv(self, length):
        buf = ''
        while length > 0:
            tmp = self._sock.recv(length)
            if tmp:
                buf += tmp
                length -= len(tmp)
            else:
                break
        return buf
    
    def read(self):
        head = self._recv(4)
        if len(head) != 4:
            log_err('Stream', 'failed to receive head')
            return
        total, =  struct.unpack('I', head)
        cnt = 0
        res = ''
        while cnt < total:
            head = self._recv(2)
            if len(head) != 2:
                log_err('Stream',  'failed to receive')
                return
            length, = struct.unpack('H', head)
            body = self._recv(length)
            if len(body) != length:
                log_err('Stream',  'failed to receive body')
                return
            if self._key:
                res += rsa.decrypt(body, self._key)
            else:
                res += body
            cnt += 1
        self._sock.sendall('0')
        return res
    
    def readall(self):
        uid = self._recv(UID_LEN)
        if len(uid) != UID_LEN:
            log_err('Stream',  'failed to receive uid')
            return (None, None, '')
        buf = self._recv(FLG_LEN)
        if len(buf) != FLG_LEN:
            log_err('Stream',  'failed to receive flag')
            return (None, None, '')
        flg = struct.unpack('I', buf)[0]
        buf = self.read()
        return (uid, flg, buf)
