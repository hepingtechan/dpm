#      rpcclient.py
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
from lib.package import pack
from dpmclient import DPMClient

class RPCClient():
    def __init__(self, addr, port):
        self.dpmclient = DPMClient()
        self.addr = addr
        self.port = port
        
    def request(self, op, args, kwargs):
        buf = pack(op, args, kwargs)
        res = self.dpmclient.request(self.addr, self.port, buf)
        if res:
            ret = bson.loads(res)
            return ret['res']


if __name__ == '__main__':
    rpcclient = RPCClient('127.0.0.1', 9001)
    print rpcclient.request('matchfunc', [1, 2], {})
                                 

