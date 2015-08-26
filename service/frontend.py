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


from rpcserver import RPCServer
from rpcclient import RPCClient
from lib.log import log_debug

class Frontend(RPCServer):
    def __init__(self, addr, port):
        super(Frontend, self).__init__(addr, port)
        self.rpcclient = RPCClient('127.0.0.1', 9002)
        
    def matchfunc(self, a, b, c = 3):
        x = a
        y = b
        z = c
        return x+y+c
    
    def upload(self, username, name, version, src_type, buf):
        #rpcclient =  RPCClient('127.0.0.1', 9002)
        ret = self.rpcclient.request('upload', [username], {'name':name, 'version':version, 'src_type':src_type, 'buf':buf})
        log_debug('Frontend.upload()', 'the return of Backend.upload() is : %s' % str(ret))
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! lack a judgement of returning True or False 
        return True
    
    def download_src(self, username, src_name, src_type):
        ret = self.rpcclient.request('download_src', [username], {'src_name':src_name, 'src_type':src_type})
        return ret
        
    
def main():
    frontend = Frontend('127.0.0.1', 9001)
    frontend.run()
    
if __name__ == '__main__':
    main()    