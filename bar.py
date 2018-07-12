import argparse
import blocks
import subprocess
import sys
from time import sleep
from yaml import load


class Bar:
    def __init__(self, update_interval=1, offset={'x':0, 'y':0},
                 dimensions={'w':'all', 'h':20}, fonts=None,
                 xresources=True, colors=None, underline_thickness=1):
        self.update_interval = update_interval

        self.offset = offset
        self.dimensions = dimensions
        self.fonts = fonts
        self.underline_thickness = underline_thickness
        #TODO:
        self.colors = self._load_xresources() if xresources else colors

        self.command = 'lemonbar -d -p'.split()
        for font in self.fonts:
            self.command += ['-f', font['str'],
                             '-o', str(font['offset'])]
        self.command += ['-g',
                         '{w}x{h}+{x}+{y}'.format(**self.dimensions,
                                                  **self.offset)]
        self.command += ['-u', str(self.underline_thickness)]
        self.command += ['-F', self.colors['foreground'],
                         '-B', self.colors['background']]

        self.callback_blocks = []
        self.blocks = []

    def _load_xresources(self):
        # TODO
        pass

    def add_block(self, block):
        # if hasattr(block, 'foreground') and not block.foreground:
        #     block.foreground = self.__foreground
        # if hasattr(block, 'background') and not block.background:
        #     block.background = self.__background

        # if block.is_callback_block:
        if False:
            self.callback_blocks.append(block)
        else:
            self.blocks.append(block)

    def add_blocks(self, blocks):
        for block in blocks:
            self.add_block(block)

    def feed(self):
        return ''.join([b() for b in self.blocks]) + '\n'

    def start(self, feed_only=False):
        if not feed_only:
            lemonbar = subprocess.Popen(self.command, stdin=subprocess.PIPE)

        while True:
            if feed_only:
                print(self.feed(), end='')
                sys.stdout.flush()
            else:
                lemonbar.stdin.write(self.feed().encode())
                lemonbar.stdin.flush()

            sleep(self.update_interval)


def main():
    from pprint import pprint
    parser = argparse.ArgumentParser(description='Feed script for LemonBar')
    parser.add_argument('-c', '--config', default='config.yaml', help='YAML Config file')
    parser.add_argument('-f', '--feed', action='store_true', help='Only print feed data (don\'t start lemonbar')
    args = parser.parse_args()

    try:
        config = load(open(args.config))
    except FileNotFoundError:
        print('Config file not found!')
        sys.exit(1)
    pprint(config.get('lemonbar'))

    # bar = Bar(delay=.1)
    bar = Bar(**config.get('lemonbar'))

    bar.add_blocks([
            blocks.Align('l'),
            blocks.Workspaces(monitor='eDP1',
                              padding=(2, 5)),
            blocks.Static(text='Notice the fog.'),
            blocks.Volume(interval=1),

            blocks.Align('c'),
            blocks.Clock(swap=True),

            blocks.Align('r'),
            # blocks.Weather(location='haren,gn',
            #                apikey='7c8ca2cd7dcab68d7f9e4d08a2a08595',
            #                append='°C'),
            blocks.Memory(append='M'),
            blocks.IPAddress(interface='wlp1s0'),
            blocks.Ping(append='ms', host='vps298888.ovh.net'),
            # blocks.Workspaces(monitor='DVI-I-0',
            #                   padding=(5, 2))
    ])

    try:
        bar.start()
    except KeyboardInterrupt:
        print('Closing')


if __name__ == '__main__':
    main()
