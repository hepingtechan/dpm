#      install.py
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


import os, shutil, shelve
from lib.log import log_show_to_user, log_debug
from lib.path import make_tmp_name
from lib.zip import unzip_file 
from service.rpcclient import RPCClient
from conf.config import TMP_DIR, APP, DRIVER, PATH_UPLOAD_LOG_APP, PATH_UPLOAD_LOG_DRIVER

def download_src(username, src_name, src_type):   
    rpcclient = RPCClient('127.0.0.1', 9001)
    ret  = rpcclient.request('download_src', [username], {'src_name':src_name, 'src_type':src_type})
    
    tmp_name = make_tmp_name()
    if not os.path.isdir(TMP_DIR):
        os.makedirs(TMP_DIR)
    tmpdir_path = os.path.join(TMP_DIR, tmp_name)
    if not os.path.isdir(tmpdir_path):os.mkdir(tmpdir_path)
    src_path = os.path.join(tmpdir_path, src_name)  
    print 'install.download_src() is : %s' % src_path  
    with open(src_path, 'wb') as f:
        f.write(ret)
    
    res_src_name = src_name[:-4]
    res_src_path = os.path.join(tmpdir_path, res_src_name)
    unzip_file(src_path, res_src_path)
    
    if ret:
        return res_src_path
    return None


def remove_tmpdir(src_path):
    tmp_dir_name = os.path.split(src_path)[-2]
    tmp_dir = os.path.join(TMP_DIR, tmp_dir_name)
    shutil.rmtree(tmp_dir) # after install driver, then delete the files
    
    
# added by hxf 20150804   
def get_newest_version_number(name, src_type):
    #print 'get_newest_version_number() starts!'
    if src_type == APP:
        path_upload_log = PATH_UPLOAD_LOG_APP
    if src_type == DRIVER:
        path_upload_log = PATH_UPLOAD_LOG_DRIVER
        
    release_info = shelve.open(path_upload_log)
    
    for username in release_info:
        if release_info[username].has_key(name):
            #log_debug('log_app.get_newest_version_number()', 'the newest_version_number of %s is %s' % (name, max(release_info[username][name])))
            return max(release_info[username][name])