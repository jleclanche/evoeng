#!/usr/bin/env python
import json
import logging
import os
import posixpath
import sys
from typing import Dict, List, Set

import requests

from evoeng.packages_extract import PackagesFile

logger = logging.getLogger(__name__)


MANIFEST_URL = "http://content.warframe.com/MobileExport/Manifest/ExportManifest.json"


def get_texture_manifest() -> dict:
	print(f"Downloading {MANIFEST_URL}")
	manifest = requests.get(MANIFEST_URL).json().get("Manifest", [])
	return {o["uniqueName"]: o["textureLocation"].replace("\\", "/") for o in manifest}


def make_absolute(key: str, base_key: str) -> str:
	base_dir = posixpath.dirname(base_key)
	return posixpath.join(base_dir, key)


class Extractor:
	def __init__(self, args):
		bin_path = args[0]

		if not os.path.exists("ids.json"):
			raise RuntimeError("Cannot find `ids.json`.")

		with open("ids.json", "r") as f:
			self.ids = json.load(f)

		if self.ids:
			self.max_id = max(self.ids.values())
		else:
			self.max_id = 0

		self.texture_manifest = get_texture_manifest()

		with open(bin_path, "rb") as bin_file:
			print(f"Parsing {bin_path}")
			self.packages = PackagesFile(bin_file)

	def get_or_save_id(self, key: str) -> int:
		if key in self.ids:
			return self.ids[key]
		else:
			self.max_id += 1
			self.ids[key] = self.max_id
			print(f"New id: {self.max_id} - {key}")
			return self.max_id

	def extract_for_filters(self, tag_filters: List[str]) -> Dict[str, dict]:
		print(f"Extracting: {tag_filters!r}")
		manifest = self.packages["/Lotus/Types/Lore/PrimaryCodexManifest"]
		entries = manifest.get("Entries", []) + manifest.get("AutoGeneratedEntries", [])

		ret: Dict[str, dict] = {}
		all_keys: Set[str] = set()
		orphans: Set[str] = set()

		def _get_package(key, pkgobj):
			all_keys.add(key)
			orphans.discard(key)
			d = {
				"path": key,
				"id": self.get_or_save_id(key),
				"data": pkgobj.get_full_content(self.packages),
			}
			if key in self.texture_manifest:
				d["texture"] = self.texture_manifest[key]
			if pkgobj.parent_path:
				d["parent"] = pkgobj.parent_path
				if pkgobj.parent_path not in all_keys:
					orphans.add(pkgobj.parent_path)

			item_compat = d["data"].get("ItemCompatibility", "")
			if item_compat:
				# Resolve non-absolute paths
				if not item_compat.startswith("/"):
					item_compat = d["data"]["ItemCompatibility"] = make_absolute(item_compat, key)

				# Discovery for unknown keys
				if item_compat not in all_keys:
					orphans.add(item_compat)
			return d

		for entry in entries:
			if "tag" in entry and entry["tag"] in tag_filters:
				key = entry["type"]

				pkgobj = self.packages._packages[key]
				d = _get_package(key, pkgobj)
				d["tag"] = entry["tag"]

				# Resolve behaviors packages
				for behavior in d["data"].get("Behaviors", []):
					for k, v in behavior.items():
						for path_key in ["projectileType", "AIMED_ACCURACY"]:
							if path_key in v:
								if len(v[path_key]) > 0:
									k = make_absolute(v[path_key], key)
									_pkgobj = self.packages._packages[k]
									v[path_key] = _pkgobj.get_full_content(self.packages)
								else:
									v[path_key] = {}

				ret[key] = d

		print("Processing orphan keys…")
		while orphans:
			for key in list(orphans):
				try:
					pkgobj = self.packages._packages[key]
					ret[key] = _get_package(key, pkgobj)
				except KeyError as e:
					print(f"Cannot find key={key} ({e})")
					orphans.discard(key)
					ret[key] = {"path": key, "id": self.get_or_save_id(key)}

		return ret

	def extract_all(self) -> dict:
		return {
			"Mods": self.extract_for_filters(["Mod", "RelicsAndArcanes"]),
			"Items": self.extract_for_filters(
				["Sentinel", "SentinelWeapon", "Warframe", "Weapon"]
			),
		}


def main() -> None:
	extractor = Extractor(sys.argv[1:])
	data = extractor.extract_all()

	with open("ids.json", "w") as f:
		json.dump(extractor.ids, f, indent="\t", sort_keys=True)

	with open(f"data.json", "w") as f:
		json.dump(data, f, indent="\t", sort_keys=True)


if __name__ == "__main__":
	main()
