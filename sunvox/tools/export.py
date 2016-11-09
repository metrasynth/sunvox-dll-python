"""A SunVox to WAV file exporter.

Usage: python -m sunvox.tools.export FILE
       python -m sunvox.tools.export --help

Note: Before running, install the necessary packages::

    $ pip install -r requirements/tools.txt
"""

import argparse
import logging
import os
import sys

from sunvox.api import Slot
from sunvox.buffered import BufferedProcess, float32, int16


log = logging.getLogger(__name__)


parser = argparse.ArgumentParser(description='SunVox to WAV file exporter')
parser.add_argument(
    'filename',
    metavar='FILE', type=str, nargs=1,
    help='SunVox file to export')
parser.add_argument(
    '--int16',
    dest='data_type', action='store_const', const=int16,
    default=float32,
    help='Output 16-bit signed integer values')
parser.add_argument(
    '--float32',
    dest='data_type', action='store_const', const=float32,
    default=float32,
    help='Output 32-bit floating point values')
parser.add_argument(
    '--freq',
    metavar='RATE', action='store', dest='freq', type=int, nargs=1,
    default=[44100],
    help='Output frequency (44100 or 48000)')
parser.add_argument(
    '--channels',
    metavar='CHANNELS', action='store', dest='channels', type=int, nargs=1,
    default=[2],
    help='Channels (1 or 2)')
parser.add_argument(
    '--out',
    metavar='FILE', action='store', dest='out_filename', type=str, nargs=1,
    default=None,
    help='Output file to write (defaults to "inputname.wav")')


def main():
    logging.basicConfig(level=logging.DEBUG)
    try:
        import numpy as np
        from scipy.io import wavfile
        from tqdm import tqdm
    except ImportError:
        log.error('Please "pip install -r requirements/tools.txt" '
                  'to use sunvox.tools.export')
        return 1
    args = parser.parse_args()
    in_filename = args.filename[0]
    out_filename = args.out_filename and args.out_filename[0]
    if not out_filename:
        root, ext = os.path.splitext(in_filename)
        out_filename = '{}.wav'.format(root)
    data_type = args.data_type
    freq = args.freq[0]
    channels = args.channels[0]
    log.debug('%r', channels)
    log.debug('Start SunVox process')
    p = BufferedProcess(
        freq=freq, size=freq, channels=channels, data_type=data_type)
    slot = Slot(in_filename, process=p)
    length = slot.get_song_length_frames()
    output = np.zeros((length, 2), data_type)
    position = 0
    log.info('Rendering at %s frames/sec, %s channels, %s resolution',
             freq, channels, data_type.__name__)
    slot.play_from_beginning()
    pbar = tqdm(total=length, unit_scale=True, unit='frame',
                dynamic_ncols=True)
    with pbar as pbar:
        while position < length:
            buffer = p.fill_buffer()
            end_pos = min(position + freq, length)
            copy_size = end_pos - position
            output[position:end_pos] = buffer[:copy_size]
            position = end_pos
            pbar.update(copy_size)
    log.info('Saving to %r', out_filename)
    wavfile.write(out_filename, freq, output)
    log.debug('Stop SunVox process')
    p.deinit()
    p.kill()
    log.info('Finished')


if __name__ == '__main__':
    sys.exit(main())
