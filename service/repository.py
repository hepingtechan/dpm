#      repository.py
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


from threading import Thread

from rpcserver import RPCServer
from ftpclient import FTPClient
from ftpserver import FTPServer
from lib.log import log_debug
from lib.upload_register import write_upload_log


class Repository(RPCServer):
    def __init__(self, addr, port):
        super(Repository, self).__init__(addr, port)
        self.ftpclient = FTPClient()
        self.ftpserver = FTPServer()
    
    def upload(self, username, name, version, src_type, buf):
        ret = self.upload_src(name, version, buf)
        self.upload_register(username, name, version, src_type)
        
    def upload_src(self, name, version, buf):
        addr, port = calculate_the_ftpserver_addr()
        ret = self.ftpclient.upload(addr, port, name, version, buf)
        log_debug('Repository.upload()', 'the return of FTPClient.upload() is : %s' % str(ret))
        return ret
    
    def upload_register(self, username, name, version, src_type):
        write_upload_log(username, name, version, src_type)
        
    def install(self, username, name, version, src_type):
        pass
        #return self.download_src(name, version, src_type)
        
    
    def download_src(self, username, src_name, src_type):
        addr, port = calculate_the_ftpserver_addr()
        ret = self.ftpclient.download(addr, port, src_name, src_type)
        return ret
    
    def install_register(self):
        pass
    
    def start(self):
        t = Thread(target=self.run)
        t.start()
        self.ftpserver.run()
        t.join()
        
        
def calculate_the_ftpserver_addr():
    addr = '127.0.0.1'
    port = 21
    return addr, port 

    
def main():
    repo = Repository('127.0.0.1', 9003)
    repo.start()
    

if __name__ == '__main__':
    main()