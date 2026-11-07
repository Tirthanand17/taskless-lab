"""B4e3 explicit owner review artifact: 3 physical MP4 hash/provenance guards."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import autopilot.manual_rehearsal_review_export_b4e3 as review


REPO_WORKFLOW = (
    Path(__file__).resolve().parent.parent /
    ".github/workflows/flowminute-daily-cloud-foundation.yml"
)


def qa_and_three_original_mp4s(root: Path) -> dict:
    episodes=[]
    for i,(slot,_,count) in enumerate(review.SLOT_NAMES):
        name=f"flowminute_demo_{slot}"
        folder=root/name
        folder.mkdir(parents=True)
        # Synthetic test media bytes, not a claim this is a playable clip:
        # full video decode has already been checked by the upstream QA.
        data=(bytes([30+i])*(310000+i*100))
        source=folder/"EPHEMERAL_FULL_ORIGINAL_NARRATED_REHEARSAL.mp4"
        source.write_bytes(data)
        from autopilot.audio_scene_navigation_b4g1 import build_audio_scene_timeline
        duration=(57.8,241.5,57.3)[i]
        durations=[duration/count]*count
        episodes.append({
            "episode_id":name,
            "slot":slot,
            "original_full_scene_count":count,
            "all_original_voiceover_paragraphs_physically_spoken":True,
            "actual_full_ffmpeg_decode_passed":True,
            "srt_caption_baseline_inside_reserved_panel":True,
            "no_concentric_spinner_or_continuously_rotating_circle":True,
            "first_real_encoded_one_shot_checkpoint_reveal_frame_verified":True,
            "source_rights_reviewed":False,
            "news_facts_approved":False,
            "human_full_audio_visual_watch_completed":False,
            "fully_release_ready_for_youtube":False,
            "youtube_uploaded":False,
            "release_authorized":False,
            "encoded_h264_aac_sha256":sha256(data).hexdigest(),
            "total_actual_encoded_bytes":len(data),
            "real_pcm_measured_seconds":duration,
            "scene_timeline_derived_from_actual_pcm":True,
            "pcm_derived_scene_timeline_seconds":build_audio_scene_timeline(
                durations,duration,count),
        })
    return {
        "status":review.REPORT_STATUS,
        "full_daily_nonfactual_rehearsal_videos_encoded":3,
        "actually_voiced_complete_original_scene_count":17,
        "full_4_9_4_scene_voiceover_text_all_spoken":True,
        "all_three_real_h264_aac_ffmpeg_full_decodes_passed":True,
        "all_17_scenes_with_verified_distinct_one_time_reveal_pngs":True,
        "all_three_actual_mp4_first_one_shot_reveal_frames_verified":True,
        "all_pcm_timed_subtitles_fit_caption_panels":True,
        "all_caption_reading_rates_approved":False,
        "rehearsal_only_not_factual_news_or_final_review":True,
        "real_news_facts_approved":0,"rights_approvals":0,
        "human_full_watches":0,"paid_model_provider_calls":0,
        "youtube_uploads":0,"release_authorized":False,
        "episodes":episodes,
    }


class ManualReviewBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.root=Path(self.temp.name)/"ephemeral-original-qa"
        self.root.mkdir()
        self.dest=Path(self.temp.name)/"review-only"
        self.report=qa_and_three_original_mp4s(self.root)
        self.config=patch.multiple(review,ROOT=self.root,TARGET=self.dest)
        self.config.start()

    def tearDown(self):
        self.config.stop()
        self.temp.cleanup()

    def exported(self,**changes):
        data=deepcopy(self.report)
        for k,v in changes.items():
            data[k]=v
        return review.prepare_review_export(self.root,self.dest,data)

    def test_three_sha_verified_actual_original_video_copies_only(self):
        output=self.exported()
        self.assertEqual(output["status"],review.EXPORT_STATUS)
        self.assertEqual(output["artifact_retention_days"],1)
        self.assertEqual(output["original_synthetic_educational_video_files"],3)
        self.assertFalse(output["publishing_authorized"])
        self.assertFalse(output["source_news_and_publisher_article_passages_included"])
        self.assertEqual(output["youtube_releases"],0)
        self.assertEqual(output["rights_and_owner_approvals"],0)
        expected={name for _,name,_ in review.SLOT_NAMES}
        self.assertEqual(set(f.name for f in self.dest.iterdir()),
                         expected|{"REVIEW_ONLY_NO_PUBLISH.json","READ_ME_FIRST.txt",
                                   "HUMAN_REVIEW_WORKSHEET_UNFILLED.json",
                                   "OPEN_LOCAL_REVIEW_DASHBOARD.html"})
        for entry in output["videos"]:
            self.assertEqual(sha256((self.dest/entry["file"]).read_bytes()).hexdigest(),
                             entry["sha256"])
            self.assertFalse(entry["youtube_upload_authorized"])
        self.assertNotIn("publisher",json.dumps(output).lower().replace(
            "source_news_and_publisher_article_passages_included",""))
        self.assertIn("repository read access",
                      (self.dest/"READ_ME_FIRST.txt").read_text())

    def test_sha_bound_worksheet_is_unreviewed_for_all_17_scenes(self):
        result=self.exported()
        data=json.loads((self.dest/"HUMAN_REVIEW_WORKSHEET_UNFILLED.json").read_text())
        self.assertEqual(data["schema"],"B4E5_SHA_BOUND_BLANK_HUMAN_QA_WORKSHEET_V1")
        self.assertFalse(data["human_review_completed"])
        self.assertFalse(data["youtube_publish_authorized"])
        self.assertFalse(data["rights_approved"])
        self.assertFalse(data["factual_news_approved"])
        self.assertEqual([len(v["scenes"]) for v in data["videos"]],[4,9,4])
        for video,original in zip(data["videos"],result["videos"]):
            self.assertEqual(video["sha256"],original["sha256"])
            self.assertEqual(video["filename"],original["file"])
            self.assertEqual(video["overall_human_decision"],"NOT_REVIEWED")
            self.assertTrue(all(s["review_status"]=="NOT_REVIEWED" for s in video["scenes"]))
            self.assertTrue(all(status=="NOT_REVIEWED" for status in video["checks"].values()))
        self.assertEqual(sum(len(v["scenes"]) for v in data["videos"]),17)

    def test_tampered_media_never_exports_blank_worksheet(self):
        self.report["episodes"][1]["encoded_h264_aac_sha256"]="a"*64
        with self.assertRaises(review.ReviewExportRefused):
            self.exported()
        self.assertFalse(self.dest.exists())

    def test_do_not_write_any_wav_srt_source_json_or_model_weights(self):
        (self.root/"untrusted_publisher_article.html").write_text(
            "<html>TOP SECRET COPYRIGHTED ARTICLE SOURCE</html>")
        (self.root/"voice_model.bin").write_bytes(b"fake bundled model")
        result=self.exported()
        packaged=" ".join(f.name for f in self.dest.iterdir())
        self.assertNotIn("model.bin",packaged)
        self.assertNotIn("article.html",packaged)
        self.assertNotIn("WAV",packaged)
        self.assertNotIn("SRT",packaged)
        self.assertEqual(len(result["videos"]),3)

    def test_missing_copied_bytes_or_changed_digest_fail_closed(self):
        self.report["episodes"][0]["encoded_h264_aac_sha256"]="0"*64
        with self.assertRaises(review.ReviewExportRefused):
            self.exported()
        self.assertFalse(self.dest.exists())

    def test_missing_one_video_cleans_partial_three_video_package(self):
        file=self.root/self.report["episodes"][2]["episode_id"]/(
            "EPHEMERAL_FULL_ORIGINAL_NARRATED_REHEARSAL.mp4")
        file.unlink()
        with self.assertRaises(review.ReviewExportRefused):
            self.exported()
        self.assertFalse(self.dest.exists())

    def test_reordered_episode_or_wrong_scene_count_rejected(self):
        bad=deepcopy(self.report)
        bad["episodes"][1]["slot"]="short_am"
        with self.assertRaises(review.ReviewExportRefused):
            self.exported(episodes=bad["episodes"])
        self.assertFalse(self.dest.exists())

    def test_forged_human_or_source_rights_approval_rejected(self):
        for mutation in (
            lambda x:x.update(real_news_facts_approved=1),
            lambda x:x.update(rights_approvals=1),
            lambda x:x.update(youtube_uploads=1),
            lambda x:x.update(release_authorized=True),
            lambda x:x.update(all_three_real_h264_aac_ffmpeg_full_decodes_passed=False),
            lambda x:x["episodes"][1].update(news_facts_approved=True),
            lambda x:x["episodes"][1].update(human_full_audio_visual_watch_completed=True),
            lambda x:x["episodes"][1].update(fully_release_ready_for_youtube=True),
        ):
            obj=deepcopy(self.report)
            mutation(obj)
            with self.subTest(mutation=str(mutation)),self.assertRaises(
                    review.ReviewExportRefused):
                review.prepare_review_export(self.root,self.dest,obj)
            self.assertFalse(self.dest.exists())

    def test_symlinked_media_from_other_location_rejected(self):
        p=self.root/self.report["episodes"][0]["episode_id"]/(
            "EPHEMERAL_FULL_ORIGINAL_NARRATED_REHEARSAL.mp4")
        other=self.root/"other"
        p.rename(other)
        p.symlink_to(other)
        with self.assertRaises(review.ReviewExportRefused):
            self.exported()
        self.assertFalse(self.dest.exists())

    def test_any_noncanonical_root_or_target_is_rejected(self):
        with self.assertRaises(review.ReviewExportRefused):
            review.prepare_review_export(Path("/"),self.dest,self.report)
        with self.assertRaises(review.ReviewExportRefused):
            review.prepare_review_export(self.root,Path("/tmp/unrelated-folder"),self.report)

    def test_preexisting_destination_never_overwritten(self):
        self.dest.mkdir()
        (self.dest/"OWNER_PRIVATE.txt").write_text("not for deletion")
        with self.assertRaises(review.ReviewExportRefused):
            self.exported()
        self.assertTrue((self.dest/"OWNER_PRIVATE.txt").is_file())

    def test_workflow_always_disables_media_retention_for_scheduled_or_push_runs(self):
        workflow=REPO_WORKFLOW.read_text(encoding="utf8")
        self.assertIn("retain_rehearsal_review_artifact:",workflow)
        self.assertIn("type: boolean",workflow)
        self.assertIn("default: false",workflow)
        opt="github.event_name == 'workflow_dispatch' && inputs.retain_rehearsal_review_artifact == true && github.ref == 'refs/heads/main'"
        self.assertGreaterEqual(workflow.count(opt),2)
        self.assertIn("retention-days: 1",workflow)
        self.assertIn("B4E3_LOCAL_REVIEW_MEDIA_CLEANED",workflow)
        self.assertIn("if: always()",workflow)
        self.assertIn('FLOWMINUTE_ENABLE_PUBLISH: "0"',workflow)
        self.assertIn('FLOWMINUTE_DAILY_SPEND_CAP_USD: "0"',workflow)
        self.assertNotIn("contents: write",workflow)
        self.assertNotIn("actions: write",workflow)

    def test_review_export_prohibited_without_event_flag(self):
        # main() checks the manual trigger BEFORE any local file reading.
        with patch.dict(os.environ,{
            "GITHUB_EVENT_NAME":"push",
            "FLOWMINUTE_EXPLICIT_REVIEW_OPT_IN":"true",
        }):
            with patch("sys.argv",["manual_rehearsal_review_export_b4e3",
                    "--report",str(self.root/"qa.json"),
                    "--origin",str(self.root),"--output-dir",str(self.dest)]):
                with self.assertRaises(review.ReviewExportRefused):
                    review.main()
        with patch.dict(os.environ,{
            "GITHUB_EVENT_NAME":"workflow_dispatch",
            "FLOWMINUTE_EXPLICIT_REVIEW_OPT_IN":"false",
        }):
            with patch("sys.argv",["manual_rehearsal_review_export_b4e3",
                    "--report",str(self.root/"qa.json"),
                    "--origin",str(self.root),"--output-dir",str(self.dest)]):
                with self.assertRaises(review.ReviewExportRefused):
                    review.main()

    def test_review_manifest_refrains_from_approval_or_news_claims(self):
        package=self.exported()
        txt=json.dumps(package).lower()
        self.assertIn("human visual/audio review",txt)
        self.assertIn("original synthetic educational",txt)
        self.assertNotIn("youtube_uploaded",txt)
        self.assertFalse(package["publishing_authorized"])
        self.assertTrue(all(not i["all_rights_and_fact_approvals"]
                            for i in package["videos"]))


if __name__=="__main__":
    unittest.main()
