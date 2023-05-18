import os


def gen_parser():
    from lark import Lark
    with open(os.path.join(os.path.dirname(__file__), "grammar.lark"), "r") as f:
        return Lark(f.read(), start="program")


if __name__ == "__main__":  # test
    parser = gen_parser()
    loc = os.path.join(os.path.dirname(__file__), "examples")
    for fname in os.listdir(loc):
        fpath = os.path.join(loc, fname)
        if os.path.splitext(fpath)[1] == ".sc":
            with open(fpath) as f:
                try:
                    parser.parse(text=f.read())
                    print(f"{fpath} succeeded")
                except Exception as e:
                    print(f"{fpath} failed: {e}")
