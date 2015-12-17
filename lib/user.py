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
import rsa
import uuid
from lib.util import get_uid
from hash_ring import HashRing
from pymongo import MongoClient
from conf.path import PATH_SHELVEDB
from lib.log import log_debug, log_err
from conf.config import MONGO_PORT, USERDB_SERVERS, SHOW_TIME

TABLE_USERINFO = 'userdb'

if SHOW_TIME:
    from datetime import datetime

CACHE_MAX = 4096

class User(object):
    def __init__(self):
        self._clients = []
        self._private_keys = {}
        self._public_keys = {}
        for i in USERDB_SERVERS:
            self._clients.append(MongoClient(i, MONGO_PORT).test) 
    
    def _get_collection(self, uid, table):
        ring = HashRing([i for i in range(len(USERDB_SERVERS))])
        cli = self._clients[ring.get_node(uid)]
        return cli[table]
    
    def _generate_key(self):
        log_debug('User', 'generate_key starts')
        try:
            pubkey, privkey = rsa.newkeys(512)
            pub = pubkey.save_pkcs1()
            priv = privkey.save_pkcs1()
            return (pub, priv)
        except:
            log_err('User', 'failed to generate key')
            
    def get_public_key(self, user):
        log_debug('User', 'get_public_key->user=%s' % str(user))
        try:
            uid = get_uid(user)
            key = self._public_keys.get(uid)
            if not key:
                coll = self._get_collection(uid, TABLE_USERINFO)
                res = coll.find_one({'user': user})
                key = res.get('pubkey')
                if key:
                    if len(self._public_keys) >= CACHE_MAX:
                        self._public_keys.popitem()
                    self._public_keys.update({uid:key})
            return (uid, key)
        except:
            log_err('User', 'failed to get public key')
        
    def get_private_key(self, uid):
        log_debug('User', 'get_private_key->uid=%s' % str(uid))
        try:
            key = self._private_keys.get(uid)
            if not key:
                coll = self._get_collection(uid, TABLE_USERINFO)
                res = coll.find_one({'uid': uid})
                key = res.get('privkey')
                if key:
                    if len(self._private_keys) >= CACHE_MAX:
                        self._private_keys.popitem()
                    self._private_keys.update({uid:key})
            return key
        except:
            log_err('User', 'failed to get private key')
    
    def get_password(self, user):
        log_debug('User', 'get_password->user=%s' % str(user))
        try:
            uid = get_uid(user)
            coll = self._get_collection(uid, TABLE_USERINFO)
            res = coll.find_one({'user': user})
            if res:
                return res.get('password')
        except:
            log_err('User', 'failed to get password')
        
    def get_name(self, uid):
        log_debug('User', 'get_name->uid=%s' % str(uid))
        try:
            coll = self._get_collection(uid, TABLE_USERINFO)
            res = coll.find_one({'uid': uid})
            if res:
                return res.get('user')
        except:
            log_err('User', 'failed to get name')
    
    def add(self, user, pwd, email):
        log_debug('User', 'add starts, add->user=%s, pwd=%s, email=%s' % (str(user), str(pwd), str(email)))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            uid = get_uid(user)
            coll = self._get_collection(uid, TABLE_USERINFO)
            res = coll.find_one({'user':user})
            if res:
                log_err('User', 'failed to register, invalid user, the user has been registered')
                return
            pubkey, privkey = self._generate_key()
            info = coll.save({'user':user, 'password':pwd, 'email':email, 'uid':uid, 'pubkey':pubkey, 'privkey':privkey})
            if not info:
                log_err('User', 'failed to register, failed to save user info')
                return
            if SHOW_TIME:
                log_debug('User', 'add, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            return uid
        finally:
            pass
        #except:
        #    log_err('User', 'failed to register, invalid register infotmation')
    
    def remove(self, user):
        log_debug('User', 'remove starts')
        try:
            uid = get_uid(user)
            coll = self._get_collection(uid, TABLE_USERINFO)
            info = coll.find_one({'user':user})
            if info:
                coll.remove(info['_id'])
                return True
        except:
            log_err('User', 'failed to get public key')
    