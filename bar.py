from sys import stdout
from time import sleep
import blocks


class Bar:
    def __init__(self, delay=1, foreground='#FFFFFF', background='#000000',
                 xresources=False):
        self.__delay = delay
        if xresources:
            # TODO: Load xResources
            pass
        else:
            self.__foreground = foreground
            self.__background = background
        self.blocks = []

    def add_block(self, block):
        # if hasattr(block, 'foreground') and not block.foreground:
        #     block.foreground = self.__foreground
        # if hasattr(block, 'background') and not block.background:
        #     block.background = self.__background
        self.blocks.append(block)

    def add_blocks(self, blocks):
        for block in blocks:
            self.add_block(block)

    def render(self):
        print(''.join([b() for b in self.blocks]))
        stdout.flush()

    def start(self):
        while True:
            self.render()
            sleep(self.__delay)


def main():
    bar = Bar(delay=5)

    bar.add_blocks([
            blocks.Align('l'),
            blocks.Workspaces(monitor='DVI-D-0',
                              padding=(2, 5)),
            blocks.Static(text='Notice the fog.'),
            blocks.Volume(interval=1),

            blocks.Align('c'),
            blocks.Clock(swap=True),

            blocks.Align('r'),
            blocks.Weather(location='haren,gn',
                           apikey='7c8ca2cd7dcab68d7f9e4d08a2a08595',
                           append='°C'),
            blocks.Memory(append='M'),
            blocks.IPAddress(interface='enp3s0'),
            blocks.Ping(append='ms', host='vps298888.ovh.net'),
            blocks.Workspaces(monitor='DVI-I-0',
                              padding=(5, 2))
    ])

    try:
        bar.start()
    except KeyboardInterrupt:
        print('Closing')


if __name__ == '__main__':
    main()
