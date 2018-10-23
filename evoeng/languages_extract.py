#!/usr/bin/env python
import json
import logging
import os
import sys
from typing import BinaryIO, List, Optional, Union, NamedTuple

from binreader import BinaryReader

logger = logging.getLogger(__name__)


class IDString(NamedTuple):
	id: str
	unk: bytes


class Group(NamedTuple):
	name: str
	unk: int
	encrypted_data: bytes
	string_ids: List[IDString]


class LanguagesFile:
	def __init__(self, bin_file: BinaryIO) -> None:
		reader = BinaryReader(bin_file)

		self.hash = reader.read(16)
		self.unk1 = reader.read_int32()
		format_version = reader.read_int32()
		logger.info(f"Extracting languages from Languages.bin format {format_version}")
		if format_version >= 29:
			logger.warning("Text is encrypted")

		def read_length_prefixed_str(encoding: Optional[str]="utf-8") -> Union[str, bytes]:
			sz = reader.read_int32()
			if encoding:
				return reader.read_string(sz, encoding=encoding)
			else:
				return reader.read(sz)

		self.unk2 = reader.read(5)

		self.languages: List[str] = []
		num_languages = reader.read_int32()
		for _ in range(num_languages):
			language = read_length_prefixed_str()
			logger.info(f"Got language {language}")

		self.groups: List[Group] = []
		num_groups = reader.read_int32()
		for _ in range(num_groups):
			prefix = read_length_prefixed_str()
			logger.info(f"Got group {prefix}")
			unk1 = reader.read_int32()
			strings_count = reader.read_int32()
			encoded_strings = read_length_prefixed_str(None)
			strings: List[IDString] = []
			for _ in range(strings_count):
				name = read_length_prefixed_str()

				# in older versions apparently this is 11
				unk2 = reader.read(8)
				strings.append(IDString(
					id=name,
					unk=unk2
				))
			self.groups.append(Group(
				name=prefix,
				unk=unk1,
				encrypted_data=encoded_strings,
				string_ids=strings
			))

	def to_dict(self) -> dict:
		return {
			'hash': repr(self.hash),
			'languages': self.languages,
			'groups': [
				{
					'prefix': g.name,
					'unk1': g.unk,
					'string_ids': [
						{
							'id': i.id,
							'unk': repr(i.unk)
						} for i in g.string_ids
					],
					'encrypted_data': repr(g.encrypted_data)
				} for g in self.groups
			]
		}


def main() -> None:
	logging.basicConfig(level=logging.DEBUG)
	for bin_path in sys.argv[1:]:
		with open(bin_path, "rb") as bin_file:
			languages = LanguagesFile(bin_file)
		with open(os.path.basename(bin_path).rsplit(".")[0] + ".json", "w") as f:
			json.dump(languages.to_dict(), f, indent=1)


if __name__ == "__main__":
	main()
