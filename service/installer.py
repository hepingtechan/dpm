#      installer.py
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

from threading import Thread
from component.app import App
from component.driver import Driver
from conf.config import INSTALLER_PORT
from component.rpcserver import RPCServer
from lib.util import APP, DRIVER, localhost, show_error

class Installer(RPCServer):
    def __init__(self, addr, port):
        RPCServer.__init__(self, addr, port)
        self._app = App()
        self._driver = Driver()
    
    def install(self, uid, package, version, typ):
        if typ == APP:
            return self._app.install(uid, package, version)
        elif typ == DRIVER:
            return self._driver.install(uid, package, version)
        else:
            show_error(self, 'failed to install, invalid type, typ=%s' % str(typ))
    
    def uninstall(self, uid, package, typ):
        if typ == APP:
            return self._app.uninstall(uid, package)
        else:
            show_error(self, 'failed to uninstall, invalid type, typ=%s' % str(typ))
    
    def get_packages(self, uid, typ):
        if typ == APP:
            return self._app.get_packages(uid)
    
    def has_package(self, uid, package, typ):
        if typ == APP:
            return self._app.has_package(uid, package)
    
    def start(self):
        t = Thread(target=self.run)
        t.start()
        t.join()

def main():
    inst = Installer(localhost(), INSTALLER_PORT)
    inst.start()
