# Real Life RPG — Image Generation Brief

This file is for YOU to use with an image generation tool (Midjourney, DALL·E, whatever you have access to) — not for the coding agent. It lists every image asset the theme needs, as individual ready-to-paste prompts. Generate them one at a time, save each with its exact filename into its exact folder, and the coding agent will pick them up automatically (see the companion file `coding-agent-guide.md` for how it handles missing/placeholder art in the meantime).

You do not have to generate all 23 before starting on the code — the coding agent guide is built to work with partial or zero real art and show clean placeholders instead. Generate in priority order if you're rationing prompts: the 4 base hero seasons matter most, then the 4 tier-4 ("fully developed") region images, then fill in tiers 1-3, then the 3 health overlays last (they're subtle and least noticeable).

---

## Preamble — prepend this to every single prompt below

```
Painterly digital illustration style, semi-realistic, soft painterly brushwork.
Not a photograph. Not a 3D render. Not flat vector or cartoon style. Not anime.
Single warm light source from the upper-left of the frame, low golden-hour sun,
shadows falling toward the lower-right. Color grading: sky gradient from deep
violet (#5B2A6E) at top, through magenta-red (#C4416B) and orange (#E86A3B),
to warm gold (#F4A93C) near the horizon, where relevant. No humans or people
anywhere in the image. No readable text, no logos, no watermarks, no signature.
No lens flare, no film grain, no heavy HDR glow. sRGB color.
```

---

## Group 1 — Base hero backgrounds (4 images, highest priority)

Save to: `static/img/`

All 4 share the exact same composition: wide-angle Japanese garden valley at dusk, elevated vantage point, distant mountain silhouettes across the top third, open sky above them, garden terrain filling the bottom two-thirds, a visible path or stream running from the lower-left corner toward the center. Leave the areas where the Academy, River bridge, Moon shrine, and Village would go as open, undeveloped terrain — do not draw any buildings into these base images, those come from Group 2. **Generate all 4 in the same session/seed if your tool supports it, so the composition actually matches across seasons** — this matters more than any other consistency requirement in this whole brief.

**1. `garden-hero-spring.jpg`** — 1800×1200px, 3:2 ratio
> [Preamble] + Spring version of the garden valley scene described above. Cherry blossom trees in full pink bloom scattered through the terrain. Green grass. No snow, no fallen leaves.

**2. `garden-hero-summer.jpg`** — 1800×1200px, 3:2 ratio
> [Preamble] + Summer version of the same garden valley scene, identical composition to the spring version. Dense deep-green foliage, no blossoms. Green grass. Slightly brighter, warmer sky near the horizon.

**3. `garden-hero-autumn.jpg`** — 1800×1200px, 3:2 ratio
> [Preamble] + Autumn version of the same garden valley scene, identical composition. Foliage in red, orange, and yellow tones, some trees bare. A scatter of fallen leaves along the path. Warmer amber cast overall.

**4. `garden-hero-winter.jpg`** — 1800×1200px, 3:2 ratio
> [Preamble] + Winter version of the same garden valley scene, identical composition. Bare branches, or branches with a light dusting of snow. A light dusting of snow on the path edges, no deep drifts. Sky shifted slightly cooler and bluer than the other seasons.

---

## Group 2 — Region tier overlays (16 images)

Save to: `static/img/regions/`

Every file in this group: **400×400px, PNG, transparent background**, subject centered with at least 40px of empty transparent margin on all sides. Ask your tool for a transparent background explicitly, or generate on a plain solid-color backdrop and remove it afterward (background-removal tools like remove.bg work fine here).

### Academy (INT — cyan #34C6E8)

**5. `academy-tier1.png`**
> [Preamble] + One small wooden hut with a thatched roof, isolated on transparent background. No lit lantern. 1-2 sparse small bushes nearby. A short fragment of dirt path. Muted, low-saturation colors.

**6. `academy-tier2.png`**
> [Preamble] + A small single-story wooden building, isolated on transparent background, with one paper lantern lit, glowing cyan-white. 3-4 small trees or shrubs around it. A short stone path segment leading to the door.

**7. `academy-tier3.png`**
> [Preamble] + A two-story pagoda-style building, isolated on transparent background. Two lit lanterns with cyan-tinted glow. A small stone courtyard in front. One stone lantern post. A denser line of trees behind. A small hanging fabric banner, plain, no text.

**8. `academy-tier4.png`**
> [Preamble] + A full academy complex, isolated on transparent background: a two-story pagoda plus one smaller adjoining library building connected by a covered walkway. Four or more lit lanterns with soft cyan glow halos. A stone-paved courtyard. Cherry blossom trees flanking the entrance. A small torii gate at the courtyard entrance. Warm illuminated windows.

### River (STA — water renders in cool blue/teal, not red/orange)

**9. `river-tier1.png`**
> [Preamble] + A thin trickling stream over bare rocks, isolated on transparent background. No bridge. A few sparse reeds at the bank.

**10. `river-tier2.png`**
> [Preamble] + A wider stream, isolated on transparent background. A handful of flat stepping stones crossing it. Small clusters of reed grass on both banks.

**11. `river-tier3.png`**
> [Preamble] + A flowing river with visible ripple linework on the surface, rendered in teal-blue tones, isolated on transparent background. A simple flat wooden plank bridge crosses it. A few koi fish silhouettes visible just beneath the surface.

**12. `river-tier4.png`**
> [Preamble] + A full river scene, isolated on transparent background: an arched ornate wooden bridge with simple railings in traditional Japanese garden style. Stone-lined riverbanks. Multiple visible koi fish. Small lanterns along the bank with reflections in the water. A willow tree or dense reed bed on one bank.

### Moon (FCS — deep indigo/violet environment, gold accents)

**13. `moon-tier1.png`**
> [Preamble] + A single small flat stone marker under open sky, isolated on transparent background. A faint pale moon visible above it. No structure.

**14. `moon-tier2.png`**
> [Preamble] + A small stone shrine fragment or single torii post, isolated on transparent background. Dim moonlight. One or two flat meditation stones nearby.

**15. `moon-tier3.png`**
> [Preamble] + A small shrine building with a circular "moon gate" opening, isolated on transparent background. A patch of deep indigo-violet sky directly above it. Gold-lit lanterns flanking the shrine. A small arrangement of meditation stones in front.

**16. `moon-tier4.png`**
> [Preamble] + A full moon shrine, isolated on transparent background: an elevated circular moon-gate structure on a raised stone platform, accessed by a few stone steps. Multiple gold-glowing lanterns. A pronounced indigo-violet glow in the sky directly above. Drifting cherry blossom petals in the air around it.

### Village (CHA — purple #9B7FE8)

**17. `village-tier1.png`**
> [Preamble] + A single empty market stall frame, isolated on transparent background: wooden posts and a bare roof beam, no walls, no goods, no lanterns.

**18. `village-tier2.png`**
> [Preamble] + Two small stalls or huts, isolated on transparent background. A few paper lanterns present but unlit. Minimal decoration.

**19. `village-tier3.png`**
> [Preamble] + A small cluster of 3-4 buildings resembling a teahouse district, isolated on transparent background. Purple paper lanterns, lit. Simple plain-colored fabric banners, no text.

**20. `village-tier4.png`**
> [Preamble] + A full village/festival district, isolated on transparent background: several buildings, strings of lit purple lanterns strung between them, plain fabric banners, a small gathering square with empty benches or low tables, possibly a small footbridge connecting to the rest of the garden. No people.

---

## Group 3 — Garden-health mood overlays (3 images, lowest priority)

Save to: `static/img/`. Every file in this group: **1800×1200px, PNG, semi-transparent**, same dimensions as the base hero so it layers directly on top at 1:1 scale. These are subtle translucent washes, not full scenes.

**21. `garden-health-flourishing.png`**
> A very subtle warm gold-tinted brightening wash, strongest as a soft vignette lightening near the edges, roughly 15-20% opacity overall. No scene content, just a translucent color wash. Transparent PNG.

**22. `garden-health-stable.png`**
> A fully transparent PNG, every pixel at 0% opacity. (You can generate a blank 1800×1200 transparent PNG yourself in any image editor — no need to spend a generation prompt on this one.)

**23. `garden-health-neglected.png`**
> A subtle desaturating dark vignette wash, strongest near the edges, roughly 20-25% opacity overall, with a faint cool grey-blue mist tint. No scene content, just a translucent color wash. Transparent PNG.

---

## After generating

Save every file at the exact filename and folder shown above (filenames are case-sensitive on most servers). Don't resize, crop, or rename anything after saving — the coding agent's CSS positioning is calibrated to these exact dimensions and paths. If a generated image comes back at the wrong size, resize the canvas (not just scale the image) to match the exact px dimensions listed, padding with transparency if needed, rather than stretching it.
