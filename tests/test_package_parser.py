import json
import os

import pytest
from evoeng import package_parser


with open(os.path.join(os.path.dirname(__file__), "packages.json"), "r") as f:
	packages = json.load(f)


@pytest.mark.parametrize(
	"package_text",
	packages,
	ids=[str(i) for i in range(len(packages))]
)
def test_packages(package_text):
	assert package_parser.loads(package_text)


PACKAGES = {
	"A=B": {"A": "B"},
	"A=1": {"A": 1},
	"A=1.0": {"A": 1.0},
	"A={}": {"A": []},
	"A={\nA=1\n}": {"A": {"A": 1}},
	"A={1,2,3}": {"A": [1, 2, 3]},
	"A={\nRawString1,RawString2\n}": {"A": ["RawString1", "RawString2"]},
	"A={\nRawString1,RawString2,\n}": {"A": ["RawString1", "RawString2"]},
	"A=1x1": {"A": "1x1"},
	"A=1.8000001e+05": {"A": 1.8000001e+05},
	"A=-9.2029601e-05": {"A": -9.2029601e-05},
	"A=88c1934b-3e5e-4f63-a599-1670f585aee2": {"A": "88c1934b-3e5e-4f63-a599-1670f585aee2"},
	'A={\nB=""\n}': {"A": {"B": ""}},
	'A={\nB="https://example.com/?a=b"\n}': {"A": {"B": "https://example.com/?a=b"}},
}

@pytest.mark.parametrize(
	("package_text,expected_value"),
	PACKAGES.items(),
	ids=lambda s: s if isinstance(s, str) else repr(s)
)
def test_package_correct_structure(package_text, expected_value):
	assert package_parser.loads("\n" + package_text + "\n") == expected_value
