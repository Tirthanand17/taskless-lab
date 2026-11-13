"""Adversarial original-only CLIVOX arcade pilot story + media QA tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.branch3_original_arcade_pilots import (
    CATALOG, ArcadeDenied, validate_catalog, render_size,
    draw_scene, draft_srt, sha,
)
from scripts.branch3_original_arcade_qa import (
    OriginalQARejected, check_caption_draft, validate_episode_report,
)


def sample():
    data=json.loads(CATALOG.read_text("utf-8"))
    validate_catalog(data)
    return data


def manifest_for(episode):
    w,h,fps=render_size(episode["format"],"preview")
    return {
        "schema_version":1,
        "channel_id":sample()["channel_id"],
        "stage":"A4_A5_ORIGINAL_FIRST_PARTY_EDITORIAL_REVIEW_NOT_RELEASE",
        "episode_id":episode["id"],
        "format":episode["format"],
        "title":episode["title"],
        "description":episode["description"],
        "duration_seconds":episode["duration_seconds"],
        "output_width":w,"output_height":h,"fps":fps,
        "render_mode":"preview",
        "source_media_downloaded":False,
        "external_images_video_or_audio_used":False,
        "original_script_and_vector_art":True,
        "tts_voice_synthetic_not_human_recording":True,
        "srt_is_draft_not_forced_aligned":True,
        "video_file":"original-review-preview.mp4",
        "video_sha256":"a"*64,
        "video_bytes":550000,
        "audio_file":"original-tts-and-procedural-ambience.wav",
        "audio_sha256":"b"*64,
        "subtitle_file":"narration-timing-draft.srt",
        "subtitle_sha256":"c"*64,
        "scene_count":len(episode["beats"]),
        "real_voice_actor_or_music_license_verified":False,
        "human_editorial_review_completed":False,
        "owner_exact_asset_signed":False,
        "ready_to_upload":False,
        "ready_to_schedule":False,
        "ready_to_publish":False,
        "actual_external_api_calls":0
    }


def fake_probe(ep):
    w,h,fps=render_size(ep["format"],"preview")
    return {"streams":[
        {"codec_type":"video","codec_name":"h264",
         "pix_fmt":"yuv420p","width":w,"height":h,
         "avg_frame_rate":f"{fps}/1"},
        {"codec_type":"audio","codec_name":"aac",
         "sample_rate":"48000","channels":1}
    ],"format":{"duration":str(ep["duration_seconds"]),
                  "size":"550000"}}


def subtitles(ep):
    with tempfile.TemporaryDirectory() as work:
        f=Path(work)/"captions.srt"
        draft_srt(ep,f)
        return f.read_text("utf-8")


class OriginalPilotQATests(unittest.TestCase):

    def test_three_pure_first_party_original_episodes_are_source_free(self):
        catalog=sample()
        eps=validate_catalog(catalog)
        self.assertEqual(len(eps),3)
        self.assertEqual([x["format"] for x in eps],
                         ["short","short","long"])
        self.assertEqual([x["duration_seconds"] for x in eps],
                         [36,36,108])
        self.assertEqual([len(x["beats"]) for x in eps],
                         [5,5,13])
        self.assertFalse(catalog["third_party_clips_included"])
        self.assertFalse(catalog["external_images_or_audio_included"])
        self.assertFalse(catalog["upload_schedule_or_publish_authorized"])
        self.assertFalse(catalog["owner_signed_release_completed"])
        for ep in eps:
            result=check_caption_draft(subtitles(ep),ep["duration_seconds"])
            self.assertGreaterEqual(result["draft_caption_cues"],
                                    len(ep["beats"]))
            self.assertTrue(result["owner_must_review_speech_sync"])

    def test_no_publication_or_false_rights_flags_can_be_promoted(self):
        names=(
            "music_or_game_footage_included","third_party_clips_included",
            "external_images_or_audio_included",
            "human_editorial_review_completed",
            "owner_signed_release_completed",
            "upload_schedule_or_publish_authorized"
        )
        for name in names:
            doc=copy.deepcopy(sample())
            doc[name]=True
            with self.subTest(name=name),self.assertRaises(ArcadeDenied):
                validate_catalog(doc)

    def test_wrong_channel_or_unapproved_borrowed_clip_denied(self):
        for field,value in (
            ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("stage","LICENSED_GAME_FOOTAGE"),
            ("creative_origin","BORROWED_CLIP"),
            ("original_speech_generation","HUMAN_REVIEWED")
        ):
            doc=copy.deepcopy(sample());doc[field]=value
            with self.subTest(field=field),self.assertRaises(ArcadeDenied):
                validate_catalog(doc)
        doc=sample()
        doc["source_url"]="https://example.com/external_clip"
        with self.assertRaises(ArcadeDenied):
            validate_catalog(doc)

    def test_tampered_narration_timeline_art_and_licensing_denied(self):
        for key,value in (
            ("start_s",8),("end_s",99),
            ("art","gta_gameplay"),("headline",""),
            ("subheadline","https://untrusted.example/borrowed_game_clip"),
            ("spoken","https://untrusted.example/gaming"),
            ("spoken","t"*200)
        ):
            doc=copy.deepcopy(sample())
            doc["episodes"][0]["beats"][0][key]=value
            with self.subTest(key=key),self.assertRaises(ArcadeDenied):
                validate_catalog(doc)
        doc=sample()
        doc["episodes"][0]["beats"][0]["unlicensed_source"]={"foo":1}
        with self.assertRaises(ArcadeDenied):
            validate_catalog(doc)

    def test_technical_format_differs_for_short_long_and_full(self):
        self.assertEqual(render_size("short","preview"),(540,960,24))
        self.assertEqual(render_size("long","preview"),(960,540,24))
        self.assertEqual(render_size("short","full"),(1080,1920,30))
        self.assertEqual(render_size("long","full"),(1920,1080,30))
        with self.assertRaises(ArcadeDenied):
            render_size("copyrighted", "preview")

    def test_pillow_scene_is_new_original_procedural_art(self):
        ep=sample()["episodes"][0]
        with tempfile.TemporaryDirectory() as work:
            output=Path(work)/"scene.png"
            draw_scene(ep["beats"][0],ep=ep,index=0,out=output,
                       mode="preview")
            self.assertTrue(output.is_file())
            from PIL import Image
            with Image.open(output) as im:
                self.assertEqual(im.size,(540,960))
                self.assertEqual(im.mode,"RGB")
            self.assertEqual(len(sha(output)),64)

    def test_qa_positive_still_quarantines_all_content(self):
        for ep in sample()["episodes"]:
            d=validate_episode_report(
                ep,manifest_for(ep),fake_probe(ep),subtitles(ep)
            )
            self.assertTrue(d["actual_ffprobe_checks_passed"])
            self.assertTrue(d["audio_is_synthetic_narration_and_procedural_ambience"])
            self.assertFalse(d["human_editorial_video_review_completed"])
            self.assertFalse(d["youtube_upload_authorized"])
            self.assertFalse(d["youtube_schedule_authorized"])
            self.assertFalse(d["youtube_publish_authorized"])
            self.assertFalse(d["real_clivox_private_first_upload_exists"])

    def test_qa_denies_fake_human_clearance_and_release(self):
        ep=sample()["episodes"][0]
        for field,value in (
            ("source_media_downloaded",True),
            ("external_images_video_or_audio_used",True),
            ("real_voice_actor_or_music_license_verified",True),
            ("human_editorial_review_completed",True),
            ("owner_exact_asset_signed",True),
            ("ready_to_upload",True),
            ("ready_to_schedule",True),
            ("ready_to_publish",True),
            ("tts_voice_synthetic_not_human_recording",False),
            ("original_script_and_vector_art",False),
            ("actual_external_api_calls",1)
        ):
            man=manifest_for(ep)
            man[field]=value
            with self.subTest(field=field),self.assertRaises(OriginalQARejected):
                validate_episode_report(ep,man,fake_probe(ep),subtitles(ep))
        man=manifest_for(ep)
        man["channel_id"]="UCCcL9Q_jqVq6LJmnYUSAFZA"
        with self.assertRaises(OriginalQARejected):
            validate_episode_report(ep,man,fake_probe(ep),subtitles(ep))

    def test_actual_technical_qa_rejects_bad_tracks_dimensions_fps(self):
        ep=sample()["episodes"][0]
        for kind,field,value in (
            ("video","codec_name","vp9"),
            ("video","width",720),
            ("video","height",1280),
            ("video","pix_fmt","yuv444p"),
            ("video","avg_frame_rate","10/1"),
            ("audio","codec_name","mp3"),
            ("audio","sample_rate","44100"),
            ("audio","channels",0)
        ):
            result=fake_probe(ep)
            s=next(x for x in result["streams"]
                   if x["codec_type"]==kind)
            s[field]=value
            with self.subTest(field=field),self.assertRaises(OriginalQARejected):
                validate_episode_report(
                    ep,manifest_for(ep),result,subtitles(ep)
                )
        result=fake_probe(ep)
        result["format"]["duration"]="14"
        with self.assertRaises(OriginalQARejected):
            validate_episode_report(ep,manifest_for(ep),
                                    result,subtitles(ep))

    def test_srt_broken_cues_and_fake_sound_sync_denied(self):
        for bad in (
            "",
            "1\n00:00:02,000 --> 00:00:01,000\nbad",
            "1\n00:00:00,000 --> 00:00:36,000\n"+"x"*150,
            subtitles(sample()["episodes"][0]).replace(
                "00:00:36,000","00:00:35,000")
        ):
            with self.subTest(bad=bad[:40]),self.assertRaises(OriginalQARejected):
                check_caption_draft(bad,36)


if __name__=="__main__":
    unittest.main()
