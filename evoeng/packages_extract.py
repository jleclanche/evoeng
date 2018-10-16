#!/usr/bin/env python
import dataclasses
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, BinaryIO, Dict, List, Tuple

from binreader import BinaryReader
from package_parser import loads


logger = logging.getLogger(__name__)


@dataclass
class Package:
	name: str
	parent_path: str
	header_path: str
	data: bytes

	@property
	def content(self) -> Dict[str, Any]:
		return loads(self.data.decode())

	@property
	def parent_full_path(self):
		return os.path.join(self.header_path, self.parent_path)

	@property
	def full_path(self):
		return os.path.join(self.header_path, self.name)


class PackagesFile:
	def __init__(self, bin_file: BinaryIO) -> None:
		reader = BinaryReader(bin_file)
		self.hash = reader.read(29)

		def read_length_prefixed_str() -> str:
			sz = reader.read_int32()
			return reader.read_string(sz)

		self.structs: List[Tuple[str, int]] = []
		num_structs = reader.read_int32()
		logger.info(f"Reading {num_structs} top level structs")
		for _ in range(num_structs):
			name = read_length_prefixed_str()
			unk = reader.read_int32()
			self.structs.append((name, unk))

		chunks: List[bytes] = []
		chunksize = reader.read_int32()
		chunk_reader = BinaryReader(BytesIO(reader.read(chunksize)))
		num_chunks = reader.read_int32()

		logger.info(f"Reading {num_chunks} chunks in {chunksize} bytes")
		for i in range(num_chunks):
			chunks.append(chunk_reader.read_cstring())

		self.packages: List[Package] = []
		logger.info(f"Parsing {len(chunks)} chunks into packages")
		for chunk in chunks:
			path = read_length_prefixed_str()
			name = read_length_prefixed_str()
			reader.read(5)
			parent_path = read_length_prefixed_str()
			reader.read(4)  # always 0

			self.packages.append(Package(
				name=name,
				parent_path=parent_path,
				header_path=path,
				data=chunk,
			))


def main() -> None:
	logging.basicConfig(level=logging.DEBUG)
	for bin_path in sys.argv[1:]:
		with open(bin_path, "rb") as bin_file:
			packages = PackagesFile(bin_file)

		outdir, _ = os.path.splitext(bin_path)
		def get_local_path(path: str) -> str:
			return os.path.join(outdir, path.lstrip("/"))

		for package in packages.packages:
			dirname = get_local_path(package.header_path)
			if not os.path.exists(dirname):
				os.makedirs(dirname)

			local_path = get_local_path(package.full_path)
			logger.info(f"Extracting {local_path}")
			with open(f"{local_path}.wfpkg", "wb") as f:
				f.write(package.data)

			try:
				decoded_data = package.content
			except Exception:
				logger.exception(f"Could not decode data for {package.full_path!r}")
			else:
				with open(f"{local_path}.json", "w") as fp:
					json.dump(decoded_data, fp)


if __name__ == "__main__":
	main()
