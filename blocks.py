from datetime import datetime
from time import time
from alsaaudio import Mixer
import i3ipc
from urllib.request import urlopen
import json


class Base:
    i3 = i3ipc.Connection()

    def __init__(self, icon='', interval=1, padding=0):
        self.__icon = icon
        # self.__template = '%{{{align}}}%{{{foreground}}}%{{{background}}}{value}%{{F-}}%{{B-}}'
        self.__interval = interval
        self.__prevtime = 0
        self.__padding = padding
        self.output = ''

    def __call__(self):
        if self.__interval == -1:
            if self.__prevtime != -1:
                self.update()
                self.__prevtime = -1
        elif time() >= self.__prevtime + self.__interval:
            self.update()
            self.__prevtime = time()

        conf = dict(
                    lpadding=' ' * (self.__padding[0] if type(self.__padding)
                                    == tuple else self.__padding),
                    rpadding=' ' * (self.__padding[1] if type(self.__padding)
                                    == tuple else self.__padding),
                    icon=self.__icon,
                    value=self.output
                )
        return '{lpadding}{value}{rpadding}'.format_map(conf)

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
