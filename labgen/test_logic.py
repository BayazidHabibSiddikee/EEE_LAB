import subprocess
import os

cir_path = "runs/complex_triac_and_diac_circuit/dynamic.cir"
txt_out = "runs/complex_triac_and_diac_circuit/iv_data.txt"
r_vals = ["1k", "5k", "10k"]

success_sim = False
for r_idx, r_val in enumerate(r_vals):
    loop_txt_out = txt_out.replace('.txt', f'_{r_idx}.txt')
    res = subprocess.run(["ngspice", "-b", cir_path], capture_output=True)
    if res.returncode == 0 and os.path.exists(loop_txt_out):
        success_sim = True
        print(f"Success for {r_val}")
    else:
        print(f"Failed for {r_val}, rc={res.returncode}, exists={os.path.exists(loop_txt_out)}")

print(f"Final success: {success_sim}")
