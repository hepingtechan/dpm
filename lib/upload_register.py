#      upload_register.py
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


import os, shelve
from conf.config import PATH_UPLOAD_LOG_APP, PATH_UPLOAD_LOG_DRIVER, APP, DRIVER
from lib.log import log_show_to_user, log_debug
   
# added by hxf 20150804
def write_upload_log(username, name, version, src_type):
    log_debug('upload_register.write_upload_log()', 'write_upload_log() starts!')
    
    if src_type == APP:
        path_upload_log = PATH_UPLOAD_LOG_APP
    if src_type == DRIVER:
        path_upload_log = PATH_UPLOAD_LOG_DRIVER
    
    parent_dir = os.path.dirname(path_upload_log)
    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    
    release_info = shelve.open(path_upload_log, writeback = True)
    
    if release_info.has_key(username):
        if release_info[username].has_key(name):
            release_info[username][name].append(version)
        else :
            release_info[username][name] = [version]
    else :
        release_info[username] = {name:[version]}
        
    log_debug('upload_register.write_upload_log()', "%s'%s upload logs are as follows:" % (username, src_type))
    log_debug('upload_register.write_upload_log()', 'the release_info is : %s' % release_info[username])
          
    
        
    