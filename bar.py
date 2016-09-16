from sys import stdout
from time import sleep
import blocks


class Bar:
    def __init__(self, delay=5):
        self.__delay = delay
        self.blocks = []

    def add_block(self, block):
        self.blocks.append(block)

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

    bar.add_block(blocks.Align('l'))
    bar.add_block(blocks.Volume(interval=1, padding=(5, 2)))
    bar.add_block(blocks.ActiveWindow())

    bar.add_block(blocks.Align('c'))
    bar.add_block(blocks.Workspaces())

    bar.add_block(blocks.Align('r'))
    bar.add_block(blocks.Weather(location='haren,gn',
                                 apikey='7c8ca2cd7dcab68d7f9e4d08a2a08595',
                                 padding=(0, 2)))
    bar.add_block(blocks.Clock())

    try:
        bar.start()
    except KeyboardInterrupt:
        print('Closing')


if __name__ == '__main__':
    main()
