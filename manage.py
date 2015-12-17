import sys
import argparse
from lib.log import log_debug
from conf.config import ALLOCATOR_PORT
from component.rpcclient import RPCClient

def add_installer(allocator, installer):
    log_debug('manage->add_installer', 'allocator=%s' % str(allocator))
    rpcclient = RPCClient(allocator, ALLOCATOR_PORT)
    res = rpcclient.request('add_installer', addr=installer)
    if res:
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
