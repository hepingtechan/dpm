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
from hash_ring import HashRing
from pymongo import MongoClient
from conf.path import PATH_SHELVEDB
from lib.log import log_debug, log_err
from conf.config import MONGO_PORT, USERDB_SERVERS, SHOW_TIME

TABLE_USERINFO = 'userdb'

if SHOW_TIME:
    from datetime import datetime


class User(object):
    def __init__(self):
        self._clients = []
        for i in USERDB_SERVERS:
            self._clients.append(MongoClient(i, MONGO_PORT).test) 
    
    def _get_uid(self, user):
        return uuid.uuid3(uuid.NAMESPACE_DNS, user).hex
    
    def _get_collection(self, uid, table):
        ring = HashRing([i for i in range(len(USERDB_SERVERS))])
        cli = self._clients[ring.get_node(uid)]
        #print '2@2, User, get_collection-->cli=%s, uid=%s' % (str(cli), str(uid))
        return cli[table]
    
    def _generate_key(self):
        #log_debug('User', 'generate_key starts')
        try:
            pubkey, privkey = rsa.newkeys(512)
            pub = pubkey.save_pkcs1()
            priv = privkey.save_pkcs1()
            return (pub, priv)
        except:
            log_err('User', 'failed to generate key')
            
    def get_public_key(self, user):
        log_debug('User', 'get_public_key->user=%s' % str(user))
        uid = self._get_uid(user)
        coll = self._get_collection(uid, TABLE_USERINFO)
        res = coll.find_one({'user': user})
        if res:
            print '8 User->get_public_key', str(res.get('pubkey'))
            return (res.get('uid'), res.get('pubkey'))
        
    def get_private_key(self, uid):
        log_debug('User', 'get_private_key->uid=%s' % str(uid))
        coll = self._get_collection(uid, TABLE_USERINFO)
        res = coll.find_one({'uid': uid})
        if res:
            return res.get('privkey')
    
    def get_password(self, user):
        log_debug('User', 'get_password->user=%s' % str(user))
        uid = self._get_uid(user)
        coll = self._get_collection(uid, TABLE_USERINFO)
        res = coll.find_one({'user': user})
        if res:
            return res.get('password')
        
    def get_name(self, uid):
        log_debug('User', 'get_name->uid=%s' % str(uid))
        coll = self._get_collection(uid, TABLE_USERINFO)
        res = coll.find_one({'uid': uid})
        if res:
            print 'User->get_name-->usernamer=%s' %str(res.get('user'))
            return res.get('user')
    
    def add(self, user, pwd, email):
        #log_debug('User', 'add->user=%s, pwd=%s, email=%s' % (str(user), str(pwd), str(email)))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            #print '2-0'
            uid = self._get_uid(user)
            #print '2-1 User->add-->user=%s, uid=%s' % (str(user), str(uid))
            coll = self._get_collection(uid, TABLE_USERINFO)
            #print '2-2'
            res = coll.find_one({'user':user})
            #print '2-3 res=%s' % str(res)
            if res:
                log_err('############# User', 'failed to register, invalid user, the user has been registered')
                return
            pubkey, privkey = self._generate_key()
            info = coll.save({'user':user, 'password':pwd, 'email':email, 'uid':uid, 'pubkey':pubkey, 'privkey':privkey})
            if not info:
                log_err('&&&&&&&&&&&&&&&&&&  User', 'failed to register, failed to save user info')
                return
            if SHOW_TIME:
                log_debug('User', 'add, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            #print '2-4'
            return uid
        finally:
            pass
        #except:
        #    log_err('User', 'failed to register, invalid register infotmation')
    
    def remove(self, user):
        uid = self._get_uid(user)
        coll = self._get_collection(uid, TABLE_USERINFO)
        info = coll.find_one({'user':user})
        if info:
            coll.remove(info['_id'])
            return True
    