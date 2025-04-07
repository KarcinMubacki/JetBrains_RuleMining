import pandas as pd
from collections import deque


def parse_rules(rules_raw):
    rule_lines = [line.strip() for line in rules_raw.strip().split("\n") if line.strip()]
    parsed_rules = []

    for rule in rule_lines:
        lhs, _ = rule.split("=>")
        lhs_items = lhs.strip().split("AND")
        antecedent = frozenset(item.strip() for item in lhs_items)
        parsed_rules.append({
            "Antecedent": antecedent,
        })

    return pd.DataFrame(parsed_rules)


def matches_antecedent(row, antecedent):
    for cond in antecedent:
        if cond.startswith("NOT "):
            item = cond[4:]
            value = row.get(item, pd.NA)
            if pd.isna(value):
                return pd.NA
            if value:
                return False
        else:
            value = row.get(cond, pd.NA)
            if pd.isna(value):
                return pd.NA
            if not value:
                return False
    return True


def compute_support_confidence_single_rule(rule, data_df):
    total_rows = len(data_df)
    antecedent = rule["Antecedent"]
    matches = data_df.apply(lambda row: matches_antecedent(row, antecedent), axis=1)
    valid = matches.notna()
    matches_clean = matches[valid]
    targets = data_df.loc[valid, 'donor_is_old']
    matches_with_target = matches_clean & targets

    support = matches_with_target.sum() / total_rows
    confidence = (matches_with_target.sum() / matches.sum()) if matches.sum() > 0 else 0.0
    return support, confidence


def compute_support_confidence(rules_df, data_df):
    supports = []
    confidences = []

    for _, rule in rules_df.iterrows():
        support, confidence = compute_support_confidence_single_rule(rule, data_df)
        supports.append(support)
        confidences.append(confidence)

    rules_df["Support"] = supports
    rules_df["Confidence"] = confidences
    return rules_df


def prune_overly_specific_rules(rules_df):
    def is_overly_specific(idx):
        rule = rules_df.loc[idx]
        for j, other in rules_df.iterrows():
            if j == idx:
                continue
            if other["Antecedent"].issubset(rule["Antecedent"]):
                if other["Confidence"] >= 0.98*rule["Confidence"]:
                    return True
        return False

    rules_df["Overly_Specific"] = rules_df.index.to_series().apply(is_overly_specific)
    return rules_df[~rules_df["Overly_Specific"]].drop(columns="Overly_Specific")


def merge_rules(rules_df, data_df, min_support, min_confidence, max_iterations=10000):
    queue = deque(rules_df.to_dict("records"))
    final_rules = []
    seen = set()
    loop_counter = 0

    while queue:
        if loop_counter > max_iterations:
            break
        loop_counter += 1

        current_rule = queue.popleft()
        merged = False
        new_queue = deque()

        while queue:
            candidate_rule = queue.popleft()
            merged_antecedent = current_rule["Antecedent"].intersection(candidate_rule["Antecedent"])
            if not merged_antecedent or merged_antecedent in seen:
                new_queue.append(candidate_rule)
                continue

            support, confidence = compute_support_confidence_single_rule(
                {"Antecedent": merged_antecedent}, data_df
            )
            if support >= min_support and confidence >= min_confidence:
                seen.add(merged_antecedent)
                queue.appendleft({
                    "Antecedent": merged_antecedent,
                    "Support": support,
                    "Confidence": confidence
                })
                merged = True
                break
            else:
                new_queue.append(candidate_rule)

        if not merged:
            current_fs = current_rule["Antecedent"]
            if current_fs not in seen:
                seen.add(current_fs)
                final_rules.append(current_rule)

        queue = new_queue + queue

    return pd.DataFrame(final_rules)


def score_rules(rules_df, alpha):
    rules_df["Score"] = alpha*rules_df["Confidence"] + (1 - alpha)*rules_df["Support"]
    return rules_df.sort_values(by="Score", ascending=False).reset_index(drop=True)


def save_rules_to_file(rules_df, output_file):
    with open(output_file, "w", encoding='utf-8') as f:
        for _, row in rules_df.iterrows():
            antecedent_str = " AND ".join(sorted(row["Antecedent"]))
            f.write(f"{antecedent_str} => donor_is_old\n")


def parse_and_prune_ruleset(
    rules_raw, data_df,
    alpha=0.8, min_support=0.0, min_confidence=0.0, output_file="output/compressed_ruleset.txt"
):
    rules_df = parse_rules(rules_raw)
    rules_df = compute_support_confidence(rules_df, data_df)

    rules_df = rules_df[
        (rules_df["Support"] >= min_support) &
        (rules_df["Confidence"] >= min_confidence)
    ]

    pruned_df = prune_overly_specific_rules(rules_df)
    merged_df = merge_rules(pruned_df, data_df, min_support, min_confidence)
    scored_merged_rules_df = score_rules(merged_df, alpha)
    save_rules_to_file(scored_merged_rules_df, output_file)