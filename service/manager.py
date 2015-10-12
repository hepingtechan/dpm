#      repository.py
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
import socket
import zerorpc
from lib.util import APP
from datetime import datetime
from pymongo import MongoClient
from lib.log import log_debug, log_err
from component.rpcclient import RPCClient
from component.rpcserver import RPCServer
from conf.config import BACKEND_PORT, MANAGER_PORT

MDB_ADDR = '127.0.0.1'
MANAGER_ADDR = '127.0.0.1'

MDB_PORT = 27017

PAGE_SIZE = 3
TABLE_CAT = 'pkgcat'
TABLE_TOP = 'pkgtop'
TABLE_INSTALL = 'pkginst'
TABLE_AUTHOR = 'pkgauth'
TABLE_COUNTER = 'pkgcnt'
TABLE_PACKAGE = 'pkginfo'
TABLE_DESCRIPTION = 'pkgdesc'

TOP = 4
TOP_NAME = "top%d" % TOP

class Manger(RPCServer):
    def __init__(self, hidden=False):
        self._hidden = hidden
        self._client =  MongoClient(MDB_ADDR, MDB_PORT)
    
    def _dump(self, buf):
        return json.dumps(buf)
    
    def _get_collection(self, name):
        return self._client.test[name]
    
    def _get_table(self, prefix, name):
        return str(prefix) + str(name)
    
    def _get_backend(self, uid):
        return '127.0.0.1'

    def _update_counter(self, category):
        log_debug('Manger', '_update_counter->category=%s' % str(category))
        try:
            coll = self._get_collection(TABLE_COUNTER)
            res = coll.find_and_modify({'cat': category}, {'$inc':{'cnt':1}}, upsert=True)
            log_debug('Manger', '_update_counter->res=%s' %str(res))
            if not res:
                return 0
            else:
                return res.get('cnt')
        except:
             log_err('Manger', 'failed to update counter')
    
    def upload(self, uid, category, package, title, description):
        if self._hidden:
            return
        log_debug('Manger', 'upload->category=%s, package=%s' % (str(category), str(package)))
        try:
            if not category or not package or not description:
                log_err('Manger', 'failed to upload, invalid arguments')
                return
            t = str(datetime.utcnow())
            cnt = self._update_counter(category)
            rank = cnt / PAGE_SIZE
            table = self._get_table(TABLE_CAT, category)
            coll = self._get_collection(table)
            coll.update({'rank':rank}, {'$addToSet':{'packages':{'pkg':package, 't':t}}}, upsert=True)
            coll = self._get_collection(TABLE_DESCRIPTION)
            coll.update({'pkg':package}, {'pkg':package,'title':title, 'des':description}, upsert=True)
            coll = self._get_collection(TABLE_PACKAGE)
            coll.update({'pkg':package}, {'pkg':package,'cat':category,'t':t}, upsert=True)
            coll = self._get_collection(TABLE_AUTHOR)
            coll.update({'uid':uid}, {'$set':{package:''}}, upsert=True)
            return True
        except:
             log_err('Manger', 'failed to upload')
    
    def install(self, uid, package, version, typ):
        log_debug('Manger', 'install->package=%s' %str(package))
        addr = self._get_backend(uid)
        rpcclient = RPCClient(addr, BACKEND_PORT)
        info = rpcclient.request('install', uid=uid, package=package, version=version, typ=typ)
        log_debug('Manger', 'install->info=%s' %str(info))
        if not info:
            return
        try:
            coll = self._get_collection(TABLE_INSTALL)
            res = coll.find_and_modify({'pkg': package}, {'$inc':{'cnt':1}}, upsert=True)
            if not res:
                cnt = 1
            else:
                cnt = res.get('cnt')
                if cnt != None:
                    cnt += 1
                if not cnt:
                    log_err('Manger', 'failed to install, invalid counter')
                    return
            coll = self._get_collection(TABLE_PACKAGE)
            res = coll.find_one({'pkg':package})
            if not res:
                log_err('Manger', 'failed to install, cannot get package')
                return
            category = res.get('cat')
            if not category:
                log_err('Manger', 'failed to install, cannot get category')
                return
            table = self._get_table(TABLE_TOP, category)
            coll = self._get_collection(table)
            res = coll.find_one({'name':TOP_NAME})
            if not res or len(res) < TOP + 2:
                coll.update({'name':TOP_NAME},  {'$set':{package:cnt}}, upsert=True)  
            else:
                del res['name']
                del res['_id']
                if package not in res:
                    for i in res:
                        if res[i] < cnt:
                            coll.update({'name':TOP_NAME}, {'$unset':{i:''}})
                            coll.update({'name':TOP_NAME},  {'$set':{package:cnt}}, upsert=True)
                            break
                    return True
                else:
                    coll.update({'name':TOP_NAME},  {'$set':{package:cnt}})
        except:
            log_err('Manger', 'failed to install')
        finally:
            return info
    
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
                    addr = self._get_backend(uid)
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
            addr = self._get_backend(uid)
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
    
    def uninstall(self, uid, package):
        try:
            addr = self._get_backend(uid)
            rpcclient = RPCClient(addr, BACKEND_PORT)
            res = rpcclient.request('uninstall', uid=uid, package=package, typ=APP)
            if res:
                log_debug('Manger', 'uninstall->res=%s' %str(res))
                return res
        except:
            log_err('Manger', 'failed to uninstall')
    
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
            cnt, auth, title = self._get_package_detail(pkg)
            item = {'pkg':pkg, 'title':title, 'auth':auth, 'cnt':cnt}
            res.append(item)
        if res:
            return self._dump(res)
    
    def get_packages_details(self, category, rank):
        log_debug('Manger', 'get_packages_details starts')
        info = self._get_packages(category, rank)
        res = []
        for i in info:
            cnt, auth, title = self._get_package_detail(i)
            item = {'pkg':i, 'title':title, 'auth':auth, 'cnt':cnt}
            res.append(item)
        if res:
            return self._dump(res)
    
    def _get_package_detail(self, package, check_inst=True):
        try:
            cnt = None
            if check_inst:
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
        addr = self._get_backend(uid)
        rpcclient = RPCClient(addr, BACKEND_PORT)
        res = rpcclient.request('has_package', uid=uid, package=package, typ=APP)
        if res:
            return True
        return False
    
def main():
    s = zerorpc.Server(Manger())
    s.bind("tcp://%s:%d" % (MANAGER_ADDR, MANAGER_PORT))
    s.run()
