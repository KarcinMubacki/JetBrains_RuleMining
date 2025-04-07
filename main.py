import argparse
import functionalities
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--rules",
        type=str,
        required=True,
    )
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.rules, encoding="utf-8") as f:
        rules_raw = f.read()
    df = pd.read_csv(args.data, sep="\t")
    functionalities.parse_and_prune_ruleset(rules_raw, df, min_support=0.1, min_confidence=0.15)
    return


if __name__ == '__main__':
    main()