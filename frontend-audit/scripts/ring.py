#!/usr/bin/env python3
"""Preview a crop with its highlight boxes drawn the way the review report draws them.

Usage: python3 ring.py <crop.png> <preview.png> "x,y,w,h" ["x,y,w,h" ...]

Boxes are in the crop's own pixels. The rest of the picture is dimmed and each box
is ringed, so a box that is off shows at once. The crop itself is never changed.
"""
import sys

from PIL import Image, ImageDraw

RING = '#ff2d8a'
RING_WIDTH = 3
DIM = 0.5


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    boxes = [tuple(int(v) for v in arg.split(',')) for arg in sys.argv[3:]]
    img = Image.open(src).convert('RGB')
    w, h = img.size
    for x, y, bw, bh in boxes:
        if bw <= 0 or bh <= 0 or x < 0 or y < 0 or x + bw > w or y + bh > h:
            sys.exit('box %s is outside the %dx%d picture' % ((x, y, bw, bh), w, h))
    if boxes:
        dimmed = Image.blend(img, Image.new('RGB', img.size, '#000000'), 1 - DIM)
        for x, y, bw, bh in boxes:
            dimmed.paste(img.crop((x, y, x + bw, y + bh)), (x, y))
        draw = ImageDraw.Draw(dimmed)
        for x, y, bw, bh in boxes:
            draw.rectangle((x, y, x + bw - 1, y + bh - 1), outline=RING, width=RING_WIDTH)
        img = dimmed
    img.save(out)
    print('wrote %s (%dx%d, %d box%s)' % (out, w, h, len(boxes), '' if len(boxes) == 1 else 'es'))


if __name__ == '__main__':
    main()
