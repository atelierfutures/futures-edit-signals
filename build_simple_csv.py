import os, pandas as pd
import papermill as pm

# Run the notebook to produce outputs/signals_ranked_plus.csv
pm.execute_notebook("signals_pipeline_colab_global_PLUS.ipynb", "executed.ipynb", parameters={})

# Keep your 7 columns
df = pd.read_csv("outputs/signals_ranked_plus.csv")
simple = df[["published","title","link","category","primary_keyword","trend_score","status"]]

# Write to docs/ so GitHub Pages serves it at the site root
os.makedirs("docs", exist_ok=True)
simple.to_csv("docs/signals_simple.csv", index=False)
print("✅ wrote docs/signals_simple.csv")
