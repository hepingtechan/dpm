#      ftpclient.py
#      
#      Copyright (C) 2015 Xiao-Fang Huang <huangxfbnu@163.com>
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
import shutil
import tempfile
from ftplib import FTP
from lib.util import get_filename, show_info

PRINT = False
ADMIN_NAME = 'admin'
ADMIN_PASSWORD = 'adminpassword'

class FTPClient():
    def __init__(self):
        self.ftp =  FTP()
    
    def _print(self, text):
        if PRINT:
            show_info(self, text)
    
    def _generate_zip(self, path, package, version, buf):
        filename = get_filename(package, version)
        filepath = os.path.join(path, filename)
        os.mknod(filepath)    
        with open(filepath, 'w') as f:
            f.write(buf)
        return filename
    
    def upload(self, addr, port, package, version, buf):
        dirname = tempfile.mkdtemp()
        try:
            filename = self._generate_zip(dirname, package, version, buf)
            filepath = os.path.join(dirname, filename)
            self.ftp.connect(addr, port)
            self.ftp.login(ADMIN_NAME, ADMIN_PASSWORD)
            ret = self.ftp.storbinary('STOR ' + filename, open(filepath, 'rb'), 1024)
            self.ftp.quit()
            self._print('finished uploading %s, version=%s, ret=%s'  % (str(package), str(version), str(ret)))
            return ret
        finally:
            shutil.rmtree(dirname)
    
    def download(self, addr, port, package, version):
        dirname = tempfile.mkdtemp()
        filename = get_filename(package, version)
        path = os.path.join(dirname, filename)
        self.ftp.connect(addr, port)
        self.ftp.login(ADMIN_NAME, ADMIN_PASSWORD)
        try:
            ret = self.ftp.retrbinary("RETR " + filename, open(path, 'wb').write)
            with open(path, 'rb') as f:
                buf = f.read()
            self._print('finished downloading %s, version=%s'  % (str(package), str(version)))
            return buf
        finally:
            shutil.rmtree(dirname)
