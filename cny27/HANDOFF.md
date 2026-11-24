# HANDOFF: CNY27 v2 (Hello Seasons / Simon) - read this first
Ray's prefs: terse, answer-first, link files, no narration. Footer on deliveries: `via Claude (Codex unreachable)` (Airaven offers no Remote Control folder; Codex-first fallback applies). Sonnet executes. Branch: `claude/practical-fermat-6wsfkj` (repo has no base branch, so no PR possible; just push).

## Goal
Redo v1 product backgrounds (~72 JPGs, 1536x1024, 3:2) for client Simon. NO 对联/couplets, no horse imagery, no third-party products. Style: crimson wall + gold clouds, lanterns, plum blossom, glossy red table, sheep (Goat 2027) props. Product labels must stay EXACT. Output -> Drive Output folder `1-QE616QL-EllGMqZCDkdVx_ZZ1GxsnFr` (subfolder `v2 2026-11-24`).
Drive folders: Raw 2 `1C4r2rQ9a-U-WFmTavBqegQH9XcUx2FRK` (has `Completed` subfolder `1Dzyx4OcCrR5RpNUhMb4LpvxPheyNG1gD` = the 72 v1 JPGs), Raw 1 `13ZMWZh81gRN6WN3Ih3EretsanQLdWEOL` (Jan 2026 ARW/PSD, not these products), Reference `14erDwe6p4Y1QJDjDLbzckiCNiXIS_A84`. List v1 IDs with Drive `search_files` `parentId = '<Completed id>'`.

## Done / approved by Ray
- Hero A 喜气羊羊 (3 bags + 4 abalone cans in front). Ray: "looks a lot better". Look APPROVED; Ray said GO for the batch. The final JPG lives only in the previous container (`cny27/out/CNY27_v2_XiQiYangYang.jpg`) and was sent to Ray in chat. If it is gone, rebuild with the recipe below (generation ids in NOTES.md; refresh via `get_ai_tool_image_result`, no new credits) or ask Ray for the copy.
- Recipe that worked (scripts in cny27/scripts, run from cny27/work):
  1. Drive download (v1 composite) -> `work/src/<title>.jpg`.
  2. Photoroom: `prepare_image_upload` -> curl PUT (headers from result; URL expires in 300s; PUT immediately; use `set +m` and `-o /dev/null` to keep output quiet) -> `complete_image_upload`.
  3. `generate_remove-background` -> download PNG (link ~5 min) -> `cutclean.py in out [x0 x1]` (keeps the centre object; an x-range crop such as 0.39 0.625 removes stock-room junk touching narrow items; the v1 stock background has a wine display at left that remove-background sometimes keeps). Needs `pip install opencv-python-headless`.
  4. `pad32.py cut.png in.jpg` (white 1536x1024, product centred) -> upload -> `generate_subject-edits` with MASTER prompt + one prop set (prompts.md). subject-edits keeps input aspect; native output 1248x832.
  5. `finish.py` -> 1536x1024 JPEG <=1MB.
  6. IMPORTANT: Photoroom re-renders products and garbles labels (ABALONE->AEALONE, THANK YOU garbled). Always run `restore.py gen layout.json out.jpg` (edge template match, pastes ORIGINAL pixels; works for single items; layout.json = [{png,x,y,w,h,smin,smax}] in composite coords; pad32.py does not write it yet, add that). For clustered small items (cans) matching failed, so cans were pasted by `place_front.py` (grade, lid squash, footprint shadow, reflection, grain, scene colour transfer); the AI never touches them.
- Ray's feedback on the pasted cans (fixed in place_front.py): looked pasted, tilted forward, too punchy -> flatten lid ellipse, ground with footprint shadow, match scene colours. Reuse that grading for anything pasted after restaging.

## To do
1. **大发羊财** hero (red window box with 雪蛤膏, 燕窝, 鸡精 jars, 天力 abalone cans; lion-dance badge; red leather handle; decor = sheep 福 felt ornaments per Simon). NOT in any Drive folder (closest v1: CNY_BCC07247 = empty red window box). Ask Ray to put the photo in Raw 2; do it last. Use prop set P1.
2. Batch the remaining v1 images. Rotate prop sets P1-P4. Raw 2 has full-res BCC07180/07183/07192 (4608x3072); prefer those over the v1 versions.
   - Ask Ray before processing these (multi-SKU / empty): DSC06385, DSC06386, DSC06388, DSC06398 (multi-SKU); DSC06393, DSC06396 (empty baskets); BCC07239, BCC07242, BCC07247, DSC02245, DSC06361, DSC06363 (empty packaging).
   - Limitation: only v1 composites exist for most SKUs; wide boxes may keep old-room traces after remove-background. Clean originals would fix this (Ray may upload). Check every cut-out via contact sheet (`sheet.py`, <=12 thumbs).
   - Chunks of ~24; keep `cny27/manifest.csv` (title, status, generationId, notes) so runs resume. Max ~6 parallel Photoroom calls. If out of credits, stop and tell Ray.
3. QA watch-outs: gibberish text on generated sheep cubes (prompt says only 福) - re-roll or drop P2; no couplets; labels exact; contact shadows; consistent set look.
4. Deliver: Drive subfolder under Output; upload JPGs with `create_file(base64Content="sha256:<hex>:<abs path>", contentMimeType="image/jpeg", disableConversionToGoogleType=true)`, plus hero, contact sheets, `v2_changelog.txt` (v1->v2 vs Simon's points). Commit `cny27/` text files (work/ and out/ are gitignored) and push.
5. Token rules: each downloaded Drive image costs ~1.6K tokens inline; download once, keep local copies, QA via contact sheets, delegate bulk looking to a Sonnet subagent.

## Simon's feedback (summary)
喜气羊羊 = 3 colour bags (beige bamboo / red / pink) with 4 天力牌 abalone cans in front (done). 大发羊财 = red window box + sheep 福 ornaments. Decor to draw on: sheep stacking cubes (羊年堆堆盒), red handled candy boxes, sheep 福 felt ornaments, mini mandarin trees (吉). Use references as inspiration, not copy.
