import ast, sys

files = [
    "src/execution/seaport.py",
    "src/execution/auto_executor.py",
    "src/workers/scan_worker.py",
    "src/workers/stream_sniper.py",
    "src/config.py",
    "src/main.py",
]
ok = True
for f in files:
    try:
        with open(f, "r", encoding="utf-8") as fh:
            ast.parse(fh.read())
        print(f"OK: {f}")
    except SyntaxError as e:
        print(f"SYNTAX ERROR in {f}: {e}")
        ok = False
if ok:
    print("All files parse correctly.")
else:
    print("FIX SYNTAX ERRORS ABOVE!")
    sys.exit(1)
