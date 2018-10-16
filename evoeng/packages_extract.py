#!/usr/bin/env python
import dataclasses
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from io import BytesIO
from typing import BinaryIO, List, NamedTuple, Dict

from binreader import BinaryReader
from package_parser import loads

logger = logging.getLogger(__name__)


class TopStruct(NamedTuple):
	name: str
	unk: int


@dataclass
class Package:
	name: str
	base_package: str
	header_path: str
	raw_content: bytes
	content: Dict[str, object] = field(init=False)

	def __post_init__(self) -> None:
		try:
			text = self.raw_content.decode()
			self.content = loads(text)
		except Exception as e:
			logger.exception(f"Failed to decode package {self.name}", exc_info=e)
			self.content = None


class PackagesFile:
	def __init__(self, bin_file: BinaryIO) -> None:
		reader = BinaryReader(bin_file)
		self.hash = reader.read(29)

		def read_length_prefixed_str() -> str:
			sz = reader.read_int32()
			return reader.read_string(sz)

		self.structs: List[TopStruct] = []
		num_structs = reader.read_int32()
		logger.info(f"Reading {num_structs} top level structs")
		for _ in range(num_structs):
			name = read_length_prefixed_str()
			unk = reader.read_int32()
			self.structs.append(TopStruct(
				name=name,
				unk=unk
			))

		chunks: List[bytes] = []
		chunksize = reader.read_int32()
		chunk_reader = BinaryReader(BytesIO(reader.read(chunksize)))
		num_chunks = reader.read_int32()
		logger.info(f"Reading {num_chunks} chunks in {chunksize} bytes")
		for i in range(num_chunks):
			chunks.append(chunk_reader.read_cstring())

		self.packages = []
		logger.info(f"Parsing {len(chunks)} chunks into packages")
		for chunk in chunks:
			path = read_length_prefixed_str()
			name = read_length_prefixed_str()
			reader.read(5)
			basename = read_length_prefixed_str()
			reader.read(4)

			self.packages.append(Package(
				name=name,
				base_package=basename,
				header_path=path,
				raw_content=chunk,
			))

	def to_dict(self, include_raw_content=False) -> dict:
		packages = []
		for p in self.packages:
			d = dataclasses.asdict(p)
			if not include_raw_content:
				del d["raw_content"]
			packages.append(d)
		return {
			"structs": [
				s._asdict() for s in self.structs
			],
			"packages": packages
		}


def main() -> None:
	logging.basicConfig(level=logging.DEBUG)
	for bin_path in sys.argv[1:]:
		assert bin_path.endswith(".bin")

		with open(bin_path, "rb") as bin_file:
			packages = PackagesFile(bin_file)
		with open(os.path.basename(bin_path).replace(".bin", ".json"), "w") as f:
			json.dump(packages.to_dict(), f, indent=1)


if __name__ == "__main__":
	main()
