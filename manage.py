from random import randint
from component.rpcclient import RPCClient
from conf.config import ALLOCATOR_PORT, ALLOCATOR_SERVERS
addr1 = '192.168.10.161'
addr2 = '192.168.10.162'
addr3 = '192.168.10.163'
addr4 = '192.168.10.164'

def add_installer(addr):
    n = randint(0, len(ALLOCATOR_SERVERS) - 1)
    address = ALLOCATOR_SERVERS[n]
    print 'manage->add_installer, allocator address=%s' % str(address)
    rpcclient = RPCClient(address, ALLOCATOR_PORT)
    res = rpcclient.request('add_installer', addr=addr)
    if res:
        print 'manage->add_installer, addr=%s' % str(addr)
        return True
    return False
if __name__ == '__main__':
    print '222333'
    add_installer(addr4)
