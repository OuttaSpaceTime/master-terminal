# Design moves

Starting points for versions, not answers. Each move states what it predicts and what it
costs. A move is only as good as its counts: a version built from it must win on the
lenses, or the prediction failed for this code. None of these is good or bad in itself.

| Move | Predicts | Costs | Signal in the code |
|---|---|---|---|
| Move a misplaced decision home (⌂) | readers and sibling changes find it where its kind lives; every caller passes through it | usually none; tests move to the home's level | an action, job, endpoint handler or API client doing what its siblings do in a model, a base-class hook, a service or a component |
| Put a rule with the data it reads | the rule's places drop to 1; tests need less setup | can bloat the data owner; watch Read | the rule reads mostly one other object's data |
| Give one rule one home | lockstep places disappear | one more unit if the home is new | the same condition or constant in 2+ places |
| Split by groups that share no state | smaller setup per case | +1 unit, maybe +1 Read file | methods fall into groups that share no fields, or the unit is described with "and" |
| Merge or inline a pass-through | −1 Read file | the merged unit grows | deleting the unit moves its complexity rather than spreading it to callers |
| One state value instead of several flags | invalid states disappear; fewer cases | a schema change if the flags are stored | several booleans or optional fields checked together |
| A value object for values that travel together | a new field touches one place | +1 concept | the same 2–4 parameters passed along together |
| One map or polymorphism instead of repeated branches | the branching decision drops to 1 place | +1 concept per variant class | the same `if` or `case` on the same value in 2+ places today |
| Move a side effect out of a lifecycle callback into the use case | "when it happens" stays in 1 place as entry points multiply | the use case grows by one call | mail, HTTP or indexing triggered from a save or init hook while several entry points exist |
| Separate fetching from display | display tests need almost no setup; a second screen reuses the display | +1 unit | one unit both loads data and renders it |
| One wrapper for an outside library | the library decision drops to 1 place | +1 unit | the same library called directly from 2+ units |
| A shared component, partial or helper | a duplicated display decision drops to 1 place | +1 file | the same markup or template logic in 2+ places |
| A store, service object or form object | a decision several callers derive or repeat drops to 1 place | +1 to +3 files | only pays when 2+ callers repeat the decision today; with one caller it spreads one decision over more files |
| A seam, registry or strategy | variants live in one place each | +1 interface, +2 concepts | pays only with 2+ real variants today; one variant is indirection |
