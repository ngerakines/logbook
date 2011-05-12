
import logbook.parser

tests = [
	"#logbook",
	"#logbook #meeting",
	"#logbook @carolyn",
	"#logbook @carolyn #programming",
	"#logbook @carolyn #programming @vanessa",
	"\"#open source\"",
	"\"@Carolyn Gerakines\"",
	"#logbook \"#open source\" \"@Carolyn Gerakines\" @vanessa",
	"\"!1:30 pm\"",
	"!today",
	"#logbook \"#open source\" \"@carolyn gerakines\" \"!Yesterday at 1:30pm\"",
	"--",
	"#meeting task @steve --",
	"-- #meeting"
]

def test():
	for test in tests:
		parts = logbook.parser.Parser.parse(test)
		if parts != []:
			print test, "->", parts
		else:
			print "FAILED: %s" % test
			return
	print "HOORAY!"

if __name__ == '__main__':
	test()

