#      allocator.py
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

import random
from conf.config import DEBUG
from lib.util import APP, localhost
from lib.rpcclient import RPCClient
from lib.rpcserver import RPCServer
from pymongo import MongoClient
from conf.log import LOG_ALLOCATOR
from lib.log import show_info, show_error
from conf.servers import SERVER_ALLOCDB
from conf.mongodb import MONGO_PORT
from conf.servers import ALLOCATOR_PORT

CACHE_MAX = 4096
INST_SEARCH_FACTOR = 4

TABLE_INST_TOTAL = 'insttotal'
TABLE_INST_ALLOC = 'installoc'
TABLE_INST_ADDR = 'instaddr'
TABLE_INST_USER = 'instuser'

class Allocator(RPCServer):
    def __init__(self, addr, port):
        RPCServer.__init__(self, addr, port)
        self._cache = {}
        if SERVER_ALLOCDB:
            self._client =  MongoClient(SERVER_ALLOCDB[0], MONGO_PORT)
        else:
            self._client =  MongoClient(localhost(), MONGO_PORT)
        if DEBUG:
            self._alloc_cnt = 0
    
    def _print(self, text):
        if LOG_ALLOCATOR:
            show_info(self, text)
    
    def _get_collection(self, name):
        return self._client.test[name]
    
    def add_installer(self, addr):
        self._print('add_installer starts!')
        try:
            coll = self._get_collection(TABLE_INST_ADDR)
            info = coll.find_one({'addr':addr})
            if info:
                show_error(self, 'failed to add installer, the address has been added')
                return
            if len(addr.split('.')) != 4:
                show_error(self, 'failed to add installer, invalid installer address')
                return
            coll = self._get_collection(TABLE_INST_TOTAL)
            coll.find_and_modify({}, {'$inc':{'cnt':1}}, upsert=True)
            res = coll.find_one({})
            if not res:
                show_error(self, 'failed to add installer, invalid installer total number table')
                return
            inst = res.get('cnt')
            coll = self._get_collection(TABLE_INST_ALLOC)
            coll.save({'_id':inst, 'count':0})
            coll = self._get_collection(TABLE_INST_ADDR)
            coll.save({'_id':inst,'addr':addr})
            return True
        except:
             show_error(self, 'failed to add installer')
    
    def check_installer(self, addr):
        self._print('add_installer starts!')
        try:
            coll = self._get_collection(TABLE_INST_ADDR)
            info = coll.find_one({'addr':addr})
            if info:
                return True
        except:
             show_error(self, 'have not added installer %s' % addr)
        
    def alloc_installer(self, uid):
        self._print('start to allocate installer')
        try:
            coll = self._get_collection(TABLE_INST_TOTAL)
            info = coll.find_one({})
            if not info:
                show_error(self, 'failed to allocate installer, invalid installer total number table')
                return
            cnt = info.get('cnt')
            if cnt <= 0:
                show_error(self, 'failed to allocate installer, invalid cnt')
                return
            
            candidates = []
            if cnt >= INST_SEARCH_FACTOR:
                total = INST_SEARCH_FACTOR
            else:
                total = cnt
            while len(candidates) < total:
                    i = random.randint(1, cnt)
                    if i not in candidates:
                        candidates.append(i)
                        
            coll = self._get_collection(TABLE_INST_ALLOC)
            result = coll.find({'_id':{'$in':candidates}})
            best = result[0].get('count')
            inst = result[0].get('_id')
            for item in result:
                cnt = item.get('count')
                if best > cnt:
                    inst = item.get('_id')
                    best = cnt
            
            info = coll.find_and_modify({'_id':inst}, {'$inc':{'count':1}}, upsert=True)
            if not info:
                show_error(self, 'failed to allocate installer, cannot update inst_alloc table')
                return
            
            coll = self._get_collection(TABLE_INST_ADDR)
            result = coll.find_one({'_id':inst})
            if not result:
                show_error(self, 'failed to allocate installer, cannot get addr table')
                return
            addr = result.get('addr')
            coll = self._get_collection(TABLE_INST_USER)
            info = coll.save({'user':uid, 'addr':addr})
            if not info:
                show_error(self, 'failed to allocate installer, cannot save inst_user table')
                return
            if DEBUG:
                self._alloc_cnt += 1
                self._print('alloc_installer-->count=%d' % self._alloc_cnt)
            return True
        except:
            show_error(self, 'failed to allocate installer')
    
    def get_installer(self, uid):
        self._print('start to get installer, uid=%s' % str(uid))
        try:
            cache = self._cache
            addr = cache.get(uid)
            if addr:
                return addr
            else:
                coll = self._get_collection(TABLE_INST_USER)
                info = coll.find_one({'user':uid})
                if not info:
                    show_error(self, 'failed to get installer,  no info')
                    return
                addr = info.get('addr')
                if len(cache) >= CACHE_MAX:
                    cache.popitem()
                cache.update({uid:addr})
                return addr
        except:
            show_error(self, 'failed to get installer')

def main():
    allocator = Allocator(localhost(), ALLOCATOR_PORT)
    allocator.run()
