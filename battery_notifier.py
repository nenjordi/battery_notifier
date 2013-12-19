#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Jordi Ortiz (jordi.ortiz@um.es)
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os, time
from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent

batcapacityfilename='/sys/class/power_supply/BAT0/capacity'
batpowerfilename='/sys/class/power_supply/BAT0/power_now'
batstatusfilename='/sys/class/power_supply/BAT0/status'
batfullenergyfilename='/sys/class/power_supply/BAT0/energy_full'
batalarmfilename='/sys/class/power_supply/BAT0/alarm'
batnowenergyfilename='/sys/class/power_supply/BAT0/energy_now'

energy_full=''
alarm=''
try:
    fullfile = open(batfullenergyfilename,'r')
    energy_full = fullfile.readline().replace('\n','')
    alarmfile = open(batalarmfilename,'r')
    alarm = alarmfile.readline().replace('\n','')
    fullfile.close()
    alarmfile.close()
except:
    print('Error opening file')
    sys.exit(1)

class PTmp(ProcessEvent):
    def process_IN_ACCESS(self, event):
        try:
            batfile = open(batcapacityfilename, 'r')
            statusfile = open(batstatusfilename, 'r')
            cap = int(batfile.readline())
            stat = statusfile.readline()
            stat = stat.replace('\n','')
            batfile.close()
            statusfile.close()

            energynowfile = open(batnowenergyfilename, 'r')
            energy_now = energynowfile.readline().replace('\n', '')
        except:
            print('Error opening file ' + batfile)
        if stat=='Discharging' and cap==1:
            os.system('notify-send -u critical "BATTERY" "BATTERY IS DISCHARGING %s. POWERING OFF"' % cap)
            time.sleep(5)
            os.system('systemctl poweroff -i')

        if energy_now == energy_full:
            os.system('notify-send -u low "BATTERY" "BATTERY IS FULL"')
        if int(energy_now) < int(alarm):
            os.system('notify-send -u CRITICAL "BATTERY" "BATTERY LEVEL IS CRITICAL. SUSPENDING IN 5 SECONDS"')
            time.sleep(5)
            os.system('systemctl suspend -i')
        if stat=='Discharging' and cap < 5:
            os.system('notify-send -u critical "BATTERY" "BATTERY IS DISCHARGING %s"' % cap)
            time.sleep(5)
            os.system('systemctl suspend -i')

    def process_IN_DELETE(self, event):
        print("Remove: %s" %  os.path.join(event.path, event.name))


wm = WatchManager()
mask = EventsCodes.FLAG_COLLECTIONS['OP_FLAGS']['IN_ACCESS'] | EventsCodes.FLAG_COLLECTIONS['OP_FLAGS']['IN_DELETE']  # watched events
fillnotifier = Notifier(wm,PTmp())
wdd = wm.add_watch(batpowerfilename, mask, rec=True)

while True:
    try:
       fillnotifier.process_events()
       if fillnotifier.check_events():
            fillnotifier.read_events()
    except Exception:
        fillnotifier.stop()
        break
