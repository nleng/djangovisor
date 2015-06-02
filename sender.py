import requests
import json
import xmlrpclib
import time
import socket
import os
import subprocess

#####################################################################################

# url to the main server with djangovisor app running:
collector_url = "http://djangovisor.cfs-me-research.net/djangovisor/collector"

# login for the local supervisor web interface:
username = 'corni'
password = 'q3eq3ew4r'
port = 9001

#####################################################################################

# some of the functions are snitched from the psutil source code

"""
psutil is distributed under BSD license reproduced below.

Copyright (c) 2009, Jay Loden, Dave Daeschler, Giampaolo Rodola'
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
 * Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
 * Neither the name of the psutil authors nor the names of its contributors
   may be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
def memory_usage():
    """Return memory usage."""
    f = open('/proc/meminfo', 'rb')
    try:
        mem_total, mem_free, mem_percent, swap_total, swap_free, swap_percent = 0, 0, 0, 0, 0, 0
        for line in f:
            if line.startswith('MemTotal'):
                mem_total = float(line.strip().split()[1])/1000.
            if line.startswith('MemFree'):
                mem_free = float(line.strip().split()[1])/1000.
            if line.startswith('SwapTotal'):
                swap_total = float(line.strip().split()[1])/1000.
            if line.startswith('SwapFree'):
                swap_free = float(line.strip().split()[1])/1000.
        if mem_total > 0:
            mem_percent = round(100.*(mem_total-mem_free)/mem_total, 1)
        if swap_total > 0:
            swap_percent = round(100.*(swap_total-swap_free)/swap_total, 1)
        # mem_total, mem_used, mem_percent, swap_total, swap_used, swap_percent
        return round(mem_total, 1), round(mem_total-mem_free, 1), mem_percent, round(swap_total, 1), round(swap_total-swap_free, 1), swap_percent
        raise RuntimeError("line 'btime' not found")
    finally:
        f.close()


def disk_usage():
    ds = os.statvfs('/')
    free = ds.f_bavail * ds.f_frsize
    total = ds.f_blocks * ds.f_frsize
    used = (ds.f_blocks - ds.f_bfree) * ds.f_frsize
    percent = round(100.*used/total, 1)
    return round(total/1.e6, 1), round(used/1.e6, 1), percent

# don't forget to devide /total_mem since i also want percentage
def memory_info(pid):
    PAGESIZE = os.sysconf("SC_PAGE_SIZE")
    f = open("/proc/%s/statm" % pid, 'rb')
    try:
        vms, rss = f.readline().split()[:2]
        return float(rss) * PAGESIZE / 1.e6
        # return (float(rss) * PAGESIZE / 1.e6, float(vms) * PAGESIZE / 1.e6)
    finally:
        f.close()


def cpu_times(pid):
    try:
        with open('/proc/%s/stat' % pid, 'r') as pidfile:
            proctimes = pidfile.readline()
            # get utime from /proc/<pid>/stat, 14 item
            utime = float(proctimes.split(' ')[13])/100.
            # get stime from proc/<pid>/stat, 15 item
            stime = float(proctimes.split(' ')[14])/100.
            # /100. to stay in tune with psutil output
            return utime, stime
    except:
        print "yolo"
        
def system_cpu_times():
    f = open('/proc/stat', 'r')
    try:
        values = f.readline().split()[1:]
    finally:
        f.close()
    fields = ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq']
    # /100. to stay in tune with psutil output
    return float(values[0])/100., float(values[2])/100., float(values[4])/100., sum([float(value)/100. for value in values])

# better use cpu_times(), cause want to stay in tune with psutil
# def cpu_percent(pid):
#     cpu_str = subprocess.check_output(["ps", "-p", str(pid), "-o", "%cpu"])
#     return cpu_str.strip().split('\n')[1]

# exactly from the psutil source code
def cpu_count_logical():
    """Return the number of logical CPUs in the system."""
    try:
        return os.sysconf("SC_NPROCESSORS_ONLN")
    except ValueError:
        # as a second fallback we try to parse /proc/cpuinfo
        num = 0
        f = open('/proc/cpuinfo', 'rb')
        try:
            lines = f.readlines()
        finally:
            f.close()
        PROCESSOR = b('processor')
        for line in lines:
            if line.lower().startswith(PROCESSOR):
                num += 1

    # unknown format (e.g. amrel/sparc architectures), see:
    # https://github.com/giampaolo/psutil/issues/200
    # try to parse /proc/stat as a last resort
    if num == 0:
        f = open('/proc/stat', 'rt')
        try:
            lines = f.readlines()
        finally:
            f.close()
        search = re.compile('cpu\d')
        for line in lines:
            line = line.split(' ')[0]
            if search.match(line):
                num += 1

    if num == 0:
        # mimic os.cpu_count()
        return None
    return num

def boot_time():
    """Return the system boot time expressed in seconds since the epoch."""
    f = open('/proc/stat', 'rb')
    try:
        for line in f:
            if line.startswith('btime'):
                ret = float(line.strip().split()[1])
                return ret
        raise RuntimeError("line 'btime' not found")
    finally:
        f.close()

def get_children(pid):
    try:
        children_str = subprocess.check_output(["ps", "--ppid", str(pid)])
        children = []
        for line in children_str.strip().split('\n')[1:]:
            children.append(line.split()[0])
        return children
    except: 
        return []

#################################################################

def request_data():
    localhostname = socket.gethostname()
    server_uptime = int(time.time())-boot_time()
    ip_address = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    platform = os.uname()
    cpu_num = cpu_count_logical()
    load_avg_all = os.getloadavg()
    # json doen't like / characters
    # supervisor_logtail = supervisor.readLog(-1000, 0).replace('\n', '\\n')
    supervisor_logtail = '\\n'.join(supervisor.readLog(-1000, 0).split('\n')[1:])  # .replace('"', '\"')
    
    user_time, sys_time, wait_time, total_time = system_cpu_times()
    
    server_disk_total, server_disk_used, server_disk_percent = disk_usage()
    
    server_memory_total, server_memory_megabyte, server_memory_percent, swap_total, swap_megabyte, swap_percent = memory_usage()
    
    for process in processes:
        del process['group']
        del process['description']
        del process['spawnerr']
        del process['stderr_logfile']
        del process['stdout_logfile']
        del process['logfile']
        # strip everything before the first \n and replace all \n with \\n because json doesn't like \n
        process['log_stderr'] = '\\n'.join(supervisor.tailProcessStderrLog(process['name'], 0, 800)[0].split('\n')[1:])  # .replace('"', '\"')
        process['log_stdout'] = '\\n'.join(supervisor.tailProcessStdoutLog(process['name'], 0, 800)[0].split('\n')[1:])  # .replace('"', '\"')
        
        process['children'] = None
        process['cpu_user_time'] = None
        process['cpu_sys_time'] = None
        process['memory_megabyte_total'] = None
        process['memory_percent_total'] = None
        
        pid = process['pid']
        if pid > 0:
            children = get_children(pid)
            process['children'] = len(children)

            times = cpu_times(pid)
            cpu_user_time = times[0]
            cpu_sys_time = times[1]
            memory_total_rss = memory_info(pid)
            for child in children:
                times = cpu_times(child)
                cpu_user_time += times[0]
                cpu_sys_time += times[1]
                memory_total_rss += memory_info(child)
            process['cpu_user_time'] = cpu_user_time  # don't round this!
            process['cpu_sys_time'] = cpu_sys_time
            process['memory_megabyte_total'] = round(memory_total_rss, 1)
            process['memory_percent_total'] = round(100.*memory_total_rss/server_memory_total, 1)
            
    # print supervisor_logtail
      
    data={'server_disk_total': server_disk_total, 'server_disk_used': server_disk_used, 'server_disk_percent': server_disk_percent, 'username': username,
          'password': password, 'port': port, 'processes': processes, 'localhostname': localhostname, 'ip_address':ip_address, 'server_uptime': server_uptime, 'platform': platform,
          'cpu_num': cpu_num, 'load_avg_all': load_avg_all, 'total_time': total_time, 'user_time': user_time, 'sys_time': sys_time, 'wait_time': wait_time,
          'server_memory_total': server_memory_total, 'server_memory_percent': server_memory_percent, 'server_memory_megabyte': server_memory_megabyte, 
          'swap_total': swap_total, 'swap_percent': swap_percent, 'swap_megabyte': swap_megabyte, 'supervisor_logtail': supervisor_logtail}
    return data


if __name__ == "__main__":
    sender_url = 'http://%s:%s@localhost:%s/RPC2' % (username, password, port)
    server = xmlrpclib.Server(sender_url)
    supervisor = server.supervisor
    processes = supervisor.getAllProcessInfo()
    for process in processes:
        print process['name']
    # send data as json ###
    json_data = json.dumps(request_data())
    # print json_data
    r = requests.post(collector_url, json_data)
    print(r.status_code, r.reason)
    print(r.text[:300] + '...')
