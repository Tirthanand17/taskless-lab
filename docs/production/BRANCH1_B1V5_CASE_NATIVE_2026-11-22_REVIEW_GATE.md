# Branch 1 — 22 November 2026 B1v5 case-native video recovery
**Channel:** FlowMinute Lab (`UCCcL9Q_jqVq6LJmnYUSAFZA`)  
**Status:** Three fully rendered narrated **review candidates**; **0 owner-approved, 0 YouTube uploads, 0 schedules, 0 Studio checks**.  
**Timezone:** Asia/Kolkata.

## What changed

1. Replaced the repeating terminal-panel B1v4 preview with the source-backed, case-specific B1v5 renderer in `autopilot/branch1_nov22_case_native_b1v5.py`. It uses ten distinct demonstrations for the landscape long-form (actual generated sample rows, string types, hidden spaces, exact duplicates, conflicting IDs, missing values, count reconciliation and ₹1,218 sum), and five different scenes per Short. No rotating/spinning circle or misrepresented real customer data.
2. **Replaced the near-duplicate Excel TRIM Short** (the channel had already scheduled similar content for November 13) with an original reproducible pandas merge-join cautionary example: 3 generated orders total $90; a duplicate join key produces 4 joined rows totaling $120; `validate="one_to_one"` produces `MergeError`. Docs: https://pandas.pydata.org/docs/user_guide/merging.html and https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html. This is a warning/detection feature, not an automatic repair.
3. Narration is English synthetic speech with separate voice personas for two Shorts and speech-timed external SRT. The new merge Short has an 11-cue SRT; original ID Short 10 cues; long 37 cues. Separate WebVTT tracks and an offline HTML full-watch interface prepared.
4. Technical final-file QA: H264/AAC full decoding, expected dimensions/24fps, caption timestamps, HTML review assets, title/description/hashtags/tags length checks, thumbnails, loudness parsing, audio long-silence scan, reproducible sample outputs. QA passes; **human subjective listening and rights clearance remain separate**.

## Exact locked candidate bytes

| Media candidate | Seconds | Resolution | SHA256 | Captions |
|---|---:|---|---|---:|
| `short1_B1V5_NATIVE_REVIEW_ONLY.mp4` — preserve CSV IDs | 27.167 | 1080×1920 | `391abac1f9337fad052f43ac87dcd0d9fadc9074eeddc2b84798436257b8b1eb` | 10 |
| `short2_B1V5_NATIVE_REVIEW_ONLY.mp4` — validate duplicate join keys | 35.250 | 1080×1920 | `24d5eebb0b306cfdc0d208f4a1fbb1df1851f49be167b3f871d6af6bae7dfb2e` | 11 |
| `long_B1V5_NATIVE_REVIEW_ONLY.mp4` — protect records during CSV cleaning | 113.542 | 1920×1080 | `38380ac479de5cbdc05c3691c91bc5d2e9be4d9f9c29cbd92fa182f581ef0e2f` | 37 |

**Local owner folder:** `C:\Users\Dell\Desktop\youtube con\nov22-branch1-recovery`. This is the existing authorized non-secret media workspace, not a new cloud storage owner. Non-secret original Python proof and data are stored there, along with `B1V5_RELEASE_LOCKED_REPORT.json`, `youtube_metadata_draft.json`, contact sheets, thumbnail PNGs, MP4s, SRTs and `FlowMinute_B1V5_REVIEW_START_HERE.html`. The zip is **review-only**.

## Hard gates that prevent publication now

- **Owner final media review:** Playback and visual/font legibility on phone, natural narration listening through headphones, rights verification, accurate captions and facts. The technical QA does not itself approve the media. Only owner-approved exact MP4 SHA, not a previous batch authorization, can be released.
- **Google OAuth unavailable:** Direct read-only YouTube Data API request failed refresh with `invalid_grant`, matching historical November 11 outage. Do not infer a YouTube channel inventory, upload or schedule from locally generated media.
- **Same-day slot handling:** Intended local slots 11:00 / 16:00 / 20:30 on Nov 22 are **proposals** only. Before any future authenticated write, verify the exact channel and existing uploads/schedule; never pass a timestamp that has become past, because the API can publish immediately. No duplicate upload retries after ambiguous writes.
- **Shorts custom thumbnails:** An original 9:16 cover image was prepared but not set on YouTube. Official July 2026 YouTube update initially introduced custom Shorts thumbnail upload for YPP creators and may limit account access; verify the thumbnail control is available in desktop Studio before claiming success. Use an accurate cover frame fallback when unavailable. See https://blog.youtube/news-and-events/youtube-studio-custom-thumbnail-updates/ and https://support.google.com/youtubecreatorstudio/answer/72431.
- **Studio required:** After separately approved, channel-authorized private upload and SRT/thumbnail attachment, inspect every remote video ID for title, description, hashtags, tags, audience choice, captions, checks, restrictions, privacy and exact future schedule. No such remote readback exists for Nov 22.

**Overall:** Media created 3/3; automated technical QA 3/3; editorial approval 0/3; direct YouTube API authorization not available; YouTube uploads 0/3; Studio verification 0/3. Neither the earlier B1v4 preview nor these B1v5 candidates were published in this continuation.

**No credentials, tokens, unpublished media binaries or customer data were committed to GitHub.**


## Existing API publisher integration — fail-closed proof

The owner Windows workspace also now contains three episode JSONs and three exact-SHA release manifest templates in `nov22-branch1-recovery/`:

- `fm_20261122_csv_leading_zeros_short_en.release_LOCKED.json`
- `fm_20261122_safe_csv_orders_long_en.release_LOCKED.json`
- `fm_20261122_merge_duplicate_keys_short_en.release_LOCKED.json`

All six JSONs and `stage_b1v5_publisher_manifests.py` are included in the **40-file** offline owner-review ZIP `FlowMinute_Nov22_B1V5_3Videos_REVIEW_ONLY.zip`. The zip was checked for no duplicate members, corrupt entries or approved release flags; archive SHA256 = `639adf000b02a7eb4de78fe550dc958e64406615a9f8d5a0622e0a3cc7f8930e`.

The existing `scripts/youtube_publisher.py prepare <manifest>` was actually invoked with all three templates and each **correctly refused** with `qa_approved must be explicitly true`. No approval flags were changed; `qa_approved=false`, `captions_reviewed=false`, `owner_exact_hash_approved=false` and `synthetic_media=null` are retained. The release UTC instants are the previously requested proposed slots, not YouTube schedules and must be updated before validation if they have become past. No API mutation and no browser/Studio claim.


## 2026-11-22 11:00+ IST — Owner instructed to continue scheduling; still blocked

The owner requested proceeding to the three YouTube release schedules. This authorizes continuation of the *workflow*, but does not produce the missing exact-media human-listening/rights signoff or renew a revoked OAuth credential.

- At 11:00 IST, the existing Windows Desktop Commander device `Nirala` was still connected, but **monthly remote command quota was exhausted**; the remote connector refused any new command. Do not retry/reconnect to bypass its quota.
- Previously authenticated publisher OAuth refresh returned `invalid_grant`. Google's documented recovery is secure owner sign-in and consent for new tokens, not repurposing existing Gmail cookies or storing credentials in source. Thus no direct YouTube API channel inventory, upload, captions or private schedule can currently run.
- Connected vidIQ identity had been verified for the correct channel, but the paid-credit actions needed for owner upload/schedule readback were unavailable until 2026-12-02.
- Connected Metricool brand **does not have any social network connected**, per current connector response. User connection location: `https://app.metricool.com/brands/connections?blogId=7197146`. This would be an alternate app workflow, not an authorized replacement for the requested *direct* YouTube API pipeline.
- The prior proposed `2026-11-22 11:00 IST` slot has passed. Never send the corresponding past UTC timestamp to `status.publishAt`: YouTube documentation says that may make the video immediately public. Select a fresh date/time only after approved, authenticated read-only inventory and final-media checks, with safe processing lead time.
- Do not alter exact SHA manifests or change `qa_approved=false`, `owner_exact_hash_approved=false`, `captions_reviewed=false` without genuine full review and explicit approval. Do not claim scheduling from the GitHub commit alone.

**Release status after this attempt: 0 uploads, 0 schedules, 0 YouTube Studio checks for all three November 22 candidates.**

The next actual execution requires (1) owner full-playback/rights signoff for the three exact hashes documented above; (2) secure Google YouTube publisher OAuth reauthorization to the channel; (3) an operational uploader connection/runtime (or explicitly authorized equivalent); then (4) no-duplicate owner API inventory, private upload, SRT/thumbnail attachment, future UTC scheduling, readback and Studio verification.
