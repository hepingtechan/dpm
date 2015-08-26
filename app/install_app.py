#      install_app.py
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


import os, shutil, commands, shelve
from lib.install import download_src, remove_tmpdir, get_newest_version_number
from conf.config import APP, PATH_APP, PATH_VDTOOLS, PATH_INSTALL_LOG_APP
from app.log_app import write_install_log

def install_app(username, name, version, src_type):
    if version is None:
        version = get_newest_version_number(name, src_type)
        
    app_name = '%s-%s.zip' % (name, version)
    tmp_app_path = download_src(username, app_name, APP)
    cmd = 'python PATH_VDTOOLS %s' % tmp_app_path
    status, output = commands.getstatusoutput(cmd)
    if status ==  0:
        write_install_log(username, name, version, tmp_app_path)
    remove_tmpdir(tmp_app_path) # after install app, then delete the files   
    if tmp_app_path:
        return True
    return False    


# added by hxf 20150805
def uninstall_app(username, name):
    install_log = shelve.open(PATH_INSTALL_LOG_APP, writeback = True)
    
    if install_log.has_key(username):
        if install_log[username].has_key(name):
            del install_log[username][name]
            return True     
    else :
        return False