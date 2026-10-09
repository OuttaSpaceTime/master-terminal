# Design moves

Starting points for versions, not answers. Each move states what it predicts and what it
costs. A move is only as good as its counts: a version built from it must win on the
lenses, or the prediction failed for this code. The repo's own way of doing a thing comes
before any move here.

| Move | Predicts | Costs | Signal in the code |
|---|---|---|---|
| Put a rule with the data it reads | fewer units for "change the rule"; unit tests instead of request or TestBed tests | can bloat the data owner; watch Read | most of the code's reads go to one other object |
| Give one rule one home | fewer lockstep edits | one more unit if the home is new | the same condition or constant in 2+ places |
| Split by groups that share no state | Change touches one part; smaller test setup | +1 unit, maybe +1 Read file | methods fall into groups that share no fields, or the unit is described with "and" |
| Merge or inline a pass-through | −1 Read file, fewer units | the merged unit grows | deleting the unit moves its complexity rather than spreading it to callers |
| One state value instead of several flags | fewer cases to test; checks for invalid combinations disappear | a schema change if the flags are stored | several booleans or optional fields checked together |
| A value object for values that travel together | fewer edits when the group gains a field | +1 concept | the same 2–4 parameters passed along together |
| One map or polymorphism instead of repeated branches | "add a variant" touches one place | +1 concept per variant class | the same `if` or `case` on the same value in 2+ places |
| A seam (port, adapter, injected collaborator) | unit tests without the outside system | +1 interface | only pays off with two real implementations, production and test; with one it is indirection |
| A strategy, registry or plugin point | "add a variant" without touching existing code | +2 concepts | pays off only with 2+ variants today, or a scenario confirmed by history |
| Move a side effect out of a lifecycle callback into the use case | the side effect stops firing from imports, the console and tests; "new entry point" scenarios get cheaper | the use case grows by one call | mail, HTTP or indexing triggered from a save or init hook |
| Separate fetching from display | display is tested with plain inputs; "another screen shows it" reuses it | +1 unit | one unit both loads data and renders it |
