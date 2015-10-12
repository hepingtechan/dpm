#      driver.py
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

from lib.log import log_err, log_debug
from component.rpcclient import RPCClient
from conf.config import REPOSITORY_PORT

class Driver(object):
        def _get_repo(self, package):
            return '127.0.0.1'
        
        def install(self, uid, package, version):
            addr = self._get_repo(package)
            rpcclient = RPCClient(addr, REPOSITORY_PORT)
            if not version:
                version = rpcclient.request('version', package=package)
                if not version:
                    log_err('Driver', 'failed to install, invalid version, uid=%s, package=%s' % (uid, package))
                    return
            ret = rpcclient.request('download', package=package, version=version)
            log_debug('Driver', 'finished installing %s, version=%s' % (package, version))
            return ret
