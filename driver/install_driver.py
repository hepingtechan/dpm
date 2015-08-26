#      install_driver.py
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


import os,shutil
from lib.install import download_src, remove_tmpdir
from lib.log import log_show_to_user
from conf.config import DRIVER, PATH_DRIVER

def install_driver(username, name, version, src_type):
    if version is None:
        version = get_newest_version_number(name, src_type)
        
    driver_name = '%s-%s.zip' % (name, version)
    tmp_driver_path = download_src(username, driver_name, DRIVER)
    driver_path = os.path.join(PATH_DRIVER, name)
    
    dependency_path = os.path.join(tmp_driver_path, 'dependency')
    if not install_dependent_packages(dependency_path): # install dependent packages of the driver. added by hxf 20150806
        print 'dependent packages install error: text format error!'
        return False
    os.remove(dependency_path)
    
    if not os.path.isdir(driver_path):
        shutil.copytree(tmp_driver_path, driver_path)
    remove_tmpdir(tmp_driver_path) # after install driver, then delete the files   
    if tmp_driver_path:
        return True
    return False


def install_dependent_packages(dependency_path):
    #print 'in install_dependent_packages(), install_dependent_packages() starts!' # show to programmer
    if os.path.isfile(dependency_path):
        with open(dependency_path) as file_dependency:
            lines = file_dependency.readlines()
            for line in lines:
                try:
                    # initialize the key attrbutes
                    package_version = ''
                    installer_name = ''
                    res_split_finished = []
                    
                    # split the line by '=' & ' '(blank)
                    res_split_equal = line.split('=')
                    for str_equal in res_split_equal:
                        if str_equal.strip(): # not blank
                            res_split_blank = str_equal.split()
                            for str_blank in res_split_blank:
                                res_split_finished.append(str_blank)
                    
                    #print 'after split, res_split_finished is :', res_split_finished
                    
                    # split joint for install command
                    if (len(res_split_finished) % 2 == 0):# if the current line is null or format error, then continue.
                        if len(res_split_finished):
                            print "'%s' is format error!" % line.strip()
                            return False
                        
                        continue # if it is blank, then continue
                        
                    else:
                        #print 'split joint for install command starts!'
                        package_name =  res_split_finished[0]
                        
                        for index_to_match in range(1, len(res_split_finished), 2):
                            if res_split_finished[index_to_match] == 'installer':
                                installer_name = res_split_finished[index_to_match + 1]
                                continue
                            if res_split_finished[index_to_match] == 'version':
                                package_version = res_split_finished[index_to_match + 1]
                                continue
                        
                        # execute the command
                        #print 'execute the command starts!'
                        if installer_name == '': # no installer
                            installers = ['pip', 'apt-get']
                            for installer in installers:
                                installer_name = installer
                                if package_version == '': # no version
                                    cmd = '%s install %s' % (installer_name, package_name)
                                else :
                                    cmd = '%s install %s==%s' % (installer_name, package_name, package_version)
                                #print 'no installer -> install_cmd is: %s' % cmd # show to programmer
                                status,output = commands.getstatusoutput(cmd)
                                if status == 0:
                                    print 'Successfully installed %s!' % package_name
                                    break
                        else :
                            if package_version == '':# no version
                                cmd = '%s install %s' % (installer_name, package_name)
                            else:
                                cmd = '%s install %s==%s' % (installer_name, package_name, package_version)
                            #print 'install_cmd is: %s' % cmd # show to programmer
                            status, output = commands.getstatusoutput(cmd)
                            if status == 0:
                                print 'Successfully installed %s!' % package_name
                            else:
                                print 'failed to install %s!' % (package_name)
                                
                except:
                    continue # if it is blank, continue. else return False above
    return True