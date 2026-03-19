import tarfile
import json
from datetime import datetime
import argparse

def extract_top_records(tar_path, output_path):
    articles = []

    def parse_last_updated(article):
        # Try to get the last_updated field, fallback to created_date or 0
        date_str = article.get("last_updated") or article.get("created_date") or "1970-01-01T00:00:00Z"
        try:
            return datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return datetime.min

    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.isfile() and member.name.endswith(".json"):
                f = tar.extractfile(member)
                if f:
                    try:
                        data = json.load(f)
                        data.sort(key=parse_last_updated, reverse=True)
                        top = data[:100]
                        articles.extend(top)
                    except Exception as e:
                        print(f"Error reading {member.name}: {e}")

            # Sort articles by last_updated (descending)
            if len(articles) > 100:
                articles.sort(key=parse_last_updated, reverse=True)

                # Get top 100
                articles = articles[:100]

    with open(output_path, "w", encoding="utf-8") as out:
        for art in articles:
            title = art.get("bibjson", {}).get("title", "NO TITLE")
            last_updated = art.get("last_updated", "NO DATE")
            out.write(f"{title}\t{last_updated}\n")

    print(f"Wrote top 100 records to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract top 100 records from a tar.gz archive of JSON files.")
    parser.add_argument("tar_path", help="Path to the tar.gz file")
    parser.add_argument("output_path", help="Path to the output txt file")
    args = parser.parse_args()
    extract_top_records(args.tar_path, args.output_path)
