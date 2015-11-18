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
from lib.util import APP, localhost
from pymongo import MongoClient
from lib.log import log_debug, log_err
from component.rpcclient import RPCClient
from component.rpcserver import RPCServer
from conf.config import ALLOC_DB, MONGO_PORT, ALLOCATOR_PORT, DEBUG

CACHE_MAX = 4096
INST_SEARCH_FACTOR = 3

TABLE_INST_TOTAL = 'insttotal'
TABLE_INST_ALLOC = 'installoc'
TABLE_INST_ADDR = 'instaddr'
TABLE_INST_USER = 'instuser'

class Allocator(RPCServer):
    def __init__(self, addr, port, hidden=False):
        RPCServer.__init__(self, addr, port)
        self._cache = {}
        self._hidden = hidden
        self._client =  MongoClient(ALLOC_DB, MONGO_PORT)
        if DEBUG:
            self._alloc_cnt = 0
        
    def _get_collection(self, name):
        return self._client.test[name]
    
    def add_installer(self, addr):
        if self._hidden:
            return
        log_debug('Allocator', 'add_installer starts!')
        try:
            coll = self._get_collection(TABLE_INST_ADDR)
            info = coll.find_one({'addr':addr})
            if info:
                log_err('Allocator', 'failed to add installer, the address has been added')
                return
            if len(addr.split('.')) != 4:
                log_err('Allocator', 'failed to add installer, invalid installer address')
                return
            coll = self._get_collection(TABLE_INST_TOTAL)
            coll.find_and_modify({}, {'$inc':{'cnt':1}}, upsert=True)
            res = coll.find_one({})
            if not res:
                log_err('Allocator', 'failed to add installer, invalid installer total number table')
                return
            inst = res.get('cnt')
            print '11', inst
            coll = self._get_collection(TABLE_INST_ALLOC)
            coll.save({'_id':inst, 'count':0})
            print '11-1'
            coll = self._get_collection(TABLE_INST_ADDR)
            coll.save({'_id':inst,'addr':addr})
            print '11-2'
            return True
        except:
             log_err('Allocator', 'failed to add installer')
        
    def alloc_installer(self, uid):
        #log_debug('Allocator', 'start to allocate installer')
        try:
            coll = self._get_collection(TABLE_INST_TOTAL)
            info = coll.find_one({})
            if not info:
                log_err('Allocator', 'failed to allocate installer, invalid installer total number table')
                return
            cnt = info.get('cnt')
            #print '12->Allocator', 'allocate->cnt=%d' % cnt
            if cnt <= 0:
                log_err('Allocator', 'failed to allocate installer, invalid cnt')
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
            #log_debug('12-1->Allocator', 'allocate -> candidates=%s, len(candidates)=%d' % (str(candidates), len(candidates)))
            
            coll = self._get_collection(TABLE_INST_ALLOC)
            result = coll.find({'_id':{'$in':candidates}})
            best = result[0].get('count')
            #print '13->Allocator', 'allocate->best=%d' % best
            inst = result[0].get('_id')
            #print '13-1', inst
            for item in result:
                #print '14->Allocator', 'allocate, result->item=%s' % str(item)
                cnt = item.get('count')
                #print '14-1', cnt
                if best > cnt:
                    inst = item.get('_id')
                    best = cnt
            #print '15->Allocator', 'allocate, result->id=%d' % inst
            
            info = coll.find_and_modify({'_id':inst}, {'$inc':{'count':1}}, upsert=True)
            if not info:
                log_err('Allocator', 'failed to allocate installer, cannot update inst_alloc table')
                return
            
            coll = self._get_collection(TABLE_INST_ADDR)
            result = coll.find_one({'_id':inst})
            #print '17->Allocator', 'allocate->result=%s' % str(result)
            if not result:
                log_err('Allocator', 'failed to allocate installer, cannot get addr table')
                return
            addr = result.get('addr')
            #print '18->Allocator', 'allocate->uid=%s, addr=%s' % (str(uid), str(addr))
            coll = self._get_collection(TABLE_INST_USER)
            info = coll.save({'user':uid, 'addr':addr})
            if not info:
                log_err('Allocator', 'failed to allocate installer, cannot save inst_user table')
                return
            if DEBUG:
                self._alloc_cnt += 1
                log_debug('Allocator', 'alloc_installer-->count=%d' % self._alloc_cnt)
            return True
        except:
            log_err('Allocator', 'failed to allocate installer')
    
    def get_installer(self, uid):
        log_debug('Allocator', 'start to get installer, uid=%s' % str(uid))
        try:
            cache = self._cache
            print '1 find', cache
            addr = cache.get(uid)
            print '2, find', addr
            if addr:
                return addr
            else:
                coll = self._get_collection(TABLE_INST_USER)
                info = coll.find_one({'user':uid})
                if not info:
                    log_err('Allocator', 'failed to get installer,  no info')
                    return
                addr = info.get('addr')
                if len(cache) >= CACHE_MAX:
                    cache.popitem()
                print '3 find', cache,'##', addr
                cache.update({uid:addr})
                print '4 find', cache,'##', addr
                return addr
        except:
            log_err('Allocator', 'failed to get installer')

def main():
    allocator = Allocator(localhost(), ALLOCATOR_PORT)
    allocator.run()
