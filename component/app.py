#      app.py
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

import os
import shutil
import zerorpc
import tempfile
import commands
from threading import Lock
from lib.db import Database
from lib.zip import unzip_file
from rpcclient import RPCClient
from hash_ring import HashRing
from conf.path import PATH_INSTALLER
from lib.util import APP, localhost, show_info, show_error
from conf.config import REPOSITORY_PORT, REPOSITORY_SERVERS, APP_DB

PRINT = False

class App():
    def __init__(self):
        self._lock = Lock()
        if APP_DB:
            self._db = Database(addr=APP_DB, domain=APP)
        else:
            self._db = Database(addr=localhost(), domain=APP)
    
    def _print(self, text):
        if PRINT:
            show_info(self, text)
    
    def _get_repo(self, package):
        ring = HashRing(REPOSITORY_SERVERS)
        server = ring.get_node(package)
        return server
    
    def _install(self, buf):
        dirname = tempfile.mkdtemp()
        try:
            src = os.path.join(dirname, 'app.zip')
            with open(src, 'wb') as f:
                f.write(buf)
            dest = os.path.join(dirname, 'app')
            unzip_file(src, dest)
            cmd = 'python %s %s' % (PATH_INSTALLER, dest)
            status, output = commands.getstatusoutput(cmd)
            if status ==  0:
                return output
        finally:
            shutil.rmtree(dirname)
    
    def install(self, uid, package, version):
        self._lock.acquire()
        try:
            if self._db.has_package(uid, package, None):
                show_error(self, 'failed to install, cannot install %s again' % package)
                return
            else:
                addr = self._get_repo(package)
                rpcclient = RPCClient(addr, REPOSITORY_PORT)
                if not version:
                    version = rpcclient.request('version', package=package)
                    if not version:
                        show_error(self, 'failed to install, invalid version, uid=%s, package=%s' % (uid, package))
                        return
                ret = rpcclient.request('download', package=package, version=version)
                if ret:
                    result = self._install(ret)
                    if result:
                        self._db.set_package(uid, package, version, result)
                        self._print('finished installing %s, version=%s' % (package, version))
                        return True
            show_error(self, 'failed to install %s' % package)
            return
        finally:
            self._lock.release()
        
    def _uninstall(self, uid, package, info):
        pass
        
    def uninstall(self, uid, package):
        self._lock.acquire()
        try:
            if not self._db.has_package(uid, package, None):
                show_error(self, 'failed to uninstall %s ' % package)
                return
            version, info = self._db.get_package(uid, package, None)
            if info:
                self._uninstall(uid, package, info)
            self._db.rm_package(uid, package, version)
            return True
        finally:
            self._lock.release()
    
    def get_packages(self, uid):
        return self._db.get_packages(uid)
    
    def has_package(self, uid, package):
        return self._db.has_package(uid, package)

    