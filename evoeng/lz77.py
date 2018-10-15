import struct
from io import BytesIO
from typing import BinaryIO


class LZ77Error(Exception):
	pass


def lz_decompress(cache: BinaryIO, decompressed_size: int) -> bytes:
	ret = BytesIO()

	size = 0
	while size < decompressed_size:
		comp_len, decomp_len = struct.unpack(">HH", cache.read(4))
		compressed = cache.read(comp_len)

		if comp_len == decomp_len:
			decompressed = compressed
		else:
			decompressed = b""
			pos = 0
			while pos < len(compressed):
				code = compressed[pos]
				pos += 1
				if code <= 0x1f:
					# literal string
					assert pos + code < len(compressed), "Attempted to read past compressed buffer"
					assert len(decompressed) + code < decomp_len, "Attempted to write past decompression buffer"
					decompressed += compressed[pos:pos + code + 1]
					pos += code + 1
				else:
					# dictionary entry
					copylen = code >> 5
					if copylen == 7:
						# 7 or more bytes to copy
						assert pos < len(compressed), "Attempted to read past compressed buffer"
						copylen += compressed[pos]
						pos += 1
					copylen += 2

					assert pos < len(compressed), "Attempted to read past compressed buffer"
					lookback = ((code & 0x1f) << 8) | compressed[pos]
					pos += 1

					decomp_index = (len(decompressed) - 1) - lookback
					assert decomp_index >= 0, "Attempted to read below decompression buffer"

					# only do byte-by-byte copy if we have to
					# i.e. if we are reading and writing the same portion of the buffer
					if decomp_index + copylen > len(decompressed):
						for i in range(decomp_index, decomp_index + copylen):
							decompressed += decompressed[i:i + 1]
					else:
						decompressed += decompressed[decomp_index:decomp_index + copylen]

		if len(decompressed) != decomp_len:
			raise LZ77Error(f"Error decompressing chunk (Expected {decomp_len} bytes, got {len(decompressed)})")

		ret.write(decompressed)
		size += decomp_len

	if size != decompressed_size:
		raise LZ77Error(f"Error decompressing stream (Expected {decompressed_size} bytes, got {size})")

	return ret.getvalue()
