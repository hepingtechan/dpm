#      manage.py
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

import sys
import argparse
from lib.log import log_debug 
from conf.config import ALLOCATOR_PORT
from component.rpcclient import RPCClient

def add_installer(allocator, installer):
    log_debug('manage', 'add_installer, allocator=%s' % str(allocator))
    rpcclient = RPCClient(allocator, ALLOCATOR_PORT)
    res = rpcclient.request('add_installer', addr=installer)
    if res:
        log_debug('manage', 'add_installer, installer=%s' % str(installer))
        return True
    return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', dest='allocator', default=None)
    parser.add_argument('-i', dest='installer', default=None)
    args = parser.parse_args(sys.argv[1:])
    allocator = args.allocator
    installer = args.installer
    add_installer(allocator, installer)
