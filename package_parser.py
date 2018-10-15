from typing import Any, Dict

from parsimonious.grammar import Grammar


GRAMMAR = Grammar(r"""
package = NEWL* (dict_content)? NEWL*

dict_content = dict_pair*
dict_pair = dict_key EQUALS dict_value NEWL
dict_key = (DICT_KEY_CHARS)+
dict_value = value

list_content = NEWL* list_item ( COMMA NEWL? list_item )* COMMA? NEWL*
list_item = value

literal_value = FLOAT / INT / STRING
value = literal_value / TABLE

LIST = BRACE_L list_content? BRACE_R
DICT = BRACE_L NEWL dict_content BRACE_R
TABLE = LIST / DICT

RAW_STRING_CHARS = ~"[^{},\n]"
DICT_KEY_CHARS = ~"[^={},\n]"
STRING_CHARS = ~'[^"]'
quoted_string = QUOTE STRING_CHARS* QUOTE
raw_string = RAW_STRING_CHARS+

INT = ~"(-)?[0-9]+![^0-9]"
FLOAT = ~"(-)?[0-9]+\.[0-9]+(e(\+|\-)[0-9]+)?"
STRING = quoted_string / raw_string

NEWL = ~" *\n"
BRACE_L = "{"
BRACE_R = "}"
COMMA = ","
EQUALS = "="
QUOTE = '"'
""")


def loads(text: str) -> Dict[str, Any]:
	pass
