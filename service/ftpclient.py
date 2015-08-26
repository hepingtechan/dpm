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


import os, sys, tempfile, shutil
from ftplib import FTP
from lib.log import log_debug
from conf.config import ADMIN, ADMINPASSWORD, PATH_DOWNLOAD_SRC

class FTPClient():
    def __init__(self):
        self.ftp =  FTP()
    
    def upload(self, addr, port, name, version, buf):       
        tmpdir = create_tmpdir()
        zipfilename = generate_zipfile(name, version, buf, tmpdir)
        zipfilepath = os.path.join(tmpdir, zipfilename)
               
        self.ftp.connect(addr, port)
        self.ftp.login(ADMIN, ADMINPASSWORD) # must be normal user, for anonymous users are forbidden to change the filesystem
        ret = self.ftp.storbinary('STOR '+ zipfilename, open(zipfilepath, 'rb'), 1024)
        log_debug('FTPClient.upload()', 'the return of FTP.storbinary is : %s' % str(ret))
        self.ftp.quit()
        
        delete_tmpdir(tmpdir)
        return ret
    
    def download(self, addr, port, src_name, src_type):
        self.ftp.connect(addr, port)
        self.ftp.login(ADMIN, ADMINPASSWORD)
        ret = self.ftp.retrbinary("RETR " + src_name, open(PATH_DOWNLOAD_SRC, 'wb').write)
        with open(PATH_DOWNLOAD_SRC, 'rb') as f:
            buf = f.read()
            
        os.remove(PATH_DOWNLOAD_SRC)
        return buf
        
        
  
def generate_zipfile(name, version, buf, tmpdir):
    zipfilename = '%s-%s.zip' % (name, version)
    zipfilepath = os.path.join(tmpdir, zipfilename)
    os.mknod(zipfilepath)
    
    with open(zipfilepath, 'w') as f:
        f.write(buf)
    return zipfilename


# generate a tmpdir in current dir        
def create_tmpdir():
    tmpfilepath = tempfile.mktemp()
    tmpname = os.path.split(tmpfilepath)[-1]
    tmpdir = './%s' % tmpname
    os.mkdir(tmpdir)
    return tmpdir


def delete_tmpdir(tmpdir):
    shutil.rmtree(tmpdir) 
    return True


          