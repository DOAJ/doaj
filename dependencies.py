import subprocess
import pandas as pd
import json

if __name__ == "__main__":
    rc = subprocess.call("./dependencies.sh")

    with open("dependencies_analysis/dependencies.json", encoding='utf-8') as file:
        lst = json.load(file)

    with open("dependencies_analysis/upgrade.json", encoding='utf-8') as file:
        upg = json.load(file)

    out = []
    for d in lst:
        out.append({})
        for k, v in d["package"].items():
            out[-1][f"package.{k}"] = v
        out[-1]["dependencies"] = "; ".join(v["key"] for v in d["dependencies"])

    df_dep = pd.DataFrame(out)
    df_upgrade = pd.DataFrame(upg)

    all = df_dep.merge(right=df_upgrade, how="left", left_on="package.package_name", right_on="name")
    all_short = all.drop(columns=["name","version", "latest_filetype", "editable_project_location"])
    all_short = all_short[["package.key","package.package_name","package.installed_version","package.required_version","latest_version","dependencies"]]
    all_short.to_csv("dependencies_analysis/dependencies.csv", index=False)
