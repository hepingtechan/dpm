#      server.py
#      
#      Copyright (C) 2015 Xiao-Fang Huang <huangxfbnu@163.com>,  Xu Tian <tianxu@iscas.ac.cn>
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

import sys
import resource
import argparse

def create_server(): 
    parser = argparse.ArgumentParser()
    parser.add_argument('-f',  '--frontend', action='store_true')
    parser.add_argument('-b', '--backend', action='store_true')
    parser.add_argument('-m', '--manager', action='store_true')
    parser.add_argument('-r',  '--repository', action='store_true')
    parser.add_argument('-a',  '--allocator', action='store_true')
    parser.add_argument('-i',  '--installer', action='store_true')
    parser.add_argument('-d',  '--recorder', action='store_true')
    args = parser.parse_args(sys.argv[1:])
    if args.frontend:
        from service import frontend
        frontend.main()
    elif args.backend:
        from service import backend
        backend.main()
    elif args.manager:
        from service import manager
        manager.main()
    elif args.repository:
        from service import repository
        repository.main()
    elif args.installer:
        from service import installer
        installer.main()
    elif args.allocator:
        from service import allocator
        allocator.main()
    elif args.recorder:
        from service import recorder
        recorder.main()

if __name__ == '__main__':
    max_open_files_soft, max_open_files_hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (4096, max_open_files_hard))
    create_server()
