# Garden Hero Background Image — Prompt Spec

**File to generate:** `garden-hero.jpg`
**Save to (relative to repo root):** `app/static/assets/img/garden-hero.jpg`
**Aspect ratio / framing:** Wide, landscape hero background (approx 3:1 to 4:1). It fills the tall center column of the Garden RPG dashboard. Design it to work behind overlaid UI cards (see note at the bottom).

---

## One-line summary
A serene Japanese zen garden at dusk — cherry blossoms, a stone bridge over a pond, a wooden pagoda, and distant mountains, glowing with warm lantern light.

## Detailed scene description
- **Setting:** A peaceful Japanese zen garden at dusk (twilight, deep blues with warm orange/pink accents). Sky is a gradient from dark indigo overhead to warm amber/pink near the horizon.
- **Foreground:** A gently arched **stone footbridge** crossing a small koi pond. Still water reflects the lanterns and blossoms.
- **Mid-ground:** Cherry blossom (**sakura**) branches in soft pink framing the upper edges/third. A wooden **pagoda** rising among lightly pruned trees.
- **Background:** Layered **distant mountain** silhouettes fading into haze.
- **Lighting:** **Warm paper lantern light** — a few glowing lanterns along the path and near the bridge, creating cozy focal points and soft warm pools of light.
- **Mood:** Calm, disciplined, aspirational, "zen" — aligns with the app tagline *"Discipline today. Freedom tomorrow."*
- **Palette:** Deep navy/indigo (`#0a0e1a`, `#0f1a2e`) base; accents of sakura pink, warm lantern amber, and teal. Keep the **sides darker** and the center well-lit so UI overlays remain readable.

## Technical / stylization notes
- **Illustration / matte-painting style** (not photorealistic, not clip-art). Painterly, a little stylized, high enough resolution that it stays crisp at ~1200–1500px wide.
- **Darker overall exposure** than a daytime scene — this is the night side of a day/night toggle app, so keep it atmospheric but not gloomy.
- **No text, no watermark, no UI elements, no people close-up.**
- Optional but helpful: a hint of a moon in the upper sky (used by the "Moon" region badge in the UI).

## Composition guidance (so the UI cards sit cleanly on top)
The dashboard overlays absolutely-positioned cards on this image (a "Petals" card ~bottom-left, a "Seeds" card ~bottom-center, and three region badges upper-left/center/right). To keep those readable:
- Keep the **upper-center** and **lower-left / lower-center** areas relatively **plain / low-detail** (soft sky, water, or path) where the dark glass cards land.
- Concentrate visual interest along the **upper edges** (blossoms) and to the **upper-right / upper-left** where the badges sit — but keep enough contrast that solid dark badges still stand out.
- Avoid bright highlights directly behind the centered quote.
