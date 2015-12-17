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

import uuid
import json
import zerorpc
from lib.util import localhost
from random import randint
from lib.stream import ANON
from datetime import datetime
from hash_ring import HashRing
from threading import Lock, Thread
from lib.log import log_debug, log_err
from recorder import RecorderServer
from lib.util import APP, get_md5, get_uid
from component.rpcclient import RPCClient
from conf.config import BACKEND_PORT, BACKEND_SERVERS, MANAGER_PORTS, SHOW_TIME, DEBUG, MANAGER_WEBSOCKET

if MANAGER_WEBSOCKET:
    import tornado.ioloop
    import tornado.web
    import tornado.websocket
    import tornado.template
    from websocket import create_connection

TOP = 4
TOP_NAME = "top%d" % TOP
INPUT_MAX = 1024

if SHOW_TIME:
    from datetime import datetime

class Manager(object):
    def __init__(self):
        self._lock = Lock()
        self._recorder = RecorderServer()
        if DEBUG:
            self._register_cnt = 0
            self._install_cnt = 0
    
    def _get_user_backend(self, user):
        ring = HashRing(BACKEND_SERVERS)
        uid = get_uid(user)
        server = ring.get_node(uid)
        return server
    
    def _get_backend(self):
        n = randint(0, len(BACKEND_SERVERS) - 1)
        server =  BACKEND_SERVERS[n]
        return server
    
    def install(self, uid, package, version, typ):
        log_debug('Manager', 'install->package=%s' %str(package))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            addr = self._get_backend()
            rpcclient = RPCClient(addr, BACKEND_PORT)
            info = rpcclient.request('install', uid=uid, package=package, version=version, typ=typ)
            if not info:
                log_err('Manager', 'failed to install, invalid return info')
                return
            if SHOW_TIME:
                log_debug('Manager', 'install , time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if DEBUG:
                self._install_cnt += 1
                log_debug('Manger', 'install, count=%d' % self._install_cnt)
            return info
        except:
            log_err('Manager', 'failed to install')
    
    def uninstall(self, uid, package):
        try:
            addr = self._get_backend()
            rpcclient = RPCClient(addr, BACKEND_PORT)
            res = rpcclient.request('uninstall', uid=uid, package=package, typ=APP)
            if not res:
                log_err('Manager', 'failed to uninstall, invalid return res')
                return
            return res
        except:
            log_err('Manager', 'failed to uninstall')
    
    def get_categories(self):
        return self._recorder.get_categories()
    
    def get_packages(self, category, rank):
        log_debug('Manager', 'get_packages starts' )
        try:
            ret = self._recorder.get_packages(category, rank)
            if ret:
                return ret
        except:
            log_err('Manager', 'failed to get packages')
       
    def get_descripton(self, package):
        log_debug('Manager', 'get_descripton starts' )
        try:
            ret = self._recorder.get_description(package)
            if ret:
                return ret
        except:
             log_err('Manager', 'get_descripton failed')
    
    def get_inst(self, package):
        log_debug('Manager', 'get_inst starts, package=%s' %str(package))
        try:
            return self._recorder.get_inst(package)
        except:
             log_err('Manager', 'get_inst failed')
    
    def get_top(self, category):
        log_debug('Manager', 'get_top starts, category=%s' %str(category))
        try:
            ret = self._recorder.get_top(category)
            if ret:
                return ret
        except:
             log_err('Manager', 'get_top failed')
    
    def get_top_details(self, category):
        log_debug('Manger', 'get_top_details starts')
        try:
            ret = self._recorder.get_top_details(category)
            if ret:
                for i in ret:
                    pkg = i.get('pkg')
                    if not pkg:
                        log_err('Manager', 'get_top_details failed, invalid package')
                        return
                    auth = self.get_author(pkg)
                    i.update({'auth':auth})
                return ret
        except:
             log_err('Manager', 'get_top_details failed')
    
    def get_package_detail(self, package):
        log_debug('Manager', 'get_package_detail starts')
        try:
            cnt, title = self._recorder.get_package_detail(package)
            auth = self.get_author(package)
            if not auth:
                log_err('Manager', 'get_package_detail failed, no author')
                return
            return {'cnt':cnt, 'auth':auth, 'title':title}
        except:
            log_err('Manager', 'get_package_detail failed')
    
    def get_packages_details(self, category, rank):
        log_debug('Manager', 'get_packages_details starts')
        try:
            ret = self._recorder.get_packages_details(category, rank)
            if ret:
                for i in ret:
                    pkg = i.get('pkg')
                    if not pkg:
                        log_err('Manager', 'get_packages_details failed, invalid package')
                        return
                    auth = self.get_author(pkg)
                    i.update({'auth':auth})
                return ret
        except:
             log_err('Manager', 'get_packages_details failed')
            
    def get_counter(self, category):
        log_debug('Manager', 'get_counter->category=%s' % str(category))
        try:
            return self._recorder.get_counter(category)
        except:
            log_err('Manager', 'get_counter failed')
    
    def get_author(self, package):
        log_debug('Manager', 'get_author starts, package=%s' % str(package))
        try:
            uid = self._recorder.get_uid(package)
            if uid:
                addr = self._get_backend()
                rpcclient = RPCClient(addr, BACKEND_PORT)
                name = rpcclient.request('get_name', uid=uid)
                if name:
                    return str(name)
        except:
             log_err('Manager', 'get_author failed')
    
    def get_installed_packages(self, uid):
        log_debug('Manager', 'get_installed_packages starts')
        try:
            addr = self._get_backend()
            rpcclient = RPCClient(addr, BACKEND_PORT)
            res = rpcclient.request('get_installed_packages', uid=uid, typ=APP)
            if res:
                log_debug('Manager', 'get_installed_packages->res=%s' %str(res))
                result = []
                for i in res:
                    result.append(str(i))
                return result
        except:
            log_err('Manager', 'failed to get installed packages')
    
    def has_package(self, uid, package):
        log_debug('Manager', 'has_package starts , package=%s' % str(package))
        addr = self._get_backend()
        rpcclient = RPCClient(addr, BACKEND_PORT)
        res = rpcclient.request('has_package', uid=uid, package=package, typ=APP)
        if res:
            return True
        return False
    
    def register(self, user, password, email):
        log_debug('Manager', 'register starts')
        self._lock.acquire()
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            pwd = get_md5(password)
            addr = self._get_user_backend(user)
            rpcclient = RPCClient(addr, BACKEND_PORT)
            res = rpcclient.request('register', user=user, pwd=pwd, email=email)
            if SHOW_TIME:
                log_debug('Manager', 'register , time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if res:
                if DEBUG:
                    self._register_cnt += 1
                    log_debug('Manger', 'register, count=%d' % self._register_cnt)
                return True
            else:
                return False
        finally:
            self._lock.release()
    
    def login(self, user, password):
        log_debug('Manager', 'login starts')
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            pwd = get_md5(password)
            addr = self._get_user_backend(user)
            rpcclient = RPCClient(addr, BACKEND_PORT)
            uid, key = rpcclient.request('login', user=user, pwd=pwd)
            if SHOW_TIME:
                log_debug('Manager', 'login , time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if uid and key:
                if DEBUG:
                    self._register_cnt += 1
                    log_debug('Manager', 'login, count=%d' % self._register_cnt)
                return (uid, key)
        except:
            log_err('Manager', 'failed to login')

if MANAGER_WEBSOCKET:
    manager = Manager()

class  ManagerWSHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, message):
        if len(message) > INPUT_MAX:
            log_err('ManagerWSHandler', 'invalid message' )
            return
        ret = ''
        info = json.loads(message)
        if not info or type(info) != dict or len(info) < 2:
            log_err('ManagerWSHandler', 'invalid message' )
            return
        op = info.get('operator')
        if not op:
            log_err('ManagerWSHandler', 'invalid handler')
        try:
            if op == 'register':
                user = info['user']
                password = info['password']
                email = info['email']
                if len(password) > 16:
                    log_err('ManagerWSHandler', 'failed to register, invalid register password length')
                else:
                    ret = manager.register(user, password, email)
            
            elif op == 'login':
                user = info['user']
                password = info['password']
                ret = manager.login(user, password)
            
            elif op == 'install':
                uid = info['uid']
                pkg = info['package']
                ver = info['version']
                typ = info['typ']
                ret = manager.install(uid, pkg, ver, typ)
            
            elif op == 'uninstall':
                uid = info['uid']
                pkg = info['package']
                manager.uninstall(uid, pkg)
            
            elif op == 'get_categories':
                ret = manager.get_categories()
            
            elif op == 'get_packages':
                cat = info['category']
                rank = info['rank']
                ret = manager.get_packages(cat, rank)
            
            elif op == 'get_description':
                pkg = info['package']
                ret = manager.get_description(pkg)
            
            elif op == 'get_inst':
                pkg = info['package']
                ret = manager.get_inst(pkg)
            
            elif op == 'get_top':
                cat = info['category']
                ret = manager.get_top(cat)
            
            elif op == 'get_top_details':
                cat = info['category']
                ret = manager.get_top_details(cat)
            
            elif op == 'get_package_detail':
                pkg = info['package']
                ret = manager.get_package_detail(pkg)
            
            elif op == 'get_packages_details':
                cat = info['category']
                rank = info['rank']
                ret = manager.get_packages_details(cat, rank)
            
            elif op == 'get_counter':
                cat = info['category']
                ret = manager.get_counter(cat)
            
            elif op == 'get_author':
                pkg = info['package']
                ret = manager.get_author(pkg)
            
            elif op == 'get_installed_packages':
                uid = info['uid']
                ret = manager.get_installed_packages(uid)
            
            elif op == 'has_package':
                uid = info['uid']
                pkg = info['package']
                ret = manager.has_package(uid, pkg)
        finally: 
            self.write_message(json.dumps(ret))
    
class ManagerServer(Thread):
    def __init__(self, port):
        Thread.__init__(self)
        self.port = port
    
    def run(self):
        if MANAGER_WEBSOCKET:
            application = tornado.web.Application([(r'/', ManagerWSHandler)])
            application.listen(self.port)
            tornado.ioloop.IOLoop.instance().start()
        else:
            s = zerorpc.Server(Manager())
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
