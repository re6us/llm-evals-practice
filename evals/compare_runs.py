import argparse
import csv
import math

from config import RUNS

METRICS = ["recall@5", "precision@5", "f1@5", "recall@10", "precision@10", "f1@10", "mrr"]
MOVERS_METRICS = ["recall@10", "mrr"]
N_MOVERS = 5


def load_per_query(run_name):
    with open(RUNS / f"{run_name}_per_query.csv", "r", encoding="utf-8") as f:
        return {row["query_id"]: row for row in csv.DictReader(f)}


def paired_diff(base, other, metric):
    diffs = [float(other[q][metric]) - float(base[q][metric]) for q in base]
    n = len(diffs)
    mean = sum(diffs) / n
    variance = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    half = 1.96 * math.sqrt(variance / n)
    better = sum(d > 0 for d in diffs)
    worse = sum(d < 0 for d in diffs)
    return mean, half, better, worse, n - better - worse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    parser.add_argument("other")
    args = parser.parse_args()

    base = load_per_query(args.base)
    other = load_per_query(args.other)
    assert base.keys() == other.keys(), "runs cover different queries"

    print(f"{args.other} vs {args.base}, {len(base)} queries, paired\n")
    print(f"{'metric':<14}{args.base:>10}{args.other:>10}   {'diff':>16}   better/worse/same  verdict")
    for m in METRICS:
        b = sum(float(r[m]) for r in base.values()) / len(base)
        o = sum(float(r[m]) for r in other.values()) / len(other)
        mean, half, better, worse, same = paired_diff(base, other, m)
        verdict = "real" if abs(mean) > half else "noise"
        print(f"{m:<14}{b:>10.3f}{o:>10.3f}   {mean:>+7.3f} ± {half:.3f}   "
              f"{better:>3} / {worse:>3} / {same:>3}      {verdict}")

    for m in MOVERS_METRICS:
        moves = sorted(
            ((float(other[q][m]) - float(base[q][m]), q) for q in base),
            reverse=True,
        )
        print(f"\nbiggest gains in {m}:")
        for d, q in moves[:N_MOVERS]:
            print(f"  {q}  {float(base[q][m]):.2f} -> {float(other[q][m]):.2f}  ({d:+.2f})  {base[q]['query']}")
        print(f"biggest losses in {m}:")
        for d, q in moves[-N_MOVERS:][::-1]:
            print(f"  {q}  {float(base[q][m]):.2f} -> {float(other[q][m]):.2f}  ({d:+.2f})  {base[q]['query']}")


if __name__ == "__main__":
    main()