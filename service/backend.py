#      backend.py
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


from rpcclient import RPCClient
from rpcserver import RPCServer
from ftpclient import FTPClient
from lib.log import log_debug

class Backend(RPCServer):
    def __init__(self, addr, port):
        super(Backend, self).__init__(addr, port)
        self.ftpclient = FTPClient()
        self.rpcclient = RPCClient('127.0.0.1', 9003)
    
    def upload(self, username, name, version, src_type, buf):
        print 'upload in backend starts!'
        ret = self.rpcclient.request('upload', [username], {'name':name, 'version':version, 'src_type':src_type, 'buf':buf})
        log_debug('Backend.upload()', 'the retrun of Repository.upload() is : %s' % str(ret))
        return ret
    
    def download_src(self, username, src_name, src_type):
        ret = self.rpcclient.request('download_src', [username], {'src_name':src_name, 'src_type':src_type})
        return ret

         
def main():
    backend = Backend('127.0.0.1', 9002)
    backend.run()
    
    
if __name__ == '__main__':
    main()