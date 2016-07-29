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
        print 'Scan @3-0@ files=%s' % str(files)
        result = scan(files)
        print 'Scan @3-1@ result=%s' % str(result)
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
        print 'Scannner @2-0@ flies=%s' % str(files)
        print 'Scannner @2-1@ flienames=%s' % str(filenames)
        info = {}
        for name in filenames:
            file = files.get(name)
            info.update({name: file})
        print 'Scannner @2-2@ info=%s' % str(info)
        return info
    
    def _scan(self, buf):
        print 'Scannner @1-0@'
        text = zlib.decompress(buf)
        content = json.loads(text)
        print 'Scannner @1-3@ content=%s' % str(content)
        print 'Scannner @1-4@ type=%s' % type(content)
        if not content or type(content) != dict:
            show_error(self, 'invalid content')
            return
        print 'Scannner @1-5@'
        files = self._extract(content)
        print 'Scannner @1-7@ flies=%s' % str(files)
        if not files:
            show_error(self, 'failed to extract package')
            return
        print 'Scannner @1-8@'
        if not self._do_scan(files):
            raise Exception('this package contains invalid files')
        print 'Scannner @1-9@'
        print 'Scannner @1-9@ description=%s' % str(content.get('description'))
        return content.get('description')
    
    def scan(self, buf):
        return self._scan(buf)
