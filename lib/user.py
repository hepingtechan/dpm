#      user.py
#      
#      Copyright (C) 2015 Xu Tian <tianxu@iscas.ac.cn>
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
from lib.log import log_debug, log_err
from pymongo import MongoClient
from conf.path import PATH_SHELVEDB

COLLECTION = 'userdb'
ADDR = ('127.0.0.1', 27017)

class User(object):
    def _get_addr(self):
        return ADDR
    
    def _get_collection(self):
        addr, port = self._get_addr()
        client = MongoClient(addr, port)
        return client.test[COLLECTION]
    
    def get_public_key(self, user):
        log_debug('User', 'get_public_key->user=%s' % str(user))
        coll = self._get_collection()
        res = coll.find_one({'user': user})
        if res:
            return (res.get('uid'), res.get('pubkey'))
        
    def get_private_key(self, uid):
        log_debug('User', 'get_private_key->uid=%s' % str(uid))
        coll = self._get_collection()
        res = coll.find_one({'uid': uid})
        if res:
            return res.get('privkey')
    
    def get_password(self, user):
        log_debug('User', 'get_password->user=%s' % str(user))
        coll = self._get_collection()
        res = coll.find_one({'user': user})
        if res:
            return res.get('password')
        
    def get_name(self, uid):
        log_debug('User', 'get_name->uid=%s' % str(uid))
        coll = self._get_collection()
        res = coll.find_one({'uid': uid})
        if res:
            return res.get('user')
    