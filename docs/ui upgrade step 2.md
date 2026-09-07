# UI Migration Plan — Current → Desired

The desired UI should be treated as a **structural redesign**, not simply a recolor. The current implementation already has the right major information categories, but the desired version changes the **visual hierarchy, density, panel proportions, layering, and relationship between the garden artwork and the UI**.

The biggest shift is:

> **Current:** dashboard sitting around a large standalone image.
> **Desired:** dashboard integrated into a dark, atmospheric game interface where the artwork becomes the visual foundation and the UI panels feel like translucent HUD elements sitting over it.

---

## 1. Overall Layout Transformation

### Current

The current screen is essentially:

```text
┌──────────────────────────────────────────────────────────────┐
│ HEADER                                                       │
├──────────────┬───────────────────────────────┬───────────────┤
│              │                               │               │
│ ATTRIBUTES   │                               │ MISSIONS      │
│              │      LARGE HERO IMAGE         │               │
│ GARDEN       │                               │ SYSTEM JUDGE  │
│              │                               │               │
├──────────────┴───────────────┬───────────────┴───────────────┤
│ WAYFARER      │ XP FLOW      │ DISCIPLINE     │ ACTIVITY     │
└──────────────────────────────────────────────────────────────┘
```

The central image is a **contained rectangular card**. The side panels are visually separate from it.

### Desired

Move toward:

```text
┌──────────────────────────────────────────────────────────────┐
│                       TOP HUD                                │
├──────────────┬───────────────────────────────┬───────────────┤
│ ATTRIBUTES   │                               │ TODAY'S       │
│              │                               │ MISSIONS      │
│ GARDEN       │       INTEGRATED GARDEN       │               │
│ STATUS       │          WORLD SCENE          │ SYSTEM JUDGE  │
│              │                               │               │
├──────────────┼───────────────┬───────────────┼───────────────┤
│ WAYFARER     │ XP FLOW       │ DISCIPLINE    │ RECENT        │
│              │               │               │ ACTIVITY      │
├──────────────────────────────────────────────────────────────┤
│                       BOTTOM NAV                             │
└──────────────────────────────────────────────────────────────┘
```

The desired design has **more panels**, but each panel is smaller and more information-dense.

---

# 2. Background / Hero Scene — Highest Priority

This is probably the most important visual change.

### Current problem

The current garden image is a large rectangular image with:

* hard rectangular boundaries
* strong orange dominance
* little integration with the surrounding UI
* relatively bright background
* circular image markers that compete heavily with the scene
* no meaningful visual relationship between the artwork and the dashboard chrome

The image effectively behaves like a **hero card**.

### Desired behavior

The garden should feel like the **environment behind the dashboard**, rather than a card placed inside it.

Use the artwork from approximately the central **50–55% of the viewport**, but allow its edges to visually disappear beneath the surrounding HUD.

The desired image is darker and more atmospheric:

* deep violet in upper sky
* magenta/red transition
* orange around the horizon
* warm gold near the light source
* dark blue/green vegetation
* warm architectural highlights

The important change is **color balance**.

### Target color distribution

```text
TOP
Deep violet
    ↓
Violet / magenta
    ↓
Muted crimson
    ↓
Warm orange
    ↓
Golden horizon
BOTTOM
Dark blue-green / charcoal vegetation
```

Don't allow the current orange to dominate the entire image.

The desired UI has approximately **equal visual weight between cool dark tones and warm environmental tones**.

---

# 3. Color Blending — Critical

The UI should not look like:

> black panels + bright photograph underneath.

Instead, it should look like:

> **one unified dark interface with a warm garden world bleeding through it.**

### Introduce a dark atmospheric overlay

Place a translucent dark layer above the background artwork.

Something approximately in this family:

```text
rgba(5, 10, 17, 0.25–0.45)
```

The exact opacity should vary spatially.

### Edge blending

Darken the artwork toward:

* left edge
* right edge
* bottom edge
* especially behind dense UI panels

Keep the central garden brighter.

Conceptually:

```text
DARK                     DARK
██████████████████████████████
██                          ██
██      BRIGHT GARDEN       ██
██       LIGHT SOURCE       ██
██                          ██
██████████████████████████████
             DARK
```

This allows the panels to feel embedded rather than pasted on.

### Warm light blending

The upper-left light source should influence nearby UI elements subtly.

Not with a giant glow.

Instead:

* warm highlights on nearby borders
* slightly warmer panel transparency
* subtle gold reflection around garden-related controls
* muted warm gradients around the center

**Avoid:** lens flare, bloom, HDR glow, or neon orange lighting.

---

# 4. Top Header — Major Redesign

The current header is too empty and horizontally stretched.

The desired header is much more information-dense.

### Current

The level/XP information occupies a small area near the left, while the right side has a lot of unused space.

### Desired

Create a continuous HUD bar containing:

1. Menu
2. Brand
3. Streak
4. DCP
5. Level
6. XP
7. Today
8. Map
9. Journal
10. Stats
11. Profile

### Level should become the visual centerpiece

The desired level indicator is a large circular ring roughly centered within the header.

Make it substantially larger than the current tiny circle.

Structure:

```text
           27
        ┌──────┐
       ╱        ╲
      │  LEVEL   │
       ╲        ╱
        └──────┘
```

Use a subtle **pink → orange → cyan** gradient around the ring.

Do not make the ring glow excessively.

---

# 5. Header Typography

The current typography is too small in several places and has insufficient hierarchy.

Use approximately three levels:

### Primary

Large:

* `27`
* `17`
* `86`
* `12,840`

### Secondary

Medium:

* `STREAK`
* `DCP`
* `XP`
* `TODAY`
* `MISSIONS`

### Metadata

Small:

* `BEST 24`
* `DISCIPLINE`
* timestamps
* status labels

The desired UI uses **uppercase condensed-looking labels** combined with larger numeric values.

---

# 6. Left Column — Attributes

This is one area where the current structure is already good.

However, migrate it visually toward the desired design.

### Current

The attribute rows are relatively spacious and rounded.

### Desired

Make the panel:

* slightly narrower
* taller
* more compact
* more technical/HUD-like
* less like a generic web card

Each attribute row should have:

```text
ICON   INTELLIGENCE              72  ▲2
       ███████████████░░░
```

Use thin horizontal progress bars.

### Attribute colors

Preserve the semantic colors:

* INT → cyan
* STA → red/coral
* FCS → gold
* CHA → purple
* DSC → green

But **desaturate them slightly**.

They should look like colored light emitted by the interface, not solid UI paint.

---

# 7. Garden Status — Expand Its Importance

The current Garden Status panel is too small.

The desired version gives it a much stronger visual identity.

Add:

* circular growth meter
* garden illustration/icon
* growth percentage
* season
* day count

Suggested structure:

```text
GARDEN STATUS                 DAY 42

       ◯
    72% growth

       SPRING
```

The circular meter should use a **pink/cyan gradient**, matching the level ring.

This creates a deliberate visual connection between:

**Level → Garden → Progress**

---

# 8. Central Garden Scene

This needs a substantial redesign.

### Remove the current circular floating images

The current:

* River circle
* Academy circle
* Moon circle
* Village circle

feel like separate image buttons.

The desired version replaces that visual language with **small HUD location cards embedded into the scene**.

Use rectangular/angled dark translucent labels.

For example:

```text
┌─────────────────┐
│ 📖 ACADEMY      │
│ INT 72          │
└─────────────────┘
```

And:

```text
┌──────────────┐
│ ≋ RIVER      │
│ STA 81       │
└──────────────┘
```

### Important

The labels should **not obscure the artwork**.

They should feel like game-world markers.

---

# 9. Central Scene Should Be Less Saturated

This is a key difference between current and desired.

Current:

> orange image + colorful circles + colorful labels

Desired:

> muted atmospheric scene + selective UI color accents

Therefore:

* reduce overall image saturation
* preserve warm sunset highlights
* deepen shadows
* cool the vegetation
* allow UI cyan/pink/gold to stand out

Think:

**70–80% environment / 20–30% UI color.**

---

# 10. Missions Panel

The current Missions panel is extremely empty.

The desired panel is much more information-dense.

Instead of:

> No missions today.

Build a stacked task list:

```text
TODAY'S MISSIONS     4

○ [MAIN] Study Control Systems
  14:00 – 16:00               +120 XP

✓ [DAILY] Read 30 min
  07:30 – 08:00          DONE  +40 XP

○ [SIDE] Exercise (HIIT)
  18:00 – 18:45               +60 XP

○ [SIDE] Build project
  20:00 – 21:30               +80 XP
```

Each mission becomes a compact horizontal row.

Use colored category labels but keep the actual panel dark.

---

# 11. System Judge

Current:

> No pending reviews

Desired:

```text
SYSTEM JUDGE             View Log

LAST REVIEW
Study Control Systems

3 missed tasks

Validity        ███████░░ 78%
Responsibility  ██████░░░ 72%
Consistency     ████████░ 89%

Penalty                    -47 XP
```

This is important because the desired UI makes the dashboard feel like an **active game system**, rather than a static profile page.

Use thin cyan progress bars and red penalty indicators.

---

# 12. Middle / Lower Dashboard

The current lower section has good foundations but needs much more deliberate segmentation.

Desired arrangement:

### Row 1

```text
WAYFARER      XP FLOW       DISCIPLINE      RECENT ACTIVITY
```

Four visually independent panels.

### Wayfarer

Turn the current large "Seeding" heading into:

```text
WAYFARER
Current Title

12,840 / 15,600 XP
━━━━━━━━━━━━━━━━

REWARDS
Level 28   New Title   +5 Max Energy
```

### XP Flow

Make the chart more compact and polished.

Use cyan/blue bars with subtle transparency.

### Discipline

Make the circular `86 / 100` meter the focal point.

### Recent Activity

Use a compact timeline/list rather than a blank state.

---

# 13. Panel Geometry

The desired UI uses **less conventional rounded rectangles** than the current UI.

Move away from:

```css
border-radius: 16px;
```

everywhere.

Instead use:

* subtle 4–8px rounding
* clipped/angular corners
* thin borders
* occasional chamfered corners

The desired aesthetic is closer to:

**premium game HUD / futuristic RPG interface**

rather than:

**modern SaaS dashboard**.

---

# 14. Panel Backgrounds

Current panels are essentially opaque black.

Change to translucent layered surfaces.

For example conceptually:

```css
background:
  linear-gradient(
    135deg,
    rgba(18, 25, 34, 0.82),
    rgba(7, 12, 19, 0.88)
  );
```

Then add a very subtle border:

```text
rgba(150, 180, 200, 0.18)
```

The artwork should occasionally be visible through the panels.

**Do not use full transparency.**

The information must remain readable.

---

# 15. Panel Borders

The desired UI has a distinctive thin technical border.

Use:

* 1px border
* low-opacity cool gray
* occasional cyan/pink/gold accent
* subtle inner highlight

Avoid thick glowing borders.

The border should be noticeable only when looking for it.

---

# 16. Spacing System

The current UI has inconsistent spacing.

Adopt a deliberate spacing scale:

```text
4px
8px
12px
16px
24px
32px
```

### Outer margin

Approximately:

**8–12px**

rather than the larger generic card margins in the current UI.

### Between panels

Approximately:

**8–12px**

### Panel internal padding

Approximately:

**14–18px**

This creates the denser desired HUD appearance.

---

# 17. Reduce Dead Space

This is one of the largest improvements.

The current screenshot has large empty areas inside:

* Today's Missions
* System Judge
* Recent Activity
* header
* central image

The desired UI uses that space for **secondary information**.

The objective is:

> More information without making the interface feel crowded.

Achieve this with:

* smaller typography
* tighter row spacing
* dividers
* compact metadata
* progress bars
* icons
* timestamps
* status indicators

---

# 18. Bottom Navigation

The current bottom navigation is too small and visually detached.

The desired version has a strong full-width navigation bar.

Items:

```text
HOME | MISSIONS | GARDEN | STATS | JOURNAL | INVENTORY | SHOP
```

with:

* icon
* label
* active state

### Active state

Home should have a soft pink/coral illumination.

Not a solid pink rectangle.

Use a subtle:

```text
dark panel
+
pink border
+
soft pink atmospheric gradient
```

---

# 19. Iconography

The current icons are somewhat generic.

The desired interface uses icons as **part of the visual language**.

Use consistent:

* thin line icons
* simple geometric forms
* occasional filled accent icons

Avoid mixing:

* emoji
* thick icons
* thin icons
* photographic icons

The icon system should feel like one game HUD.

---

# 20. Color System

Use the desired UI's palette as the foundation.

### Base

```text
Near-black       #070B11
Deep navy        #0B1119
Panel navy       #101720
Border           muted blue-gray
```

### Accent

```text
Cyan             #16BCE8
Pink             #E85A83
Magenta          #C4416B
Gold             #F4A93C
Orange           #E86A3B
Green            #38C878
Purple           #8B5BD8
```

### Background gradient

```text
#5B2A6E
   ↓
#C4416B
   ↓
#E86A3B
   ↓
#F4A93C
```

But **do not apply this gradient to UI components globally**.

It belongs primarily to the environmental lighting.

---

# 21. Color Blending Strategy

This deserves its own implementation layer.

Think of the screen as four visual layers:

```text
LAYER 4 — HUD
icons / text / progress / controls

LAYER 3 — translucent panels
dark navy glass

LAYER 2 — atmospheric color wash
violet / magenta / orange / gold

LAYER 1 — garden artwork
```

The atmospheric wash connects Layers 1 and 3.

This prevents the UI from looking like it was cut out and placed over the image.

### Flourishing state

Your requested `garden-health-flourishing.png` should be used as an **additional subtle warm-gold lift**, not as a visible graphic.

Approximately:

**15–20% effective opacity**

with the strongest effect near the edges.

It should make the whole dashboard feel slightly more alive/warm.

### Stable state

No additional wash.

Let the base artwork and neutral HUD palette speak for themselves.

### Neglected state

Use the cool gray-blue vignette to pull saturation and brightness down.

The result should feel like:

> the same world, but emotionally colder and less maintained.

Not:

> a blue filter slapped over the entire UI.

---

# 22. Important Layering Rule

The health overlays should sit **between the garden artwork and the HUD panels**.

```text
BACKGROUND IMAGE
       ↓
DARK ATMOSPHERIC VIGNETTE
       ↓
GARDEN HEALTH WASH
       ↓
TRANSLUCENT UI PANELS
       ↓
TEXT / ICONS / CONTROLS
```

Do **not** put the health overlay above text.

Otherwise the state changes will alter readability.

---

# 23. Typography Direction

Move toward a sophisticated RPG/HUD typography system.

Use:

### Headings

Uppercase, compact:

`TODAY'S MISSIONS`

`SYSTEM JUDGE`

`GARDEN STATUS`

### Values

Large and bright:

`27`

`86`

`12,840`

### Secondary labels

Small, muted:

`DISCIPLINE`

`CURRENT TITLE`

`LAST REVIEW`

The desired screenshot has much stronger contrast between **labels and values** than the current UI.

---

# 24. Visual Hierarchy

The final hierarchy should be:

### Tier 1 — Immediate attention

1. Level
2. Garden world
3. Current missions
4. Discipline score

### Tier 2

5. Attributes
6. Garden status
7. System Judge
8. Wayfarer

### Tier 3

9. XP Flow
10. Recent Activity
11. navigation metadata

This is important because currently the large orange image dominates everything.

In the desired version, the **garden is visually dominant but operationally subordinate to the HUD**.

---

# 25. Recommended Implementation Order

Don't attempt to restyle every component simultaneously.

### Phase 1 — Structural

Change:

* overall grid
* header
* left column
* center column
* right column
* lower four-panel row
* bottom navigation

### Phase 2 — Garden

Change:

* hero dimensions
* image treatment
* location markers
* dark vignette
* atmospheric blending

### Phase 3 — Panels

Change:

* transparency
* borders
* corner geometry
* spacing
* shadows
* internal padding

### Phase 4 — Data density

Populate:

* missions
* judge metrics
* recent activity
* XP information
* rewards
* discipline metrics

### Phase 5 — Color system

Apply:

* cyan
* pink
* gold
* purple
* green
* environmental gradient

### Phase 6 — Polish

Finally tune:

* typography
* icon sizing
* micro-spacing
* progress-bar thickness
* subtle glows
* active states
* hover states
* panel blending

---

# 26. The Most Important Don'ts

Avoid these during the migration:

**Don't** simply put the current cards over the desired background.

**Don't** keep the giant orange rectangular hero treatment.

**Don't** use opaque black cards everywhere.

**Don't** make every accent neon.

**Don't** use large rounded SaaS-style cards.

**Don't** let the orange environment overpower the UI.

**Don't** add blur/glow everywhere.

**Don't** use gradients indiscriminately on buttons and panels.

**Don't** make the garden-health overlay visibly identifiable as an image.

---

# Final Target

The end result should feel like:

> **A living RPG command center embedded inside a mystical garden world.**

The current UI already has the **correct information architecture**, so the goal isn't to throw it away. The migration should preserve its underlying data/components while radically changing the **presentation layer**:

**Current → Desired**

`large hero card` → `immersive environmental background`

`opaque cards` → `translucent HUD panels`

`large empty spaces` → `compact information density`

`generic rounded UI` → `technical/angular RPG HUD`

`orange-dominant artwork` → `violet → magenta → orange → gold atmospheric palette`

`floating circular images` → `small integrated world markers`

`isolated components` → `one cohesive layered visual system`

And most importantly, **the color blending should make the garden and interface appear to belong to the same world rather than being two separate layers.**
