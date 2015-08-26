#      log_app.py
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

import shelve
from conf.config import PATH_INSTALL_LOG_APP, PATH_UPLOAD_LOG_APP
from lib.log import log_show_to_user, log_debug

# added by hxf 20150728
def write_install_log(username, name, version, output):
    log_debug('log_app.write_install_log()', 'write_install_log() starts!')
    
    register_info = shelve.open(PATH_INSTALL_LOG_APP, writeback = True)
    
    if(register_info.has_key(username)):
        if(register_info[username].has_key(name)):
            register_info[username][name][version] = output
        else:
            register_info[username][name] = {version:output}
    else:
        register_info[username] = {name:{version:output}}
        
    log_debug('log_app.write_install_log()', "%s'app install logs are as follows:" % username)
    log_debug('log_app.write_install_log()', 'the register_info is : %s' % register_info[username])
    
    register_info.close()
    

#added by hxf 2050805
def is_app_installed(username, name):
    log_debug('log_app.is_app_installed()', 'is_app_installed() starts!')
    
    register_info = shelve.open(PATH_INSTALL_LOG_APP)
    
    if register_info.has_key(username):
        if register_info[username].has_key(name):
            return True
    return False

    
# added by hxf 20150804
def write_upload_log(username, name, version):
    log_debug('log_app.write_upload_log()', 'write_upload_log() starts!')
    
    release_info = shelve.open(PATH_UPLOAD_LOG_APP, writeback = True)
    
    if release_info.has_key(username):
        if release_info[username].has_key(name):
            release_info[username][name].append(version)
        else :
            release_info[username][name] = [version]
    else :
        release_info[username] = {name:[version]}
        
    log_debug('log_app.write_upload_log()', "%s'app upload logs are as follows:" % username)
    log_debug('log_app.write_upload_log()', 'the release_info is : %s' % release_info[username])



#added by hxf 20150805
def is_version_number_correct(name, version):
    log_debug('log_app.is_version_number_correct()', 'is_version_number_correct() starts!')
    
    release_info = shelve.open(PATH_UPLOAD_LOG_APP)
    
    for username in release_info:
        if release_info[username].has_key(name):
            try :
                release_info[username][name].index(version)
                return True
            except ValueError:
                continue # no action, to perfect the format
    
    return False            
    
        
    