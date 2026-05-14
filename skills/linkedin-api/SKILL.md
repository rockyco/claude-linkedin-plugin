---
name: linkedin-api
description: Use when composing LinkedIn posts - writes post text and carousel/image assets to a local directory for manual review and publishing. Optimized for the 2026 LinkedIn algorithm (dwell time, Golden Hour, document carousel format).
---

# LinkedIn Post Authoring (Save-Local Workflow)

This skill **does not publish to LinkedIn**. It produces a self-contained bundle (post text + images / carousel pages) in a local `linkedin/` directory. The user uploads and publishes manually at https://www.linkedin.com/feed/?shareActive=true.

Why save-only in 2026: LinkedIn's March 2026 Authenticity Update demotes automation-pattern content. The REST API also silently truncates text past ~3000 chars and adds round trips that risk shadow-truncated posts. Manual upload gives full control over preview, media order, and timing.

## Local Output Convention

Every post is a folder bundle:

```
<project>/linkedin/
  post.txt              # first-3-line hook + body + hashtags, final copy-paste-ready
  01-cover.png          # assets in upload order (1-9 images or 5-10 PDF pages)
  02-*.png
  ...
  carousel.pdf          # optional, for Document-post upload (best-performing format)
  publishing-checklist.md  # optional short checklist for the user
```

Default target directory: `<project-root>/docs/linkedin/` or `<project-root>/linkedin/`. Ask the user if the path is ambiguous.

## Algorithm Mechanics (2026)

LinkedIn's 2026 algorithm ranks by **dwell time** above everything else - the actual seconds a reader spends on the post. Likes barely register. Comments are weighted ~15x a like. Every authoring choice should maximize read-time and comment substance.

### Dwell-time tiers

| Read duration | Engagement rate | Distribution |
|---------------|-----------------|--------------|
| 0-3 s | 1.2% | Limited |
| 11-30 s | 6.1% | Extended |
| 31-60 s | 10.2% | Maximum |
| 61+ s | 15.6% | Exceptional (~2.5x wider reach) |

### Golden Hour

The first 60-90 minutes after posting determine distribution tier. Only ~5% of posts that underperform in hour one ever recover. Tactics:
- Post during working-hour windows: Tue-Thu 8-10 AM local (primary), 12-2 PM (secondary)
- Reply to every comment within the first hour - each reply compounds dwell measurement
- Seed with 2-3 trusted colleagues who leave substantive (5+ word) comments

### Demotion triggers (know them cold)

- **External URLs in the post body**: ~60% reach reduction. Do not include links unless the user accepts the penalty. "Link in first comment" callouts are also detected and demoted.
- **Engagement-bait phrases**: "Comment YES if you agree", "Like to see the PDF", "DM me for the link", "Follow for more" - NLP-flagged.
- **Polls**: dead format (~0.07% engagement in 2026).
- **AI-pattern text**: the March 2026 Authenticity Update flags em-dash-heavy prose, "It's not X, it's Y" templates, generic LinkedIn-speak ("In today's fast-paced world..."), and other boilerplate.
- **Bro-etry**: single-sentence paragraphs one after another with no substance.

### Comment mechanics

Comments are 15x a like in the ranking model, but LinkedIn weighs comment quality:
- Short "Nice!" / emoji-only comments are filtered as low quality
- Substantive comments (5+ words, especially questions, disagreements, anecdotes) count
- Every author reply roughly doubles the comment's signal value
- A comment that triggers a multi-reply thread is the strongest signal on the platform

## Format Performance (2026)

| Format | Avg engagement | Notes |
|--------|---------------|-------|
| LinkedIn Live video | 29.6% | Premium, rare, highest reach |
| **PDF / Document carousel** | **6.6%** | **278% above video, 596% above text.** Default recommendation for technical / B2B |
| Multi-image carousel | ~6.6% | Similar weight to PDF but less searchable |
| Native video (< 90 s, vertical) | 5.6% | Growing 2x faster than other formats. Hardcoded captions required |
| Text post | 2-4% | Baseline |
| Single image | Below text | Lowest of the standard formats |

**Default for technical content: PDF document carousel, 5-10 slides at 1080×1080.** Every swipe is tracked as a dwell-time increment, multi-slide interaction is measured, and numbered frameworks ("5 lessons...", "3 mistakes...") add a further 20-30% to dwell.

## Post Types

- **Text only** - quick takes, discussion prompts. Baseline reach.
- **Single image** - when one visual carries the whole point. Lowest-engagement standard format.
- **Multi-image / PDF carousel** - the workhorse. 5-10 slides at 1080×1080.
- **Native video** - under 90 seconds, vertical, hardcoded captions.
- **Article** - long-form publisher tool (outside this skill).

## Asset Specifications (2026)

| Asset | Dimensions | Aspect | Max size |
|-------|-----------|--------|----------|
| Single image | 1200×627 | 1.91:1 | 5 MB |
| Multi-image carousel | 1080×1080 each | 1:1 | 10 MB each |
| PDF document carousel | 1080×1080 per page | 1:1 | 100 MB, up to 300 pages |
| Slide deck (16:9 alternative) | 1920×1080 | 16:9 | 100 MB |
| Banner | 1128×191 | 6:1 | 4 MB |
| Video (landscape) | 1920×1080 | 16:9 | 5 GB, 3 s to 10 min |
| Video (vertical) | 1080×1920 | 9:16 | 5 GB, 3 s to 10 min |

### Carousel design rules

- **1080×1080 square is the default**. LinkedIn does not render portrait carousel aspect ratios correctly.
- **5-10 slides** is the sweet spot - more hurts completion rate.
- **Cover slide is self-contained**: topic + hook promise + swipe cue.
- **Every slide stands alone** - a reader may land mid-deck via a share. Do not rely on "as shown on the previous slide".
- **Minimum in-slide text: 24 pt** - LinkedIn compresses PDFs aggressively, smaller text renders illegibly.
- **Numbered frameworks** outperform unnumbered (+ ~25% dwell).
- **Consistent style across all slides** - same fonts, palette, margins, card styling.

### Carousel narrative arc

1. **Slide 1 (cover)**: hook + promise + swipe cue
2. **Slide 2**: problem / agitation - why the reader cares
3. **Slides 3-N-2**: solution - numbered framework, one insight per slide
4. **Slide N-1**: result / proof / data payoff
5. **Slide N**: punchline + open question CTA

### Diagram visual style (IMPORTANT)

Default to **clean technical-diagram style**, not marketing-social style. Carousel slides for technical audiences (engineers, researchers, hardware / ML / infra professionals) read as credible when they look like figures from a research paper or trade magazine, not like influencer promo graphics.

**Prefer this style** (proven to work for technical B2B):

- **Light pastel gradient backgrounds** (e.g., `#eff6ff → #dbeafe` for blue cards, `#f0fdf4 → #dcfce7` for green, `#fefce8 → #fef9c3` for yellow). White canvas background.
- **Rounded cards** (`rx="14"` to `rx="16"`) with thin 2-2.5 px colored strokes that echo the card's accent hue.
- **Helvetica Neue / Arial** sans-serif. No custom display fonts.
- **Information-dense layout**: body labels around 17-22 px, headings 26-36 px, page counter and captions 16-20 px.
- **Right-side info chips** on layered cards (like era markers, year badges). White-filled chips with same stroke color as the parent card.
- **Muted accent palette**: slate `#334155`, blue `#1971c2`, green `#059669`, amber `#ca8a04`, red `#dc2626`. Dark text colors matching stroke (`#1971c2` heading on blue card, `#065f46` on green, `#854d0e` on amber).
- **Small label ribbons** in dark slate (`#1e293b`) with white text for slot markers like `LESSON 1`, `PROOF`, `TAKEAWAY`.
- **Subtle italic subtitle** in `#64748b` below the bold title.
- **Page counter** in `#94a3b8` at bottom-right: `3 / 7`.

**Avoid this style** (looks AI-marketing, lowers perceived credibility for technical readers):

- Bold violet/magenta gradients (`#a855f7 → #3b82f6`) as dominant color
- Oversized display headlines (>60 px) that crowd out content
- Gradient-filled "LESSON" badges with glow effects
- Gradient title text (title text filled with a `<linearGradient>`)
- Decorative circuit-dot / hexagon backgrounds that look AI-generated
- Heavy drop shadows or glow halos
- Fewer than 3 information blocks per slide (too much negative space = looks padded)

**Minimum in-slide font is still 24 pt** — but a dense technical slide with 17-22 pt body text inside 60+ px card sections reads well because the card itself acts as visual structure. A slide with one giant 80 pt headline and nothing else reads as "AI slop" even though it passes the minimum-font check.

**Reference / reuse rule:** if the same article has a Chinese WeChat version with clean technical diagrams, create the English carousel by re-authoring those diagrams at 1080×1080 in English — preserve the same visual language across language versions. Do not redesign from scratch; the brand / credibility signal is the style consistency.

## Post Text Best Practices

### Length & structure
- **Hard cap**: 3000 characters (past this the API silently truncates; manual paste just cuts off)
- **Optimal for dwell time**: 1000-1300 characters
- **Paragraphs**: 2-3 lines max. Longer is fine if broken by white space between short paragraphs
- **White space** between paragraphs drives ~40% more dwell time vs wall-of-text

### The hook (first 3 lines, ~210 chars desktop / ~49 mobile)

LinkedIn truncates on mobile at about 49 characters and on desktop at 2-3 lines. The reader has to click "see more" to trigger dwell-time accumulation. Without that click the post dies.

Proven hook patterns:

| Pattern | Template | Example |
|---------|----------|---------|
| Contrarian | "X is not the problem. Y is." | "Hand-writing Verilog isn't the bottleneck. Architecture iteration is." |
| Unexpected stat | "<specific number> <outcome>." | "28 DSP blocks instead of 52. A 46% saving nobody on our team predicted." |
| High-stakes problem | "If you <A>, you're about to hit <B>." | "If your pipeline breaks every time you change N, you are burning weeks per project." |
| Origin / vulnerable | "Six months ago I <struggle>. Here's what changed." | "Six months ago I was hand-writing 2000 lines of Verilog per project. Today AI writes them. Here is the tradeoff." |
| Question | "Why does <surprising premise>?" | "Why does AI write better pipelined hardware than most junior engineers?" |

### Body structure (after the hook)

- **Context paragraph** - 1-2 sentences: why the topic matters now
- **Value section** - bullets, numbered list, or short before/after contrast
- **Takeaway** - one specific lesson the reader can apply today
- **CTA question** - open, short, personal - see CTAs section

### Narrative / story-telling structure (default for experience-driven posts)

The flat structure above is fine for a pure reference post, but a **narrative arc reads as
more interesting and earns more dwell time** whenever the post is about something you *did*
(an experiment, a debug session, a build, a mistake). Prefer it by default for those.

Arc that works (proven this session - a bulleted feature-dump rewritten as narrative was
markedly more readable):

1. **Setup** - first person, concrete stakes. "I handed an AI a real timing failure and watched it work."
2. **Rising tension** - what was tried and what went wrong. Keep the failures in; they are the interesting part.
3. **The turn** - the single pivot. One sentence, set off by white space, often the emotional core ("Here is the part people assume an AI cannot do: it backed out.").
4. **Resolution** - what actually worked, with the specific numbers kept intact for credibility.
5. **Reflection + CTA** - what it means, then the open question. Returning the CTA to the hook's phrasing closes the loop.

Story-telling craft rules:
- **Show the struggle, not just the win.** Dead ends, reverts, and wrong assumptions are what makes it a story instead of a brochure. A post that is all wins reads as marketing.
- **First person, past tense, specific.** "It came back at -0.642 ns. Worse." beats "results were suboptimal."
- **One idea per paragraph, 2-3 lines, white space between.** The arc should be skimmable on mobile.
- **Keep every concrete number.** Narrative makes it readable; the numbers make it credible. Do not trade one for the other.
- **Narrative posts run longer** - 1500-2200 chars is normal and acceptable here even though the pure-reference optimum is 1000-1300. The dwell time the story earns outweighs the length. Still respect the 3000 hard cap.
- **Genuine arc, not story scaffolding.** This is the opposite of the flagged anti-pattern. Do NOT open with "Let me share a story...", "Here's the thing:", or "Picture this:". Just start *in* the story with a concrete first action. The structure carries it; announcing it does not.

### Formatting rules

- **Max 2-3 emojis** per post, and only where they replace punctuation or act as bullet markers
- **Unicode bullets** (•, →, ▸) render cleanly; native markdown does not
- **No em-dashes** (one of the strongest AI-detection signals in 2026). Use colon, parenthesis, or a period.
- **No all-caps shouting**
- **No repeated ellipses...** (pattern-flagged)
- **Keep the first sentence punchy** - every character before the "see more" cut is valuable

### CTAs that generate substantive comments

Comments are worth 15x a like. Always close with an open question that invites a 5+ word reply.

| Good CTA | Why |
|----------|-----|
| "What's the part of <X> you'd most want to automate?" | Personal, open |
| "Curious how others handle <problem>." | Invites shared experience |
| "Disagree? I want to hear the counter-case." | Invites contrarian replies (strongest signal) |
| "Which of these <N> surprised you?" | Forces a choice, easy to reply to |
| "What would you add to this list?" | Invites extension, low-effort for reader |

**Never use** (NLP-flagged, demotes the post):
- "Comment YES if you agree"
- "Drop a 🔥 below"
- "Like this post to see the PDF"
- "DM me and I'll send the link"
- "Follow for more"
- "Tag someone who needs this"

### Hashtag strategy

- **3-5 hashtags** max. More is spam-pattern and demoted.
- Place at the very end of the post, each on its own line is fine or all on one line
- First hashtag carries the most weight - make it the most relevant
- Mix tiers: 1-2 broad (#AI, #FPGA) + 2-3 niche (#HardwareDesign, #Verilog, #RFSoC)

## Post Templates

### Template A - Technical insight (carousel, recommended)

```
<Hook: contrarian or specific-number, 1 line>

<Context: 1-2 lines on why this matters now>

<Value payoff, 2-4 lines, with specific numbers>

<Takeaway: 1 line, what the reader should do differently>

<CTA question>

#Tag1 #Tag2 #Tag3 #Tag4
```

Target length: 900-1300 chars. Pair with 5-10 slides.

### Template B - Carousel slide sequence

```
Slide 1 (cover): 3-line headline + promise + "swipe →"
Slide 2: Problem framing / agitation
Slide 3-N-2: Solution, one insight per slide, numbered
Slide N-1: Result / proof - charts, stats, screenshots
Slide N: Punchline recap + open-question CTA (same as post body)
```

### Template C - Short discussion post (text only)

```
<Hook: question or contrarian claim, 1-2 lines>

<Context: 2-3 lines>

<Observation or specific example>

<CTA question>

#Tag1 #Tag2 #Tag3
```

Target length: 500-900 chars.

## Posting cadence & timing (user-side)

Include these in the publishing checklist you give the user:

- **Frequency**: 3-5 posts / week. Less than 2/week means the algorithm can't categorize your expertise; more than 5 splits engagement across posts
- **Best windows** (local time): Tue-Thu 8-10 AM (primary peak), 12-2 PM (secondary)
- **Avoid**: weekends, Friday afternoons, Monday mornings
- **Spacing**: 18-24 hours between posts, otherwise the earlier one cannibalizes the later one
- **First hour**: stay near the app, reply to every comment within 5-10 minutes

## Authoring workflow

When this skill is invoked to produce a post:

1. **Identify target directory**. Default `<project>/docs/linkedin/`. Create if missing.
2. **Decide format** (ask user if ambiguous):
   - Technical / B2B / explanatory -> PDF document carousel (default)
   - Opinion / discussion / short take -> text-only
   - Announcement / launch -> single image or short carousel
3. **Produce assets**:
   - Carousel: 1080×1080 SVGs, render via `rsvg-convert -w 1080 -h 1080 page.svg -o page.png`
   - Single image: 1200×627
   - Follow asset specs above exactly
4. **Optionally combine carousel PNGs into PDF** for Document-post upload:
   ```bash
   # Preferred: ephemeral img2pdf via uv (no install, works with no venv active).
   uv run --with img2pdf python3 -c "import img2pdf, glob; open('carousel.pdf','wb').write(img2pdf.convert(sorted(glob.glob('0*.png'))))"
   # If already on PATH: img2pdf 01-*.png 02-*.png ... -o carousel.pdf
   # Do NOT rely on bare `img2pdf`, `convert`, or `uv pip install img2pdf` -- in a
   # clean environment all three commonly fail (not installed / no active venv).
   ```
5. **Write `post.txt`**:
   - First 3 lines must hook
   - Optimal 1000-1300 chars
   - 3-5 hashtags at the end
   - No em-dashes, no banned CTA phrases, no external URLs
6. **Validate**:
   - `wc -c post.txt` under 3000, aim for 1000-1300
   - Image dimensions match spec
   - Hashtag count 3-5
   - Grep for banned strings: em-dash, "Comment YES", "DM me", "link in comment", "follow for more"
7. **Optionally write `publishing-checklist.md`** with the manual steps:
   - Which compose option to pick (text / image / document)
   - Upload order
   - Best posting time
   - Golden-hour reply reminder
8. **Report** the full bundle path to the user. Do not attempt to publish.

## Anti-patterns (never produce)

- External URLs in post body (60% reach penalty)
- "Link in first comment" cues
- Any engagement-bait phrase from the CTA anti-patterns list
- Polls
- Single long paragraph ("wall of text")
- Single-sentence-per-paragraph bro-etry
- Em-dash prose (also avoid em-dashes inside diagram text — user convention is hyphen or colon)
- More than 5 hashtags
- Portrait or 16:9 carousel when user didn't specify - default is 1:1 square
- AI-pattern openings: "In today's fast-paced world...", "Let me share a story...", "It's not X, it's Y.", "Here's the thing:"
- Auto-publishing via the REST API (truncation risk, authenticity penalty)
- Marketing-gradient carousel slides (bold violet → blue backgrounds, gradient-filled display headlines, glowing "LESSON N" badges) for technical audiences — see "Diagram visual style" above

## Optional: Legacy API Reference

Scripts at `${CLAUDE_PLUGIN_ROOT}/scripts/` are retained for users who explicitly want programmatic publishing:
- `oauth-server.py` - OAuth 2.0 flow
- `linkedin-api.py` - publish, upload, verify

**The default workflow no longer uses these.** If a user explicitly requests auto-publish, warn them:
- LinkedIn's 2026 Authenticity Update demotes automation-pattern posts
- The REST API silently truncates `commentary` past ~3000 chars (no error returned)
- Text truncation requires Playwright-based edit-in-browser fix
- Manual upload is safer and often reaches more people

If they still want it, see `scripts/linkedin-api.py --help` and the published-post truncation fix flow described in `commands/post.md` (advanced section).
