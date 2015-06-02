# djangovisor

This is a django project, which collects data from <a href="https://github.com/Supervisor/supervisor" target="_blank">supervisor</a> instances on one or multiple servers, stores it and plots it it using <a href="http://getbootstrap.com/" target="_blank">bootstrap</a> and the javascript library <a href="http://dygraphs.com/" target="_blank">dygraphs</a>. Example website: http://djangovisor.cfs-me-research.net/djangovisor/. 

There is a very similar app for the server monitoring tool <a href="https://mmonit.com/monit/" target="_blank">monit</a> called <a href="https://github.com/nleng/django-monit-collector" target="_blank">django-monit-collector</a>.

### Features
- Collects supervisor data from one or multiple servers. 
- Collects process cpu and memory usage and stores the data for a given time period. 
- Displays it in pretty graphs. 
- Start/stop/restart buttons for processes. 
- Shows the tails of spuervisor and process specific logfiles. 
- Status tables and graphs are refreshing automatically via ajax.
- Processes are automatically removed when they stop sending data (removed from supervisord.conf). Servers can be deleted manually.

### Installation

Just install it via pip:
```
pip install djangovisor
```
Or clone the repository if you want to modify the code:
```
git clone https://github.com/nleng/djangovisor
```

Add 'djangovisor' to your installed apps in settings.py:
```
INSTALLED_APPS = [
    'djangovisor',
    # ...
]
```
Include djangovisor in your url.py:
```
url(r'^djangovisor/', include('djangovisor.urls')),
```
On every server that should be monitored enable the xml web interface in your supervisord.conf:
```
[inet_http_server]
port=*:9001
username=yourname
password=yourpassword
```
If you use another port, you would have to change it in the sender.py script. Also, the port must not be blocked by the firewall, e.g.
```
ufw allow 9001
```
Since supervisor does not send process cpu and memory information, we use a script sender.py, which you have to copy to any server you want to observe. 
You have to change the user and password in the script sender.py. Then the simplest solution is to just run a cronjob, e.g. every minute:
```
crontab -e
* * * * * /usr/bin/python /path/to/sender.py
```
You can also use the script sender_psutil.py if you prefer using the library psutil, which has to be installed. 

If you want to you can change the default values in your settings.py:
```
# in seconds, should be the same as set in the crontab
UPDATE_PERIOD = 60
# maximum days to store data, only correct, if UPDATE_PERIOD is set correctly
MAXIMUM_STORE_DAYS = 7
```
Set up your webserver and run:
```
python manage.py collectstatic
python manage.py migrate
python manage.py createsuperuser
```

### License
BSD License.

