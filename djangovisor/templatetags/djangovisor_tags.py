from django import template
from django.utils import timezone
import time
import settings
register = template.Library()

try:
    monit_update_period = settings.MONIT_UPDATE_PERIOD
except:
    monit_update_period = 60

@register.filter
def timestamp_to_date(timestamp):
    if not isinstance(timestamp, int):
        return ""
    return timezone.datetime.fromtimestamp(timestamp)

@register.filter
def time_class(timestamp):
    if not isinstance(timestamp, int):
        return ""
    if int(time.time()) > int(timestamp) + 3*monit_update_period:
        return "danger"
    return ""

@register.filter
def time_str(uptime):
    """ converts uptime in seconds to a time string """
    if not isinstance(uptime, int):
        return ""
    mins = (uptime/60) % 60
    hours = (uptime/60/60) % 24
    days = (uptime/24/60/60) % 365
    years = uptime/365/24/60/60
    if years == 0:
      if days == 0:
        if hours == 0:
          return "%sm" % mins
        return "%sh %sm" % (hours, mins)
      return "%sd %sh %sm" % (days, hours, mins)
    return "%sy %sd %sh %sm" % (years, days, hours, mins)

@register.filter
def status_class(status):
    if status == 'RUNNING':
        return 'green'
    elif status == 'STOPPED':
        return 'blue'
    if status in ['	STARTING', 'STOPPING', 'RESTARTING']:
        return 'yellow'
    # else return error color
    return 'red'

@register.filter
def last_item(item_list_str):
  if not isinstance(item_list_str, basestring):
    return ""
  item_list = item_list_str.strip('[]').split()
  if len(item_list) <1:
    return ""
  return item_list[-1]

@register.filter
def in_MB(value):
    if not isinstance(value, float):
        return ""
    return str(round(value, 1))+" MB"

@register.filter
def in_GB(value):
    if not isinstance(value, float):
        return ""
    return str(round(value/1000., 1))+" GB"

@register.filter
def percent(value):
    if not isinstance(value, float):
        return "wait another update"
    return str(round(value, 1))+"%"

@register.filter
def line_breaks(string):
    return string.replace('\\n', '\n')

