# 05 · pen.dev pitfalls — symptom → cause → fix

This file only adds what the official pen.dev skill does not say, or says in a place that is easy to miss. It never restates the API: read the official files first (`mcp__pencil__read_skill()` → `SKILL.md`, `pen-schema.md`, `execute.md`; `generate.md` before any `Generate`; `guide/components.md` before building Subs). "Official" lines point to the file and section to open. Items marked *observed* were found on real canvases and are not in the official docs.

## Contents
1. Metadata is only kept at creation · 2. `Replace` on a normal layer · 3. Instances drop metadata · 4. Invalid fonts · 5. Translucent colours · 6. `Generate` is async · 7. No wrap · 8. Invisible text · 9. One scope per call · 10. Placement · 11. Failed `execute` · 12. Multiplayer · 13. `fit_content` / `fill_container` loop · 14. Screenshot discipline · 15. Variable opacity · 16. Hidden layers count as clipped · 17. Copied state frames lose frame props · 18. Transparent and dark-scoped overrides · 19. Opacity-0 empty states · 20. Insert index · 21. Copied anim ids, backdrop instances · 22. Strikethrough not stored · 23. Moving layers in a master drops overrides · 24. Stale bounds, false clip · 25. State alternatives need wrapper frames · 26. `letterSpacing` is px · 27. False sizing warnings inside instances · 28. Copies into `layout: "none"` stages

## 1. Metadata is only kept at creation *(observed)*
- **Symptom:** `Update(id, {metadata:{…}})` returns without error, but a later `Get` shows the old or no metadata; CHK `rootmeta`, `anim` or `textclass` fails on a layer you "fixed".
- **Cause:** pen.dev keeps `metadata` from the `Insert`/`Copy` that created the node; later writes are not persisted.
- **Fix:** write the final `name`, flat `metadata` and `context` in the creating `Insert` (build each root frame's tree with all metadata in one call). To correct metadata on an existing layer, recreate that layer with the §2 recipe.
- **Official:** `pen-schema.md` (`Entity.metadata`, `Entity.context`) defines the fields; persistence is not documented.

## 2. `Replace` on a normal layer throws "reading 'type'" *(observed)*
- **Symptom:** `Replace(layerId, {...})` on a layer that is *not* inside an instance fails with `Cannot read properties of undefined (reading 'type')`.
- **Cause:** `Replace` is meant for instance descendants (`instanceId/childId`). On regular frames the official guidance is to `Insert`.
- **Fix — insert at index → Move → Delete → re-point overrides:**
  1. Read where the old layer sits and which instances override it (read-only call; persist with bare assignment):
     ```js
     Get((n,c)=>{ if(n.id===OLD){ at={parent:c.parentCtx.node.id,index:c.index}; c.skipChildren() } })
     Get(n => n.type==="ref" && n.ref===COMP ? Print(n.id, n.name, JSON.stringify(Object.keys(n.descendants||{}).filter(k=>k.includes(OLD)))) : undefined)
     ```
     `COMP` is the id of the reusable root that contains `OLD` (for a section: the `P/Section/<Key>@device` frame). `n.type==="ref" && n.ref===COMP` lists every instance of that component (page frames, other sections).
  2. `newId = Insert(at.parent, {…full node with final name + metadata…})`, then `Move(newId, at.parent, at.index)` (Insert appends at the end). If the old layer had children you keep, `Move(childId, newId)` each.
  3. `Delete(OLD)`.
  4. Re-point overrides: for each instance printed in step 1, re-apply the same override values on the new id: `Update(instId + "/" + newId, {…})`. Overrides keyed by the deleted id are dead — they silently stop applying.
  5. Run the unit's checks again (CHK `anim`, `textclass`, `pages`).
- **Official:** `execute.md` §Replace and §Move; `guide/components.md` "When modifying component instance descendants" (use `Insert` when the parent is a regular frame).

## 3. Instances and overrides drop metadata → put IDs in `context` *(observed)*
- **Symptom:** a `Get(n => n.metadata?.anim …)` scan of a page returns fewer anim ids than the plan; instance layers show no `metadata`.
- **Cause:** metadata lives on the component's own nodes. A `ref` has no children of its own, so a scan without `resolveInstances: true` never reaches them. With `resolveInstances: true` every instance layer reports the master's metadata, nested instances and imported components included (*observed*). What is lost is metadata written on an instance or an override: `Update(instance + "/child", {metadata})` returns without error and is not stored.
- **Fix:** every animated layer inside a reusable root also writes its ids in `context` (`"P-HERO-02 · M-07 · …"`). Verification scans the union of `metadata.anim` and the `context` regex, with `resolveInstances: true` (CHK `anim`). Never re-add metadata per instance.
- **Official:** `guide/components.md` (instances have no children of their own; overrides via `descendants`).
- **Props too:** a label on a Sub instance (Button, FormField, SectionHeading) or in a state override cannot carry `metadata.prop`; write `props <name> <TYPE>` into the instance's `context` (02 §5a). CHK `props` counts these marks.

## 4. Invalid fonts *(observed)*
- **Symptom:** `execute` warns "Font family … is invalid"; text renders in a fallback face.
- **Cause:** not every Google family name is accepted, despite "All Google fonts are available".
- **Fix:**
  - Change the `font-*` variable value, not individual nodes.
  - Add the family to the deny list: `INVALID_FONTS` in `scripts/lint_plan.py`, so lint L13 stops every later plan that picks it.
  - Variable-font axes cannot be set; pick a family that is already condensed. Re-check Turkish glyphs (`04-ikas-constraints.md` §4).
- **Deny list, not an allow list:** any Google family is allowed until pen.dev rejects it. The DS step's first `Insert` that uses each `font-*` variable is the proof. Read that response for the warning before building further.
- **Denied so far:** `Mona Sans Condensed`, `Big Shoulders Display`.
- **Official:** `SKILL.md` §Style ("All Google fonts are available"); `execute.md` top (fix warnings in the next call).

## 5. Translucent colours need their own variable
- **Symptom:** you want `$color-text` at 60% (scrim, gradient start, overlay) and there is no property for it.
- **Cause:** colour-fill opacity exists only as the hex alpha channel; a `$variable` reference cannot take an extra alpha.
- **Fix:** define a dedicated themed colour variable whose value is `#RRGGBBAA`: `color-scrim` (`#0D0D0D99`), `color-transparent` (`#RRGGBB00`, the gradient start that matches the section background). Never hardcode the hex on the node (CHK `hardcoded`).
- **Official:** `pen-schema.md` `Color` and `Fill` ("Fill opacity can only be set via the hex alpha channel").

## 6. `Generate` is async
- **Symptom:** the screenshot right after `Generate` shows an empty frame; a second `Generate` doubles the cost.
- **Fix:** keep building; check later with a cheap `Get` (fill `url` no longer `pencil:pending-image-…`, or SVG frame `placeholder` cleared), screenshot only after it landed. Never re-generate pending work. Logos once, as a reusable `P/Sub/Logo`.
- **Official:** `generate.md` §Waiting for a result.

## 7. Flex layout never wraps
- **Symptom:** a chip row, 4-column grid or tag cloud runs off the frame.
- **Fix:** build rows explicitly (one horizontal frame per row inside a vertical frame). On `@mobile`, a horizontally scrolling rail is drawn as one row that overflows a `clip: true` container (name it `…-track`, so CHK `clip` exempts it).
- **Official:** `SKILL.md` §Flexbox Layout ("single-axis only with no item wrapping").

## 8. Text is invisible without `fill`
- **Fix:** every text node gets `fill: "$color-…"`. Put `fill` in the shared text style object you spread.
- **Official:** `SKILL.md` §Objects ("Text has no `fill` by default").

## 9. One scope per `execute` call
- **Symptom:** `ReferenceError` for a helper or id from the previous call.
- **Fix:** persist ids with bare assignment (`heroId = Insert(…)`), redefine helpers in each call, keep `Get` results out of globals. The build log records root ids so a new session can resume.
- **Official:** `execute.md` intro ("Each `execute` is executed in its own scope").

## 10. Placement: `FindEmptySpace`, `placeholder`, bands
- **Fix:** every new root frame is placed with `FindEmptySpace` (chain with `nodeId` = previous root) and created with `placeholder: true`; clear it when that unit's checks pass (CHK `placeholder`). Respect the contract's bands (DS → Sub → Section → Page → Overlay → Motion, top to bottom; desktop and mobile of one unit side by side — `02-contract.md`). Never place loose text or shapes at the document root; notes are `note` nodes beside the frame.
- **Official:** `execute.md` §FindEmptySpace; `SKILL.md` §Using placeholders and §General instructions (clean document root).

## 11. A failed `execute` must be patched, not resent
- **Fix:** all changes of a failed call are rolled back. Patch the same snippet with `edits` + the `editId` from the error; on a second failure keep patching under the same `editId` (the `find` must match the already-patched text). Resending the snippet creates divergent code and loses the edit history.
- **Official:** `execute.md` intro (error handling).

## 12. Multiplayer: the canvas changes under you
- **Fix:** before editing a unit from an earlier session, re-read it (`Get(rootId, {depth: 2})` or a visitor). If a node is missing or different, re-read instead of recreating, and never undo the user's edits. Resume from `docs/pendev/build-log.md` node ids, then verify they still exist.
- **Official:** `SKILL.md` §General instructions (collaborative multiplayer).

## 13. `fit_content` parent with only `fill_container` children
- **Symptom:** a frame collapses to 0 (or to its fallback size) and its text disappears.
- **Fix:** at least one axis must be defined from outside: give the parent a fixed or `fill_container` width, or give one child an intrinsic size. Typical case: a text with `textGrowth: "fixed-width"` + `width: "fill_container"` inside a `fit_content` card.
- **Official:** `SKILL.md` §Flexbox Layout (circular dependency, antipattern block).

## 14. Screenshot discipline
- **Rule:** one `TakeScreenshot` per finished unit (a root pair or a Sub with its states), of the smallest meaningful node, at the end of the call that finished it. Structure, sizing and clipping are checked with `Get` visitors (`ctx.bounds`, `ctx.problems`) and the CHK snippet, not with screenshots. Note the screenshot in the build-log line.
- **Official:** `execute.md` §TakeScreenshot.

## 15. `opacity: "$opacity-inactive"` renders invisible *(observed)*
- **Symptom:** a disabled button, sold-out chip or loading cart line is missing from the screenshot; CHK passes.
- **Cause:** pen.dev accepts a number variable on `opacity` but renders the node as fully transparent.
- **Fix:** write the variable's number (e.g. `0.4`) and append `opacity: $opacity-inactive` to the node's `context`; `02-contract.md` §3 allows this raw value. Find old cases with `Get(n => n.opacity === "$opacity-inactive" …)`, including `descendants` overrides on refs.

## 16. Hidden layers and hidden refs count as clipped *(observed)*
- **Symptom:** CHK `clip` warns on many children of blocks that are `enabled:false` (state-only blocks such as a bundle list or a back-in-stock form).
- **Cause:** a hidden frame with `width: "fill_container"` gets width 0; a hidden `ref` reports the master's absolute position; a hidden child taller than its fit-content parent overflows it.
- **Fix:** give hidden frames a fallback, `width: "fill_container(<column width>)"`; never hide a `ref` directly, wrap it in a hidden frame and toggle the frame in state overrides; prefer making the taller variant the default and hiding the smaller one; name intentional crops `…-mask` (e.g. a half star).

## 17. Copying a state frame to the other device drops frame-level properties *(observed)*
- **Symptom:** a new `@mobile — <state>` frame shows its children side by side, or loses the background image of the desktop state (e.g. a transparent header over a hero photo).
- **Cause:** a script that rebuilds a state frame from the desktop one copies the children and the ref overrides but not the root frame's own `layout`, `clip`, `fill`, `width` and `height`; a frame without `layout` lays its children out horizontally.
- **Fix:** copy `layout`, `clip`, `fill`, `height` and the device width with the children; after a batch, compare those keys between every `@desktop — s` / `@mobile — s` pair (`Get` the two roots, diff the keys) and screenshot one per section.

## 18. Transparent and dark-scoped overrides *(observed)*
- **Symptom:** a "transparent header" state still shows the light bar, or its icons and logo turn dark on a dark photo.
- **Cause:** the section component's root frame has its own `fill: $color-bg`, which an override on an inner frame (`header-main`) does not clear. Inside a node overridden with `theme: {mode: "dark"}`, `$color-inverse-text` resolves to the dark value.
- **Fix:** also override the ref's own `fill` with `$color-transparent`; colour icons, logo paths and text inside the dark-scoped node with `$color-text` (which is light there), never `$color-inverse-text`.

## 19. Empty states drawn as `opacity: 0` + `layoutPosition: "absolute"` *(observed)*
- **Symptom:** the `— boş` state frame still shows the filled list; the empty block never appears; CHK passes.
- **Cause:** the empty block sits in the component at `opacity: 0`, absolutely positioned, and the state override only changed a counter or hid the summary.
- **Fix:** in the state frame hide the filled list (`enabled: false`) and set the empty block to `{opacity: 1, layoutPosition: "auto"}` so it takes the list's place in the flow. Screenshot every `— boş` state at both devices.

## 20. `Insert(parent, node, index)` may append instead of inserting *(observed)*
- **Symptom:** a new wrapper (e.g. `order-meta`) lands at the end of the row although index 0 was passed.
- **Fix:** follow the `Insert` with `Move(id, parent, index)` and check the order with `Get(parent).children` in the **next** call (same-call reads can be stale).

## 21. Copied layers bring their anim ids; backdrop instances leak ids *(observed)*
- **Symptom:** the port manifest lists `anim-extra-on-canvas`, for example `QuickBuy.I-PDP-03` or `MenuOverlay.I-HDR-01`.
- **Cause:**
  - Layers copied from another unit keep the source's ids in `context`.
  - A Header instance drawn behind an overlay used to be scanned as part of the overlay. In a `resolveInstances` walk the instance comes back as a plain frame with the ref's id, so a `type === "ref"` test alone misses it.
- **Fix:**
  - Re-key copied ids to the target unit's own plan ids in the same call.
  - Leave backdrop refs untouched: CHK `anim` (`foreign`) and the manifest dump skip them by id (02 §5b).

## 22. `strikethrough` / `underline` are not stored *(observed)*
- **Symptom:** `Update(id, {strikethrough: true})` returns OK, but a later `Get` shows no such key and the compare price renders without a line. Inserting a new text with `strikethrough: true` drops it too.
- **Cause:** the schema lists the property, but the current canvas does not persist it.
- **Fix:** wrap the text in a vertical frame and draw the line as a sibling: `{type: "frame", layout: "vertical", gap: floor(h/2) - h, padding: [0, 0, h - floor(h/2) - 1, 0]}` with the text first and `{type: "rectangle", width: "fill_container", height: 1, fill: <text fill>}` second. The line follows the text width, so content overrides on instances still fit. The tool warns about circular sizing on the wrapper; the render is correct. Keep the text's visibility or opacity on the wrapper so the line hides with it.

## 23. Moving a layer inside a component master drops instance overrides *(observed)*
- **Symptom:** after `Move(textId, wrapperId)` inside a reusable component, every instance that had `descendants[textId]` (content, `enabled`, `opacity`) loses that override.
- **Fix:** before the move, list all refs whose `descendants` keys end with the moved id and save the values; after the move, write them back with `Update(refId + "/" + id, {...})` (or onto the new wrapper, for `enabled` / `opacity`). Check one instance per key with `Get(refId).descendants`.

## 24. Stale bounds report a false clip *(observed)*
- **Symptom:** right after a resize, CHK `clip` (or `ctx.problems`) reports a child overflowing its parent, but the screenshot shows it fits.
- **Cause:** bounds read in the same call as the change, or right after it, can still hold the old layout.
- **Fix:** nudge the parent's size by ±1 and back (two `Update`s), then run CHK `clip` again in the **next** call. Only a clip that survives the recheck is real.

## 25. State alternatives need wrapper frames *(observed)*
- **Symptom:** a state copied as a `ref` (`— sepette`, `— tükendi`) loses `{type, role, state}`; CHK `rootmeta` fails on it and the manifest misses the state.
- **Cause:** a `ref` cannot hold its own metadata (§3), so a bare ref root has none.
- **Fix:** every state alternative is a plain frame that carries `{type, role, state}` and holds the state `ref` as its only child. Build the wrapper in the same `Insert` as the state.

## 26. `letterSpacing` is in px *(observed)*
- **Symptom:** a heading looks crushed or spread far apart after you copy tracking from the reference CSS.
- **Cause:** pen.dev reads `letterSpacing` as px. CSS tracking often comes in `em` (`0.02em`) or %.
- **Fix:** convert before writing: `px = em × fontSize`. Keep the `em` value in the typography token's `context` for the port.

## 27. False sizing warnings inside instances *(observed)*
- **Symptom:** `execute` warns "Collapsed size" or reports a `fill_container` loop on a layer inside a `ref`, but the instance renders at the right size.
- **Cause:** the check runs on the instance tree before the master's sizes resolve.
- **Fix:** if the master shows no warning and the instance screenshot is right, ignore it. If the master warns too, fix it there (§13).

## 28. Copies into a `layout: "none"` stage need fixed widths *(observed)*
- **Symptom:** a frame copied into a motion stage (`layout: "none"`) collapses or stretches. Its text wraps per letter, or it runs off the stage.
- **Cause:** `fill_container` has no flex parent to fill inside `layout: "none"`.
- **Fix:** in the same call as the `Copy`, set a fixed `width` (and `height` when needed) on each copied root, for example the device width or the source's measured width.
