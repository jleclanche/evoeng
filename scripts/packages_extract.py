#!/usr/bin/env python
import json
import logging
import os
import sys

from evoeng.packages_extract import PackagesFile

logger = logging.getLogger(__name__)


def main() -> None:
	logging.basicConfig(level=logging.DEBUG)

	for bin_path in sys.argv[1:]:
		with open(bin_path, "rb") as bin_file:
			packages = PackagesFile(bin_file)

		outdir, _ = os.path.splitext(bin_path)

		def get_local_path(path: str) -> str:
			return os.path.join(outdir, path.lstrip("/"))

		for package in packages.packages:
			dirname = get_local_path(os.path.dirname(package.path))
			if not os.path.exists(dirname):
				os.makedirs(dirname)

			local_path = get_local_path(package.path)
			logger.info(f"Extracting {local_path}")

			try:
				decoded_data = package.content
			except Exception:
				logger.exception(f"Could not decode data for {package.path!r}")
				with open(f"{local_path}.wfpkg", "wb") as f:
					f.write(package.data)
			else:
				with open(f"{local_path}.json", "w") as fp:
					json.dump(decoded_data, fp)


if __name__ == "__main__":
	main()
