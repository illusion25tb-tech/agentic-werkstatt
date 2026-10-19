import sys, pathlib
for f in sys.argv[1:]:
    for i, l in enumerate(pathlib.Path(f).read_text(encoding="utf-8").splitlines(), 1):
        if len(l) > 64: print(f"{f}:{i}: {len(l)}: {l}")
