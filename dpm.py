#      dpm.py
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

import sys, argparse, shelve, time
from app.install_app import install_app, uninstall_app
from app.log_app import write_install_log, is_app_installed, write_upload_log, is_version_number_correct
from driver.install_driver import install_driver
from lib.upload import upload
from lib.log import log_show_to_user
from conf.config import APP, DRIVER
from lib.install import get_newest_version_number
    

def dpm(): # changed to a function by hxf 20160731
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--driver', action='store_true')
    parser.add_argument('-a', '--app', action='store_true')
    parser.add_argument('-u',  dest='username', default=None)
    parser.add_argument('-p',  dest='password', default=None)
    parser.add_argument('-v',  dest='version', default=None)
    parser.add_argument('-s',  dest='source', default=None)
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()
    
    cmd = sys.argv[1]
    name = sys.argv[2]
    args = parser.parse_args(sys.argv[3:])
    username = args.username
    password = args.password
    version = args.version
    source = args.source
    
    # if version is given, get version. added by hxf 20150805
    if len(name.split('==')) > 1 :
        name, version = get_version_from_input_name(name)
    
    if args.app:
        if cmd == 'upload':
            if upload(name, username, password, version, source, APP):
                #write_upload_log(username, name, version)
                log_show_to_user('upload %s %s successfully!' % (name, version))
                return True
            log_show_to_user('fail to upload app %s!' % name)
            return False
           
        elif cmd == 'install':
            # judge the version, correct or not. added by hxf 20150805
            if version is not None:
                if not is_version_number_correct(name, version):
                    log_show_to_user("Can't find a matching version!")
                    return False
            
            # whether the app is installed or not. if True: stop installing, if false: continue installing. added by hxf 20150805
            if is_app_installed(username, name):
                log_show_to_user('app %s has been already existed, if you want to install another version of %s, you should uninstall current version first!' % (name, name))
                return False
            
            if install_app(username, name, version, APP):
                if version is None:
                    version = get_newest_version_number(name, APP)
                write_install_log(username, name, version, time.strftime('%Y-%m-%d %X', time.localtime()))
                log_show_to_user('Successfully install app %s %s!' % (name, version))
                return True
            log_show_to_user('fail to install app %s' % name)
            return False
        
        elif cmd == 'uninstall':#added by hxf 20150805
            if uninstall_app(username, name):
                log_show_to_user('Successfully uninstall app %s!' % name)
                return True
            log_show_to_user('fail to uninstall app %s!' % name)
            return False
        
        
    elif args.driver:
        if cmd == 'upload':
            if upload(name, username, password, version, source, 'driver'):
                log_show_to_user('Successfully upload driver %s %s!' % (name, version))
                return True
            log_show_to_user('fail to upload driver %s!' % name)
            return False
                
        elif cmd == 'install':
            if install_driver(username, name, version, DRIVER):
                log_show_to_user('Successfully install driver %s' % name)
                return True
            log_show_to_user('fail to install driver %s!' % name)
            return False
            
    log_show_to_user('input command error!')
    return False
                

#added by hxf 20150805
def get_version_from_input_name(name):
    res = name.split('==')
    return res[0].strip(), res[1].strip()
    
      
if __name__ == '__main__': 
    dpm()
