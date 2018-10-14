#!/usr/bin/env python
import os
import struct
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import List

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
		if timestamp == -1:
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
		local_path = get_local_path(entry.full_path)
		if entry.is_directory:
			if not os.path.exists(local_path):
				os.makedirs(local_path)
		else:
			with open(local_path, "wb") as f:
				cache.seek(entry.offset)
				assert entry.compressed_size == entry.size, "LZ not supported yet"
				f.write(cache.read(entry.compressed_size))

			# Set write time to the entry's filetime
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
