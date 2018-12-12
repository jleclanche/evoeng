#!/usr/bin/env python
import json
import os
import sys


COLLECTION_PATH = "/Lotus/Types/GameRules/LotusPlatformIconCollection"


def main():
	with open(sys.argv[1], "r") as f:
		collection = json.load(f).get("Icons", [])

	outdir = os.path.abspath("./icons")
	for pd in ("DIT_PC", "DIT_XBONE", "DIT_STEAM", "DIT_PS4"):
		os.makedirs

	for icon in collection:
		name = icon["Name"]
		for platform in icon.get("Platforms", []):
			ip = platform.get("IconPlatform", "DIT_UNKNOWN")

			dirname = os.path.join(outdir, ip)
			if not os.path.exists(dirname):
				os.makedirs(dirname)

			with open(os.path.join(dirname, f"{name}.meta.json"), "w") as f:
				json.dump(platform, f)

			material = platform.get("Material")
			if material:
				with open(os.path.join(dirname, f"{name}.material"), "w") as f:
					f.write(material + "\n")


if __name__ == "__main__":
	main()
