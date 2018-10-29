#!/usr/bin/env python
import json
import logging
import os
import sys

from evoeng.packages_extract import PackagesFile

logger = logging.getLogger(__name__)


def main() -> None:
	bin_path = sys.argv[1]

	with open(bin_path, "rb") as bin_file:
		packages = PackagesFile(bin_file)

	mods = []

	for package in packages.packages:
		if not package.path.startswith("/Lotus/Powersuits/"):
			continue
		if package.path.startswith("/Lotus/Powersuits/PowersuitAbilities"):
			continue
		mod = {"path": package.path, "data": package.get_full_content(packages)}
		mods.append(mod)

	with open("Warframes.json", "w") as f:
		json.dump(mods, f)


if __name__ == "__main__":
	main()
