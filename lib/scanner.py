#      scanner.py
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

import zlib
import json
from log import show_error
from conf.config import SCAN_TOOL

if SCAN_TOOL == 'pyblade':
    from pyblade import scan

class Scanner(object):
    def _do_scan(self, files):
        result = scan(files)
        if result:
            return True
    
    def _extract(self, content):
        if content.get('app'):
            files = content.get('app')
        elif content.get('driver'):
            files = content.get('driver')
        else:
            show_error(self, 'cannot extract')
            return
        filenames = filter(lambda f: f.endswith('.py'), files)
        info = {}
        for name in filenames:
            file = files.get(name)
            info.update({name: file})
        return info
    
    def _scan(self, buf):
        text = zlib.decompress(buf)
        content = json.loads(text)
        if not content or type(content) != dict:
            show_error(self, 'invalid content')
            return
        files = self._extract(content)
        if files:
            if not self._do_scan(files):
                raise Exception('this package contains invalid files')
        return content.get('description')
    
    def scan(self, buf):
        return self._scan(buf)
