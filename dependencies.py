import subprocess
import pandas as pd
import json

if __name__ == "__main__":
    rc = subprocess.call("./dependencies.sh")

    with open("dependencies.json", encoding='utf-8') as file:
        lst = json.load(file)

    out = []
    for d in lst:
        out.append({})
        for k, v in d["package"].items():
            out[-1][f"package.{k}"] = v
        out[-1]["dependencies"] = "; ".join(v["key"] for v in d["dependencies"])

    df = pd.DataFrame(out)
    print(df)
    df.to_csv("dependencies.csv", index=False)
