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
from random import randint
from lib.stream import ANON
from datetime import datetime
from hash_ring import HashRing
from threading import Lock, Thread
from recorder import RecorderServer
from component.rpcclient import RPCClient
from lib.util import localhost, APP, get_md5, get_uid, show_class, show_error
from conf.config import BACKEND_PORT, BACKEND_SERVERS, MANAGER_PORTS, SHOW_TIME, DEBUG, MANAGER_WEBSOCKET

if MANAGER_WEBSOCKET:
    import tornado.ioloop
    import tornado.web
    import tornado.websocket
    import tornado.template
    from websocket import create_connection

if SHOW_TIME:
    from datetime import datetime

PRINT = False
TOP = 4
TOP_NAME = "top%d" % TOP
INPUT_MAX = 1024

class Manager(object):
    def __init__(self):
        self._lock = Lock()
        self._recorder = RecorderServer()
        if DEBUG:
            self._register_cnt = 0
            self._login_cnt = 0
            self._install_cnt = 0
            self._uninstall_cnt = 0
    
    def _print(self, text):
        if PRINT:
            show_class(self, text)
    
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
        self._print('install->package=%s' %str(package))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            addr = self._get_backend()
            rpcclient = RPCClient(addr, BACKEND_PORT)
            info = rpcclient.request('install', uid=uid, package=package, version=version, typ=typ)
            if not info:
                show_error(self, 'failed to install, invalid return info')
                return
            if SHOW_TIME:
                self._print('install , time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if DEBUG:
                self._install_cnt += 1
                self._print('install, count=%d' % self._install_cnt)
            return info
        except:
            show_error(self, 'failed to install')
    
    def uninstall(self, uid, package):
        try:
            addr = self._get_backend()
            rpcclient = RPCClient(addr, BACKEND_PORT)
            res = rpcclient.request('uninstall', uid=uid, package=package, typ=APP)
            if not res:
                show_error(self, 'failed to uninstall, invalid return res')
                return
            if DEBUG:
                self._uninstall_cnt += 1
                self._print('uninstall, count=%d' % self._uninstall_cnt)
            return res
        except:
            show_error(self, 'failed to uninstall')
    
    def get_categories(self):
        return self._recorder.get_categories()
       
    def get_description(self, package):
        self._print('get_descripton starts' )
        try:
            ret = self._recorder.get_description(package)
            if ret:
                return ret
        except:
             show_error(self, 'get_descripton failed')
    
    def get_inst(self, package):
        self._print('get_inst starts, package=%s' %str(package))
        try:
            return self._recorder.get_inst(package)
        except:
             show_error(self, 'get_inst failed')
    
    def get_top(self, category):
        self._print('get_top starts, category=%s' %str(category))
        try:
            ret = self._recorder.get_top(category)
            if ret:
                return ret
            else:
                return ''
        except:
             show_error(self, 'get_top failed')
    
    def get_top_details(self, category):
        self._print('get_top_details starts')
        try:
            ret = self._recorder.get_top_details(category)
            if ret:
                for i in ret:
                    pkg = i.get('pkg')
                    if not pkg:
                        show_error(self, 'get_top_details failed, invalid package')
                        return
                    auth = self.get_author(pkg)
                    i.update({'auth':auth, 'category':category})
                return ret
            else:
                return ''
        except:
             show_error(self, 'get_top_details failed')
    
    def get_package_detail(self, package):
        self._print('get_package_detail starts')
        try:
            inst, title = self._recorder.get_package_detail(package)
            auth = self.get_author(package)
            if not auth:
                show_error(self, 'get_package_detail failed, no author')
                return
            return {'inst':inst, 'auth':auth, 'title':title}
        except:
            show_error(self, 'get_package_detail failed')
    
    def get_packages_details(self, category, rank):
        self._print('get_packages_details starts')
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            ret = self._recorder.get_packages_details(category, rank)
            if ret:
                for i in ret:
                    pkg = i.get('pkg')
                    if not pkg:
                        show_error(self, 'get_packages_details failed, invalid package')
                        return
                    auth = self.get_author(pkg)
                    i.update({'auth':auth})
                if SHOW_TIME:
                    self._print('get_packages_details , time=%d sec' % (datetime.utcnow() - start_time).seconds)
                return ret
        except:
             show_error(self, 'get_packages_details failed')
            
    def get_counter(self, category):
        self._print('get_counter->category=%s' % str(category))
        try:
            return self._recorder.get_counter(category)
        except:
            show_error(self, 'get_counter failed')
    
    def get_author(self, package):
        self._print('get_author starts, package=%s' % str(package))
        try:
            uid = self._recorder.get_uid(package)
            if uid:
                addr = self._get_backend()
                rpcclient = RPCClient(addr, BACKEND_PORT)
                name = rpcclient.request('get_name', uid=uid)
                if name:
                    return str(name)
        except:
             show_error(self, 'get_author failed')
    
    def get_installed_packages(self, uid):
        self._print('get_installed_packages starts')
        try:
            addr = self._get_backend()
            rpcclient = RPCClient(addr, BACKEND_PORT)
            res = rpcclient.request('get_installed_packages', uid=uid, typ=APP)
            if res:
                result = []
                for i in res:
                    result.append(str(i))
                return result
            else:
                return ''
        except:
            show_error(self, 'failed to get installed packages')
    
    def has_package(self, uid, package):
        self._print('has_package starts , package=%s' % str(package))
        addr = self._get_backend()
        rpcclient = RPCClient(addr, BACKEND_PORT)
        res = rpcclient.request('has_package', uid=uid, package=package, typ=APP)
        if res:
            return True
        return False
    
    def register(self, user, password, email):
        self._print('register starts')
        self._lock.acquire()
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            pwd = get_md5(password)
            addr = self._get_user_backend(user)
            rpcclient = RPCClient(addr, BACKEND_PORT)
            res = rpcclient.request('register', user=user, pwd=pwd, email=email)
            if SHOW_TIME:
                self._print('register , time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if res:
                if DEBUG:
                    self._register_cnt += 1
                    self._print('register, count=%d' % self._register_cnt)
                return True
            else:
                show_error(self, 'failed to register %s' % str(user))
                return False
        finally:
            self._lock.release()
    
    def login(self, user, password):
        self._print('login starts')
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            pwd = get_md5(password)
            addr = self._get_user_backend(user)
            rpcclient = RPCClient(addr, BACKEND_PORT)
            uid, key = rpcclient.request('login', user=user, pwd=pwd)
            if SHOW_TIME:
                self._print('login , time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if uid and key:
                if DEBUG:
                    self._login_cnt += 1
                    self._print('login, count=%d' % self._login_cnt)
                return (uid, key)
        except:
            show_error(self, 'failed to login')

if MANAGER_WEBSOCKET:
    manager = Manager()

class  ManagerWSHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, message):
        if len(message) > INPUT_MAX:
            show_error(self, 'invalid message' )
            return
        ret = ''
        info = json.loads(message)
        if not info or type(info) != dict or len(info) < 1:
            show_error(self, 'invalid message' )
            return
        op = info.get('operator')
        if not op:
            show_error(self, 'invalid handler')
        try:
            if op == 'register':
                user = info['user']
                password = info['password']
                email = info['email']
                if len(password) > 16:
                    show_error(self, 'failed to register, invalid register password length')
                else:
                    ret = manager.register(user, password, email)
                result = {'operator':'register', 'user':user, 'data':ret}
            
            elif op == 'login':
                user = info['user']
                password = info['password']
                ret = manager.login(user, password)
                result = {'operator':'login', 'user':user, 'data':ret}
            
            elif op == 'install':
                uid = info['uid']
                pkg = info['package']
                ver = info['version']
                typ = info['typ']
                ret = manager.install(uid, pkg, ver, typ)
                result = {'operator':'install', 'uid':uid, 'data':ret}
            
            elif op == 'uninstall':
                uid = info['uid']
                pkg = info['package']
                ret = manager.uninstall(uid, pkg)
                result = {'operator':'uninstall', 'uid':uid, 'data':ret}
            
            elif op == 'get_categories':
                ret = manager.get_categories()
                result = {'operator':'get_categories', 'data':ret}
            
            elif op == 'get_description':
                pkg = info['package']
                ret = manager.get_description(pkg)
                result = {'operator':'get_description', 'package':pkg, 'data':ret}
            
            elif op == 'get_inst':
                pkg = info['package']
                ret = manager.get_inst(pkg)
                result = {'operator':'get_inst', 'package':pkg, 'data':ret}
            
            elif op == 'get_top':
                cat = info['category']
                ret = manager.get_top(cat)
                result = {'operator':'get_top', 'category':cat, 'data':ret}
            
            elif op == 'get_top_details':
                cat = info['category']
                ret = manager.get_top_details(cat)
                result = {'operator':'get_top_details', 'category':cat, 'data':ret}
            
            elif op == 'get_package_detail':
                pkg = info['package']
                ret = manager.get_package_detail(pkg)
                result = {'operator':'get_package_detail', 'package':pkg, 'data':ret}
            
            elif op == 'get_packages_details':
                cat = info['category']
                rank = info['rank']
                ret = manager.get_packages_details(cat, rank)
                result = {'operator':'get_packages_details', 'category':cat, 'rank':rank, 'data':ret}
            
            elif op == 'get_counter':
                cat = info['category']
                ret = manager.get_counter(cat)
                result = {'operator':'get_counter', 'category':cat, 'data':ret}
            
            elif op == 'get_author':
                pkg = info['package']
                ret = manager.get_author(pkg)
                result = {'operator':'get_author', 'package':pkg, 'data':ret}
            
            elif op == 'get_installed_packages':
                uid = info['uid']
                ret = manager.get_installed_packages(uid)
                result = {'operator':'get_installed_packages', 'uid':uid, 'data':ret}
            
            elif op == 'has_package':
                uid = info['uid']
                pkg = info['package']
                ret = manager.has_package(uid, pkg)
                result = {'operator':'has_package', 'package':pkg, 'data':ret}
        finally: 
            self.write_message(json.dumps(result))
    
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
