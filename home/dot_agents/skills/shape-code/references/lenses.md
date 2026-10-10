# Lenses: how to count

Counts are estimates in round numbers. They exist to compare versions of the same diff,
so count every version the same way, and don't argue about a line or two.

## Decisions

List what the code in the reach decides, one row per decision, by kind:

| Kind | Example |
|---|---|
| Business rule | what counts as an active account; when a discount applies |
| Data field and its flow | the `tags` field: stored, permitted, serialized, shown, edited |
| Display format | how money is formatted; how a date shows in a list |
| Permission | who may save a story; what a logged-out visitor sees |
| Interface | a method, endpoint, component input or event the diff creates or widens |
| Outside library | the HTTP client, chart library or gem the code calls directly |
| The feature itself | everything that would go if the feature were removed |

For each decision and version, count its **places**: the units that would have to change
if that decision changed. Name them. Mark places as **lockstep** (⛓) when they must
change together or behavior breaks: a condition repeated in three queries, a field added
to the form but not to the permitted params.

- A decision in one place is robust, however untidy that place looks. Don't move it.
- A decision in several places has no home yet. That is where versions earn their keep.
- For the feature itself, count the units outside its own files that would need editing
  to remove it: that is how tangled the feature is with shared code.
- For an outside library, count the units that call it directly rather than through one
  wrapper or service. More than one is a decision spread out.
- For an interface, count its callers in the reach: they are the places that break when
  the interface changes.

Count edits in existing code too. The reach is in scope.

**Search the whole codebase** for each decision's places, not only the diff's files.
Grep for the rule's tell-tale names, conditions, constants and columns: a filter the
diff adds to one query often already exists in five older ones, and those are places of
the same decision.

### History

For each decision in more than one place, look up how often its places changed
together: `git log --format=%h -- <files of its places>`, then count the commits that
touched at least two of those places, checking with `git show <sha>` that the change
was about this decision and not a mass reformat. Skip the commit that introduced the
decision or copied it into a new place: only later changes to places that already
existed show its cost coming due. For places inside one large file, use
`git log -L :<method>:<file>` per method instead. Report it as 🔥n, or no mark when n
is 0.

History sets urgency, not importance. A decision in several places is worth bringing to
one either way; 🔥 says its cost has been coming due. A decision in one place needs no
history lookup.

## Test

1. **List the behavior cases** once, from the requirements and the branches of the rules:
   each distinct input class with its expected outcome (active, inactive, no accounts).
   The wiring of the feature (does the controller call the rule, does the component show
   its result) is a case of its own.
2. **For each version and case:** the cheapest test that verifies it, and what that test
   has to **set up**: every collaborator it builds or fakes before it can run. Count one
   for each:
   - a record, factory or fixture created;
   - a logged-in user or session;
   - a stubbed or mocked service, spy, clock or HTTP fake;
   - an entry in a test bed: each import, provider, mock provider or schema;
   - the plumbing to render and drive it: a component fixture, change detection, a
     request, a page visit.
   Then the lines of the test, setup included.
3. **Report** the total test lines and the **average setup per case**. Setup per case is
   the number that makes framework weight visible: a rule in a plain function or a model
   method needs 0–2, the same rule inside a component under a test bed often 4–6.

A healthy shape tests most cases with little setup and has one heavier test per wiring.
When a version needs heavy setup for every case, the rule is sitting in the layer the
heavy setup drives. Setup that grows with each case means the unit asks its caller to
know too much.

## Read

Choose one question a colleague would ask about the behavior, like "what discount does
order 42 get, and why?" or "when does this email go out?". Follow the code from the entry
point to the full answer, and count the files you must open. Framework and library files
don't count. Every version uses the same question.

More files is worse even when each file is small. A version that brings decisions to one
place but adds files to Read has split something a reader needs together; it may add at
most one file per decision it brings to one place.

## Invalid states

Only when the diff adds flags or optional fields that together describe one state: count
the combinations the code allows and how many of them are valid, like "3 flags: 4 of 8
valid". A version that makes the invalid ones unrepresentable (one state value instead of
several flags) also shrinks the behavior cases.

## Planned work

When the human named upcoming work, count it as an extra decision row marked `planned`:
the places that work would touch in each version. Never add planned rows yourself.
