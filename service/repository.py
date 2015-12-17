#      repository.py
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
import time
from threading import Lock
from lib.util import localhost
from lib.db import Database
from threading import Thread
from hash_ring import HashRing
from lib.log import log_debug, log_err
from component.rpcserver import RPCServer
from conf.config import REPOSITORY_PORT, REPO_DB, UPLOAD_SERVERS, SHOW_TIME, DEBUG, HDFS, REPOSITORY_SERVERS

if SHOW_TIME:
    from datetime import datetime

if HDFS:
    from conf.config import HDFS_PORT
    from component.hdfsclient import HDFSClient
else:
    from conf.config import FTP_PORT
    from component.ftpclient import FTPClient
    from component.ftpserver import FTPServer

LOCK_MAX = 1024

class Repository(RPCServer):
    def __init__(self, addr, port):
        RPCServer.__init__(self, addr, port)
        len_up = len(UPLOAD_SERVERS)
        len_repo = len(REPOSITORY_SERVERS)
        if len_up < len_repo or len_up % len_repo != 0:
            log_err('Repository', 'failed to initialize')
            raise Exception('failed to initialize')
        addr = localhost()
        if addr not in REPOSITORY_SERVERS:
            log_err('Repository', 'failed to initialize')
            raise Exception('failed to initialize REPOSITORY_SERVERS')
        for i in range(len(REPOSITORY_SERVERS)):
            if  addr == REPOSITORY_SERVERS[i]:
                break
        total = len_up / len_repo 
        self._upload_servers = UPLOAD_SERVERS[i * total:(i + 1) * total]
        log_debug('Repository', 'upload_servers=%s' % str(self._upload_servers))
        if HDFS:
            self._port = HDFS_PORT
            self._client = HDFSClient()
        else:
            self._port = FTP_PORT
            self._client = FTPClient()
            self._server = FTPServer()
        if REPO_DB:
            self._db = Database(addr=REPO_DB)
        else:
            self._db = Database(addr=addr)
        locks = []
        for _ in range(LOCK_MAX):
            locks.append(Lock())
        self._locks = HashRing(locks)
        if DEBUG:
            self._upload_cnt = 0
            self._download_cnt = 0
    
    def _get_addr(self, package):
        ring = HashRing(self._upload_servers)
        addr = ring.get_node(package)
        return addr
    
    def _get_lock(self, package):
        return self._locks.get_node(package)
    
    def _upload(self, package, version, buf):
        addr = self._get_addr(package)
        return self._client.upload(addr, self._port, package, version, buf)
    
    def upload(self, uid, package, version, buf):
        lock = self._get_lock(package)
        lock.acquire()
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            owner, ver = self._db.get_version(package)
            if owner and owner != uid:
                log_err('Repository', 'failed to upload, invalid owner, package=%s, version=%s' % (str(package), str(version)))
                return False
            if ver == version:#The version of package has been uploaded.
                log_err('Repository', 'failed to upload, invalid version, package=%s, version=%s' % (str(package), str(version)))
                return False
            else:
                ret = self._upload(package, version, buf)
                if not ret:
                    log_err('Repository', 'failed to upload, cannot upload %s-%s to hdfs' % (str(package), str(version)))
                    return
                self._db.set_package(uid, package, version, '')
                if not ver or ver < version:
                    self._db.set_version(uid, package, version)
                #log_debug('Repository', 'finished uploading, package=%s, version=%s' % (str(package), str(version)))
                if DEBUG:
                    self._upload_cnt += 1
                    log_debug('Repository', 'upload, count=%d' % self._upload_cnt)
                if SHOW_TIME:
                    log_debug('Repository', 'upload, time=%d sec' % (datetime.utcnow() - start_time).seconds)
                return True
        finally:
            lock.release()
    
    def download(self, package, version):
        #log_debug('Repository', 'start to download, package=%s, version=%s' % (str(package), str(version)))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            addr = self._get_addr(package)
            uid, ver = self._db.get_version(package)
            if not version:
                version = ver
            if not self._db.has_package(uid, package, version):
                log_err('Repository', 'failed to download, invalid version, package=%s, version=%s' % (str(package), str(version)))
                return
            if DEBUG:
                self._download_cnt += 1
                log_debug('Repository', 'download, count=%d' % self._download_cnt)
            if SHOW_TIME:
                log_debug('Repository', 'download, time=%d sec' % (datetime.utcnow() - start_time).seconds)            
            return self._client.download(addr, self._port, package, version)
        except:
            log_err('Repository', 'failed to download')
    
    def version(self, package):
        log_debug('Repository', 'start to get version, uid=%s, package=%s' % (str(uid), str(package)))
        _, ver = self._db.get_version(package)
        return ver
    
    def start(self):
        t = Thread(target=self.run)
        t.start()
        if not HDFS:
            self._server.run()
        t.join()

def main():
    repo = Repository(localhost(), REPOSITORY_PORT)
    repo.start()
