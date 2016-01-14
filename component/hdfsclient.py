#      hdfsclient.py
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

from hdfs.client import Client
from conf.config import SHOW_TIME
from lib.util import get_filename, show_class

if SHOW_TIME:
    from datetime import datetime

PRINT = False
CACHE = False

class HDFSClient(object):
    def __init__(self):        
        self._clients = {}
    
    def _print(self, text):
        if PRINT:
            show_class(self, text)
    
    def _get_client(self, addr, port):
        if not CACHE or not self._clients.has_key(addr):
            cli = Client('http://%s:%s' % (str(addr), str(port)))
            if CACHE:
                self._clients.update({addr:cli})
        else:
            cli = self._clients.get(addr)
        return cli
    
    def upload(self, addr, port, package, version, buf):
        self._print('start to upload, package=%s, version=%s' % (package, version))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            if not buf:
                show_error(self, 'invalid buf, cannot upload buf to HDFS')
                return
            cli = self._get_client(addr, port)
            filename = get_filename(package, version)
            with cli.write(filename) as writer:
                writer.write(buf)
            if SHOW_TIME:
                self._print('upload, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            return True
        except:
            show_error(self, 'failed to upload')
    
    def download(self, addr, port, package, version):
        self._print('start to download, package=%s, version=%s' % (package, version))
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            ret = None
            cli = self._get_client(addr, port)
            filename = get_filename(package, version)
            with cli.read(filename) as reader:
                ret = reader.read()
            if SHOW_TIME:
                self._print('download, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if ret:
                return ret
        except:
            show_error(self, 'failed to download')
    