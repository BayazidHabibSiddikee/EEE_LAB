import pandas as pd
import numpy as np
import random
from pipeline.validators.data import _interpolate_simulation, _relative_error

v_data = np.linspace(-15, 15, 300)
i_data = np.sin(v_data) * 0.05
# Add duplicate x values or something?
df = pd.DataFrame({"V": v_data, "I": i_data}).sort_values("V").reset_index(drop=True)

v = list(df["V"])
i = list(df["I"])
n_points = min(10, len(v))
indices = [int(j * (len(v) - 1) / (n_points - 1)) for j in range(n_points)]

for idx in indices:
    v_val = v[idx]
    i_val = i[idx] * 1000
    
    i_claimed_ma = float(f"{i_val:.1f}")
    i_actual = _interpolate_simulation(df, v_val)
    i_actual_ma = i_actual * 1000
    print(f"V: {v_val:.1f} -> claimed: {i_claimed_ma:.1f} mA, actual: {i_actual_ma:.1f} mA, error: {_relative_error(i_claimed_ma, i_actual_ma):.1f}%")

