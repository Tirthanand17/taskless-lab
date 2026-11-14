"""Adversarial original-only CLIVOX arcade pilot story + media QA tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.branch3_original_arcade_pilots import (
    CATALOG, ArcadeDenied, validate_catalog, render_size,
    draw_scene, draft_srt, sha, encode_video,
    original_review_typography, native_ass_caption_style,
)
from scripts.branch3_original_arcade_qa import (
    OriginalQARejected, check_caption_draft, validate_episode_report,
    visible_caption_safezone_qa,
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
        "srt_measured_synthesized_pcm_speech_windows":True,
        "srt_word_timing_is_estimated_not_forced_aligned":True,
        "draft_captions_burned_into_review_mp4":True,
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

    def test_audio_pcm_window_srt_is_shorter_than_beat_and_owner_still_review_required(self):
        from scripts.branch3_original_arcade_qa import srt_seconds
        for episode in sample()["episodes"]:
            regions=[]
            for beat in episode["beats"]:
                # Simulate a post-synthesis PCM interval shorter than the
                # original beat; real renderer measures exact samples.
                regions.append((beat["start_s"]+.08,beat["end_s"]-.65))
            with tempfile.TemporaryDirectory() as folder:
                p=Path(folder)/"spoken.srt"
                draft_srt(episode,p,voice_regions=regions)
                content=p.read_text("utf-8")
                result=check_caption_draft(
                    content,episode["duration_seconds"]
                )
                self.assertTrue(result["owner_must_review_speech_sync"])
                self.assertFalse(result["machine_forced_alignment_proven"])
                parts=content.strip().split("\n\n")
                cue_times=[]
                for section in parts:
                    lines=section.splitlines()
                    a,b=lines[1].split(" --> ")
                    cue_times.append((srt_seconds(a),srt_seconds(b)))
                self.assertAlmostEqual(cue_times[0][0],.08,delta=.003)
                self.assertAlmostEqual(cue_times[-1][1],
                                       episode["duration_seconds"],delta=.003)
                # In beat 1, the final draft caption no longer fills the
                # full screenplay beat; its end derives from actual voice.
                first_end=next(
                    end for start,end in reversed(cue_times)
                    if end<=episode["beats"][0]["end_s"]
                )
                self.assertLessEqual(first_end,
                                     episode["beats"][0]["end_s"]-.60+.01)

    def test_rejects_unmeasured_or_overlap_speech_regions(self):
        episode=sample()["episodes"][0]
        regions=[
            (b["start_s"]+.08,b["end_s"]-.65)
            for b in episode["beats"]
        ]
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"spoken.srt"
            for bad in (
                regions[:-1],
                [(0,999),*regions[1:]],
                [(0.4,.45),*regions[1:]],
                ["malicious",*regions[1:]],
                [[-1,5],*regions[1:]],
            ):
                with self.subTest(bad=str(bad)[:30]),self.assertRaises(
                    (ArcadeDenied,TypeError,ValueError)
                ):
                    draft_srt(episode,p,voice_regions=bad)

    def test_review_video_encoding_adds_safe_burned_caption_filter(self):
        from unittest.mock import patch
        episode=sample()["episodes"][0]
        with tempfile.TemporaryDirectory() as folder:
            work=Path(folder)
            scenes=[work/f"scene-{i:02}.png" for i in
                    range(len(episode["beats"]))]
            captions=work/"narration-timing-draft.srt"
            captions.write_text(subtitles(episode),"utf-8")
            calls=[]
            def mocked_run(args,**kwargs):
                calls.append(args)
            with patch("scripts.branch3_original_arcade_pilots.subprocess.run",
                       side_effect=mocked_run):
                encode_video(episode,scenes,work/"fictional.wav",
                             work/"review.mp4","preview",captions=captions)
            self.assertEqual(len(calls),1)
            args=calls[0]
            graph=args[args.index("-filter_complex")+1]
            self.assertIn("subtitles=filename=",graph)
            self.assertIn("MarginV=",graph)
            self.assertIn("force_style=",graph)
            self.assertIn("format=yuv420p[outv]",graph)
            self.assertNotIn("http:",graph)
            self.assertNotIn("youtube",graph.lower())
            with self.assertRaises(ArcadeDenied):
                encode_video(episode,scenes,work/"fictional.wav",
                             work/"review.mp4","preview",
                             captions=work/"missing.srt")

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

    def test_caption_virtual_units_cannot_escape_portrait_or_cover_landscape_heading(self):
        for kind in ("short","long"):
            s=native_ass_caption_style(kind)
            self.assertIn("FontName=DejaVu Sans",s)
            self.assertIn("Alignment=2",s)
            self.assertIn("Outline=",s)
            self.assertIn("MarginL=28",s)
            self.assertIn("MarginR=28",s)
            parts=dict(x.split("=",1) for x in s.split(","))
            # SRT-to-libass coordinates are 384x288 virtual units.
            # The previous pixel-based MarginV=345 pushed 9:16 text
            # completely off screen, while MarginV=172 floated landscape
            # text over the headline. Detect regression in pure tests.
            self.assertLessEqual(int(parts["MarginV"]),70)
            self.assertGreaterEqual(int(parts["MarginV"]),40)
            self.assertLessEqual(int(parts["FontSize"]),12)
            self.assertGreaterEqual(int(parts["FontSize"]),7)
            self.assertEqual(int(parts["MarginV"]),
                             50 if kind=="short" else 55)
            self.assertEqual(int(parts["FontSize"]),
                             8 if kind=="short" else 11)
        with self.assertRaises(ArcadeDenied):
            native_ass_caption_style("copyrighted")

    def test_brand_and_footer_safe_geometry_for_9_16_and_16_9(self):
        for kind in ("short","long"):
            for mode in ("preview","full"):
                w,h,_=render_size(kind,mode)
                v=original_review_typography(w,h,kind)
                with self.subTest(kind=kind,mode=mode):
                    self.assertLess(v["brand_y"]+v["brand_font_px"],
                                    v["tagline_y"])
                    self.assertLess(v["tagline_y"]+v["tagline_font_px"],
                                    round(h*.16))
                    self.assertLess(v["footer_y"]+v["footer_font_px"],
                                    v["warning_y"])
                    self.assertLess(v["warning_y"]+v["warning_font_px"],h)
                    if kind=="long":
                        self.assertLess(v["brand_font_px"],80)
                        self.assertLess(v["warning_font_px"],32)
        with self.assertRaises(ArcadeDenied):
            original_review_typography(1920,1080,"unknown")

    def test_actual_frame_visual_caption_safezone_regression_checks(self):
        try:
            from PIL import Image, ImageDraw
        except ModuleNotFoundError:
            self.skipTest("Pillow is installed in dedicated real-media CI")
        from io import BytesIO
        from types import SimpleNamespace
        from unittest.mock import patch
        ep=sample()["episodes"][0]
        srt=subtitles(ep)
        with tempfile.TemporaryDirectory() as directory:
            fake_video=Path(directory)/"fake-review.mp4"
            fake_video.write_bytes(b"synthetic-test-only"*8000)
            def simulated_frame(*,white_in_zone:bool):
                im=Image.new("RGB",(540,960),(12,19,31))
                dr=ImageDraw.Draw(im)
                if white_in_zone:
                    dr.rectangle((120,745,380,775),fill=(240,243,249))
                else:
                    dr.rectangle((120,120,380,150),fill=(240,243,249))
                buf=BytesIO()
                im.save(buf,format="PNG")
                return SimpleNamespace(stdout=buf.getvalue())
            with patch("scripts.branch3_original_arcade_qa.subprocess.run",
                       return_value=simulated_frame(white_in_zone=True)):
                d=visible_caption_safezone_qa(fake_video,srt)
                self.assertTrue(d["first_voice_cue_visible_in_safe_zone"])
                self.assertGreater(d["white_text_pixel_count_in_safe_zone"],
                                   d["minimum_required_white_caption_pixels"])
                self.assertFalse(d["caption_layout_human_approved"])
            with patch("scripts.branch3_original_arcade_qa.subprocess.run",
                       return_value=simulated_frame(white_in_zone=False)):
                with self.assertRaisesRegex(
                    OriginalQARejected,"BURNED_CAPTION_MISSING_OR_OFFSCREEN"
                ):
                    visible_caption_safezone_qa(fake_video,srt)

    def test_pillow_scene_is_new_original_procedural_art(self):
        try:
            from PIL import Image
        except ModuleNotFoundError:
            self.skipTest("Pillow only installed in the dedicated media rendering QA job")
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
