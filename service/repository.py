#      repository.py
#      
#      Copyright (C) 2015 Xiao-Fang Huang <huangxfbnu@163.com>,  Xu Tian <tianxu@iscas.ac.cn>
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

import os
import time
from threading import Lock
from lib.db import Database
from threading import Thread
from lib.log import log_debug, log_err
from conf.config import REPOSITORY_PORT
from component.ftpclient import FTPClient
from component.ftpserver import FTPServer
from component.rpcserver import RPCServer

class Repository(RPCServer):
    def __init__(self, addr, port):
        RPCServer.__init__(self, addr, port)
        self._ftpclient = FTPClient()
        self._ftpserver = FTPServer()
        self._db = Database(local=False)
        self._lock = Lock()
        
    def _get_addr(self, package):
        return ('127.0.0.1', 21)
    
    def _upload(self, package, version, buf):
        addr, port = self._get_addr(package)
        self._ftpclient.upload(addr, port, package, version, buf)
       
    def upload(self, uid, package, version, buf):
        self._lock.acquire()
        try:
            owner, ver = self._db.get_version(uid, package)
            if owner and owner != uid:
                log_err('Repository', 'failed to upload, invalid owner, package=%s, version=%s' % (str(package), str(version)))
                return False
            if ver == version:#The version of package has been uploaded.
                log_err('Repository', 'failed to upload, invalid version, package=%s, version=%s' % (str(package), str(version)))
                return False
            else:
                self._upload(package, version, buf)
                self._db.set_package(uid, package, version, '')
                if not ver or ver < version:
                    self._db.set_version(uid, package, version)
                log_debug('Repository', 'finished uploading, package=%s, version=%s' % (str(package), str(version)))
                return True
        finally:
            self._lock.release()
    
    def download(self, package, version):
        log_debug('Repository', 'start to download, package=%s, version=%s' % (str(package), str(version)))
        addr, port = self._get_addr(package)
        uid, ver = self._db.get_version(package)
        if not version:
            version = ver
        if not self._db.has_package(uid, package, version):
            log_err('Repository', 'failed to download, invalid version, package=%s, version=%s' % (str(package), str(version)))
            return
        return self._ftpclient.download(addr, port, package, version)
    
    def version(self, package):
        log_debug('Repository', 'start to get version, uid=%s, package=%s' % (str(uid), str(package)))
        _, ver = self._db.get_version(package)
        return ver
    
    def start(self):
        t = Thread(target=self.run)
        t.start()
        self._ftpserver.run()
        t.join()

def main():
    repo = Repository('127.0.0.1', REPOSITORY_PORT)
    repo.start()
