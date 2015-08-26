#      rpcserver.py
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


import bson
from lib.package import unpack
from dpmserver import DPMServer
from lib.log import log_debug

class RPCServer(object):   
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.dpmserver = DPMServer()
    
    def run(self):
        self.dpmserver.run(self)
    
    def __proc(self, op, args, kwargs):
        res = ''
        func = getattr(self, op)
        if func:
            ret = func(*args,**kwargs)
            if ret:
                #log_debug('RPCServer._proc', 'the return of func is : %s' % str(ret))
                res = ret
        return bson.dumps({'res':res})
    
    def proc(self, buf):
        op, args, kwargs = unpack(buf)
        return self.__proc(op, args, kwargs)
    