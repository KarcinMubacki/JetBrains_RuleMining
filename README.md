Solution description for JetBrains' 'Enabling quantitative variables in association rule mining' internship/project task

TL;DR description:
given a ruleset and (binary) dataset it refers to, compress it

Solution idea:

Rely on two basic ARM concepts: support and confidence

Support of a rule - % of instances (rows) sufficing the rule's antecendent

Confidence of a rule - among the ones sufficing rule's antecendent, % of instances sufficing target (donor_is_old in this case)

NA handling:

Done at the level of calculation of support/confidence: since dropping rows with NAs might lose too much data it was decided that
during the calculations for specifics rules observations with NAs will be disregarded

Redundant rules:

We will say a rule is redundant (overly specific) if there exists its 'subset' in the ruleset (example: A AND B is a 'subset' of A AND B AND NOT C)
and the subset has a similar or higher confidence (precisely: confidence(subset) >= 0.98*confidence(superset))
Redundant rules will be deleted from the ruleset

Rule merging:

Since some rules can 'close' in the predictive sense we would like to found such relations and merge such rules into single ones
We do that using a queue:
- we set up a queue of all the rules currently in the dataset (after deleting redundant rules);
- check the first rule against other rules by taking their intersection (example: A AND B intersected with B AND C will give B) and computing their support/confidence
- if the metrics exceed a super-specified minimum the rules are merged (the intersection being the new rule) and the new rule is put at the end of the queue 
- if after going through the entire queue the rule is not merged with any other rule it is treated as a 'final rule'
- looping until queue is empty or number of iterations exceeds safety threshold (escaping potential infinite loops)

Output:
After deleting redundant rules and merging potential rules we sort the remaining rules by a convex combination of support and confidence of the rule (by default 0.8*confidence + 0.2*support)
and the rules are saved into a desired .txt file

Run the code with
python main.py --data data/dataset.tsv --rules data/rules.txt
