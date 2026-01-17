import json
import yaml
import numpy as np
from fmpy import simulate_fmu

def flatten_cfg(cfg: dict) -> dict:
    flat = {}
    for k1, v1 in cfg.items():
        if isinstance(v1, dict):
            for k2, v2 in v1.items():
                if isinstance(v2, dict):
                    for k3, v3 in v2.items():
                        flat[f"{k1}.{k2}.{k3}"] = v3
                else:
                    flat[f"{k1}.{k2}"] = v2
        else:
            flat[k1] = v1
    return flat

def first_crossing_time(t: np.ndarray, y: np.ndarray, target: float):
    idx = np.where(y >= target)[0]
    if len(idx) == 0:
        return None
    i = int(idx[0])
    if i == 0:
        return float(t[0])
    t0, t1 = float(t[i-1]), float(t[i])
    y0, y1 = float(y[i-1]), float(y[i])
    if y1 == y0:
        return t1
    alpha = (target - y0) / (y1 - y0)
    return t0 + alpha * (t1 - t0)

def main():
    fmu_path = "LongitudinalVehicle.fmu"

    with open("sim_input.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    with open("mapping.yaml", "r", encoding="utf-8") as f:
        mapping = yaml.safe_load(f)

    flat = flatten_cfg(cfg)

    start_values = {}
    for sysml_key, fmu_var in mapping.items():
        if sysml_key not in flat:
            raise KeyError(f"Missing key in sim_input.json: {sysml_key}")
        start_values[fmu_var] = float(flat[sysml_key])

    t_max = float(start_values.get("tMax", 30.0))
    res = simulate_fmu(
        fmu_path,
        start_values=start_values,
        stop_time=t_max,
        output=["time", "v"]
    )

    t = np.array(res["time"], dtype=float)
    v = np.array(res["v"], dtype=float)

    v_target = float(start_values.get("vTarget", 27.78))
    t_0_100 = first_crossing_time(t, v, v_target)

    limit = float(cfg["requirements"]["REQ_ACC_001"]["limit_s"])
    passed = (t_0_100 is not None) and (t_0_100 <= limit)

    out = {
        "vehicle_id": cfg["vehicle"]["id"],
        "t_0_100_s": t_0_100,
        "limit_s": limit,
        "pass": passed,
        "start_values": start_values
    }

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
