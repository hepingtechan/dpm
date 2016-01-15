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
from lib.util import show_info, show_error
from conf.config import MONGO_PORT, DB_SERVERS, SHOW_TIME

if SHOW_TIME:
    from datetime import datetime

PRINT = False
RETRY_MAX = 3
CACHE_MAX = 4096
TABLE_USERINFO = 'userdb'

class User(object):
    def __init__(self):
        self._clients = []
        self._private_keys = {}
        self._public_keys = {}
        for i in DB_SERVERS:
            self._clients.append(MongoClient(i, MONGO_PORT).test) 
    
    def _print(self, text):
        if PRINT:
            show_info(self, text)
    
    def _get_collection(self, uid, table):
        ring = HashRing([i for i in range(len(DB_SERVERS))])
        cli = self._clients[ring.get_node(uid)]
        return cli[table]
    
    def _generate_key(self):
        self._print('generate_key starts')
        try:
            pubkey = None
            privkey = None
            for _ in range(RETRY_MAX):
                try:
                    pubkey, privkey = rsa.newkeys(512)
                    break
                except:
                    pass
            if pubkey and privkey:
                pub = pubkey.save_pkcs1()
                priv = privkey.save_pkcs1()
                return (pub, priv)
        except:
            show_error(self, 'failed to generate key')
            
    def get_public_key(self, user):
        self._print('get_public_key->user=%s' % str(user))
        try:
            uid = get_uid(user)
            key = self._public_keys.get(uid)
            if not key:
                coll = self._get_collection(uid, TABLE_USERINFO)
                res = coll.find_one({'user': user}, {'pubkey':1, '_id':0})
                key = res.get('pubkey')
                if key:
                    if len(self._public_keys) >= CACHE_MAX:
                        self._public_keys.popitem()
                    self._public_keys.update({uid:key})
            return (uid, key)
        except:
            show_error(self, 'failed to get public key')
        
    def get_private_key(self, uid):
        self._print('get_private_key->uid=%s' % str(uid))
        try:
            key = self._private_keys.get(uid)
            if not key:
                coll = self._get_collection(uid, TABLE_USERINFO)
                res = coll.find_one({'uid': uid}, {'privkey':1, '_id':0})
                key = res.get('privkey')
                if key:
                    if len(self._private_keys) >= CACHE_MAX:
                        self._private_keys.popitem()
                    self._private_keys.update({uid:key})
            return key
        except:
            show_error(self, 'failed to get private key')
    
    def get_password(self, user):
        self._print('get_password->user=%s' % str(user))
        try:
            uid = get_uid(user)
            coll = self._get_collection(uid, TABLE_USERINFO)
            res = coll.find_one({'user': user}, {'password':1, '_id':0})
            if res:
                return res.get('password')
        except:
            show_error(self, 'failed to get password')
        
    def get_name(self, uid):
        self._print('get_name->uid=%s' % str(uid))
        try:
            coll = self._get_collection(uid, TABLE_USERINFO)
            res = coll.find_one({'uid': uid}, {'user':1, '_id':0})
            if res:
                return res.get('user')
        except:
            show_error(self, 'failed to get name')
    
    def add(self, user, pwd, email):
        self._print('add starts, add->user=%s, pwd=%s, email=%s' % (str(user), str(pwd), str(email)))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            uid = get_uid(user)
            coll = self._get_collection(uid, TABLE_USERINFO)
            res = coll.find_one({'user':user}, {'uid':1, '_id':0})
            if res:
                show_error(self, 'failed to register, invalid user, the user has been registered')
                return
            pubkey, privkey = self._generate_key()
            info = coll.save({'user':user, 'password':pwd, 'email':email, 'uid':uid, 'pubkey':pubkey, 'privkey':privkey})
            if not info:
                show_error(self, 'failed to register, failed to save user info')
                return
            if SHOW_TIME:
                self._print('add, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            return uid
        except:
            show_error(self, 'failed to register, invalid register information')
    
    def remove(self, user):
        self._print('remove starts')
        try:
            uid = get_uid(user)
            coll = self._get_collection(uid, TABLE_USERINFO)
            res = coll.find_one({'user':user}, {'uid':1})
            if res:
                coll.remove(res['_id'])
                return True
        except:
            show_error(self, 'failed to get public key')
    