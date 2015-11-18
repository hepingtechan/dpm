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
import uuid
from lib.user import User
from threading import Lock
from lib.util import localhost
from hash_ring import HashRing
from lib.log import log_debug, log_err
from lib.sandbox import Sandbox, OP_SCAN
from component.rpcclient import RPCClient
from component.rpcserver import RPCServer
from conf.config import BACKEND_PORT, REPOSITORY_PORT, ALLOCATOR_PORT, INSTALLER_PORT, RECORDER_PORT, REPOSITORY_SERVERS, ALLOCATOR_SERVERS, RECORDER_SERVERS, SHOW_TIME, DEBUG

LOCK_MAX = 256
CACHE_MAX = 4096

if SHOW_TIME:
    from datetime import datetime

class Backend(RPCServer):
    def __init__(self, addr, port):
        RPCServer.__init__(self, addr, port, user=User())
        self._sandbox = Sandbox()
        locks = []
        for _ in range(LOCK_MAX):
            locks.append(Lock())
        self._locks = HashRing(locks)
        self._cache = {}
        if DEBUG:
            self._register_cnt = 0
    
    def _load(self, buf):
        return json.loads(buf)
    
    def _get_uid(self, user):
        return uuid.uuid3(uuid.NAMESPACE_DNS, user).hex
    
    def _get_lock(self, user):
        uid = self._get_uid(user)
        return self._locks.get_node(uid)
    
    def _get_allocator(self, uid):
        ring = HashRing(ALLOCATOR_SERVERS)
        server = ring.get_node(uid)
        #print 'Backend->allocator_servers is', str(server)
        return server
    
    def _get_repo(self, package):
        ring = HashRing(REPOSITORY_SERVERS)
        server = ring.get_node(package)
        print 'backend->repository_servers is', str(server)
        return server
    
    def _get_recorder(self, package):
        ring = HashRing(RECORDER_SERVERS)
        server = ring.get_node(package)
        print 'backend->recorder_servers is', str(server)
        return server
    
    def _update(self, uid, category, package, title, description):
        log_debug('Backend', 'update, cat=%s, desc=%s' % (str(category), str(description)))
        addr = self._get_recorder(package)
        rpcclient = RPCClient(addr, RECORDER_PORT)
        return rpcclient.request('upload', uid=uid, category=category, package=package, title=title, description=description)
    
    def _check_category(self, category):
        res = {'game':'0', 'news':'1', 'video':'2', 'music':'3', 'soft':'4', 'forum':'5'}
        if res.has_key(category):
            return res.get(category)
        else:
            return str(len(res))
    
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
        cat = self._check_category(cat)
        if not cat:
            log_err('Backend', 'invalid category')
            return
        return self._update(uid, cat, package, title, desc)
    
    def _get_installer(self, uid):
        log_debug('Backend', 'start to get instsaller addr')
        try:
            cache = self._cache
            print '9-1 Backend->_get_instsaller, cache=%s' % str(cache)
            addr = cache.get(uid)
            print '9-2, Backend->_get_instsaller, addr=%s' % str(addr)
            if addr:
                return addr
            else:
                address = self._get_allocator(uid)
                print '9-3 Backend->_get_instsaller', address
                rpcclient = RPCClient(address, ALLOCATOR_PORT)
                print '9-4'
                addr = rpcclient.request('get_installer', uid=uid)
                if len(cache) >= CACHE_MAX:
                    cache.popitem()
                print '9-5 Backend->_get_instsaller', cache,'##', addr
                cache.update({uid:addr})
                print '9-6 Backend->_get_instsaller', cache,'##', addr
                return addr
        except:
            log_err('Backend', 'failed to get instsaller addr')
    
    
    def install(self, uid, package, version, typ):
        log_debug('Backend', 'start to install')
        addr = self._get_installer(uid)
        rpcclient = RPCClient(addr, INSTALLER_PORT)
        res = rpcclient.request('install', uid=uid, package=package, version=version, typ=typ)
        log_debug('Backend', 'install->res=%s' %str(res))
        if not res:
            log_err('Backend', 'failed to install')
            return
        addr = self._get_recorder(package)
        rpcclient = RPCClient(addr, RECORDER_PORT)
        info = rpcclient.request('install', package=package)
        print '9-2 Backend->install-->info=%s' % str(info)
        if not info:
            log_err('Backend', 'failed to install, invalid update install table')
            return
        return info
    
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
    
    def has_package(self, uid, package, typ):
        log_debug('Backend', 'has_package, package=%s' % str(package))
        addr = self._get_installer(uid)
        rpcclient = RPCClient(addr, INSTALLER_PORT)
        return rpcclient.request('has_package', uid=uid, package=package, typ=typ)
    
    def _alloc_installer(self, uid):
        #log_debug('Backend', 'alloc_installer->uid=%s' % str(uid))
        addr = self._get_allocator(uid)
        rpcclient = RPCClient(addr, ALLOCATOR_PORT)
        if  rpcclient.request('alloc_installer', uid=uid):
            return True
        else:
            log_err('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  Backend', 'failed to allocate installer')
            return False
    
    def register(self, user, pwd, email):
        #log_debug('Backend', 'register starts')
        lock = self._get_lock(user)
        lock.acquire()
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            uid = self.user.add(user, pwd, email)
            if not uid:
                log_err('Backend', 'failed to register, invalid register table')
                return False
            info= self._alloc_installer(uid)
            #print '2-6 info=%s' % str(info)
            if SHOW_TIME:
                log_debug('Backend', 'register, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if info:
                if DEBUG:
                    self._register_cnt += 1
                    log_debug('Backend', 'register, count=%d' % self._register_cnt)
                return True
            else:
                self.user.remove(user)
                log_err('@@@@@@@@@@@@ Backend', 'failed to register, invalid alloc installer table')
                return False
        finally:
            lock.release()
    
    def login(self, user, pwd):
        log_debug('Backend', 'start to login')
        password = self.user.get_password(user)
        print '7-4 Backend->login', password, type(password)
        if pwd == password:
            print '7-5'
            return self.user.get_public_key(user)
        else:
            log_err('Backend', 'failed to login, invalid login password')
            return (None, None)
    
    def get_name(self, uid):
        log_debug('Backend', 'start to get name, uid=%s' % str(uid))
        return self.user.get_name(uid)

def main():
    backend = Backend(localhost(), BACKEND_PORT)
    backend.run()
