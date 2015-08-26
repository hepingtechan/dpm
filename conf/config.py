#      config.py
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


# dpm
APP = 'app'
DRIVER = 'driver'

PATH_DPM = '/etc/default/dpm'

#path of driver
PATH_DRIVER = '/var/lib/dpm/driver'
PATH_APP = '/var/lib/dpm/app'

# path of vdtools
PATH_VDTOOLS = '/var/lib/dpm/vdtools/vdtools.py'

# for log
PATH_INSTALL_LOG_APP = '/var/lib/dpm/repo/log/install_log_app'
PATH_UPLOAD_LOG_APP = '/var/lib/dpm/repo/log/upload_log_app'
PATH_UPLOAD_LOG_DRIVER = '/var/lib/dpm/repo/log/upload_log_driver'

# for project log
LOG_SHOW_TO_USER = True
LOG_DEBUG = True
LOG_ERROR = True

# Repository
PATH_REPO = '/var/lib/dpm/repo'
PATH_FTPSERVER_ON_REPO = '/var/lib/dpm/repo/ftp'
PATH_DOWNLOAD_SRC = '/var/lib/dpm/repo/download_src'
ADMIN = 'admin'
ADMINPASSWORD = 'adminpassword'

#tmp
TMP_DIR = '/var/lib/dpm/tmp'