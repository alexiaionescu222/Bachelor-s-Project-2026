import csv
import json
import os

DATASET_CSV  = "dataset.csv"
DATASET_JSON = "dataset.json"
LOG_FOLDER   = "session_logs"

VALID_LABELS = {
    "CORRECT", "SILENCE", "PHONOLOGICAL_ERROR", "SEMANTIC_ERROR",
    "PARTIAL_ATTEMPT", "CIRCUMLOCUTION", "NEOLOGISM", "UNINTELLIGIBLE",
}

CSV_FIELDS = ["transcript", "target_word", "latency", "asr_confidence",
              "speech_detected", "label"]


def load_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def load_json_dataset(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json_dataset(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)


def is_duplicate(existing, entry):
    for row in existing:
        if (row["transcript"] == entry["transcript"]
                and row["target_word"] == entry["target_word"]
                and str(row["latency"]) == str(entry["latency"])):
            return True
    return False


def prompt_label(entry, suggested):
    print(f"  transcript : {entry['transcript']!r}")
    print(f"  target     : {entry['target_word']!r}")
    print(f"  latency    : {entry['latency']}s")
    print(f"  suggested  : {suggested}")
    while True:
        raw = input("  label [Enter=accept, or type override]: ").strip().upper()
        if raw == "":
            return suggested
        if raw in VALID_LABELS:
            return raw
        print(f"Invalid. Choose from: {', '.join(sorted(VALID_LABELS))}")


def trials_from_log(log_path):
    with open(log_path, encoding="utf-8") as f:
        data = json.load(f)
    entries = []
    for t in data.get("trials", []):
        transcript = t.get("transcript", "").strip()
        if transcript.startswith("[") and transcript.endswith("]"):
            transcript = ""
        entries.append({
            "transcript":      transcript,
            "target_word":     t.get("item", ""),
            "latency":         round(float(t.get("latency", 0.0)), 3),
            "asr_confidence":  round(float(t.get("asr_confidence", 0.0)), 3),
            "speech_detected": bool(transcript),
            "suggested_label": t.get("error_type", "PARTIAL_ATTEMPT").upper(),
        })
    return entries

def main():
    log_files = sorted([
        os.path.join(LOG_FOLDER, f)
        for f in os.listdir(LOG_FOLDER)
        if f.endswith(".json")
    ]) if os.path.exists(LOG_FOLDER) else []

    if not log_files:
        print(f"No session logs found in '{LOG_FOLDER}/'.")
        return

    all_entries = []
    for path in log_files:
        entries = trials_from_log(path)
        all_entries.extend(entries)

    csv_rows  = load_csv(DATASET_CSV)
    json_rows = load_json_dataset(DATASET_JSON)

    added = skipped = 0

    for e in all_entries:
        if is_duplicate(csv_rows, e):
            print(f"  skip (duplicate): {e['transcript']!r} / {e['target_word']!r}")
            skipped += 1
            continue

        suggested = e.pop("suggested_label")
        label = prompt_label(e, suggested)

        row = {**e, "label": label}
        csv_rows.append(row)
        json_rows.append(row)
        print(f"  + {label:<22} | {repr(e['transcript'])[:50]} → {repr(e['target_word'])}")
        added += 1

    save_csv(DATASET_CSV, csv_rows)
    save_json_dataset(DATASET_JSON, json_rows)

    print(f"  Added:   {added}")
    print(f"  Skipped: {skipped} (duplicates)")
    print(f"  Written to: {DATASET_CSV}, {DATASET_JSON}")


if __name__ == "__main__":
    main()
