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
from pymongo import MongoClient
from lib.log import log_debug, log_err
from component.rpcserver import RPCServer
from conf.config import RECORDER_PORT, RECORDERDB_SERVERS, MONGO_PORT, CATEGORYDB_SERVERS, CATEGORIES, SHOW_TIME, DEBUG

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

if SHOW_TIME:
    from datetime import datetime

class RecorderServer(object):
    def __init__(self):
        names = [TABLE_INSTALL, TABLE_AUTHOR, TABLE_COUNTER, TABLE_PACKAGE, TABLE_DESCRIPTION]
        if len(RECORDERDB_SERVERS) != len(names):
            log_err('RecorderServer', 'failed to initialize Recorder')
            raise Exception('failed to initialize Recorder')
        self._cat = {}
        cnt = 0
        for i in CATEGORIES:
            self._cat.update({CATEGORIES[i]:MongoClient(CATEGORYDB_SERVERS[cnt], MONGO_PORT).test})
            cnt += 1
        self._clients = {}
        for i in range(len(names)):
            name = names[i]
            self._clients.update({name:MongoClient(RECORDERDB_SERVERS[i], MONGO_PORT).test[name]})
        if DEBUG:
            self._upload_cnt = 0
    
    def get_collection(self, table, category=None):
        log_debug('RecorderServer', 'get_collection starts, table=%s, category=%s' % (str(table), str(category)))
        if category:
            cli = self._cat.get(category)
            if not cli:
                log_err('RecorderServer', 'failed to get collection, invalid category')
                return
            return cli["%s_%s" % (table, str(category))]
        else:
            cli = self._clients.get(table)
            if not cli:
                log_err('RecorderServer', 'failed to get collection')
                return
            return cli
    
    def get_categories(self):
        return CATEGORIES
    
    def _get_packages(self, category, rank):
        log_debug('RecorderServer', 'get_packages starts')
        try:
            result = []
            coll = self.get_collection(TABLE_CAT, category)
            res = coll.find_one({'rank':rank})
            if res.has_key('packages'): 
                for item in res['packages']:
                    result.append(str(item['pkg']))
            return result
        except:
            log_err('RecorderServer', 'get_packages failed')
    
    def get_packages(self, category, rank):
        log_debug('RecorderServer', 'get_packages starts')
        try:
            return self._get_packages(category, rank)
        except:
            log_err('RecorderServer', 'get_packages failed')
       
    def get_descripton(self, package):
        log_debug('RecorderServer', 'get_descripton starts, package=%s' %str(package))
        try:
            coll = self.get_collection(TABLE_DESCRIPTION)
            res = coll.find_one({'pkg':package})
            if res:
                return (str(res['title']), str(res['des']))
            else:
                log_debug('RecorderServer', 'get_descripton, cannot find description, package=%s' % str(package))
        except:
             log_err('RecorderServer', 'get_descripton failed')
    
    def get_inst(self, package):
        log_debug('RecorderServer', 'get_inst start, package=%s' %str(package))
        try:
            coll = self.get_collection(TABLE_INSTALL)
            res = coll.find_one({'pkg':package})
            if res:
                return str(res['cnt'])
        except:
             log_err('RecorderServer', 'get_inst failed')
    
    def get_uid(self, package):
        log_debug('RecorderServer', 'get_uid starts, package=%s' %str(package))
        try:
            coll = self.get_collection(TABLE_AUTHOR)
            res = coll.find_one({package:''})
            if res:
                return res.get('uid')
        except:
             log_err('RecorderServer', 'get_uid failed')
    
    def get_package_detail(self, package):
        log_debug('RecorderServer', 'get_package_detail starts, package=%s' % str(package))
        try:
            cnt = self.get_inst(package)
            if not cnt:
                cnt = str(0)
            title, _ = self.get_descripton(package)
            if not title:
                log_err('RecorderServer', 'get_package_detail failed, cannot find title')
                return
            return (cnt, title)
        except:
            log_err('RecorderServer', 'get_package_detail failed')
    
    def get_packages_details(self, category, rank):
        log_debug('RecorderServer', 'get_packages_details starts')
        try:
            info = self._get_packages(category, rank)
            res = []
            for i in info:
                cnt, title = self.get_package_detail(i)
                item = {'pkg':i, 'title':title, 'cnt':cnt}
                res.append(item)
            return res
        except:
            log_err('RecorderServer', 'get_packages_details failed')
    
    def _get_top(self, category):
        result = []
        coll = self.get_collection(TABLE_TOP, category)
        res = coll.find_one({'name':TOP_NAME})
        if res:
            del res['name']
            del res['_id']
            for i in res:
                result.append({str(i):str(res[i])})
        return result
    
    def get_top(self, category):
        log_debug('RecorderServer', 'get_top starts, category=%s' %str(category))
        try:
            return self._get_top(category)
        except:
             log_err('RecorderServer', 'get_top failed')
    
    def get_top_details(self, category):
        log_debug('RecorderServer', 'get_top_details starts, category=%s' % str(category))
        try:
            info = self._get_top(category)
            res = []
            for i in info:
                pkg = i.keys()[0]
                cnt, title = self.get_package_detail(pkg)
                item = {'pkg':pkg, 'title':title, 'cnt':cnt}
                res.append(item)
            return res
        except:
            log_err('RecorderServer', 'get_top_details failed')
    
    def get_counter(self, category):
        log_debug('RecorderServer', 'get_counter starts, category=%s' % str(category))
        try:
            coll = self.get_collection(TABLE_COUNTER)
            res = coll.find_one({'cat': category})
            log_debug('RecorderServer', 'get_counter->res=%s' %str(res))
            if not res:
                return str(0)
            else:
                return str(res.get('cnt'))
        except:
             log_err('RecorderServer', 'get_counter failed')

class Recorder(RPCServer, RecorderServer):
    def __init__(self, addr, port):
        RPCServer.__init__(self, addr, port)
        RecorderServer.__init__(self)
    
    def _update_counter(self, category):
        log_debug('Recorder', 'update_counter->category=%s' % str(category))
        try:
            coll = self.get_collection(TABLE_COUNTER)
            res = coll.find_and_modify({'cat': category}, {'$inc':{'cnt':1}}, upsert=True)
            if not res:
                return 0
            else:
                return res.get('cnt')
        except:
             log_err('Recorder', 'failed to update counter')
       
    def upload(self, uid, category, package, title, description):
        log_debug('Recorder', 'upload->category=%s, package=%s' % (str(category), str(package)))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            if not category or not package or not description:
                log_err('Recorder', 'failed to upload, invalid arguments')
                return
            t = str(datetime.utcnow())
            cnt = self._update_counter(category)
            rank = cnt / PAGE_SIZE
            coll = self.get_collection(TABLE_CAT, category)
            coll.update({'rank':rank}, {'$addToSet':{'packages':{'pkg':package, 't':t}}}, upsert=True)
            coll = self.get_collection(TABLE_DESCRIPTION)
            coll.update({'pkg':package}, {'pkg':package,'title':title, 'des':description}, upsert=True)
            coll = self.get_collection(TABLE_PACKAGE)
            coll.update({'pkg':package}, {'pkg':package,'cat':category,'t':t}, upsert=True)
            coll = self.get_collection(TABLE_AUTHOR)
            coll.update({'uid':uid}, {'$set':{package:''}}, upsert=True)
            if SHOW_TIME:
                log_debug('Recorder', 'upload, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if DEBUG:
                self._upload_cnt += 1
                log_debug('Recorder', 'upload, count=%d' % self._upload_cnt)
            return True
        except:
             log_err('Recorder', 'failed to upload')
    
    def install(self, package):
        log_debug('Recorder', 'install->package=%s' %str(package))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            coll = self.get_collection(TABLE_INSTALL)
            res = coll.find_and_modify({'pkg': package}, {'$inc':{'cnt':1}}, upsert=True)
            if not res:
                cnt = 1
            else:
                cnt = res.get('cnt')
                if cnt != None:
                    cnt += 1
                if not cnt:
                    log_err('Recorder', 'failed to install, invalid counter')
                    return
            coll = self.get_collection(TABLE_PACKAGE)
            res = coll.find_one({'pkg':package})
            if not res:
                log_err('Recorder', 'failed to install, cannot get package')
                return
            category = res.get('cat')
            if not category:
                log_err('Recorder', 'failed to install, cannot get category')
                return
            coll = self.get_collection(TABLE_TOP, category)
            res = coll.find_one({'name':TOP_NAME})
            if not res or len(res) < TOP + 2:
                coll.update({'name':TOP_NAME},  {'$set':{package:cnt}}, upsert=True)  
                return True
            else:
                del res['name']
                del res['_id']
                if package not in res:
                    for i in res:
                        if res[i] < cnt:
                            coll.update({'name':TOP_NAME}, {'$unset':{i:''}})
                            coll.update({'name':TOP_NAME},  {'$set':{package:cnt}}, upsert=True)
                            break
                    if SHOW_TIME:
                        log_debug('Recorder', 'install, time=%d sec' % (datetime.utcnow() - start_time).seconds)
                    return True
                else:
                    coll.update({'name':TOP_NAME},  {'$set':{package:cnt}})
                    if SHOW_TIME:
                        log_debug('Recorder', 'install, time=%d sec' % (datetime.utcnow() - start_time).seconds)
                    return True
        except:
            log_err('Recorder', 'failed to install')
    
def main():
    recorder = Recorder(localhost(), RECORDER_PORT)
    recorder.run()
