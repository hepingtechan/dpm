#      dpm.py
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

import sys
import argparse
from lib.log import log_debug
from lib.util import upload_app, upload_driver, install_app, install_driver, uninstall_app, login

def get_version(package):
    res = package.split('==')
    return res[0].strip(), res[1].strip()

def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--driver', action='store_true')
    parser.add_argument('-a', '--app', action='store_true')
    parser.add_argument('-i',  dest='uid', default=None)
    parser.add_argument('-u',  dest='username', default=None)
    parser.add_argument('-p',  dest='password', default=None)
    parser.add_argument('-v',  dest='version', default=None)
    parser.add_argument('-s',  dest='source', default=None)
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()
    
    cmd = sys.argv[1]
    if cmd == 'login':
        args = parser.parse_args(sys.argv[2:])
        uid, key = login(args.username, args.password)
        log_debug('dpm', 'finished login, uid=%s, key=%s' % (str(uid), str(key)))
        sys.exit()
    else:
        package = sys.argv[2]
        args = parser.parse_args(sys.argv[3:])
        user = args.username
        password = args.password
        version = args.version
        path = args.source
        uid = args.uid
        
    if len(package.split('==')) > 1:
        package, version = get_version(package)
    
    if args.app:
        if cmd == 'upload':
            uid, key = login(user, password)
            if upload_app(path, uid, package, version, key):
                log_debug('dpm', 'finished uploading app %s' % package)
        elif cmd == 'install':
            uid, key = login(user, password)
            if install_app(uid, package, version):
                log_debug('dpm', 'finished installing app %s' % package)
        elif cmd == 'uninstall':
            uid, key = login(user, password)
            if uninstall_app(uid, package):
                log_debug('dpm', 'finished removing app %s' % package) 
    
    elif args.driver:
        if cmd == 'upload':
            uid, key = login(user, password)
            if upload_driver(path, uid, package, version):
                log_debug('dpm', 'finished uploading driver %s' % package)
        elif cmd == 'install':
            uid, key = login(user, password)
            if install_driver(uid, package, version):
                log_debug('dpm', 'finished installing driver %s' % package)

if __name__ == '__main__': 
    main()
