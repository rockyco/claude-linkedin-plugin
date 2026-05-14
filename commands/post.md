---
name: post
description: Compose a LinkedIn post bundle (text + images / carousel) saved to a local directory for manual review and publishing
argument-hint: "[topic or description of what to post]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# LinkedIn Post (Local Bundle)

Produce a LinkedIn-ready bundle locally. The user reviews the files and uploads manually via https://www.linkedin.com/feed/?shareActive=true. This command does not call the LinkedIn API.

Follow the `linkedin-api` skill for 2026-algorithm-optimized content rules (dwell-time hook, 1000-1300 char body, numbered carousel frameworks, no engagement bait, 3-5 hashtags, no em-dashes, no external URLs).

## Step 1 - Pick the target directory

Default: `<project-root>/docs/linkedin/`. Fall back to `<project-root>/linkedin/` if `docs/` does not exist.

If the working directory does not look like a project root or the location is ambiguous, use AskUserQuestion to confirm.

Create the directory if missing:
```bash
mkdir -p "<project>/docs/linkedin"
```

## Step 2 - Decide the format

Default by content type:
- **Technical / B2B / explanatory** -> **PDF document carousel** (5-10 slides at 1080x1080). Highest 2026 engagement.
- **Opinion, discussion, short take** -> **text-only**
- **Announcement / launch with one visual** -> **single image** (1200x627)

If unclear, ask:
```
What format? options:
  1) PDF carousel (5-10 slides, highest engagement, recommended for technical content)
  2) Multi-image carousel (2-9 PNGs, similar engagement, quicker to produce)
  3) Single image (1200x627, lowest engagement but simple)
  4) Text only (short discussion-style post)
```

## Step 3 - Draft and save the post text

Apply every rule from the `linkedin-api` skill. Summary:

- First 3 lines hook the reader (contrarian, unexpected stat, high-stakes problem, origin, or question)
- Body 1000-1300 chars, 2-3 line paragraphs with white space
- No em-dashes, no "Comment YES" / "DM me" / "link in comment" bait, no polls
- Close with an open question CTA (5+ word reply invited)
- 3-5 hashtags on the last line(s), first tag is the most relevant

Write to `<dir>/post.txt`:
```bash
# Use the Write tool (not bash heredoc) for multi-line text.
```

Validate:
```bash
wc -c <dir>/post.txt                  # aim for 1000-1300, hard cap 3000
grep -cE '—|–' <dir>/post.txt         # em-dash count should be 0
grep -ciE 'comment yes|dm me|follow for more|tag someone|like this post to' <dir>/post.txt  # banned bait
grep -cE '^#' <dir>/post.txt          # sanity
```

If any banned pattern is found, revise the text before continuing.

## Step 4 - Produce assets

### Carousel (default, highest engagement)

1. Design 5-10 slides as 1080x1080 SVGs. Each slide stands alone.
2. Narrative: cover (hook) -> problem -> numbered solution slides -> result/proof -> CTA.
3. Min font 24 pt. Consistent fonts, palette, margins across slides.
4. Name files in upload order: `01-cover.svg`, `02-*.svg`, ...
5. Render each to PNG:
   ```bash
   cd <dir>
   for svg in *.svg; do
     rsvg-convert -w 1080 -h 1080 "$svg" -o "${svg%.svg}.png"
   done
   ```
6. For a PDF Document post (best performance), combine the PNGs:
   ```bash
   cd <dir>
   # Preferred: ephemeral img2pdf via uv, no install step, no environment pollution.
   # Works even when img2pdf / ImageMagick are not installed and no venv is active.
   uv run --with img2pdf python3 -c "import img2pdf, glob; open('carousel.pdf','wb').write(img2pdf.convert(sorted(glob.glob('0*.png'))))"
   # If img2pdf is already on PATH:
   # img2pdf 01-*.png 02-*.png 03-*.png 04-*.png 05-*.png ... -o carousel.pdf
   # Last resort (often not installed, and `uv pip install` needs an active venv):
   # convert 01-*.png 02-*.png ... carousel.pdf
   ```

### Single image

Design 1200x627 SVG -> render:
```bash
rsvg-convert -w 1200 -h 627 hero.svg -o hero.png
```

### Text only

No assets. Just `post.txt`.

## Step 5 - Validate assets

```bash
for png in <dir>/*.png; do
  file "$png"   # confirm dimensions: carousel = 1080 x 1080, single = 1200 x 627
done
```

Every PNG must match the expected dimensions exactly. If a carousel PNG is not 1080x1080, re-render.

## Step 6 - Write the publishing checklist

Save `<dir>/publishing-checklist.md`:

```markdown
# Publishing Checklist

## Format
<carousel / multi-image / single-image / text-only>

## Upload steps
1. Open https://www.linkedin.com/feed/?shareActive=true
2. Pick the right compose option:
   - PDF carousel: click the document icon, upload `carousel.pdf`
   - Multi-image carousel: click the image icon, upload PNGs in order (`01-*.png`, `02-*.png`, ...)
   - Single image: image icon, upload the single PNG
   - Text: no attachment
3. Paste the full contents of `post.txt` into the composer
4. Verify the hook looks right in the preview (first 3 lines visible before "see more")
5. Visibility: Public (default) unless you want Connections-only

## Timing
- Best: Tuesday-Thursday, 8-10 AM local time
- Secondary: 12-2 PM local time
- Avoid: weekends, Friday afternoons, Monday mornings

## Golden Hour rules
- Post, then stay near the app for 60-90 minutes
- Reply to every comment within 5-10 minutes
- Each reply compounds dwell-time measurement
- If seed engagement is low after 30 minutes, send the post link to 2-3 trusted colleagues and ask them to leave a substantive (5+ word) comment

## Reach demoters (avoid post-publish)
- Do not add external URLs in the first comment - partially demoted
- Do not edit the post in the first 2 hours (re-triggers quality checks)
- Do not delete low-performing posts - they are neutral after 48 h
```

## Step 7 - Report to the user

Output a concise summary:
- Absolute path to the bundle directory
- Files produced (list)
- Post text char count (must be <= 3000, ideally 1000-1300)
- Format chosen (document / carousel / image / text)
- One-line publishing tip: "Upload via the document icon; paste `post.txt`; post between Tue-Thu 8-10 AM local"

Do not print the full post text back to the user unless they ask - they review it in the file.

## Important notes

- **Never call the LinkedIn API.** This command only writes local files.
- **Always use absolute paths** when running `rsvg-convert` or `img2pdf` outside the target directory.
- **Preserve the bundle layout** (numbered PNGs in upload order, `post.txt`, optional `carousel.pdf`, optional `publishing-checklist.md`).
- If the user explicitly asks to auto-publish, route them to `/linkedin:setup` and the legacy `linkedin-api.py` script. Warn them that 2026's Authenticity Update demotes automation patterns and that the REST API silently truncates text past ~3000 chars. The manual upload path is safer.
