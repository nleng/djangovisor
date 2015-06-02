from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import  render, redirect
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
import subprocess
import xmlrpclib
import socket

from django.conf import settings
from djangovisor.models import collect_data, Server, Process

update_period = getattr(settings, 'UPDATE_PERIOD', 60)

@csrf_exempt
def collector(request):
    # only allow POSTs
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    data = request.body
    
    # for testing
    # with open("json.txt", "w") as f:
        # f.write(data)
    
    collected = collect_data(data)
    if not collected:
        return HttpResponse('wrong data format')
    return HttpResponse(collected)
   
@staff_member_required
def dashboard(request):
    if Server.objects.all().count() > 0:
        servers = Server.objects.all().order_by('localhostname')
        return render(request, 'djangovisor/dashboard.html',{'servers': servers, 'server_found': True})
    else:
       return render(request, 'djangovisor/dashboard.html',{'server_found': False})

@staff_member_required
def server(request, server_id):
    # time = datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
    # timedelta = (datetime.now()-load.date).total_seconds()*1000.
    try:
        server = Server.objects.get(id=server_id)
        processes = server.process_set.all().order_by('name')
        return render(request, 'djangovisor/server.html',{'server': server, 'processes':processes, 'update_period': update_period})
    except ObjectDoesNotExist:
        return render(request, 'djangovisor/dashboard.html',{'server_found': False})

@staff_member_required
def process(request, server_id, process_name):
  try:
    server = Server.objects.get(id=server_id)
    process = server.process_set.get(name=process_name)
    return render(request, 'djangovisor/process.html',{'process_found': True, 'server': server, 'process': process, 'update_period': update_period})
  except ObjectDoesNotExist:
    return render(request, 'djangovisor/process.html',{'process_found': False})

@staff_member_required
def process_action(request, server_id):
    if not request.POST:
        return HttpResponseNotAllowed(['POST'])
    action = request.POST['action']
    process_name = request.POST['process']
    server = Server.objects.get(id=server_id)
    process = server.process_set.get(name=process_name)
    supervisor_url = 'http://%s:%s@localhost:%s/RPC2' % (server.supervisor_user, server.supervisor_password, server.supervisor_port)
    time_out = 20
    try:
        # set the timeout to 10 seconds 
        supervisor = xmlrpclib.Server(supervisor_url).supervisor
        socket.setdefaulttimeout(time_out) 
        if action == 'start':
            supervisor.startProcess(process_name)
        elif action == 'stop':
            supervisor.stopProcess(process_name) # , wait=True
        elif action == 'restart':
            supervisor.stopProcess(process_name)
            supervisor.startProcess(process_name)
        
        # action_labels = {'start': 'starting...', 'stop': 'stopping...', 'restart': 'restarting...'}
        # if action in action_labels:
        #     process.status = action_labels.get(action)
        #     process.save()
        process.status = supervisor.getProcessInfo(process_name)['statename']
        process.save()
        socket.setdefaulttimeout(None)
        return redirect(reverse('djangovisor.views.process', kwargs={'server_id': server.id, 'process_name': process_name}))  # '/djangovisor/server/%s/process/%s' % (server.id, process_name)
    except:
        return render(request, 'monitcollector/error.html', {'time_out': time_out, 'supervisor_user': supervisor_user, 'ip_address': ip_address, 'supervisor_port': supervisor_port, 'process_name': process_name})

@staff_member_required
def confirm_delete(request, server_id):
    server = Server.objects.get(id=server_id)
    return render(request, "djangovisor/confirm_delete.html", {"server": server})

@staff_member_required
def delete_server(request, server_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    server = Server.objects.get(id=server_id)
    server.delete()
    return redirect(reverse('djangovisor.views.dashboard'))

### ajax loading views ###
def load_dashboard_table(request):
    servers = Server.objects.all().order_by('localhostname')
    table_html = render_to_string('djangovisor/includes/dashboard_table.html',{'servers': servers})
    return JsonResponse({'table_html': table_html})

def load_server_table(request, server_id):
    server = Server.objects.get(id=server_id)
    processes = server.process_set.all().order_by('name')
    table_html = render_to_string('djangovisor/includes/server_table.html',{'server': server, 'processes': processes})
    log_html = render_to_string('djangovisor/includes/server_log.html',{'server': server})
    return JsonResponse({'table_html': table_html, 'log_html': log_html})

def load_process_table(request, server_id, process_name):
    server = Server.objects.get(id=server_id)
    process = server.process_set.get(name=process_name)
    table_html = render_to_string('djangovisor/includes/process_table.html',{'process': process})
    log_html = render_to_string('djangovisor/includes/process_log.html',{'process': process})
    return JsonResponse({'table_html': table_html, 'log_html': log_html})

def load_server_data(request, server_id):
    server = Server.objects.get(id=server_id)
    processes = server.process_set.all().order_by('name')
    table_html = render_to_string('djangovisor/includes/server_table.html',{'server': server, 'processes': processes})
    data = {'table_html': table_html, 'date': server.date_last, 'load_avg01': server.load_avg01_last,
            'load_avg05': server.load_avg05_last, 'load_avg15': server.load_avg15_last, 'cpu_user': server.cpu_user_last,
            'cpu_system': server.cpu_system_last, 'cpu_wait': server.cpu_wait_last, 'memory_percent': server.memory_percent_last,
            'memory_megabyte': server.memory_megabyte_last, 'swap_percent': server.swap_percent_last, 'swap_megabyte': server.swap_megabyte_last}
    return JsonResponse(data)

def load_process_data(request, server_id, process_name):
    server = Server.objects.get(id=server_id)
    process = server.process_set.get(name=process_name)
    table_html = render_to_string('djangovisor/includes/process_table.html',{'process': process})
    data = {'date': process.date_last, 'cpu_user_percent': process.cpu_user_percent_last, 'cpu_sys_percent': process.cpu_sys_percent_last,
            'memory_percent_total': process.memory_percent_total_last, 'memory_megabyte_total': process.memory_megabyte_total_last}
    return JsonResponse(data)

# checks if this is the server where djangovisor is installed
def check_this_server(server):
    if server.localhostname == socket.gethostname():
        return True
    return False


