import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import download_model as dm

calls = {"allow": None, "ignore": None, "repo": None}
def fake_snapshot(**kw):
    calls["repo"] = kw.get("repo_id")
    calls["allow"] = kw.get("allow_patterns")
    calls["ignore"] = kw.get("ignore_patterns")
    md = kw["local_dir"]
    os.makedirs(md, exist_ok=True)
    sfx = ".int8.onnx" if (kw.get("ignore_patterns") or []) == [] else ".onnx"
    for f in [f"encoder-epoch-20-avg-10{sfx}",
              f"decoder-epoch-20-avg-10{sfx}",
              f"joiner-epoch-20-avg-10{sfx}",
              "config.json", "bpe.model"]:
        open(os.path.join(md, f), "w").write("x")
dm.snapshot_download = fake_snapshot

for use_int8 in (False, True):
    with tempfile.TemporaryDirectory() as d:
        dm.FORCE = False
        dm.USE_INT8 = use_int8
        dm.MODEL_DIR = Path(d)
        dm.main()
        suffix = ".int8.onnx" if use_int8 else ".onnx"
        expect = [f"encoder-epoch-20-avg-10{suffix}",
                  f"decoder-epoch-20-avg-10{suffix}",
                  f"joiner-epoch-20-avg-10{suffix}",
                  "config.json", "bpe.model"]
        present = all((dm.MODEL_DIR / f).exists() for f in expect)
        print(f"INT8={use_int8}: complete={dm._model_complete()} all_present={present} "
              f"allow={calls['allow']} ignore={calls['ignore']}")

calls["repo"] = "NONE"
with tempfile.TemporaryDirectory() as d:
    dm.USE_INT8 = False; dm.FORCE = False; dm.MODEL_DIR = Path(d)
    for f in ["encoder-epoch-20-avg-10.onnx", "decoder-epoch-20-avg-10.onnx",
              "joiner-epoch-20-avg-10.onnx", "config.json", "bpe.model"]:
        open(os.path.join(d, f), "w").write("x")
    dm.main()
    print(f"idempotent: snapshot={calls['repo']} -> {'SKIPPED(correct)' if calls['repo']=='NONE' else 'REDOWNLOAD(WRONG)'}")

calls["repo"] = "NONE"
with tempfile.TemporaryDirectory() as d:
    dm.USE_INT8 = False; dm.FORCE = True; dm.MODEL_DIR = Path(d)
    for f in ["encoder-epoch-20-avg-10.onnx", "decoder-epoch-20-avg-10.onnx",
              "joiner-epoch-20-avg-10.onnx", "config.json", "bpe.model"]:
        open(os.path.join(d, f), "w").write("x")
    dm.main()
    print(f"FORCE: snapshot={calls['repo']} -> {'REDOWNLOAD(ok)' if calls['repo']!='NONE' else 'SKIPPED(WRONG)'}")