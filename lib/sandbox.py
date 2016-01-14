#      sandbox.py
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
import shutil
import tempfile
from yaml import load
from zip import unzip_file

OP_SCAN = 'scan'

class Sandbox(object):
    def _scan(self, buf):
        dirname = tempfile.mkdtemp()
        try:
            src = os.path.join(dirname, 'src')
            with open(src, 'wb') as f:
                f.write(buf)
            dest = os.path.join(dirname, 'dest')
            unzip_file(src, dest)
            path = os.path.join(dest, 'description.yaml')
            with open(path) as f:
                buf = f.read()
            desc = load(buf)
            return (desc.get('category'), desc.get('title'), desc.get('description'))
        finally:
            shutil.rmtree(dirname)
    
    def evaluate(self, op, args):
        if op == OP_SCAN:
            return self._scan(args)
