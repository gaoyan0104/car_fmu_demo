import json
import re
import sys
from pathlib import Path

def find_block(text: str, header_regex: str) -> str:
    """
    Find the {...} block after a header (regex).
    Minimal brace-matching parser for PoC.
    """
    m = re.search(header_regex + r"\s*\{", text)
    if not m:
        raise ValueError(f"Cannot find block header: {header_regex}")
    start = m.end() - 1  # points at '{'
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start+1:i]  # inside braces
    raise ValueError(f"Unclosed block for: {header_regex}")

def parse_attributes(block: str) -> dict:
    """
    Parse lines like:
      attribute mass_kg = 1650;
    """
    attrs = {}
    for name, val in re.findall(r"attribute\s+([A-Za-z_]\w*)\s*=\s*([-+]?\d+(?:\.\d+)?)\s*;", block):
        attrs[name] = float(val)
    return attrs

def main():
    sysml_file = Path(sys.argv[1] if len(sys.argv) > 1 else "car_inputs.sysml")
    text = sysml_file.read_text(encoding="utf-8")

    sim_pkg = find_block(text, r"package\s+SimulationInputs")
    vehicle_block = find_block(sim_pkg, r"part\s+vehicle_A")
    scenario_block = find_block(sim_pkg, r"part\s+scenario_0_100")
    req_block = find_block(sim_pkg, r"requirement\s+REQ_ACC_001")

    v = parse_attributes(vehicle_block)
    s = parse_attributes(scenario_block)
    r = parse_attributes(req_block)

    out = {
        "vehicle": {
            "id": "vehicle_A",
            "mass_kg": v["mass_kg"],
            "Pmax_W": v["Pmax_W"],
            "CdA": v["CdA"],
            "Crr": v["Crr"]
        },
        "scenario": {
            "v0_mps": s["v0_mps"],
            "vTarget_mps": s["vTarget_mps"],
            "tMax_s": s["tMax_s"]
        },
        "requirements": {
            "REQ_ACC_001": {"limit_s": r["limit_s"]}
        }
    }

    Path("sim_input.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK: wrote sim_input.json")
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
