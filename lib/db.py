#      db.py
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
import shelve
from pymongo import MongoClient
from conf.path import PATH_SHELVEDB
from conf.config import MONGO_PORT
from lib.util import show_class, show_error

PRINT = False
TABLE_VERSION = 'pkgversion'
TABLE_PACKAGE = 'pkgcontent'

class MongoDB(object):
    def __init__(self, addr, domain=None):
        if domain:
            self._domain = domain
        else:
            self._domain = ''
        self._addr = addr
    
    def _print(self, text):
        if PRINT:
            show_class(self, text)
    
    def _get_table(self, table):
        if self._domain:
            return table + "_"  + self._domain
        else:
            return table
    
    def _get_collection(self, table):
        name = self._get_table(table)
        client = MongoClient(self._addr , MONGO_PORT)
        return client.test[name]

    def has_version(self, uid, package, version, table):
        self._print('has_version->uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
        if not version:
            show_error(self, 'failed to has version, the %s has no %s version' % (str(package), str(version)))
            return
        coll = self._get_collection(table)
        res = coll.find_one({'package': package}, {'uid': 1, 'version': 1, '_id': 0})
        if res and res.get('uid') == uid and res.get('version') == version:
            return True
    
    def get_version(self, package, table):
        self._print('get_version->package=%s' % str(package))
        coll = self._get_collection(table)
        res = coll.find_one({'package': package}, {'uid': 1, 'version': 1, '_id': 0})
        if res:
            return (res.get('uid'), res.get('version'))
        return (None, None)
    
    def set_version(self, uid, package, version, table):
        self._print('set_version->uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
        coll = self._get_collection(table)
        res = coll.find_one({'package': package}, {'uid': 1, '_id': 0})
        if res:
            if res.get('uid') == uid:
                coll.update({'package':package}, {'$set': {'version': version}}, upsert=True)
        else:
            coll.save({'uid':uid, 'package':package, 'version':version})
    
    def has_package(self, uid, package, version, table):
        self._print('has_package->uid=%s, version=%s, package=%s' % (str(uid), str(version), str(package)))
        coll = self._get_collection(table)
        res = coll.find_one({'uid': uid}, {'_id':0})
        if res and res.has_key('package'):
            if res['package'].has_key(package):
                if version:
                    versions = res['package'][package]
                    for i in versions:
                        if i['version'] == version:
                            return True
                else:
                    return True
    
    def get_package(self, uid, package, version, table):
        self._print('get_package->uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
        coll = self._get_collection(table)
        res = coll.find_one({'uid': uid}, {'_id':0})
        if res and res.has_key('package'):
            if res['package'].has_key(package):
                versions = res['package'][package]
                if not versions:
                    show_error(self, 'failed to get package, invalid versions')
                    return
                item = None
                if not version:
                    item = versions[0]
                else:
                    for i in versions:
                        if i['version'] == version:
                            item = i
                            break
                if item:
                    return (item['version'], item['output'])
    
    def set_package(self, uid, package, version, output, table):
        self._print('set_package->uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
        coll = self._get_collection(table)
        res = coll.find_one({'uid': uid}, {'uid':0, '_id':0})
        if res and res.has_key('package') and  res['package'].has_key(package):
            versions = res['package'][package]
            for item in versions:
                if item['version'] == version:
                    show_error(self, 'failed to set package, invalid version, uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
                    return
            coll.update({'uid':uid}, {'$addToSet': {'package.%s' % package: {'version':version, 'output':output}}}, upsert=True)
        else:
            if not res:
                coll.save({'uid':uid, 'package':{package: [{'version':version, 'output':output}]}})
            else:
                coll.update({'uid':uid}, {'$set': {'package.%s' % package:[{'version':version, 'output':output}]}}, upsert=True)
    
    def rm_package(self, uid, package, version, table):
        self._print('rm_package->uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
        coll = self._get_collection(table)
        res = coll.find_one({'uid': uid}, {'uid':0, '_id':0})
        if res and res.has_key('package') and res['package'].has_key(package):
            coll.update({'uid':uid}, {'$pull':{'package.%s' % package:{'version':version}}}, upsert=True)
            if 1 == len(res['package'][package]):
                coll.update({'uid':uid}, {'$unset':{'package.%s' % package:''}}, upsert=True)
    
    def get_packages(self, uid, table):
        self._print('get_packages->uid=%s' % str(uid))
        coll = self._get_collection(table)
        res = coll.find_one({'uid': uid}, {'_id':0})
        if res and res.has_key('package'):
            return res['package'].keys()
        

class ShelveDB(object):
    def __init__(self, domain=None):
        if domain:
            self._path = os.path.join(PATH_SHELVEDB, domain)
        else:
            self._path = PATH_SHELVEDB
        if not os.path.exists(self._path):
            os.makedirs(self._path, 0o755)
    
    def _print(self, text):
        if PRINT:
            show_class(self, text)
    
    def _get_path(self, table):
        return os.path.join(self._path, table)
    
    def has_version(self, uid, package, version, table):
        self._print('has_version->uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
        path = self._get_path(table)
        info = shelve.open(path)
        try:
            if not info:
                show_error(self, 'failed to has version, invalid information, package=%s, version=%s' % (str(package), str(version)))
                return
            if info.has_key(uid) and info[uid].has_key(package) and info[uid][package] == version:
                return True
        finally:
            info.close()
    
    def get_version(self, package, table):
        self._print('get_version->package=%s' % str(package))
        path = self._get_path(table)
        info = shelve.open(path)
        try:
            if info:
                for i in info:
                    if info[i].has_key(package):
                        return (i, info[i][package])
            return (None, None)
        finally:
            info.close()
    
    def set_version(self, uid, package, version, table):
         self._print('set_version->uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
         path = self._get_path(table)
         info = shelve.open(path, writeback=True)
         try:
            if info.has_key(uid):
                if info[uid].has_key(package):
                    info[uid][package] = version
                else:
                    info[uid].update({package: version})
            else:
                info[uid] = {package: version}
         finally:
            info.close()
    
    def has_package(self, uid, package, version, table):
        self._print('has_package->uid=%s, version=%s, package=%s' % (str(uid), str(version), str(package)))
        path = self._get_path(table)
        info = shelve.open(path)
        try:
            if info and info.has_key(uid) and info[uid].has_key(package):
                if version:
                    return info[uid][package].has_key(version)
                else:
                    return True
        finally:
            info.close()
    
    def get_package(self, uid, package, version, table):
        self._print('get_package->uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
        path = self._get_path(table)
        info = shelve.open(path)
        try:
            if info and info.has_key(uid) and info[uid].has_key(package):
                if not version:
                    keys = info[uid][package].keys()
                    if keys:
                        version = keys[0]
                if version:
                    return (version, info[uid][package].get(version))
            return (None, None)
        finally:
            info.close()
    
    def set_package(self, uid, package, version, buf, table):
         self._print('set_package->uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
         path = self._get_path(table)
         info = shelve.open(path, writeback=True)
         try:
            if info.has_key(uid):
                if info[uid].has_key(package):
                    info[uid][package].update({version: buf})
                else:
                    info[uid].update( {package: {version: buf}})
            else:
                info[uid] = {package: {version: buf}}
         finally:
            info.close()

    def rm_package(self, uid, package, version, table):
        self._print('rm_package->uid=%s, package=%s, version=%s' % (str(uid), str(package), str(version)))
        path = self._get_path(table)
        info = shelve.open(path, writeback=True)
        try:
            if info.has_key(uid) and info[uid].has_key(package):
                if version and info[uid][package].has_key(version):
                    del info[uid][package][version]
                    if not info[uid][package]:
                        del info[uid][package]
                else:
                    del info[uid][package]
        finally:
            info.close()
    
    def get_packages(self, uid, table):
        self._print('get_packages->uid=%s' % str(uid))
        path = self._get_path(table)
        info = shelve.open(path, writeback=True)
        try:
            if info.has_key(uid):
                return info[uid].keys()
        finally:
            info.close()
    
class Database(object):
    def __init__(self, addr=None, domain=None):
        if not addr:
            self._db = ShelveDB(domain)
        else:
            self._db = MongoDB(addr, domain)
    
    def has_version(self, uid, package, version, table=TABLE_VERSION):
        return self._db.has_version(uid, package, version, table)
    
    def get_version(self, package, table=TABLE_VERSION):
        return self._db.get_version(package, table)
    
    def set_version(self, uid, package, version, table=TABLE_VERSION):
        self._db.set_version(uid, package, version, table)
    
    def has_package(self, uid, package, version=None, table=TABLE_PACKAGE):
        return self._db.has_package(uid, package, version, table)
    
    def get_package(self, uid, package, version, table=TABLE_PACKAGE):
        return self._db.get_package(uid, package, version, table)
    
    def set_package(self, uid, package, version, buf, table=TABLE_PACKAGE):
        self._db.set_package(uid, package, version, buf, table)
    
    def rm_package(self, uid, package, version, table=TABLE_PACKAGE):
        self._db.rm_package(uid, package, version, table)
    
    def get_packages(self, uid, table=TABLE_PACKAGE):
        return self._db.get_packages(uid, table)
    