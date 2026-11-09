import tokenize

with open("input.py", "rb") as f:
    tokens = tokenize.tokenize(f.readline)

with open("output.py", "w", encoding="utf-8") as out:
    for token in tokens:
        if token.type != tokenize.COMMENT:
            out.write(token.string if token.string else "")