#      manager.py
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

import json
import uuid
import socket
import zerorpc
from lib.util import localhost
from random import randint
from lib.stream import ANON
from datetime import datetime
from hash_ring import HashRing
from lib.util import APP, get_md5
from threading import Lock, Thread
from pymongo import MongoClient
from lib.log import log_debug, log_err
from component.rpcclient import RPCClient
from component.rpcserver import RPCServer
from conf.config import BACKEND_PORT, MANAGER_PORTS, BACKEND_SERVERS, MONGO_PORT, RECORDER_DB, SHOW_TIME

REGIST_INFO_MAX = 1024
LOGIN_INFO_MAX = 1024

TABLE_CAT = 'pkgcat'
TABLE_TOP = 'pkgtop'
TABLE_INSTALL = 'pkginst'
TABLE_AUTHOR = 'pkgauth'
TABLE_DESCRIPTION = 'pkgdesc'

TOP = 4
TOP_NAME = "top%d" % TOP

REGISTER_INFO = ['user', 'password',  'email']
LOGIN_INFO = ['user', 'password']

if SHOW_TIME:
    from datetime import datetime

class Manger(RPCServer):
    def __init__(self, hidden=False):
        self._lock = Lock()
        self._hidden = hidden
        self._client =  MongoClient(RECORDER_DB, MONGO_PORT)
    
    def _dump(self, buf):
        return json.dumps(buf)
    
    def _get_uid(self, user):
        return uuid.uuid3(uuid.NAMESPACE_DNS, user).hex
    
    def _get_collection(self, name):
        return self._client.test[name]
    
    def _get_table(self, prefix, name):
        return str(prefix) + str(name)
    
    def _get_user_backend(self, user):
        ring = HashRing(BACKEND_SERVERS)
        uid = self._get_uid(user)
        server = ring.get_node(uid)
        print 'manager->user_backend_servers is', str(server)
        return server
    
    def _get_backend(self):
        n = randint(0, len(BACKEND_SERVERS) - 1)
        server =  BACKEND_SERVERS[n]
        print 'manager->backend_servers is', str(server)
        return server
    
    def install(self, uid, package, version, typ):
        log_debug('Manger', 'install->package=%s' %str(package))
        addr = self._get_backend()
        rpcclient = RPCClient(addr, BACKEND_PORT)
        info = rpcclient.request('install', uid=uid, package=package, version=version, typ=typ)
        log_debug('Manger', 'install->info=%s' %str(info))
        if not info:
            log_err('Manger', 'failed to install')
            return
        print 'Manager->install success'
        return info
    
    def uninstall(self, uid, package):
        try:
            addr = self._get_backend()
            rpcclient = RPCClient(addr, BACKEND_PORT)
            res = rpcclient.request('uninstall', uid=uid, package=package, typ=APP)
            if res:
                log_debug('Manger', 'uninstall->res=%s' %str(res))
                return res
        except:
            log_err('Manger', 'failed to uninstall')
    
    def get_categories(self):
        res = {'game':'0', 'news':'1', 'video':'2', 'music':'3', 'soft':'4', 'forum':'5'}
        return self._dump(res)
    
    def get_author(self, package):
        try:
            coll = self._get_collection(TABLE_AUTHOR)
            res = coll.find_one({package:''})
            if res:
                uid = res.get('uid')
                if uid:
                    addr = self._get_backend()
                    rpcclient = RPCClient(addr, BACKEND_PORT)
                    name = rpcclient.request('get_name', uid=uid)
                    if name:
                        return str(name)
        except:
             log_err('Manger', 'failed to get author')
    
    def _get_packages(self, category, rank):
        result = []
        table = self._get_table(TABLE_CAT, category)
        coll = self._get_collection(table)
        res = coll.find_one({'rank':rank})
        if res.has_key('packages'): 
            for item in res['packages']:
                result.append(str(item['pkg']))
        return result
    
    def get_packages(self, category, rank):
        try:
            result = self._get_packages(category, rank)
            if result:
                return self._dump(result)
        except:
            log_err('Manger', 'failed to get packages')
    
    def get_installed_packages(self, uid):
        try:
            addr = self._get_backend()
            rpcclient = RPCClient(addr, BACKEND_PORT)
            res = rpcclient.request('get_installed_packages', uid=uid, typ=APP)
            if res:
                log_debug('Manger', 'get_installed_packages->res=%s' %str(res))
                result = []
                for i in res:
                    result.append(str(i))
                return self._dump(result)
        except:
            log_err('Manger', 'failed to get installed packages')
    
    def get_descripton(self, package):
        try:
            coll = self._get_collection(TABLE_DESCRIPTION)
            res = coll.find_one({'pkg':package})
            if res:
                return (str(res['title']), str(res['des']))
        except:
             log_err('Manger', 'failed to get description')
    
    def get_inst(self, package):
        log_debug('Manger', 'get_inst->package=%s' %str(package))
        try:
            coll = self._get_collection(TABLE_INSTALL)
            res = coll.find_one({'pkg':package})
            if res:
                return str(res['cnt'])
        except:
             log_err('Manger', 'failed to get install num')
    
    def _get_top(self, category):
        result = []
        table = self._get_table(TABLE_TOP, category)
        coll = self._get_collection(table)
        res = coll.find_one({'name':TOP_NAME})
        if res:
            del res['name']
            del res['_id']
            for i in res:
                result.append({str(i):str(res[i])})
        return result
    
    def get_top(self, category):
        log_debug('Manger', 'get_top->category=%s' %str(category))
        try:
            result = self._get_top(category)
            if result:
                return self._dump(result)
        except:
             log_err('Manger', 'failed to get top')
    
    def get_top_details(self, category):
        log_debug('Manger', 'get_top_details starts')
        info = self._get_top(category)
        res = []
        for i in info:
            pkg = i.keys()[0]
            cnt, auth, title = self.get_package_detail(pkg)
            item = {'pkg':pkg, 'title':title, 'auth':auth, 'cnt':cnt}
            res.append(item)
        if res:
            return self._dump(res)
    
    def get_packages_details(self, category, rank):
        log_debug('Manger', 'get_packages_details starts')
        info = self._get_packages(category, rank)
        res = []
        for i in info:
            cnt, auth, title = self.get_package_detail(i)
            item = {'pkg':i, 'title':title, 'auth':auth, 'cnt':cnt}
            res.append(item)
        if res:
            return self._dump(res)
    
    def get_package_detail(self, package):
        try:
            cnt = self.get_inst(package)
            if not cnt:
                cnt = str(0)
            auth = self.get_author(package)
            if not auth:
                log_err('Manger', 'get_package_detail-> failed to get author')
                return
            title, _ = self.get_descripton(package)
            if not title:
                log_err('Manger', 'get_package_detail-> failed to get title')
                return
            return (cnt, auth, title)
        except:
            log_err('Manger', 'failed to get_package_detail')
    
    def has_package(self, uid, package):
        log_debug('Manger', 'has_package->package=%s' % str(package))
        addr = self._get_backend()
        rpcclient = RPCClient(addr, BACKEND_PORT)
        res = rpcclient.request('has_package', uid=uid, package=package, typ=APP)
        if res:
            return True
        return False
    
    def register(self, info):
        self._lock.acquire()
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            #log_debug('Manger', 'register starts')
            if len(info) > REGIST_INFO_MAX:
                log_err('Manger', 'failed register, invalid register information')
                return
            res = json.loads(info)
            #print '1-1 Manger->register',res
            if type(res) != dict or len(res) > len(REGISTER_INFO):
                log_err('Manger', 'failed register, invalid register user, password and email')
                return
            
            for i in res:
                if i not in REGISTER_INFO:
                    log_err('Manager', 'invalid register info')
                    return
            
            user = res.get('user').encode('utf-8')
            password = res.get('password').encode('utf-8')
            email = res.get('email').encode('utf-8')
            #print '1-2 Manger->register-->user=%s' % str(user)
            #print '1-2 Manger->register', user, password, email
            if len(password) > 16:
                log_err('Manger', 'failed to register, invalid register password length')
                return
            pwd = get_md5(password)
            addr = self._get_user_backend(user)
            rpcclient = RPCClient(addr, BACKEND_PORT)
            res = rpcclient.request('register', user=user, pwd=pwd, email=email)
            if SHOW_TIME:
                log_debug('Manger', 'register , time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if res:
                return str(True)
            else:
                return str(False)
        finally:
            self._lock.release()
    
    def login(self, info):
        log_debug('Manger', 'login starts')
        if len(info) > LOGIN_INFO_MAX:
            log_err('Manager', 'failed login, invalid login information')
            return
        res = json.loads(info)
        if type(res) != dict or len(res) > len(LOGIN_INFO):
            log_err('Manger', 'failed login, invalid login user, password')
            return
        for i in res:
            if i not in LOGIN_INFO:
                log_err('Manager', 'invalid login info')
                return
        user = res.get('user').encode('utf-8')
        password = res.get('password').encode('utf-8')
        pwd = get_md5(password)
        addr = self._get_user_backend(user)
        rpcclient = RPCClient(addr, BACKEND_PORT)
        uid, key = rpcclient.request('login', user=user, pwd=pwd)
        if uid and key:
            print '@@, Manager->login', uid, type(uid)
            print '##, Manager->login', key, type(key)
            return uid
        return 'login failed'

class ManagerServer(Thread):
    def __init__(self, port):
        Thread.__init__(self)
        self.port = port
    
    def run(self):
        s = zerorpc.Server(Manger())
        s.bind("tcp://%s:%d" % (localhost(), self.port))
        s.run()

def main():
    threads = []
    for i in MANAGER_PORTS:
        t = ManagerServer(i)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()

