#      recorder.py
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

from lib.util import localhost
from datetime import datetime
from hash_ring import HashRing
from pymongo import MongoClient
from conf.category import CATEGORIES
from lib.util import show_class, show_error
from component.rpcserver import RPCServer
from conf.config import RECORDER_PORT, DB_SERVERS, MONGO_PORT, SHOW_TIME, DEBUG

PAGE_SIZE = 8

TABLE_TOP = 'pkgtop'
TABLE_AUTHOR = 'pkgauth'
TABLE_COUNTER = 'pkgcnt'
TABLE_CATEGORY = 'pkgcat'
TABLE_DESCRIPTION = 'pkgdesc'

TOP = 4
TOP_NAME = "top%d" % TOP

if SHOW_TIME:
    from datetime import datetime

PRINT = False

class RecorderServer(object):
    def _get_table(self, srv, table):
        return srv + '_' + table
    
    def __init__(self):
        self._ring = HashRing(DB_SERVERS)
        self._cat_coll = {}
        cnt = 0
        for i in CATEGORIES:
            self._cat_coll.update({CATEGORIES[i]:MongoClient(DB_SERVERS[cnt], MONGO_PORT).test})
            cnt += 1
        self._coll = {}
        for i in DB_SERVERS:
            name = self._get_table(i, TABLE_AUTHOR)
            self._coll.update({name:MongoClient(i, MONGO_PORT).test[TABLE_AUTHOR]})
            name = self._get_table(i, TABLE_CATEGORY)
            self._coll.update({name:MongoClient(i, MONGO_PORT).test[TABLE_CATEGORY]})
        if DEBUG:
            self._upload_cnt = 0
    
    def _print(self, text):
        if PRINT:
            show_class(self, text)
    
    def get_collection(self, table, package=None, category=None):
        self._print('get_collection starts, table=%s, category=%s' % (str(table), str(category)))
        if category:
            coll = self._cat_coll.get(category)
            if not coll:
                show_error(self, 'failed to get collection, invalid category')
                return
            return coll["%s_%s" % (table, str(category))]
        else:
            srv = self._ring.get_node(package)
            name = self._get_table(srv, table)
            coll = self._coll.get(name)
            if not coll:
                show_error(self, 'failed to get collection')
                return
            return coll
    
    def get_categories(self):
        return CATEGORIES
    
    def _get_category(self, package):
            coll = self.get_collection(TABLE_CATEGORY, package=package)
            res = coll.find_one({'pkg':package}, {'pkg':0, '_id':0})
            if res:
                return res.get('cat')
    
    def get_description(self, package):
        self._print('get_description starts, package=%s' %str(package))
        try:
            category = self._get_category(package)
            if not category:
                self._print('get_description, cannot find category, package=%s' % str(package))
                return
            coll = self.get_collection(TABLE_DESCRIPTION, category=category)
            res = coll.find_one({'pkg':package}, {'title':1, 'des':1, '_id':0})
            if res:
                return (str(res['title']), str(res['des']))
            else:
                self._print('get_description, cannot find description, package=%s' % str(package))
        except:
             show_error(self, 'get_description failed')
    
    def get_inst(self, package):
        self._print('get_inst start, package=%s' %str(package))
        try:
            category = self._get_category(package)
            if not category:
                self._print('get_inst, cannot find category, package=%s' % str(package))
                return
            coll = self.get_collection(TABLE_DESCRIPTION, category=category)
            res = coll.find_one({'pkg':package}, {'inst':1, '_id':0})
            if res:
                return str(res['inst'])
            else:
                return str(0)
        except:
             show_error(self, 'get_inst failed')
    
    def get_uid(self, package):
        self._print('get_uid starts, package=%s' %str(package))
        try:
            coll = self.get_collection(TABLE_AUTHOR, package=package)
            res = coll.find_one({'pkg':package}, {'uid':1, '_id':0})
            if res:
                return res['uid']
        except:
             show_error(self, 'get_uid failed')
    
    def get_package_detail(self, package):
        self._print('get_package_detail starts, package=%s' % str(package))
        try:
            category = self._get_category(package)
            if not category:
                self._print('get_package_detail, cannot find category, package=%s' % str(package))
                return
            coll = self.get_collection(TABLE_DESCRIPTION, category=category)
            res = coll.find_one({'pkg':package}, {'inst':1, 'title':1, '_id':0})
            if res:
                inst = res['inst']
                title = res['title']
                if not inst or not title:
                    show_error(self, 'get_package_detail failed, cannot find valid message')
                    return
                return (inst, title)
        except:
            show_error(self, 'get_package_detail failed')
    
    def get_packages_details(self, category, rank):
        self._print('get_packages_details starts')
        try:
            result = []
            if SHOW_TIME:
                start_time = datetime.utcnow()
            coll = self.get_collection(TABLE_DESCRIPTION, category=category)
            res = coll.find({'rank':rank}, {'pkg':1, 'title':1, 'inst':1, '_id':0})
            if res:
                for item in res:
                    ret = {'pkg':item['pkg'], 'title':item['title'], 'inst':item['inst']}
                    result.append(ret)
            if SHOW_TIME:
                self._print('get_packages_details , time=%d sec' % (datetime.utcnow() - start_time).seconds)
            return result
        except:
            show_error(self, 'get_packages_details failed')
    
    def _get_top(self, category):
        result = []
        coll = self.get_collection(TABLE_TOP, category=category)
        res = coll.find_one({'name':TOP_NAME}, {'name':0, '_id':0})
        if res:
            for i in res:
                result.append({str(i):str(res[i])})
            return result
    
    def get_top(self, category):
        self._print('get_top starts, category=%s' %str(category))
        try:
            return self._get_top(category)
        except:
             show_error(self, 'get_top failed')
    
    def get_top_details(self, category):
        self._print('get_top_details starts, category=%s' % str(category))
        try:
            info = self._get_top(category)
            res = []
            for i in info:
                pkg = i.keys()[0]
                inst, title = self.get_package_detail(pkg)
                item = {'pkg':pkg, 'title':title, 'inst':inst}
                res.append(item)
            return res
        except:
            show_error(self, 'get_top_details failed')
    
    def get_counter(self, category):
        self._print('get_counter starts, category=%s' % str(category))
        try:
            coll = self.get_collection(TABLE_COUNTER, category=category)
            res = coll.find_one({'cat': category}, {'cnt':1, '_id':0})
            if not res:
                return str(0)
            else:
                return str(res.get('cnt'))
        except:
             show_error(self, 'get_counter failed')

class Recorder(RPCServer, RecorderServer):
    def __init__(self, addr, port):
        RPCServer.__init__(self, addr, port)
        RecorderServer.__init__(self)
    
    def _print(self, text):
        if PRINT:
            show_class(self, text)
    
    def _update_counter(self, category):
        self._print('update_counter->category=%s' % str(category))
        try:
            coll = self.get_collection(TABLE_COUNTER, category=category)
            res = coll.find_and_modify({'cat': category}, {'$inc':{'cnt':1}}, upsert=True)
            if not res:
                return 0
            else:
                return res.get('cnt')
        except:
             show_error(self, 'failed to update counter')
       
    def upload(self, uid, category, package, title, description):
        self._print('upload->category=%s, package=%s' % (str(category), str(package)))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            if not category or not package or not description:
                show_error(self, 'failed to upload, invalid arguments')
                return
            coll = self.get_collection(TABLE_CATEGORY, package=package)
            coll.update({'pkg':package}, {'cat':category, 'pkg':package}, upsert=True)
            
            t = str(datetime.utcnow())
            cnt = self._update_counter(category)
            rank = cnt / PAGE_SIZE
            coll = self.get_collection(TABLE_DESCRIPTION, category=category)
            coll.update({'pkg':package}, {'rank':rank, 'pkg':package,'title':title, 'des':description, 'inst':0, 't':t}, upsert=True)
            
            coll = self.get_collection(TABLE_AUTHOR, package=package)
            coll.update({'uid':uid}, {'$set':{'pkg':package}}, upsert=True)
            
            if SHOW_TIME:
                self._print('upload, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if DEBUG:
                self._upload_cnt += 1
                self._print('upload, count=%d' % self._upload_cnt)
            return True
        except:
             show_error(self, 'failed to upload')
    
    def install(self, package):
        self._print('install->package=%s' %str(package))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            
            category = self._get_category(package)
            if not category:
                self._print('install, cannot find category, package=%s' % str(package))
                return
            
            coll = self.get_collection(TABLE_DESCRIPTION, category=category)
            res = coll.find_and_modify({'pkg': package}, {'$inc':{'inst':1}}, upsert=True)
            if not res:
                cnt = 1
            else:
                cnt = res.get('inst')
                if cnt != None:
                    cnt += 1
                if not cnt:
                    show_error(self, 'failed to install, invalid counter')
                    return
            coll = self.get_collection(TABLE_TOP, category=category)
            res = coll.find_one({'name':TOP_NAME}, {'name':0, '_id':0})
            if not res or len(res) < TOP:
                coll.update({'name':TOP_NAME}, {'$set':{package:cnt}}, upsert=True)  
                return True
            else:
                if package not in res:
                    for i in res:
                        if res[i] < cnt:
                            coll.update({'name':TOP_NAME}, {'$unset':{i:''}})
                            coll.update({'name':TOP_NAME},  {'$set':{package:cnt}}, upsert=True)
                            break
                    if SHOW_TIME:
                        self._print('install, time=%d sec' % (datetime.utcnow() - start_time).seconds)
                    return True
                else:
                    coll.update({'name':TOP_NAME},  {'$set':{package:cnt}})
                    if SHOW_TIME:
                        self._print('install, time=%d sec' % (datetime.utcnow() - start_time).seconds)
                    return True
        except:
            show_error(self, 'failed to install')
    
def main():
    recorder = Recorder(localhost(), RECORDER_PORT)
    recorder.run()
