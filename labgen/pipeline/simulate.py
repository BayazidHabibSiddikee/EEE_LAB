import subprocess
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def run_ngspice(cir_file, output_dir):
    """Runs ngspice on the given cir file and returns paths to generated raw files."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # We will use ngspice in batch mode
    raw_file = os.path.join(output_dir, "output.raw")
    
    # Run ngspice
    cmd = ["ngspice", "-b", "-r", raw_file, cir_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("ngspice error:")
        print(result.stderr)
        print(result.stdout)
        raise RuntimeError("ngspice execution failed")
        
    return raw_file

def parse_raw_file(raw_file):
    """
    Very basic parser for ngspice ASCII raw files.
    For binary raw files, consider using PySpice or spicelib.
    Here we assume ascii output from ngspice (add `set filetype=ascii` in .spiceinit or cir)
    Actually, let's use a simple approach: we'll have the cir file use `wrdata` or `print` to output text.
    But for standard parsing, `spicelib` or `PySpice` is better.
    Let's write a simple parser for `wrdata` generated files for now, as it's just columns.
    """
    pass

def plot_diode_iv(csv_file, output_path):
    """Plots diode I-V curve from a CSV file."""
    df = pd.read_csv(csv_file, sep=r'\s+', header=None, names=['V_D', 'I_D'])
    
    plt.figure(figsize=(8, 6))
    plt.plot(df['V_D'], df['I_D'] * 1000, linewidth=2, color='b') # Convert to mA
    plt.title("Diode I-V Characteristics", fontsize=14)
    plt.xlabel("Diode Forward Voltage, $V_D$ (V)", fontsize=12)
    plt.ylabel("Diode Current, $I_D$ (mA)", fontsize=12)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.axhline(0, color='black', linewidth=1)
    plt.axvline(0, color='black', linewidth=1)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
