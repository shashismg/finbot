"""Quick terminal test: python cli.py "Should I buy Infosys?" """
import sys

from finbot.agent import TOOL_LABELS, run
from finbot.config import DISCLAIMER


def main() -> None:
    query = " ".join(sys.argv[1:]) or input("Ask FinBot about a stock: ")
    verdict = run(query, on_step=lambda name, args: print(f"  -> {TOOL_LABELS[name]} {args}"))

    print()
    if not verdict.is_stock_query:
        print(verdict.summary)
        return
    print(f"{verdict.company} ({verdict.ticker})  ->  {verdict.verdict}  [{verdict.confidence}% confidence, {verdict.time_horizon}]")
    print(f"\n{verdict.summary}\n")
    print("Bull case:")
    for p in verdict.bull_points:
        print(f"  + {p}")
    print("Bear case:")
    for p in verdict.bear_points:
        print(f"  - {p}")
    if verdict.key_metrics:
        print("\nKey metrics:")
        for k, v in verdict.key_metrics.items():
            print(f"  {k}: {v}")
    if verdict.sources:
        print("\nSources:")
        for s in verdict.sources:
            print(f"  {s}")
    print(f"\n{DISCLAIMER}")


if __name__ == "__main__":
    main()
