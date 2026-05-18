"""Pure-stdlib PNG writer — no external dependencies, no FreeCAD."""
import struct
import zlib


def write_png(width, height, pixels):
    """
    Encode an RGB image to PNG bytes.

    Args:
        width, height: image dimensions in pixels
        pixels:        flat list of (R, G, B) tuples, row-major, top-left first.
                       Each channel must be 0–255.

    Returns:
        bytes — a complete, valid PNG file.
    """
    def _chunk(tag, data):
        payload = tag + data
        return (struct.pack('>I', len(data))
                + payload
                + struct.pack('>I', zlib.crc32(payload) & 0xFFFFFFFF))

    # IHDR: width, height, bit_depth=8, color_type=2 (RGB), compress=0, filter=0, interlace=0
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)

    rows = bytearray()
    for y in range(height):
        rows.append(0)  # filter byte: None
        for x in range(width):
            r, g, b = pixels[y * width + x]
            rows += bytes([r & 0xFF, g & 0xFF, b & 0xFF])

    return (
        b'\x89PNG\r\n\x1a\n'
        + _chunk(b'IHDR', ihdr)
        + _chunk(b'IDAT', zlib.compress(bytes(rows), 6))
        + _chunk(b'IEND', b'')
    )
