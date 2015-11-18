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

from datetime import datetime
from lib.util import localhost
from pymongo import MongoClient
from lib.log import log_debug, log_err
from component.rpcserver import RPCServer
from conf.config import RECORDER_PORT, RECORDER_DB, MONGO_PORT

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

class Recorder(RPCServer):
    def __init__(self, addr, port, hidden=False):
        RPCServer.__init__(self, addr, port)
        self._hidden = hidden
        self._client =  MongoClient(RECORDER_DB, MONGO_PORT)
    
    def _get_collection(self, name):
        return self._client.test[name]
    
    def _get_table(self, prefix, name):
        return str(prefix) + str(name)
    
    def _update_counter(self, category):
        log_debug('Recorder', '_update_counter->category=%s' % str(category))
        try:
            coll = self._get_collection(TABLE_COUNTER)
            res = coll.find_and_modify({'cat': category}, {'$inc':{'cnt':1}}, upsert=True)
            log_debug('Recorder', '_update_counter->res=%s' %str(res))
            if not res:
                return 0
            else:
                return res.get('cnt')
        except:
             log_err('Recorder', 'failed to update counter')
    
    def upload(self, uid, category, package, title, description):
        if self._hidden:
            return
        log_debug('Recorder', 'upload->category=%s, package=%s' % (str(category), str(package)))
        try:
            if not category or not package or not description:
                log_err('Recorder', 'failed to upload, invalid arguments')
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
             log_err('Recorder', 'failed to upload')
    
    def install(self, package):
        log_debug('Recorder', 'install->package=%s' %str(package))
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
                    return True
                else:
                    coll.update({'name':TOP_NAME},  {'$set':{package:cnt}})
                    return True
        except:
            log_err('Manger', 'failed to install')
    
def main():
    recorder = Recorder(localhost(), RECORDER_PORT)
    recorder.run()