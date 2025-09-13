import os, pandas as pd
import papermill as pm

# 1) Run the notebook to produce outputs/signals_ranked_plus.csv
pm.execute_notebook(
    "signals_pipeline_colab_global_PLUS.ipynb",
    "executed.ipynb",
    parameters={}
)

# 2) Keep your 7 columns
df = pd.read_csv("outputs/signals_ranked_plus.csv")
simple = df[["published","title","link","category","primary_keyword","trend_score","status"]]

# 3) Publish to /site for GitHub Pages
os.makedirs("site", exist_ok=True)
simple.to_csv("site/signals_simple.csv", index=False)
print("✅ wrote site/signals_simple.csv")
