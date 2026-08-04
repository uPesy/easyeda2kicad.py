from __future__ import annotations

import base64
import struct
import textwrap

import zstandard

_HASH_SEED = 0xABBA2345
_MASK_64 = (1 << 64) - 1
_MIME_BASE64_LENGTH = 76


def _rotate_left_64(value: int, bits: int) -> int:
    return ((value << bits) | (value >> (64 - bits))) & _MASK_64


def _fmix_64(value: int) -> int:
    value ^= value >> 33
    value = (value * 0xFF51AFD7ED558CCD) & _MASK_64
    value ^= value >> 33
    value = (value * 0xC4CEB9FE1A85EC53) & _MASK_64
    value ^= value >> 33
    return value


def kicad_embedded_checksum(data: bytes) -> str:
    """Return the checksum used by KiCad's embedded-file container.

    KiCad uses its streaming MMH3_HASH implementation with a fixed seed. Its
    tail padding differs from the usual one-shot MurmurHash3 x64-128 function,
    so this deliberately mirrors KiCad rather than using a generic hash module.
    """
    c1 = 0x87C37B91114253D5
    c2 = 0x4CF5AD432745937F
    h1 = _HASH_SEED
    h2 = _HASH_SEED

    offset = 0
    while len(data) - offset >= 16:
        k1, k2 = struct.unpack_from("<QQ", data, offset)

        k1 = (k1 * c1) & _MASK_64
        k1 = _rotate_left_64(k1, 31)
        k1 = (k1 * c2) & _MASK_64
        h1 ^= k1

        h1 = _rotate_left_64(h1, 27)
        h1 = (h1 + h2) & _MASK_64
        h1 = (h1 * 5 + 0x52DCE729) & _MASK_64

        k2 = (k2 * c2) & _MASK_64
        k2 = _rotate_left_64(k2, 33)
        k2 = (k2 * c1) & _MASK_64
        h2 ^= k2

        h2 = _rotate_left_64(h2, 31)
        h2 = (h2 + h1) & _MASK_64
        h2 = (h2 * 5 + 0x38495AB5) & _MASK_64

        offset += 16

    remaining = len(data) - offset
    padding = 4 - ((remaining + 4) % 4) if remaining else 0
    padded_length = len(data) + padding
    tail_size = padded_length & 15

    if tail_size:
        tail = data[offset:] + bytes(padding)
        k1 = int.from_bytes(tail[: min(tail_size, 8)], "little")
        k1 = (k1 * c1) & _MASK_64
        k1 = _rotate_left_64(k1, 31)
        k1 = (k1 * c2) & _MASK_64
        h1 ^= k1

        if tail_size > 8:
            k2 = int.from_bytes(tail[8:tail_size], "little")
            k2 = (k2 * c2) & _MASK_64
            k2 = _rotate_left_64(k2, 33)
            k2 = (k2 * c1) & _MASK_64
            h2 ^= k2

    h1 ^= padded_length
    h2 ^= padded_length
    h1 = (h1 + h2) & _MASK_64
    h2 = (h2 + h1) & _MASK_64
    h1 = _fmix_64(h1)
    h2 = _fmix_64(h2)
    h1 = (h1 + h2) & _MASK_64
    h2 = (h2 + h1) & _MASK_64

    return f"{h1:016X}{h2:016X}"


def format_embedded_model(name: str, data: str | bytes) -> str:
    """Format a WRL model using KiCad's embedded-files S-expression."""
    model_data = data.encode("utf-8") if isinstance(data, str) else data
    compressed = zstandard.ZstdCompressor(level=15).compress(model_data)
    encoded = base64.b64encode(compressed).decode("ascii")
    chunks = textwrap.wrap(encoded, width=_MIME_BASE64_LENGTH)
    escaped_name = name.replace("\\", "\\\\").replace('"', '\\"')

    output = (
        "\t(embedded_fonts no)\n"
        "\t(embedded_files\n"
        "\t\t(file\n"
        f'\t\t\t(name "{escaped_name}")\n'
        "\t\t\t(type model)\n"
    )

    for index, chunk in enumerate(chunks):
        prefix = "\t\t\t(data |" if index == 0 else "\t\t\t\t"
        suffix = "|\n" if index == len(chunks) - 1 else "\n"
        output += f"{prefix}{chunk}{suffix}"

    output += (
        "\t\t\t)\n"
        f'\t\t\t(checksum "{kicad_embedded_checksum(model_data)}")\n'
        "\t\t)\n"
        "\t)\n"
    )
    return output
