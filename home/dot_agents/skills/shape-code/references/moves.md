# Design moves

Starting points for versions, not answers. Each move states what it predicts and what it
costs. A move is only as good as its counts: a version built from it must win on the
lenses, or the prediction failed for this code. The repo's own way of doing a thing comes
before any move here.

## General moves

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

## Rails

| Kind of code | Usual home | Notes |
|---|---|---|
| A business rule, invariant or derived value | the model it reads from (models need not be ActiveRecord: plain classes in `app/models` are fine) | |
| One user interaction that spans models, or has virtual attributes | a form model (ActiveModel, or ActiveType where the repo uses it) | keeps interaction-specific validations and callbacks off the core model |
| Translating HTTP to calls and back | the controller: params, one call into the model layer, a render or redirect | a branch on domain state in a controller is a rule in the wrong layer |
| A named, reused query | a scope; a query object if it is complex | |
| Display formatting | a helper, presenter or view component | no queries and no rules in views |
| Mail, HTTP calls, indexing | a job or mailer, triggered from the use case | `after_save` callbacks are for the record's own data integrity; side effects there also fire from the console, imports and tests |
| Authorization | the repo's policy layer | not ad hoc in models or views |
| Behavior shared as a trait by 2+ models | a concern | a concern for a single model hides size without reducing coupling |
| Service objects | follow the repo | contested: rich models and form models versus service layers; count it, don't preach either |

## Angular

| Kind of code | Usual home | Notes |
|---|---|---|
| Fetching and holding state for a screen | a container component, or a service or store it uses | |
| Display from inputs, events out | a presentational component | no injected data services; it is tested with inputs alone |
| HTTP and data access | an injectable service | not in components |
| State several components share | a service with signals, or the repo's store | local UI state stays in the component |
| Formatting for display | a pure pipe if it is reused | no logic-heavy method calls in templates: they run on every change detection |
| Reused DOM behavior | a directive | |
| Client-side business rules | plain functions or classes | tested without TestBed |
| Access checks and preloading for a route | guards and resolvers | not in `ngOnInit` |
| When to split a component | regions of its template with their own state and inputs, or it both fetches and renders | the Angular style guide's 400-line file size is a smell to check, not a rule |

## Other stacks

Use the framework's own guides for where each kind of code lives, and the general moves
above. Say in the report which guide a version followed.
