#!/usr/bin/env python
import io
import os
import struct
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import List, BinaryIO

import filetime


@dataclass
class TOCEntry:
	offset: int
	time: datetime
	compressed_size: int
	size: int
	scope_index: int
	path: str
	filename: str

	@property
	def is_directory(self):
		return self.offset == -1

	@property
	def full_path(self):
		return os.path.join(self.path, self.filename)


class TOC:
	def __init__(self) -> None:
		self.entries: List[TOCEntry] = []

	def add_entry(self, entry: TOCEntry) -> None:
		self.entries.append(entry)


def lz_decompress(entry: TOCEntry, cache: BinaryIO) -> bytes:
	out = io.BytesIO()

	size = 0
	while size < entry.size:
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

					# only do byte-by-byte copy if we have to (i.e. if we are reading and writing the same portion of the buffer)
					if decomp_index + copylen > len(decompressed):
						for i in range(decomp_index, decomp_index + copylen):
							decompressed += decompressed[i:i + 1]
					else:
						decompressed += decompressed[decomp_index:decomp_index + copylen]

		assert len(decompressed) == decomp_len, f"Did not decompress all bytes in chunk - Expected {decomp_len}, but decompressed was {len(decompressed)}"
		out.write(decompressed)
		size += decomp_len

	assert size == entry.size, f"Expected to decompress to {entry.size} bytes, but decompressed to {size}"

	return out.getvalue()


def handle_files(cache, toc, outdir):
	assert toc.read(4) == b"\x4e\xc6\x67\x18", "Invalid TOC MAGIC"
	toc_version, = struct.unpack("<i", toc.read(4))
	assert toc_version in (16, 20), f"Unreadable TOC version {toc_version}"

	directories = {0: "/"}
	directory_index = 0

	entries = []

	while True:
		data = toc.read(8 + 8 + 4 + 4 + 4 + 4 + 64)
		if not data:
			break
		offset, timestamp, compressed_size, size, scope_index, parent, filename = struct.unpack(
			"<qq4i64s", data
		)
		filename = filename.rstrip(b"\0").decode()
		if timestamp == -1 or timestamp == 0:
			file_time = None
		else:
			file_time = filetime.to_datetime(timestamp)

		if offset == -1:
			path = directories[parent]
			directory_index += 1
			directories[directory_index] = os.path.join(path, filename)
		else:
			path = directories[parent]

		entry = TOCEntry(offset, file_time, compressed_size, size, scope_index, path, filename)
		print(entry)
		entries.append(entry)

	def get_local_path(full_path):
		return os.path.join(outdir, full_path.lstrip("/"))

	for entry in entries:
		if not entry.is_directory:
			local_path = get_local_path(entry.full_path)
			dirname = os.path.dirname(local_path)
			try:
				if not os.path.exists(dirname):
					os.makedirs(dirname)
				with open(local_path, "wb") as f:
					cache.seek(entry.offset)
					if entry.compressed_size == entry.size:
						f.write(cache.read(entry.compressed_size))
					else:
						f.write(lz_decompress(entry, cache))
			except (FileNotFoundError, PermissionError) as e:
				sys.stderr.write(f"Cannot write {entry.full_path} - {e.strerror}\n")
			else:
				# Set write time to the entry's filetime
				if entry.time:
					ts = entry.time.timestamp()
					os.utime(local_path, (ts, ts))


def main():
	for cache_path in sys.argv[1:]:
		assert cache_path.endswith(".cache"), "Filename must end in .cache"
		toc_path = cache_path.replace(".cache", ".toc")
		outdir = cache_path.replace(".cache", "/")

		with open(cache_path, "rb") as cache, open(toc_path, "rb") as toc:
			handle_files(cache, toc, outdir)


if __name__ == "__main__":
	main()
