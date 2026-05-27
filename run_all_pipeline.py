# urutan pipeline : 01_obtain -> 02_scrub -> 03_explore -> 04_model -> 05_visualize

import subprocess
import sys

scripts = [
    "01_obtain.py",
    "02_scrub.py",
    "03_explore.py",
    "04_model.py",
    "05_visualize.py",
]

for script in scripts:
    print(f"\n{'='*50}")
    print(f"  Menjalankan: {script}")
    print(f"{'='*50}")
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"\n  [FAIL] {script} error. Pipeline dihentikan.")
        sys.exit(1)
print("\n  All pipelines di-execute dengan sukses.")