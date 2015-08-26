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


from threading import Lock, Event
import socket

class DPMClient():   
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ev = Event()
        self._lock = Lock()
          
    def request(self, addr, port, buf):
        self._lock.acquire()
        try:
            self.sock.connect((addr, port))
            try:
                self.sock.sendall(buf)
                response = self.sock.recv(1024)
                self.setResult(response)
                return self.getResult()
            finally:
                self.sock.close()
        finally:
            self._lock.release()

    def setResult(self, buf):
        self.ev.set()
        self.result = buf
    
    def getResult(self):
        self.ev.wait()
        return self.result


if __name__ == '__main__':
    cli = DPMClient()
    res = cli.request('127.0.0.1', 9019, 'asfasdfasdf')
    print(str(res))

