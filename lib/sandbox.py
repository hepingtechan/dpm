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
