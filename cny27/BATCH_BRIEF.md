# Per-SKU procedure (run from /home/user/secondshift/cny27/work). Be terse; do not narrate.
Inputs: `batch.tsv` columns name, v1FileId, props (P1-P4), rawFileId (if set, use the RAW Drive file instead; downscale first: `python3 -I -c "from PIL import Image;im=Image.open('X');im.thumbnail((2400,2400));im.convert('RGB').save('work/src/NAME.jpg',quality=93)"`).
Prompt text: `../prompts.md` (MASTER with {PROPS} replaced by the P1-P4 line). Add to MASTER: "Keep the product exactly as it is ... Product centred" is already in it; do not change it.
Source image: `src/CNY_<name>.jpg` already exists locally for v1 (do NOT re-download from Drive unless missing).
Tools: load with ToolSearch `select:mcp__Photoroom__prepare_image_upload,mcp__Photoroom__complete_image_upload,mcp__Photoroom__generate_remove-background,mcp__Photoroom__generate_subject-edits` (and Drive download tool only for raw files).

For each SKU:
1. `stat -c %s src/CNY_<name>.jpg`; call `prepare_image_upload(content_type=image/jpeg,size)`; run `../scripts/put.sh src/CNY_<name>.jpg "<uploadUrl>"` IMMEDIATELY (url expires in 300 s, expect 200); `complete_image_upload(reference)`.
2. `generate_remove-background(image=reference)` -> run `../scripts/fetch.sh "<downloadUrl>" cut/<name>.png` at once (link ~5 min).
3. `python3 ../scripts/single_prep.py <name> cut/<name>.png` (cleans leftover stock-room junk, builds gen/<name>_in.jpg + layout). For single cans/jars/narrow items pass the crop from the start: `0.39 0.625`. If the result later shows leftover wine-display/vase/orange-bowl bits of the OLD room attached to the product, rerun with an x-range crop, e.g. `... 0.39 0.625` for narrow items (can/jar), wider for boxes; otherwise note it.
4. Upload gen/<name>_in.jpg exactly like step 1 (new prepare/put/complete).
5. `generate_subject-edits(userImage1=reference, userPrompt1=<MASTER with props>)` -> `fetch.sh "<downloadUrl>" gen/<name>_raw.jpg` at once. Record generationId.
6. `python3 ../scripts/single_post.py <name> gen/<name>_raw.jpg` -> ../out/CNY27_v2_<name>.jpg ; note the restore score (if < 0.45, or the pasted product looks offset/doubled, mark FLAG).
7. Append a row to `manifest.csv` (name,status[ok|flag|fail],props,generationId,score,note). Never regenerate the same SKU twice without a reason; Photoroom spends credits.
Parallelise: you may run up to 3 SKUs concurrently (batch tool calls in one turn per step). Keep shell output quiet (`set +m`, `-o /dev/null`).

After the chunk: `python3 ../scripts/sheet.py gen/sheet_<chunkid>.jpg ../out/CNY27_v2_<n1>.jpg ...` (<=12 per sheet, 1600 px wide) and view each sheet ONCE. QA each tile against: no couplets/text overlays, product labels legible and unchanged, product grounded and centred, no leftover old-room objects, no horse/third-party items, any gibberish lettering/glyphs on props = FLAG. Report: table name|status|note only for non-ok items, plus counts. Do NOT upload to Drive, do NOT git commit/push.
