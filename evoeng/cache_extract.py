#!/usr/bin/env python
import os
import struct
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import List

import filetime
from lz77 import lz_decompress


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


FILE_SUFFIX = "~"


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
		if timestamp <= 0:
			file_time = None
		else:
			file_time = filetime.to_datetime(timestamp)

		if offset == -1:
			path = directories[parent]
			directory_index += 1
			directories[directory_index] = os.path.join(path, filename)
		else:
			path = directories[parent]

		entry = TOCEntry(
			offset, file_time, compressed_size, size, scope_index, path, filename
		)
		entries.append(entry)

	def get_local_path(full_path: str) -> str:
		return os.path.join(outdir, full_path.lstrip("/"))

	for directory in directories.values():
		path = get_local_path(directory)
		if not os.path.exists(path):
			os.makedirs(path)

	for entry in entries:
		if entry.is_directory:
			continue
		if not entry.time:
			print("Skipping entry without time", repr(entry))
			continue

		local_path = get_local_path(entry.full_path)
		if os.path.exists(local_path):
			if os.path.isdir(local_path):
				local_path = local_path + FILE_SUFFIX

		cache.seek(entry.offset)
		compressed = entry.compressed_size != entry.size
		print(f"Extracting {local_path} (compressed={compressed})")
		if compressed:
			data = lz_decompress(cache, entry.size)
		else:
			data = cache.read(entry.compressed_size)

		if os.path.exists(local_path):
			from hashlib import md5

			local_path += f"~{md5(data).hexdigest()[:5]}"

		try:
			with open(local_path, "wb") as f:
				f.write(data)
		except OSError as e:
			sys.stderr.write(f"Cannot write {entry.full_path} - {e.strerror}\n")
			continue

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
