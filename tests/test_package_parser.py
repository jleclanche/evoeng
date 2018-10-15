import json
import os

import pytest
from package_parser import loads


with open(os.path.join(os.path.dirname(__file__), "packages.json"), "r") as f:
	packages = json.load(f)


@pytest.mark.slow
@pytest.mark.parametrize(
	"package_text",
	packages,
	ids=[str(i) for i in range(len(packages))]
)
def test_packages(package_text):
	assert loads(package_text)