import json
from sys import argv

from sc_parser import parser


def main() -> int:
    if len(argv) == 2:
        parser.parse(argv[1])

    else:  # test
        print(json.dumps(parser.parse("sc_parser/examples/function.sc").as_dict(), indent=2))


if __name__ == "__main__":
    exit(main())
