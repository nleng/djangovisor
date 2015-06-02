from django.db import models
import json
import time
from django.conf import settings

update_period = getattr(settings, 'UPDATE_PERIOD', 60)
maximum_store_days = getattr(settings, 'MAXIMUM_STORE_DAYS', 7)

class Server(models.Model):
    localhostname = models.TextField(unique=True)
    supervisor_logtail = models.TextField(null=True)
    supervisor_user = models.TextField(null=True)
    supervisor_password = models.TextField(null=True)
    supervisor_port = models.PositiveIntegerField(null=True)
    uptime = models.PositiveIntegerField(null=True)
    address = models.TextField(null=True)
    memory = models.FloatField(null=True)
    swap = models.FloatField(null=True)
    sysname = models.TextField(null=True)
    release = models.TextField(null=True)
    version = models.TextField(null=True)
    machine = models.TextField(null=True)
    cpu = models.IntegerField(null=True)
    
    # could be time dependent, but probably not very interesting
    server_disk_total = models.FloatField(null=True)
    server_disk_used = models.FloatField(null=True)
    server_disk_percent = models.FloatField(null=True)
    
    date_last = models.PositiveIntegerField(null=True)
    date = models.TextField(null=True)
    load_avg01_last = models.FloatField(null=True)
    load_avg01 = models.TextField(null=True)
    load_avg05_last = models.FloatField(null=True)
    load_avg05 = models.TextField(null=True)
    load_avg15_last = models.FloatField(null=True)
    load_avg15 = models.TextField(null=True)
    
    cpu_time_total_last = models.FloatField(null=True)
    cpu_user_time_last = models.FloatField(null=True)
    cpu_system_time_last = models.FloatField(null=True)
    cpu_wait_time_last = models.FloatField(null=True)
    
    cpu_user_last = models.FloatField(null=True)
    cpu_user = models.TextField(null=True)
    cpu_system_last = models.FloatField(null=True)
    cpu_system = models.TextField(null=True)
    cpu_wait_last = models.FloatField(null=True)
    cpu_wait = models.TextField(null=True)
    memory_percent_last = models.FloatField(null=True)
    memory_percent = models.TextField(null=True)
    memory_megabyte_last = models.FloatField(null=True)
    memory_megabyte = models.TextField(null=True)
    swap_percent_last = models.FloatField(null=True)
    swap_percent = models.TextField(null=True)
    swap_megabyte_last = models.FloatField(null=True)
    swap_megabyte = models.TextField(null=True)
    
    @classmethod
    def update(cls, json_data, localhostname):
        s, created = cls.objects.get_or_create(localhostname=localhostname)
        s.uptime = json_data['server_uptime']
        s.address = json_data['ip_address']
        s.supervisor_user = json_data['username']
        s.supervisor_password = json_data['password']
        s.supervisor_port = json_data['port']
        s.supervisor_logtail = json_data['supervisor_logtail']
        # (sysname, nodename, release, version, machine)
        s.sysname = json_data['platform'][0]
        s.release = json_data['platform'][2]
        s.version = json_data['platform'][3]
        s.machine = json_data['platform'][4]
        s.cpu = json_data['cpu_num']
        s.memory = json_data['server_memory_total']
        s.swap = json_data['swap_total']
        
        s.server_disk_total = json_data['server_disk_total']
        s.server_disk_used = json_data['server_disk_used']
        s.server_disk_percent = json_data['server_disk_percent']
        
        # time dependent stuff:
        s.date_last = int(time.time())
        s.load_avg01_last = json_data['load_avg_all'][0]
        s.load_avg05_last = json_data['load_avg_all'][1]
        s.load_avg15_last = json_data['load_avg_all'][2]
        s.memory_percent_last = json_data['server_memory_percent']
        s.memory_megabyte_last = json_data['server_memory_megabyte']
        s.swap_percent_last = json_data['swap_percent']
        s.swap_megabyte_last = json_data['swap_megabyte']
        
        if s.cpu_time_total_last and json_data['total_time'] - s.cpu_time_total_last > 0:
            s.cpu_user_last = 100. * (json_data['user_time'] - s.cpu_user_time_last) / (json_data['total_time'] - s.cpu_time_total_last)
            s.cpu_user = json_list_append(s.cpu_user, s.cpu_user_last)
            s.cpu_system_last = 100. * (json_data['sys_time'] - s.cpu_system_time_last) / (json_data['total_time'] - s.cpu_time_total_last)
            s.cpu_system = json_list_append(s.cpu_system, s.cpu_system_last)
            s.cpu_wait_last = 100. * (json_data['wait_time'] - s.cpu_wait_time_last) / (json_data['total_time'] - s.cpu_time_total_last)
            s.cpu_wait = json_list_append(s.cpu_wait, s.cpu_wait_last)
            s.date = json_list_append(s.date, s.date_last)
            s.load_avg01 = json_list_append(s.load_avg01, s.load_avg01_last)
            s.load_avg05 = json_list_append(s.load_avg05, s.load_avg05_last)
            s.load_avg15 = json_list_append(s.load_avg15, s.load_avg15_last)
            s.memory_percent = json_list_append(s.memory_percent, s.memory_percent_last)
            s.memory_megabyte = json_list_append(s.memory_megabyte, s.memory_megabyte_last)
            s.swap_percent = json_list_append(s.swap_percent, s.swap_percent_last)
            s.swap_megabyte = json_list_append(s.swap_megabyte, s.swap_megabyte_last)
        # have to be last
        s.cpu_user_time_last = json_data['user_time']
        s.cpu_system_time_last = json_data['sys_time']
        s.cpu_wait_time_last = json_data['wait_time']
        
    
        reporting_processes = []
        for process in json_data['processes']:
            reporting_processes.append(process['name'])
            Process.update(json_data, s, process)
        # has to be very last
        s.cpu_time_total_last = json_data['total_time']
        s.save()
        remove_old_processes(s, reporting_processes)


# Service
class Process(models.Model):
    server = models.ForeignKey('Server')
    # not unique since there could be multiple server with service 'nginx', etc.
    name = models.TextField()
    uptime = models.PositiveIntegerField(null=True)
    status = models.TextField(null=True)
    pid = models.IntegerField(null=True)
    children = models.PositiveIntegerField(null=True)
    log_stderr = models.TextField(null=True)
    log_stdout = models.TextField(null=True)
    date_last = models.PositiveIntegerField(null=True)
    date = models.TextField(null=True)
    children = models.PositiveIntegerField(null=True)
    cpu_user_time_last = models.FloatField(null=True)
    cpu_sys_time_last = models.FloatField(null=True)
    cpu_user_percent_last = models.FloatField(null=True)
    cpu_user_percent = models.TextField(null=True)
    cpu_sys_percent_last = models.FloatField(null=True)
    cpu_sys_percent = models.TextField(null=True)
    memory_percent_total_last = models.FloatField(null=True)
    memory_percent_total = models.TextField(null=True)
    memory_megabyte_total_last = models.FloatField(null=True)
    memory_megabyte_total = models.TextField(null=True)

    @classmethod
    def update(cls, json_data, server, process):
        p, created = cls.objects.get_or_create(server=server,name=process['name'])
        p.uptime = process['now'] - process['start']
        p.status = process['statename']
        p.pid = process['pid']
        p.children = process['children']
        p.log_stderr = process['log_stderr']
        p.log_stdout = process['log_stdout']
        
        p.date_last = int(time.time())
        p.memory_percent_total_last = process['memory_percent_total']
        p.memory_megabyte_total_last = process['memory_megabyte_total']
        
        if p.cpu_user_time_last and p.cpu_sys_time_last and process['cpu_user_time'] and process['cpu_sys_time'] and json_data['total_time'] - server.cpu_time_total_last > 0:
            p.cpu_user_percent_last = 100. * (process['cpu_user_time'] - p.cpu_user_time_last) / (json_data['total_time'] - server.cpu_time_total_last) # important: server in denominator
            if p.cpu_user_percent_last < 0:  # after stopping and starting a service this value could be negative
                p.cpu_user_percent_last = 0.
            p.cpu_user_percent = json_list_append(p.cpu_user_percent, p.cpu_user_percent_last)
            p.cpu_sys_percent_last = 100. * (process['cpu_sys_time'] - p.cpu_sys_time_last) / (json_data['total_time'] - server.cpu_time_total_last)
            if p.cpu_sys_percent_last < 0:
                p.cpu_sys_percent_last = 0.
            p.cpu_sys_percent = json_list_append(p.cpu_sys_percent, p.cpu_sys_percent_last)
            p.date = json_list_append(p.date, p.date_last)
            p.memory_percent_total = json_list_append(p.memory_percent_total, p.memory_percent_total_last)
            p.memory_megabyte_total = json_list_append(p.memory_megabyte_total, p.memory_megabyte_total_last)
        # has to be last:
        p.cpu_user_time_last = process['cpu_user_time']
        p.cpu_sys_time_last = process['cpu_sys_time']
        p.save()

def json_list_append(json_list, value):
    try:
      new_list = json.loads(json_list)
      new_list.append(value)
    except:
      new_list = [value]
    # maximum allowed table size, if monit reports every monite, this stores data for one week
    maximum_table_length = int(maximum_store_days*24.*60.*60./update_period)
    # just remove the first one, should be better in future
    if len(new_list) > maximum_table_length:
      new_list = new_list[-int(maximum_table_length):]
    return json.dumps(new_list)

def remove_old_processes(server, process_list):
    processes = server.process_set.all()
    for process in processes:
        if process.name not in process_list:
            process.delete()

def collect_data(json_str):
    # only ready data if it has a server name
    # try:
    json_data = json.loads(json_str)
    localhostname = json_data['localhostname']
    # except:
        # return False
    Server.update(json_data, localhostname)
    return True
    
