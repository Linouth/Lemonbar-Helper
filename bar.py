from sys import stdout
from time import sleep
import blocks


class Bar:
    def __init__(self, delay=5):
        self.__delay = delay
        self.blocks = []

    def add_block(self, block):
        self.blocks.append(block)

    def add_blocks(self, blocks):
        for block in blocks:
            self.add_block(block)

    def render(self):
        # for block in self.blocks:
        #     block.update()
        print(''.join([b() for b in self.blocks]))
        stdout.flush()

    def start(self):
        while True:
            self.render()
            sleep(self.__delay)


def main():
    bar = Bar()

    bar.add_blocks([
            blocks.Align('l'),
            blocks.Workspaces(monitor='DVI-D-0'),
            blocks.Static(text='Notice the fog.', padding=(5, 2)),
            blocks.Volume(interval=1),

            blocks.Align('c'),
            blocks.Clock(),

            blocks.Align('r'),
            blocks.Weather(location='haren,gn',
                           apikey='7c8ca2cd7dcab68d7f9e4d08a2a08595',
                           padding=(0, 5)),
            blocks.Workspaces(monitor='DVI-I-0')
    ])

    try:
        bar.start()
    except KeyboardInterrupt:
        print('Closing')


if __name__ == '__main__':
    main()
