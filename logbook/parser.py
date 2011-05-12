
import sys
from pyparsing import Word, alphas, alphanums, Optional, Group, delimitedList, quotedString, OneOrMore, dblQuotedString, removeQuotes

task = Word("task")
more = Word("-")
single = dblQuotedString.setParseAction(removeQuotes) | Word(alphanums)
tag = Word("#@!" + alphanums)
terms = OneOrMore(single | tag | task | more)

class Parser:
	@staticmethod
	def parse(string):
		parts = []
		try:
			parts = terms.parseString(string)
		except:
			pass
		return parts

