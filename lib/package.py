#      package.py
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

from lib.log import log_err
from lib.bson import dumps, loads

def pack(op, args, kwargs):
    if type(op) != str or type(args) != tuple or type(kwargs) != dict:
        log_err('package', 'failed to pack, invalid type')
        return
    buf = {'op': op, 'args': args, 'kwargs': kwargs}
    return dumps(buf)

def unpack(buf):
    tmp = loads(buf)
    if type(tmp) != dict or not tmp.has_key('op') or not tmp.has_key('args') or not tmp.has_key('kwargs'):
        log_err('package', 'failed to unpack, invalid type')
        return
    op = tmp['op']
    args = tmp['args']
    kwargs = tmp['kwargs']
    if type(op) != str or type(args) != list or type(kwargs) != dict:
        log_err('package', 'failed to unpack, invalid arguments')
        return
    return (op, args, kwargs)
