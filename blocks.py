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


class Base:
    i3 = i3ipc.Connection()

    def __init__(self, icon='', interval=1, padding=1, prepend='', append='',
                 foreground=None, background=None, swap=False):
        self.__icon = icon

        self.__template = '{lpadding}{prepend}{value}{append}{rpadding}'
        self.__fg = lambda o: '%{{F{foreground}}}' + o + '%{{F-}}'
        self.__bg = lambda o: '%{{B{background}}}' + o + '%{{B-}}'
        self.__swap = lambda o: '%{{R}}' + o + '%{{R}}'

        self.__interval = interval
        self.__prevtime = 0
        self.__padding = padding
        self.__append = append
        self.__prepend = prepend

        self.foreground = foreground
        self.background = background
        self.swap = swap

        self.output = ''

    def __call__(self):
        if self.__interval == -1:
            # Only call update once
            if self.__prevtime != -1:
                self.update()
                self.__prevtime = -1
        elif time() >= self.__prevtime + self.__interval:
            self.update()
            self.__prevtime = time()

        conf = dict(
                    foreground=self.foreground,
                    background=self.background,

                    lpadding=' ' * (self.__padding[0] if type(self.__padding)
                                    == tuple else self.__padding),
                    rpadding=' ' * (self.__padding[1] if type(self.__padding)
                                    == tuple else self.__padding),
                    icon=self.__icon,
                    value=self.output,
                    append=self.__append,
                    prepend=self.__prepend
        )

        output = self.__template
        if self.foreground:
            output = self.__fg(output)
        if self.background:
            output = self.__bg(output)
        if self.swap:
            output = self.__swap(output)

        return output.format_map(conf)

    def update(self):
        raise NotImplementedError('Function needs to be implemented')


class Align:
    def __init__(self, align):
        self.__align = align

    def __call__(self):
        return '%{{{}}}'.format(self.__align)


class Clock(Base):
    def __init__(self, layout='%d %b %Y %H:%M:%S', **kwds):
        super().__init__(**kwds)
        self.layout = layout

    def update(self):
        self.output = datetime.today().strftime(self.layout)


class Volume(Base):
    def update(self):
        m = Mixer()
        self.output = m.getvolume()[0]


class ActiveWindow(Base):
    def update(self):
        self.output = self.i3.get_tree().find_focused().name


class Workspaces(Base):
    def __init__(self, activeIco='|', inactiveIco='-', monitor=None, **kwds):
        super().__init__(**kwds)
        self.activeIco = activeIco
        self.inactiveIco = inactiveIco
        self.monitor = monitor

    def update(self):
        self.output = ''

        if not self.monitor:
            ws = self.i3.get_workspaces()
            for w in ws:
                if w['focused']:
                    self.output += self.activeIco
                else:
                    self.output += self.inactiveIco
        else:
            for mon in self.i3.get_outputs():
                if mon['name'] == self.monitor:
                    self.output = mon['current_workspace']


class Weather(Base):
    def __init__(self, location='amsterdam', units='metric', apikey=None,
                 interval=600, **kwds):
        super().__init__(interval=interval, **kwds)
        self.apiurl = 'http://api.openweathermap.org/data/2.5/weather?'\
                      'q={location}&APPID={apikey}&units={units}'
        self.parameters = dict(
                location=location,
                units=units,
                apikey=apikey
        )

    def update(self):
        if self.parameters['apikey']:
            res = urlopen(self.apiurl.format(**self.parameters))
            data = json.loads(res.read().decode())
            self.output = round(data['main']['temp'], 1)


class Static(Base):
    def __init__(self, text='', interval=-1, **kwds):
        super().__init__(interval=interval, **kwds)
        self.text = text

    def update(self):
        self.output = self.text


class Memory(Base):
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


class IPAddress(Base):
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


class Ping(Base):
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
