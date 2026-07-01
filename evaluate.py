"""
py evaluate_sessions.py --sessions experiment_logs/
"""

import argparse
import json
import os
import numpy as np
from collections import Counter
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score

LABEL_ORDER = [
    "SILENCE", "UNINTELLIGIBLE", "CORRECT", "PHONOLOGICAL_ERROR",
    "SEMANTIC_ERROR", "CIRCUMLOCUTION", "NEOLOGISM", "PARTIAL_ATTEMPT",
]


def print_report(y_true, y_pred, method_name, labels):
    print(f"\n  {method_name}")
    print(f"  {'-' * 45}")
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    print(f"  Confusion matrix  (rows=true, cols=predicted)")
    print("  " + "".join(f"{l[:6]:>8}" for l in labels))
    for i, rl in enumerate(labels):
        print("  " + f"{rl[:14]:<16}" + "".join(f"{cm[i,j]:>8}" for j in range(len(labels))))


def evaluate_batch(session_folder):
    log_files = sorted([
        os.path.join(session_folder, f)
        for f in os.listdir(session_folder)
        if f.endswith(".json")
    ])

    if not log_files:
        print(f"No JSON files found in '{session_folder}'")
        return

    all_annotated = []
    print(f"\n  Loading session logs from '{session_folder}':")
    for path in log_files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        trials = data.get("trials", [])
        annotated = [t for t in trials if "gold_label" in t]
        print(f"    {os.path.basename(path):<45}  {len(annotated):>3} annotated / {len(trials):>3} total")
        all_annotated.extend(annotated)

    if not all_annotated:
        print("\n  No gold labels found in any session log.")
        print("  Make sure each trial has a 'gold_label' field.")
        return

    print(f"\n  Total annotated trials: {len(all_annotated)}")

    gold = np.array([t["gold_label"]                   for t in all_annotated])
    clf  = np.array([t["error_type"]                   for t in all_annotated])
    rb   = np.array([t.get("error_type_rb", "UNKNOWN") for t in all_annotated])

    present = [l for l in LABEL_ORDER if l in gold]

    print(f"\n  Gold label distribution:")
    counts = Counter(gold)
    for l in present:
        print(f"    {l:<25}  {counts.get(l, 0)}")

    print_report(gold, rb,  "Rule-based",    present)
    print_report(gold, clf, "Random Forest", present)

    rb_acc  = accuracy_score(gold, rb)
    rb_f1   = f1_score(gold, rb,  average="macro", zero_division=0)
    clf_acc = accuracy_score(gold, clf)
    clf_f1  = f1_score(gold, clf, average="macro", zero_division=0)

    print(f"\n  SUMMARY  (vs manual gold labels, all participants)")
    print(f"  {'Method':<28}  {'Accuracy':>10}  {'F1 macro':>10}")
    print(f"  {'-'*52}")
    print(f"  {'Rule-based':<28}  {rb_acc:>10.3f}  {rb_f1:>10.3f}")
    print(f"  {'Random Forest':<28}  {clf_acc:>10.3f}  {clf_f1:>10.3f}")

    disagreements = [t for t in all_annotated
                     if t["error_type"] != t.get("error_type_rb") or
                        t["error_type"] != t["gold_label"]]

    if disagreements:
        print(f"\n  DISAGREEMENTS  ({len(disagreements)} trials)")
        print(f"  {'Transcript':<30}  {'Gold':<22}  {'CLF':<22}  {'RB'}")
        print(f"  {'-'*90}")
        for t in disagreements:
            transcript = t.get("transcript", "")[:28]
            print(f"  {transcript:<30}  {t['gold_label']:<22}  "
                  f"{t['error_type']:<22}  {t.get('error_type_rb', '?')}")


def evaluate_single(session_path):
    with open(session_path, encoding="utf-8") as f:
        data = json.load(f)
    trials = data.get("trials", [])
    annotated = [t for t in trials if "gold_label" in t]

    if not annotated:
        print(f"No gold labels found in {session_path}")
        return

    print(f"\n  {os.path.basename(session_path)}  —  {len(annotated)} annotated / {len(trials)} total")

    gold = np.array([t["gold_label"]                   for t in annotated])
    clf  = np.array([t["error_type"]                   for t in annotated])
    rb   = np.array([t.get("error_type_rb", "UNKNOWN") for t in annotated])

    present = [l for l in LABEL_ORDER if l in gold]

    print_report(gold, rb,  "Rule-based",    present)
    print_report(gold, clf, "Random Forest", present)

    rb_acc  = accuracy_score(gold, rb)
    rb_f1   = f1_score(gold, rb,  average="macro", zero_division=0)
    clf_acc = accuracy_score(gold, clf)
    clf_f1  = f1_score(gold, clf, average="macro", zero_division=0)

    print(f"\n  SUMMARY")
    print(f"  {'Method':<28}  {'Accuracy':>10}  {'F1 macro':>10}")
    print(f"  {'-'*52}")
    print(f"  {'Rule-based':<28}  {rb_acc:>10.3f}  {rb_f1:>10.3f}")
    print(f"  {'Random Forest':<28}  {clf_acc:>10.3f}  {clf_f1:>10.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=str, default=None,
                        help="Folder with all session log JSONs")
    parser.add_argument("--session",  type=str, default=None,
                        help="Path to a single session log JSON")
    args = parser.parse_args()

    if args.sessions:
        evaluate_batch(args.sessions)
    elif args.session:
        evaluate_single(args.session)