#!/usr/bin/env python
import logging
import sys
from dataclasses import dataclass, field
from io import BytesIO
from typing import BinaryIO, List, NamedTuple, Dict

from binreader import BinaryReader

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
			self.content = self.decode()
		except Exception as e:
			logger.exception(f"Failed to decode package {self.name}", exc_info=e)
			self.content = None

	def decode(self) -> Dict[str, object]:
		data = {}
		content = self.raw_content.decode()
		lines = content.strip().replace('\r', '').splitlines()

		# TODO: parse lines of text into data dict
		# Example content is
		# Notes:
		"""
		Channels={
		{
		LoopCount=1
		Startup={}
		Events={
		{
		Sound=CorpusDoorLaserLoopWide
		Parameter={0,0}
		Latency={0,0}
		Duration=0
		FadeTime=0
		FadeAmount=1
		}
		}
		Shutdown={}
		}
		}
		"""
		for line in lines:
			pass

		return data


class BinFile:
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

		self.chunks: List[bytes] = []

		chunksize = reader.read_int32()
		chunk_reader = BinaryReader(BytesIO(reader.read(chunksize)))
		num_chunks = reader.read_int32()

		for i in range(num_chunks):
			self.chunks.append(chunk_reader.read_cstring())

		self.packages = []
		for chunk in self.chunks:
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


def main() -> None:
	logging.basicConfig(level=logging.DEBUG)
	for bin_path in sys.argv[1:]:
		with open(bin_path, "rb") as bin_file:
			print(BinFile(bin_file))


if __name__ == "__main__":
	main()
