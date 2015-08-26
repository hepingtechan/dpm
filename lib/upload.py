#      upload.py
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


import os, shutil, commands
from lib.zip import zip_dir, unzip_file 
from service.rpcclient import RPCClient

def upload(name, username, password, version, src, src_type):
    zipfilename = '%s-%s.zip' % (name, version)
    zipfilepath = os.path.join('/tmp', zipfilename)
    zip_dir(src, zipfilepath)
    
    parent_path =  os.path.dirname(src)
    with open(zipfilepath) as f:
        buf = f.read()
    
    # delete the zip file 
    os.remove(zipfilepath)
    
    rpcclient = RPCClient('127.0.0.1', 9001)
    ret  = rpcclient.request('upload', [username], {'name':name, 'version':version, 'src_type':src_type, 'buf':buf})
    if ret:
        return True
    return False
