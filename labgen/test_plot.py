import pandas as pd
import matplotlib.pyplot as plt

try:
    df = pd.read_csv("runs/complex_triac_and_diac_circuit/iv_data_0.txt", sep=r'\s+', header=None)
    plt.plot(df[2], df[3] * 1000, linewidth=2, color='b', label="R=1k")
    plt.legend()
    plt.savefig("test_plot.png")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
