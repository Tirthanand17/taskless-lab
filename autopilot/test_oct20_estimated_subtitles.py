"""October 20 actual SRT editorial files, source-bound without fake ASR.

Checks three separate valid scripts, full 42/44/480 second caption coverage,
two-line reading bounds, saved source assets and no misleading upload claim.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import re
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.oct20_estimated_subtitles import (
    _group_words,_scene_cues,create_oct20_provisional_srt,
    export_oct20_estimated_srt,MAX_LINE_CHARS,MAX_CUE_MS,
)


RE_TIME=re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
                   r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\Z")


def millis(h,m,s,ms):
    return ((int(h)*60+int(m))*60+int(s))*1000+int(ms)


def read_cues(raw):
    result=[]
    for expected,block in enumerate(raw.strip().split("\n\n"),1):
        lines=block.splitlines()
        assert lines[0]==str(expected)
        match=RE_TIME.fullmatch(lines[1])
        assert match is not None
        values=match.groups()
        begin=millis(*values[:4])
        end=millis(*values[4:])
        assert 1<=len(lines[2:])<=2
        assert all(1<=len(l)<=MAX_LINE_CHARS for l in lines[2:])
        result.append((begin,end," ".join(lines[2:])))
    return result


class October20EditorSubtitleTests(unittest.TestCase):
    def test_builds_three_actual_nonempty_editable_srt_strings(self):
        result=create_oct20_provisional_srt()
        self.assertEqual(set(result),{
            "fm_20261020_short_en",
            "fm_20261020_short_hi",
            "fm_20261020_long_hi",
        })
        for episode,seconds in (
            ("fm_20261020_short_en",42),
            ("fm_20261020_short_hi",44),
            ("fm_20261020_long_hi",480),
        ):
            with self.subTest(episode=episode):
                item=result[episode]
                cues=read_cues(item["srt"])
                self.assertEqual(cues[0][0],0)
                self.assertEqual(cues[-1][1],seconds*1000)
                self.assertEqual(item["target_seconds"],seconds)
                self.assertEqual(item["caption_count"],len(cues))
                self.assertEqual(item["original_scene_count"],
                                 7 if seconds<60 else 11)
                self.assertEqual(
                    sum(item["cues_per_scene"]),len(cues))
                self.assertGreater(len(cues),7 if seconds<60 else 30)
                for i,(a,b,text) in enumerate(cues):
                    self.assertLess(a,b)
                    self.assertLessEqual(b-a,MAX_CUE_MS)
                    self.assertGreaterEqual(b-a,500)
                    self.assertTrue(text)
                    if i: self.assertEqual(cues[i-1][1],a)
                self.assertEqual(
                    hashlib.sha256(item["srt"].encode("utf-8")).hexdigest(),
                    item["srt_sha256"],
                )
                for denied in ("real_voice_recording_observed",
                               "spoken_word_alignment_verified",
                               "commercial_voice_rights_verified",
                               "real_audio_mux_authorized",
                               "youtube_upload_authorized",
                               "youtube_publishing_authorized"):
                    self.assertFalse(item[denied])

    def test_all_spoken_script_tokens_preserved_in_order(self):
        from autopilot.oct20_owned_voice_handoff import (
            create_oct20_voice_session_packet,
        )
        plan=create_oct20_voice_session_packet()
        by_id={x["episode_id"]:x for x in plan["lanes"]}
        for episode,entry in create_oct20_provisional_srt().items():
            subtitle=" ".join(" ".join(line.split("\n"))
                              for block in entry["srt"].strip().split("\n\n")
                              for line in block.splitlines()[2:])
            original=" ".join(x["recording_text"]
                              for x in by_id[episode]["cues"])
            with self.subTest(episode=episode):
                self.assertEqual(subtitle,original)

    def test_hindi_drafts_are_not_latin_dubs(self):
        result=create_oct20_provisional_srt()
        for ep in ("fm_20261020_short_hi","fm_20261020_long_hi"):
            caption=result[ep]["srt"]
            self.assertTrue(any("\u0900"<=c<="\u097f" for c in caption))
        self.assertFalse(any("\u0900"<=c<="\u097f" for c in
            result["fm_20261020_short_en"]["srt"]))

    def test_actual_saved_srt_files_equal_reproducible_source_generated(self):
        root=Path(__file__).resolve().parents[1]
        folder=root/"content/production-packs/srt"
        for ep,entry in create_oct20_provisional_srt().items():
            saved=folder/(ep+".draft_estimated.srt")
            with self.subTest(episode=ep):
                self.assertTrue(saved.is_file())
                self.assertEqual(saved.read_text("utf-8"),entry["srt"])

    def test_export_exactly_three_srt_drafts_refusing_preexisting_assets(self):
        with TemporaryDirectory() as temp:
            destination=Path(temp)
            receipt=export_oct20_estimated_srt(destination)
            self.assertEqual(receipt["file_count"],3)
            self.assertEqual(receipt["actual_voice_recordings_received"],0)
            self.assertFalse(receipt["real_speech_alignment_verified"])
            self.assertFalse(receipt["youtube_upload_authorized"])
            self.assertFalse(receipt["youtube_publish_authorized"])
            self.assertEqual(receipt["external_network_calls"],0)
            files=sorted(destination.glob("*.draft_estimated.srt"))
            self.assertEqual(len(files),3)
            previous={x.name:x.read_bytes() for x in files}
            with self.assertRaises(WorkflowError):
                export_oct20_estimated_srt(destination)
            self.assertEqual(previous,{x.name:x.read_bytes() for x in files})

    def test_edited_word_or_missing_phrase_would_fail_saved_source_binding(self):
        root=Path(__file__).resolve().parents[1]
        filename=root/"content/production-packs/srt/fm_20261020_short_en.draft_estimated.srt"
        actual=filename.read_text("utf-8")
        self.assertIn("Chatbots",actual)
        self.assertNotEqual(
            actual.replace("Chatbots","Fake chatbots"),
            create_oct20_provisional_srt()["fm_20261020_short_en"]["srt"],
        )

    def test_chapter_word_limits_and_unrepresentable_caption_rejected(self):
        for text in (
            "verylongword"*5+" one two three four five",
            "one two three four five\nsix",
            "one two three four five <tag>",
        ):
            with self.subTest(text=text[:20]),self.assertRaises(WorkflowError):
                _scene_cues(text,0,4)
        with self.assertRaises(WorkflowError):
            _group_words(("one","x"*40,"two"))

    def test_scene_clock_and_input_types_refused(self):
        for start,end in ((0,0),(-1,4),(4,3),(True,3),
                          (0,601),(0,1.2)):
            with self.subTest(start=start,end=end):
                with self.assertRaises(WorkflowError):
                    _scene_cues("One two three four five six",start,end)

    def test_missing_target_directory_never_created(self):
        with TemporaryDirectory() as tmp:
            missing=Path(tmp)/"not_created"
            with self.assertRaises(WorkflowError):
                export_oct20_estimated_srt(missing)
            self.assertFalse(missing.exists())

    def test_provisional_srt_does_not_mean_speech_verified_or_publishable(self):
        obj=create_oct20_provisional_srt()
        for item in obj.values():
            self.assertTrue(item["scene_timing_only_estimated"])
            self.assertFalse(item["spoken_word_alignment_verified"])
            self.assertFalse(item["real_voice_recording_observed"])
            self.assertFalse(item["youtube_upload_authorized"])
            self.assertFalse(item["youtube_publishing_authorized"])


if __name__=="__main__":
    unittest.main()
