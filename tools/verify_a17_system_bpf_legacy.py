#!/usr/bin/env python3
"""Source-only inventory of archived PE Android14 system/bpf; no BPF compilation."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

def check(ok, description):
    if not ok:
        raise AssertionError(description)
    print("PASS historical inventory:", description)

def main():
    root = (ROOT / "Android.bp").read_text()
    loader = (ROOT / "bpfloader/Android.bp").read_text()
    init = (ROOT / "bpfloader/bpfloader.rc").read_text()
    lib = (ROOT / "libbpf_android/Android.bp").read_text()
    prog = (ROOT / "progs/Android.bp").read_text()
    cpp = (ROOT / "bpfloader/BpfLoader.cpp").read_text()
    maptest = json.loads((ROOT / "TEST_MAPPING").read_text())
    check('name: "bpf_defaults"' in root and 'name: "bpf_cc_defaults"' not in root, "archived Soong defaults")
    check('cc_binary {' in loader and 'name: "bpfloader"' in loader
          and '"BpfLoader.cpp"' in loader and '"libnetdutils"' in loader,
          "archived C++ system bpfloader and network utilities")
    check('name: "libbpf_android"' in lib and '"libbpf_bcc"' in lib
          and '"libbpf_minimal"' in lib, "archived C++ loader library API")
    check('name: "bpfRingbufProg.o"' in prog and 'bpf {' in prog,
          "legacy test ringbuf module rather than modern libbpf_prog output")
    check('on load_bpf_programs' in init and 'exec_start bpfloader' in init
          and 'service bpfloader /system/bin/bpfloader' in init,
          "historic early-init sequence")
    check('bpf.progs_loaded' in init and 'netd crashloop' in init,
          "archived boot failure warning and BPF netd dependency")
    check('"/apex/com.android.tethering/etc/bpf/"' in cpp
          and '"/vendor/etc/bpf/"' in cpp, "historical Mainline and vendor BPF paths")
    check(not (ROOT / "loader/bpfloader.rs").exists()
          and not (ROOT / "include/defs").exists(),
          "archived source does not include AOSP17 Rust BPF layout")
    imported = [x.get("path") for x in maptest.get("imports",[])]
    check("packages/modules/Connectivity" in imported,
          "historical connectivity integration test dependency")
    print("PASS historical source-only check. AOSP17 Rust build, verifier, kernel 5.10, netd and device NOT TESTED.")

if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, json.JSONDecodeError) as error:
        print("FAIL:", error, file=sys.stderr)
        sys.exit(1)
