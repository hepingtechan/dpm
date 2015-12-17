
from hdfs.client import Client
from lib.log import log_debug, log_err
from lib.util import get_filename
from conf.config import SHOW_TIME

if SHOW_TIME:
    from datetime import datetime

class HDFSClient(object):
    def __init__(self):        
        self._clients = {}
        
    
    def _get_client(self, addr, port):
        if not self._clients.has_key(addr):
            cli = Client('http://%s:%s' % (str(addr), str(port)))
            self._clients.update({addr:cli})
        else:
            cli = self._clients.get(addr)
        return cli
    
    def upload(self, addr, port, package, version, buf):
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            if not buf:
                return
            #log_debug('HDFSClient', 'upload->package=%s, version=%s, length=%d' % (package, version, len(buf)))
            cli = self._get_client(addr, port)
            filename = get_filename(package, version)
            with cli.write(filename) as writer:
                writer.write(buf)
            if SHOW_TIME:
                log_debug('HDFSClient', 'upload, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            return True
        finally:
            pass
        #except:
        #    log_err('HDFSClient', 'failed to upload')
    
    def download(self, addr, port, package, version):
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            ret = None
            cli = self._get_client(addr, port)
            filename = get_filename(package, version)
            with cli.read(filename) as reader:
                ret = reader.read()
            if SHOW_TIME:
                log_debug('HDFSClient', 'download, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if ret:
                #log_debug('HDFSClient', 'download->package=%s, version=%s, length=%d' % (package, version, len(ret)))
                return ret
        except:
            log_err('HDFSClient', 'failed to download')
    