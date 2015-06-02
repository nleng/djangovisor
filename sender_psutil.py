import requests
import json
import psutil
import xmlrpclib

import socket
import os

#####################################################################################

# url to the main server with djangovisor app running:
collector_url = "http://djangovisor.cfs-me-research.net/djangovisor/collector"

# login for the local supervisor web interface:
username = 'yourname'
password = 'yourpassword'
port = 9001

#####################################################################################


def request_data(supervisor):
    import time
    localhostname = socket.gethostname()
    server_uptime = int(time.time())-psutil.boot_time()
    ip_address = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    # platform:
    # (sysname, nodename, release, version, machine)
    platform = os.uname()
    cpu_num = psutil.cpu_count()
    load_avg_all = os.getloadavg()
    
    cpu_times = psutil.cpu_times()  # hier zwei felder und dann einfach
    total_time = sum([time for time in cpu_times])
    user_time = cpu_times.user
    sys_time = cpu_times.system
    wait_time = cpu_times.iowait
    
    memory = psutil.virtual_memory()
    # send memory in MB
    server_memory_total = memory.total*1.e-6
    server_memory_percent = memory.percent
    server_memory_megabyte = memory.used*1.e-6
    
    swap = psutil.swap_memory()
    swap_total = swap.total
    swap_percent = swap.percent
    swap_megabyte = swap.used
    
    disk_usage = psutil.disk_usage('/')
    server_disk_total = round(disk_usage.total/1.e6, 1)
    server_disk_used = round(disk_usage.used/1.e6, 1)
    server_disk_percent = round(disk_usage.percent/1.e6, 1)
    
    supervisor_logtail = '\\n'.join(supervisor.readLog(-1000, 0).split('\n')[1:])
    processes = supervisor.getAllProcessInfo()
    
    for process in processes:
        del process['group']
        del process['description']
        del process['spawnerr']
        del process['stderr_logfile']
        del process['stdout_logfile']
        del process['logfile']
        # strip everything before the first \n and replace all \n with \\n because json doesn't like \n
        process['log_stderr'] = '\\n'.join(supervisor.tailProcessStderrLog(process['name'], 0, 800)[0].split('\n')[1:])
        process['log_stdout'] = '\\n'.join(supervisor.tailProcessStdoutLog(process['name'], 0, 800)[0].split('\n')[1:])
        
        process['children'] = None
        process['cpu_user_time'] = None
        process['cpu_sys_time'] = None
        process['memory_megabyte_total'] = None
        process['memory_percent_total'] = None
        
        if process['pid'] > 0:
            p = psutil.Process(process['pid'])
            cpu_user_time = p.cpu_times().user
            cpu_sys_time = p.cpu_times().system
            memory_percent_total = p.memory_percent()
            memory_total_rss = p.memory_info().rss
            for child in p.get_children():
                cpu_user_time += child.cpu_times().user
                cpu_sys_time += child.cpu_times().system
                memory_percent_total += child.memory_percent()
                memory_total_rss += child.memory_info().rss
            process['cpu_user_time'] = cpu_user_time  # don't round this!
            process['cpu_sys_time'] = cpu_sys_time
            process['memory_percent_total'] = memory_percent_total
            process['memory_megabyte_total'] = round(memory_total_rss/1.e6, 1)
            process['children'] = len(p.get_children())
    
    data={'server_disk_total': server_disk_total, 'server_disk_used': server_disk_used, 'server_disk_percent': server_disk_percent, 'username': username,
          'password': password, 'port': port, 'processes': processes, 'localhostname': localhostname, 'ip_address':ip_address, 'server_uptime': server_uptime,
          'platform': platform, 'cpu_num': cpu_num, 'load_avg_all': load_avg_all, 'total_time': total_time, 'user_time': user_time, 'sys_time': sys_time,
          'wait_time': wait_time, 'server_memory_total': server_memory_total, 'server_memory_percent': server_memory_percent, 'server_memory_megabyte': server_memory_megabyte, 
          'swap_total': swap_total, 'swap_percent': swap_percent, 'swap_megabyte': swap_megabyte, 'supervisor_logtail': supervisor_logtail}
    return data



if __name__ == "__main__":
    sender_url = 'http://%s:%s@localhost:%s/RPC2' % (username, password, port)
    server = xmlrpclib.Server(sender_url)
    supervisor = server.supervisor
    
    # send data as json ###
    json_data = json.dumps(request_data(supervisor))
    print json_data
    r = requests.post(collector_url, json_data)
    print(r.status_code, r.reason)
    print(r.text[:300] + '...')

# 
