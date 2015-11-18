#      util.py
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
import fcntl
import struct
import socket
import types
import shutil
import hashlib
import random
import tempfile
import commands
from hash_ring import HashRing
from conf.path import PATH_DRIVER
from lib.zip import zip_dir, unzip_file 
from lib.log import log_err, log_debug
from component.rpcclient import RPCClient
from conf.config import IFACE, FRONTEND_SERVERS, FRONTEND_PORT

APP = 'app'
DRIVER = 'driver'

def get_filename(package, version):
    return '%s-%s.zip' % (package, version)

def _get_frontend():
    ring = HashRing(FRONTEND_SERVERS)
    num = random.randint(10,15)
    server = ring.get_node(str(num))
    print 'util->frontend_servers is', str(server)
    return server
    
def get_md5(text):
    if type(text) is types.StringType:
        tmp = hashlib.md5()   
        tmp.update(text)
        return tmp.hexdigest()
    else:
        log_err('util', 'failed to get md5')

def login(user, password):
    user = str(user)
    pwd = get_md5(str(password))
    addr = _get_frontend()
    rpcclient = RPCClient(addr, FRONTEND_PORT)
    uid, key = rpcclient.request('login', user=user, pwd=pwd)
    return (str(uid), str(key))

def upload(path, uid, package, version, typ, key):
    zipfilename = get_filename (package, version)
    zipfilepath = os.path.join('/tmp', zipfilename)
    zip_dir(path, zipfilepath)
    with open(zipfilepath) as f:
        buf = f.read()
    os.remove(zipfilepath)
    addr = _get_frontend()
    rpcclient = RPCClient(addr, FRONTEND_PORT, uid, key)
    ret  = rpcclient.request('upload', uid=uid, package=package, version=version, buf=buf, typ=typ)
    if ret:
        log_debug('util', "finished uploading, package=%s, version=%s, ret=%s" % (package, version, str(ret)))
        return True
    else:
        log_err('util', 'failed to upload, uid=%s, package=%s, version=%s, typ=%s' % (str(uid), str(package), str(version), str(typ)))
        return False
    
def upload_driver(path, uid, driver, version, key):
    return upload(path, uid, driver, version, DRIVER, key)

def upload_app(path, uid, app, version, key):
    return upload(path, uid, app, version, APP, key)

def install(uid, package, version, typ):
    addr = _get_frontend()
    rpcclient = RPCClient(addr, FRONTEND_PORT)
    ret = rpcclient.request('install', uid=uid, package=package, version=version, typ=typ)
    if not ret:
        log_err('util', 'failed to install, uid=%s, package=%s, version=%s, typ=%s' % (str(uid), str(package), str(version), str(typ)))
    return ret

def install_driver(uid, driver, version=None):
    driver_path = os.path.join(PATH_DRIVER, driver)
    if os.path.exists(driver_path):
        log_err('util', 'failed to install driver, %s exists' % str(driver))
        return False
    ret = install(uid, driver, version, DRIVER)
    if not ret:
        log_err('util', 'failed to install driver, uid=%s, driver=%s, version=%s' % (str(uid), str(driver), str(version)))
        return False
    dirname = tempfile.mkdtemp()
    try:
        src = os.path.join(dirname, driver) + '.zip'
        with open(src, 'wb') as f:
            f.write(ret)
        dest = os.path.join(dirname, driver)
        unzip_file(src, dest)
        dep_path = os.path.join(dest, 'dependency')
        if not _check_dep(dep_path):
            log_err('util', 'failed to install driver, invalid dependency, uid=%s, driver=%s, version=%s' % (str(uid), str(driver), str(version)))
            return False
        os.remove(dep_path)
        shutil.copytree(dest, driver_path)
    finally:
        shutil.rmtree(dirname)
    return True

def install_app(uid, app, version=None):
     return install(uid, app, version, APP)

def uninstall(uid, package, typ):
    addr = _get_frontend()
    rpcclient = RPCClient(addr, FRONTEND_PORT)
    ret = rpcclient.request('uninstall', uid=uid, package=package, typ=typ)
    if not ret:
        log_err('util', 'failed to uninstall, uid=%s, package=%s, typ=%s' % (str(uid), str(package), str(typ)))
    return ret

def uninstall_app(uid, app):
    uninstall(uid, app, typ=APP)

def _check_dep(path):
    if os.path.isfile(path):
        with open(path) as file_dependency:
            lines = file_dependency.readlines()
            for line in lines:
                try:
                    package_version = ''
                    installer_name = ''
                    res = []
                    
                    for str_equal in line.split('='):
                        if str_equal.strip(): # not blank
                            for str_blank in  str_equal.split():
                                res.append(str_blank)
                    
                    if (len(res) % 2 == 0):
                        if len(res):
                            log_err('util', 'failed to check dependency, invalid format' )
                            return False
                        continue # if it is blank, then continue
                    else:
                        package_name =  res[0]
                        
                        for index_to_match in range(1, len(res), 2):
                            if res[index_to_match] == 'installer':
                                installer_name = res[index_to_match + 1]
                                continue
                            if res[index_to_match] == 'version':
                                package_version = res[index_to_match + 1]
                                continue
                        
                        if installer_name == '':
                            installers = ['pip', 'apt-get']
                            for installer in installers:
                                installer_name = installer
                                if package_version == '': 
                                    cmd = '%s install %s' % (installer_name, package_name)
                                else :
                                    cmd = '%s install %s==%s' % (installer_name, package_name, package_version)
                                status, output = commands.getstatusoutput(cmd)
                                if status == 0:
                                    log_debug('util', 'check dependency, finished installing %s' % package_name)
                                    break
                        else:
                            if package_version == '':
                                cmd = '%s install %s' % (installer_name, package_name)
                            else:
                                cmd = '%s install %s==%s' % (installer_name, package_name, package_version)
                            status, output = commands.getstatusoutput(cmd)
                            if status == 0:
                                log_debug('util', 'check dependency, finished installing %s' % package_name)
                            else:
                                log_err('util', 'check dependency, failed to install %s' % package_name)
                except:
                    continue # if it is blank, continue. else return False above
    return True

def localhost():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', IFACE[:15]))[20:24])
    print '@@@@@@util->loaclhost', ip
    return ip