# Diff Outline Format

Used by `/diff-review` at **Checkpoint 2** only. Each changed file/symbol shows two layers:
the actual diff first, then the behavioral summary.

Concerns are **not** part of this format — they belong in Checkpoint 3, after invariant
analysis. Do not add concern callouts to Checkpoint 2 messages.

---

## Layer 1: Actual Diff

Show the relevant `+/-` hunk(s) from `git diff`. Trim unchanged context to ≤3 lines.

```diff
@@ -42,7 +42,10 @@ resolveCurrentUser() {
   const token = this.sessionToken;
-  return this.http.get<User>('/api/user');
+  if (!token) return of(null);
+  return this.http.get<User>('/api/user');
 }
```

If a file has multiple hunks, show each one. Label them if they are far apart in the file
to give orientation (`// ... line 84 ...`).

---

## Layer 2: Behavioral Summary

After the diff, provide the structured summary. Use only the fields that apply —
omit empty fields entirely (don't pad with "N/A" or "none").

### Per-symbol format

```
### <SymbolType>: `<SymbolName>`
Location: <path>:<line>

**What changed:** <1-2 sentences. What does the code DO differently at runtime? Avoid
  "added a null check on line 42" — say what runtime behavior changes instead.
  Example: "Returns null immediately when no session token is present, rather than
  proceeding to the HTTP call.">

**Where in flow:** Called from `<CallerSymbol>` (<path>:<line>) when <condition>.
  <Add additional call sites if there are more than one.>
  <For lifecycle hooks or framework callbacks, name the lifecycle point instead.>

**Data in → out:**
  - Input: `<type>` — <source or constraint note if non-obvious>
  - Transforms: <what happens: filtering, mapping, enriching, normalizing, etc.>
  - Output: `<type>` — <destination or consumer if non-obvious>

**Invariants:**
  - <What must always be true after this code runs>
  - <New invariants introduced by this change>
  - <Prior invariants relaxed or removed, if any>

**Notable:** <Constraints, edge cases, or non-obvious behaviors. One bullet per item.>
```

### Per-file group format

When several small symbols in the same file form one logical change, group them under
a file-level header instead of writing separate symbol blocks:

```
## `<path/to/file>`

**Change summary:** <1-2 sentences describing the combined behavioral change.>

**Symbols touched:** `SymbolA`, `SymbolB`, `SymbolC`

**Where in flow:** <how this file fits in the execution graph>

**Data in → out:** <overall data transformation if the file acts as a pipeline stage>

**Invariants:** <any cross-symbol invariants>

**Notable:** <constraints or risks>
```

---

## Omission Rules

Leave out a field entirely when it does not carry information:

- **Data in → out** — omit for void side-effect functions (logging, DOM mutations,
  event emissions with no return value consumed upstream).
- **Invariants** — omit when the symbol has no state dependencies and introduces no
  new contracts.
- **Notable** — omit when there is genuinely nothing notable. Do not pad.
- **Where in flow** — omit when the symbol is a private utility with a single obvious
  call site already mentioned in "What changed."

The format exists to build a mental model, not to fill every field.

---

## What This Format Is NOT

- Not a line-by-line diff recap ("line 12 was changed from X to Y")
- Not a correctness judgment ("this is wrong because…")
- Not pseudocode — use real symbol names and real types from the codebase
- Not generic descriptions of what a symbol type does ("methods return values")

---

## Examples

### Example 1: Guard added to a service method

```diff
@@ -84,5 +84,7 @@ resolveCurrentUser(): Observable<User | null> {
+  if (!this.sessionToken) return of(null);
   return this.http.get<User>('/api/sessions/current').pipe(
     map(res => res.data)
   );
```

```
### Method: `resolveCurrentUser`
Location: src/app/core/services/session.service.ts:84

**What changed:** Returns `null` immediately when `this.sessionToken` is absent, rather
  than proceeding to the HTTP call and throwing on response parse.

**Where in flow:** Called from `AuthGuard.canActivate()` (src/app/auth/auth.guard.ts:31)
  on every protected route navigation.

**Data in → out:**
  - Input: none (reads `this.sessionToken` from instance state)
  - Transforms: short-circuits if token absent; otherwise fetches and deserializes user
  - Output: `Observable<User | null>` — was previously `Observable<User>`

**Invariants:**
  - Callers must now handle `null` — the prior contract was `Observable<User>` (never null)
  - HTTP call is only made when token is present

**Notable:** `AuthGuard` currently passes the result directly to `router.navigate` without
  handling `null` — this is a new invariant callers must satisfy.
```

---

### Example 2: New discriminated union type

```diff
@@ -12,5 +12,9 @@ export interface ApiResponse<T> {
-  success: boolean;
-  data?: T;
+export type FilteredResponse<T> =
+  | { kind: 'ok'; data: T }
+  | { kind: 'error'; code: string };
```

```
### Type: `FilteredResponse<T>`
Location: src/app/shared/types/api.types.ts:12

**What changed:** Replaces `ApiResponse<T>` (boolean `success` flag, optional `data`)
  with a discriminated union. Callers now get exhaustive narrowing instead of a nullable
  field access.

**Where in flow:** Returned by all methods in `DataService`; consumed by `withRequestState()`
  in feature components.

**Data in → out:**
  - Input: raw HTTP response body
  - Transforms: tagged as `{ kind: 'ok', data: T }` or `{ kind: 'error', code: string }`
  - Output: `FilteredResponse<T>` — discriminated union

**Invariants:**
  - `kind` is always present; callers must narrow before accessing `data` or `code`
  - Prior callers checking `.success === true` will produce TypeScript errors

**Notable:** Seventeen call sites across feature components still use `ApiResponse<T>`.
  They will need updating before the old type can be removed.
```

---

### Example 3: Template block change (Angular)

```diff
@@ -8,4 +8,7 @@
-<div *ngFor="let item of items">
+@for (item of items; track item.id) {
   <app-inbox-card [item]="item" />
-</div>
+}
```

```
## `src/app/features/inbox/components/inbox-list/inbox-list.component.html`

**Change summary:** Replaces `*ngFor` structural directive with the `@for` block syntax
  and adds `track item.id` for diffing. Reduces reconciliation work when the list updates.

**Symbols touched:** `@for` block (replaces `*ngFor`)

**Where in flow:** Rendered by `InboxListComponent` whenever `items$` emits a new array.

**Invariants:**
  - `item.id` must be unique across the list — `track` uses it as the identity key

**Notable:** `*ngFor` without `trackBy` was previously creating new DOM nodes on every
  emission. `track item.id` preserves existing nodes for unchanged items.
```
