#      util.py
#      
#      Copyright (C) 2015 Xu Tian <tianxu@iscas.ac.cn>
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
import zlib
import json
import uuid
import fcntl
import yaml
import struct
import shutil
import socket
import hashlib
import tempfile
import commands
from random import randint
from conf.config import IFACE
from lib.rpcclient import RPCClient
from conf.path import PATH_DRIVER
from lib.log import log_err, log_debug
from conf.category import CATEGORIES
from conf.servers import SERVER_FRONTEND, FRONTEND_PORT, SERVER_MANAGER, MANAGER_PORT

APP = 'app'
DRIVER = 'driver'
APT = 'apt-get'
PIP = 'pip'
INSTALLERS = [APT, PIP]

def get_filename(package, version):
    return '%s-%s' % (package, version)

def _get_frontend():
    n = randint(0, len(SERVER_FRONTEND) - 1)
    return SERVER_FRONTEND[n]

def get_manager():
    n = randint(0, len(SERVER_MANAGER) - 1)
    return SERVER_MANAGER[n]

def get_md5(text):
    if type(text) == str or type(text) == unicode:
        tmp = hashlib.md5()   
        tmp.update(text)
        return tmp.hexdigest()
    else:
        log_err('util', 'failed to get md5')

def get_uid(user):
    return uuid.uuid3(uuid.NAMESPACE_DNS, str(user)).hex

def login(user, password):
    user = str(user)
    pwd = get_md5(str(password))
    addr = _get_frontend()
    rpcclient = RPCClient(addr, FRONTEND_PORT)
    uid, key = rpcclient.request('login', user=user, pwd=pwd)
    return (str(uid), str(key))

def dump_content(dirname, has_children=True):
    content = {}
    for name in os.listdir(dirname):
        path = os.path.join(dirname, name)
        if os.path.isdir(path):
            if name not in [APP, DRIVER]:
                raise Exception('failed to dump content')
            if has_children:
                res = dump_content(path, has_children=False)
                if res:
                    content.update({name: res})
            else:
                raise Exception('failed to dump content')
        else:
            with open(path) as f:
                buf = f.read()
            if name == 'description':
                buf = buf.replace('\n', ',')[:-1]
                res = buf.split(',')
                buf = {}
                for i in res:
                    info = i.split(':')
                    buf.update({info[0]: info[1][1:]})
                buf = yaml.dump(buf)
            content.update({name:buf})
    return content

def upload_package(buf, uid, package, version, typ, key):
    addr = _get_frontend()
    rpcclient = RPCClient(addr, FRONTEND_PORT, uid, key)
    ret = rpcclient.request('upload', uid=uid, package=package, version=version, buf=buf, typ=typ)
    if ret:
        return True
    else:
        log_err('util', 'failed to upload, uid=%s, package=%s, version=%s, typ=%s' % (str(uid), str(package), str(version), str(typ)))
        return False

def upload(path, uid, package, version, typ, key):
    if os.path.isdir(path):
        content = dump_content(path)
        buf = zlib.compress(json.dumps(content))
        return upload_package(buf, uid, package, version, typ, key)

def upload_driver(path, uid, package, version, key):
    return upload(path, uid, package, version, DRIVER, key)

def upload_app(path, uid, package, version, key):
    return upload(path, uid, package, version, APP, key)

def install(uid, package, version, typ):
    addr = _get_frontend()
    rpcclient = RPCClient(addr, FRONTEND_PORT)
    if typ == DRIVER:
        content = None
    ret = rpcclient.request('install', uid=uid, package=package, version=version, typ=typ, content=content)
    if not ret:
        log_err('util', 'failed to install, uid=%s, package=%s, version=%s, typ=%s' % (str(uid), str(package), str(version), str(typ)))
        return
    return ret

def install_driver(uid, package, version=None):
    driver_path = os.path.join(PATH_DRIVER, driver)
    if os.path.exists(driver_path):
        shutil.rmtree(driver_path)
    ret = install(uid, package, version, DRIVER)
    if not ret:
        log_err('util', 'failed to install driver, uid=%s, driver=%s, version=%s' % (str(uid), str(driver), str(version)))
        return False
    dirname = tempfile.mkdtemp()
    try:
        buf = json.loads(zlib.decompress(ret))
        dep = buf['dep']
        if not _check_dep(dep):
            log_err('util', 'failed to install driver, invalid dependency, uid=%s, driver=%s, version=%s' % (str(uid), str(driver), str(version)))
            return False
        driver = buf['driver']
        if driver:
            src = os.path.join(dirname, 'driver')
            os.mkdir(src)
            filenames = driver.keys()
            for name in filenames:
                filepath = os.path.join(src, name)
                with open(filepath, 'wb') as f:
                    f.write(driver[name])
            shutil.copytree(src, driver_path)
    finally:
        shutil.rmtree(dirname)
    return True

def uninstall(uid, package, typ):
    addr = _get_frontend()
    rpcclient = RPCClient(addr, FRONTEND_PORT)
    ret = rpcclient.request('uninstall', uid=uid, package=package, typ=typ)
    if not ret:
        log_err('util', 'failed to uninstall, uid=%s, package=%s, typ=%s' % (str(uid), str(package), str(typ)))
        return
    return ret

def uninstall_app(uid, package):
    return uninstall(uid, package, typ=APP)

def _check_dep(buf):
    if not buf:
        return
    
    dep = yaml.load(buf)
    if not dep:
        return
    
    cmds = []
    for i in dep:
        installer = dep[i].get('installer')
        if installer not in INSTALLERS:
            log_err('util', 'failed to check dependency, invalid installer')
            return
        cmd = '%s install %s' % (installer, i)
        version = dep[i].get('version')
        if version:
            if installer ==APT:
                cmd += '=%s' % version
            elif installer == PIP:
                cmd += '==%s' % version
        cmds.append(cmd)
    
    for cmd in cmds:
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            log_err('util', 'failed to check dependency')
            return
    
    return True

def localhost():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', IFACE[:15]))[20:24])
    print '@@@@@@util->loaclhost', ip
    return ip

def check_category(category):
    if CATEGORIES.has_key(category):
        return CATEGORIES.get(category)
