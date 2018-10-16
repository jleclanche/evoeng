from typing import Any, Dict, List

from parsimonious.grammar import Grammar


GRAMMAR = Grammar(r"""
package = NEWL* package_content NEWL*

package_content = (dict_content)?

dict_content = dict_pair*
dict_pair = dict_key EQUALS dict_value NEWL
dict_key = (DICT_KEY_CHARS)+
dict_value = value

list_content = NEWL* list_item ( COMMA NEWL? list_item )* COMMA? NEWL*
list_item = value

value = FLOAT / INT / QUOTED_STRING / RAW_STRING / LIST / DICT

LIST = BRACE_L list_content? BRACE_R
DICT = BRACE_L NEWL dict_content BRACE_R

RAW_STRING_CHARS = ~"[^{},\n]"
DICT_KEY_CHARS = ~"[^={},\n]"
STRING_CHARS = ~'[^"]'

QUOTED_STRING = QUOTE STRING_CHARS* QUOTE
RAW_STRING = RAW_STRING_CHARS+

INT = ~"(-)?[0-9]+"
FLOAT = ~"(-)?[0-9]+\.[0-9]+(e(\+|\-)[0-9]+)?"

NEWL = ~" *\n"
BRACE_L = "{"
BRACE_R = "}"
COMMA = ","
EQUALS = "="
QUOTE = '"'
""")


def _get_value(node) -> Any:
	value_type = node.children[0].expr_name

	if value_type == "FLOAT":
		return float(node.text)
	elif value_type == "INT":
		return int(node.text)
	elif value_type == "RAW_STRING":
		return node.text
	elif value_type == "QUOTED_STRING":
		return node.children[0].children[1].text
	elif value_type == "LIST":
		return _get_list_content(node.children[0].children[1])
	elif value_type == "DICT":
		return _get_dict_content(node.children[0].children[2])

	return None


def _get_list_content(node) -> List[Any]:
	ret: List[Any] = []
	if not node.children:
		return ret

	list_content = node.children[0]

	# {1}
	# <Node matching "1">
	#     <Node called "list_content" matching "1">
	#         <Node matching "">
	#         <Node called "value" matching "1">
	#             <RegexNode called "INT" matching "1">
	#         <Node matching "">
	#         <Node matching "">
	#         <Node matching "">

	# {1,2,3}
	# <Node matching "1,2,3">
	#     <Node called "list_content" matching "1,2,3">
	#         <Node matching "">
	#         <Node called "value" matching "1">
	#             <RegexNode called "INT" matching "1">
	#         <Node matching ",2,3">
	#             <Node matching ",2">
	#                 <Node called "COMMA" matching ",">
	#                 <Node matching "">
	#                 <Node called "value" matching "2">
	#                     <RegexNode called "INT" matching "2">
	#             <Node matching ",3">
	#                 <Node called "COMMA" matching ",">
	#                 <Node matching "">
	#                 <Node called "value" matching "3">
	#                     <RegexNode called "INT" matching "3">
	#         <Node matching "">
	#         <Node matching "">

	# extract the first item
	first_item = _get_value(list_content.children[1])
	ret.append(first_item)

	# extract remainder
	for child in list_content.children[2]:
		for subchild in child.children:
			if subchild.expr_name == "value":
				ret.append(_get_value(subchild))

	return ret


def _get_dict_content(node) -> Dict[str, Any]:
	ret = {}
	for pair in node.children:
		dict_key = pair.children[0].text
		value = _get_value(pair.children[2])
		ret[dict_key] = value

	return ret


def loads(text: str) -> Dict[str, Any]:
	package = GRAMMAR.parse(text)
	return _get_dict_content(package.children[1].children[0])


if __name__ == "__main__":
	import json
	import sys

	for path in sys.argv[1:]:
		with open(path, "r") as f:
			decoded = loads(f.read())

		json.dump(decoded, sys.stdout, indent="\t")
