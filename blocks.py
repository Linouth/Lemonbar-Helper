from alsaaudio import Mixer
from datetime import datetime
import fcntl
import i3ipc
import json
import re
import socket
import struct
import subprocess
from time import time
from urllib.request import urlopen

import gi
gi.require_version('Playerctl', '1.0')
from gi.repository import Playerctl


class Base:
    is_callback_block = False
    display = True

    def __init__(self, icon='', interval=1, margin=0, padding=0, 
                 foreground=None, background=None, swap=False):
        self.interval = interval

        template = '{value}'

        # Set icon
        if icon:
            template = '{} '.format(icon) + template

        # Set padding
        if padding:
            template = self.__set_spacing(padding, template)

        # Setting colors
        if foreground:
            template = '%{{F{}}}'.format(foreground) + template + '%{{F-}}'
        if background:
            template = '%{{B{}}}'.format(background) + template + '%{{B-}}'
        if swap:
            template = '%{{R}}' + template + '%{{R}}'

        # Set margin
        if margin:
            template = self.__set_spacing(margin, template)

        self.template = template
        self.output = ''
    
    @staticmethod
    def __set_spacing(spacing, o):
        if type(spacing) == list:
            l = ' '*spacing[0]
            r = ' '*spacing[1]
        else:
            l = ' '*spacing
            r = ' '*spacing
        return l + o + r

    def __call__(self):
        raise NotImplementedError('Function needs to be implemented')


class Widget(Base):
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.prevtime = 0

    def __call__(self):
        if self.interval == -1:
            # Only call update once
            if self.prevtime != -1:
                self.update()
                self.prevtime = -1
        elif time() >= self.prevtime + self.interval:
            self.update()
            self.prevtime = time()

        if self.display:
            return self.template.format(value=self.output)
        return ''

    def update(self):
        raise NotImplementedError('Function needs to be implemented')


class Raw(Base):
    def __init__(self, text='', **kwds):
        super().__init__(**kwds)
        self.output = text

    def __call__(self):
        return self.template.format(value=self.output)


class Align(Raw):
    def __init__(self, align, **kwds):
        super().__init__(**kwds)
        self.output = '%{{{}}}'.format(align)


class Clock(Widget):
    def __init__(self, layout='%d %b %Y %H:%M:%S', **kwds):
        super().__init__(**kwds)
        self.layout = layout

    def update(self):
        self.output = datetime.today().strftime(self.layout)


class Volume(Widget):
    def update(self):
        m = Mixer()
        self.output = '{}%'.format(m.getvolume()[0])


class WorkspacesDots(Widget):
    i3 = i3ipc.Connection()

    def __init__(self, underline=None,
                 icons={'empty': 'o', 'nonempty': '0',
                        'visible': 'x'}, **kwds):
        super().__init__(**kwds)
        self.icons = icons
        self.underline = underline

    def update(self):
        out = [self.icons['empty'] for __ in range(9)]
        for workspace in self.i3.get_workspaces():
            ind = int(workspace['num']) - 1
            if ind < 0: ind = 10
            
            if workspace['visible']:
                out[ind] = self.icons['visible']
            else:
                out[ind] = self.icons['nonempty']

            if workspace['focused']:
                out[ind] = '%{!u}' + out[ind] + '%{!u}'

        self.output = ' '.join(out)
        
        if self.underline:
            self.output = '%{{U{}}}'.format(self.underline)\
                          + self.output + '%{U-}'


class Memory(Widget):
    def __init__(self, percentage=False, interval=5, **kwds):
        super().__init__(interval=interval, **kwds)
        self.percentage = percentage

    def update(self):
        with open('/proc/meminfo', 'r') as mem:
            total = 0
            available = 0
            for line in mem:
                line_split = line.split()
                if line_split[0] == 'MemTotal:':
                    total = int(line_split[1])
                elif line_split[0] in ['MemFree:', 'Buffers:', 'Cached:']:
                    available += int(line_split[1])
        used_mb = round((total-available)/1024)
        used_perc = round((available/total)*100)
        self.output = used_perc if self.percentage else used_mb
        self.output = str(self.output) + 'M'


class IPAddress(Widget):
    def __init__(self, interface='eth0', interval=900, **kwds):
        super().__init__(interval=interval, **kwds)
        self.interface = interface.encode('utf-8')

    def update(self):
        def get_ip_address(ifname):
            # Props to 'Martin Konecny' on SO
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15])
            )[20:24])
        self.output = get_ip_address(self.interface)


class Ping(Widget):
    def __init__(self, host='8.8.8.8', interval=5, **kwds):
        super().__init__(interval=interval, **kwds)
        self.host = host

    def update(self):
        ping = subprocess.Popen('ping -c1 -W1 {}'.format(self.host),
                                shell=True, stdout=subprocess.PIPE
                                ).stdout.read()
        reg = re.search('\d\d\.\d{3}/(\d\d\.\d{3})/\d\d\.\d{3}',
                        ping.decode())
        if reg:
            self.output = round(float(reg.groups()[0]))
        else:
            self.output = 0
        self.output = str(self.output) + 'ms'


class Music(Widget):
    player = Playerctl.Player()

    def update(self):
        if self.player.get_property('status') == 'Playing':
            self.display = True
            self.output = '{} - {}'.format(self.player.get_artist(),
                                           self.player.get_title())
        else:
            self.display = False


class Battery(Widget):
    ''' Load from sys class '''
    def __init__(self, power_supply='BAT0',
                 icons={'charging': 'c', 'discharging': 'd'}, **kwds):
        super().__init__(**kwds)
        self.power_supply = power_supply
        self.icons = icons

    def update(self):
        with open('/sys/class/power_supply/{}/status'\
                  .format(self.power_supply), 'r') as f:
            charging = 'Charging' in f.read()

        with open('/sys/class/power_supply/{}/capacity'\
                  .format(self.power_supply), 'r') as f:
            capacity = f.read()

        if charging:
            self.output = '{} '.format(self.icons['charging'])
        else:
            self.output = '{} '.format(self.icons['discharging'])
        self.output += '{}%'.format(capacity)


class Wifi(Widget):
    def __init__(self, interface='wlan0', **kwds):
        super().__init__(**kwds)
        self.interface = interface

    def update(self):
        ssid = subprocess.check_output(['iw', 'dev', self.interface, 'info'])
        for l in ssid.split(b'\n\t'):
            if l.startswith(b'ssid'):
                self.output = l[5:].decode()
    
