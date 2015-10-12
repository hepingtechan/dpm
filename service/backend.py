#      backend.py
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
import json
import shutil
import zerorpc
from lib.user import User
from component.app import App
from component.driver import Driver
from lib.log import log_debug, log_err
from lib.sandbox import Sandbox, OP_SCAN
from component.rpcclient import RPCClient
from component.rpcserver import RPCServer
from conf.config import BACKEND_PORT, REPOSITORY_PORT, MANAGER_PORT, INSTALLER_PORT

BACKEND_ADDR = '127.0.0.1'

class Backend(RPCServer):
    def __init__(self, addr, port):
        RPCServer.__init__(self, addr, port)
        self._sandbox = Sandbox()
        self._user = User()
    
    def _load(self, buf):
        return json.loads(buf)
    
    def _get_repo(self, package):
        return '127.0.0.1'
    
    def _get_installer(self, uid):
        return '127.0.0.1'
    
    def _get_manager(self, package):
        return '127.0.0.1'
    
    def _update(self, uid, cagegory, package, title, description):
        log_debug('Backend', 'update, cat=%s, desc=%s' % (str(cagegory), str(description)))
        c = zerorpc.Client()
        addr = self._get_manager(package)
        c.connect("tcp://%s:%d" % (addr, MANAGER_PORT))
        c.upload(uid, cagegory, package, title, description)
    
    def _check_category(self, category, package):
        c = zerorpc.Client()
        addr = self._get_manager(package)
        c.connect("tcp://%s:%d" % (addr, MANAGER_PORT))
        res = c.get_categories()
        if res:
            info = self._load(res)
            if info.has_key(category):
                return info.get(category)
            else:
                return str(len(info))
    
    def upload(self, uid, package, version, buf, typ):
        log_debug('Backend', 'start to upload')
        addr = self._get_repo(package)
        rpcclient = RPCClient(addr, REPOSITORY_PORT)
        res = rpcclient.request('upload', uid=uid, package=package, version=version, buf=buf)
        if not res:
            log_err('Backend', 'failed to upload')
            return
        cat, title, desc = self._sandbox.evaluate(OP_SCAN, buf)
        log_debug('Backend', 'upload  cat=%s, title=%s, desc=%s' % (str(cat), str(title), str(desc)))
        if not cat or not title or not desc:
            log_err('Backend', 'invalid package')
            return
        cat = self._check_category(cat, package)
        if not cat:
            log_err('Backend', 'invalid category')
            return
        self._update(uid, cat, package, title, desc)
        return res
    
    def install(self, uid, package, version, typ):
        log_debug('Backend', 'start to install')
        addr = self._get_installer(uid)
        rpcclient = RPCClient(addr, INSTALLER_PORT)
        res = rpcclient.request('install', uid=uid, package=package, version=version, typ=typ)
        if not res:
            log_err('Backend', 'failed to install')
            return
        return res
    
    def uninstall(self, uid, package, typ):
        log_debug('Backend', 'start to uninstall')
        addr = self._get_installer(uid)
        rpcclient = RPCClient(addr, INSTALLER_PORT)
        res = rpcclient.request('uninstall', uid=uid, package=package, typ=typ)
        if not res:
            log_err('Backend', 'failed to uninstall')
            return
        return res
    
    def get_installed_packages(self, uid, typ):
        log_debug('Backend', 'start to get installed packages')
        addr = self._get_installer(uid)
        rpcclient = RPCClient(addr, INSTALLER_PORT)
        return rpcclient.request('get_packages', uid=uid, typ=typ)
    
    def login(self, user, password):
        log_debug('Backend', 'start to login, user=%s' % str(user))
        res = self._user.get_password(user)
        if res == password:
            return self._user.get_public_key(user)
        else:
            return (None, None)
    
    def get_name(self, uid):
        log_debug('Backend', 'start to get name, uid=%s' % str(uid))
        return self._user.get_name(uid)
    
    def has_package(self, uid, package, typ):
        log_debug('Backend', 'has_package, package=%s' % str(package))
        addr = self._get_installer(uid)
        rpcclient = RPCClient(addr, INSTALLER_PORT)
        return rpcclient.request('has_package', uid=uid, package=package, typ=typ)

def main():
    backend = Backend(BACKEND_ADDR, BACKEND_PORT)
    backend.run()

