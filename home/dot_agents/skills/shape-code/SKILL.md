---
name: shape-code
description: >-
  Checks whether a working change is in the right shape: where each piece of code belongs
  (model, controller, service, job, component), whether the codebase already has it,
  whether it is needed at all, and whether a decision is spread over several places. Use
  after implementing a change that works, when asking whether code is in the right place,
  how to split a class or component, or whether a pattern like a service object pays off.
argument-hint: "[base ref or commit range]"
---

# Shape code

Read the diff (the range given, else uncommitted work against `HEAD`, else the branch
against its merge-base) and the code around it. Analysis only: edit nothing unless asked.

For each decision the diff makes (a rule, a data field and its flow, a format, a
permission, an interface, a lookup, a guard) and each concept it adds (a class, method,
scope, flag, component), answer four questions with evidence from the codebase: file and
line, counts from grep.

1. **Owner.** Which unit should hold it? Count where this repo keeps that kind of code,
   like `lookups in set_* hooks: 9 · inline: 1`; the majority is home, not the code next
   to the diff. Is the change made in the unit that produces the behavior the requirement
   is about, or in a caller or screen around it?
2. **Exists.** Does the codebase already have it: a scope, helper, hook, validator, the
   parent method, the same list or condition built elsewhere in the same class? Grep the
   names it combines.
3. **Needed.** Which part of the requirement breaks if it is deleted? If none, deleting
   it is the fix; say roughly how many lines that saves. Ask it of the decision, not of
   one copy: a rule the requirement needs stays, even when this copy of it is dead code;
   then it moves to its owner.
4. **Places.** In how many units does it live? Several places that must change together
   are a problem; one place is fine, however untidy.

Recommend the shape that passes all four: move it to its owner, reuse what exists,
delete what isn't needed, bring a spread decision to one place. Tests move with the code
to the cheapest level that still covers the behavior. Before recommending a move, check
when the new home runs: a callback also fires on cascades (deleting an account destroys
each of its records) and on every other path that saves the record. Don't add structure
for variants that don't exist yet. A change to behavior or to an interface the
requirement didn't ask for is an option to weigh, never the recommendation.

Report in a few lines: one per finding with the decision, the failed question, the
numbers and the fix; recommended fixes first, then options worth weighing, then one line
of what you checked and left as is. End with the question to ask next time and this
diff's answer: "if X changed, how many files would you edit? 3 here, 1 after the fix."
