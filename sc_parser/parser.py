import os
from enum import Enum, auto

import lark


class Ast:
    def as_dict(self) -> dict:
        return {
            "class": self.__class__.__name__,
            "value": "unknown"
        }


class Statement(Ast):
    pass


class Program(Ast):
    def __init__(self, *children: Ast) -> None:
        self.children = list(children)

    def as_dict(self) -> dict:
        return {
            "class": "Program",
            "children": list(ii.as_dict() for ii in self.children)
        }

    def __str__(self) -> str:
        return f"Program({', '.join([str(i) for i in self.children])})"


class Expression(Statement):
    pass


class DType(Enum):
    u8 = auto()
    i8 = auto()
    u16 = auto()
    i16 = auto()
    u32 = auto()
    i32 = auto()
    u64 = auto()
    i64 = auto()


class TypeExpr(Expression):
    base: DType | Ast

    def __init__(self, base: str | Ast | DType, isref: bool = False) -> None:
        if isinstance(base, self.__class__):
            self = base
        elif isinstance(base, str):
            self.base = DType[base]
        else:
            self.base = None
        self.isreference = isref

    def as_dict(self) -> dict:
        return {
            "class": "TypeExpr",
            "base": self.base.name,
            "ref": self.isreference
        }

    def __str__(self) -> str:
        if not self.base:
            return f"type(unknown)"
        else:
            return f"type({self.base.name})"


class FnTypeExpr(TypeExpr):
    def __init__(self, paramlist: list[TypeExpr], ret: TypeExpr) -> None:
        self.params = paramlist
        self.ret = ret

    def as_dict(self) -> dict:
        return {
            "class": "FnTypeExpr",
            "params": list(ii.as_dict() for ii in self.params),
            "return": self.ret.as_dict()
        }

    def __str__(self) -> str:
        return f"fn({', '.join((str(i) for i in self.params))}) -> {str(self.ret)}"


class FnDef(Expression):
    def __init__(self, params: dict[str, TypeExpr], rettype: TypeExpr, body: Program = Program()):
        self.params = params
        self.ret = rettype
        self.body = body

    def params_as_dict(self) -> dict:
        n = {}
        for ii in self.params:
            jj = self.params[ii]
            n[ii] = jj.as_dict()
        return n

    def as_dict(self) -> dict:
        return {
            "class": "FnDef",
            "params": self.params_as_dict(),
            "return": self.ret.as_dict(),
            "body": self.body.as_dict()
        }

    def __str__(self) -> str:
        return f"fn({', '.join((str(i) for i in self.params))}) -> {str(self.ret)} " + "{...}"


class StmtLet(Statement):
    name: str
    type: TypeExpr
    value: Expression

    def __init__(self, _name: str, _type: TypeExpr = Expression(), _value: Expression = Expression()) -> None:
        self.name = _name
        self.type = _type
        self.value = _value

    def as_dict(self) -> dict:
        return {"class": "StmtLet", "name": self.name, "type": self.type.as_dict(), "value": self.value.as_dict()}

    def __str__(self) -> str:
        if not self.type:
            return f"Let({self.name} = {str(self.value)})"
        elif not self.value:
            return f"Let({self.name}: {str(self.type)})"
        else:
            return f"Let({self.name}: {str(self.type)} = {str(self.value)})"


def form_ast(tree: lark.Tree[lark.Token]) -> Ast:
    # print(tree.data)
    if tree.data == "program":
        cr = []
        for ii in tree.children:
            cr.append(form_ast(ii))
        return Program(*cr)
    elif tree.data == "statement":
        return form_ast(tree.children[0])
    elif tree.data == "let_typed_uninitialized":
        return StmtLet(tree.children[0], form_ast(tree.children[1]))  # type: ignore
    elif tree.data == "type":
        if isinstance(tree.children[0], lark.Token):
            return TypeExpr(tree.children[0].value)
        else:
            return form_ast(tree.children[0])
    elif tree.data == "fn_type":
        # print(tree.pretty())
        params = []
        for ii in tree.children[0].children:
            params.append(form_ast(ii))
        ret = form_ast(tree.children[1])
        return FnTypeExpr(params, ret)
    elif tree.data == "reftype":
        if isinstance(tree.children[0], lark.Token):
            return TypeExpr(tree.children[0].value, True)
        else:
            return TypeExpr(form_ast(tree.children[0]), True)
    elif tree.data == "let_fn_def":
        return StmtLet(tree.children[0], _value=form_ast(tree.children[1]))
    elif tree.data == "fn_def":
        params: dict[str, TypeExpr] = {}
        currname: str = None
        for ii in tree.children[0].children:
            if isinstance(ii, lark.Token):
                currname = ii.value
            elif isinstance(ii, lark.Tree):
                params[currname] = form_ast(ii)
                currname = None
        rettype = form_ast(tree.children[1])
        if len(tree.children) == 2:
            return FnDef(params, rettype, None)
        else:
            return FnDef(params, rettype, form_ast(tree.children[2]))

    print("TODO: form_ast/" + tree.data)
    print(tree.pretty())


def gen_parser():
    with open(os.path.join(os.path.dirname(__file__), "grammar.lark"), "r") as f:
        return lark.Lark(f.read(), start="program")


def parse(src: str, ispath: bool = True) -> Ast:
    if ispath:
        path = src
        with open(path, "r") as f:
            src = f.read()
    p = gen_parser()
    larktree = p.parse(src)
    return form_ast(larktree)


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
                except lark.UnexpectedInput as e:
                    print(f"{fpath}:{e.line}:{e.column}: {e}")
