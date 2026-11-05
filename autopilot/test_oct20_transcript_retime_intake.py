"""Current Oct20 transcript retime: true-source SRT, FAKE word timestamps.

Tests exercise 3 independent English/Hindi script/SRTs. No genuine audio,
ASR, narrator identity, legal voice rights, cloud actions or YouTube release.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.oct20_transcript_retime_intake import (
    ALLOWED,Oct20Word,Oct20TranscriptCandidate,current_oct20_cue_binding,
    inspect_oct20_untrusted_word_timing,summarize_oct20_word_timing_batch,
)


def synthetic_claim(episode:str,*,even_across_full_length:bool=False):
    source=current_oct20_cue_binding(episode)
    tokens=source["expected_words"]
    if even_across_full_length:
        total=source["duration_ms"]
        words=tuple(
            Oct20Word(text,int(total*i/len(tokens)),
                      int(total*(i+1)/len(tokens)))
            for i,(_,_,text,_) in enumerate(tokens)
        )
    else:
        counts={}
        for a,b,word,ordinal in tokens:
            counts[ordinal]=counts.get(ordinal,0)+1
        indices={}
        words=[]
        for a,b,word,ordinal in tokens:
            i=indices.get(ordinal,0)
            count=counts[ordinal]
            start=a+((b-a)*i)//count
            end=a+((b-a)*(i+1))//count
            words.append(Oct20Word(word,start,end))
            indices[ordinal]=i+1
        words=tuple(words)
    return Oct20TranscriptCandidate(
        episode_id=episode,
        language=source["language"],
        claimed_method="synthetic_test",
        claimed_wav_sha256="a"*64,
        exact_script_sha256=source["script_sha256"],
        exact_estimated_srt_sha256=source["draft_srt_sha256"],
        words=words,
    )


class Oct20UntrustedWordTimeTests(unittest.TestCase):
    def test_binding_reads_exactly_three_original_srt_and_script_hashes(self):
        for episode,(lang,total) in ALLOWED.items():
            with self.subTest(episode=episode):
                result=current_oct20_cue_binding(episode)
                self.assertEqual(result["language"],lang)
                self.assertEqual(result["duration_ms"],total)
                self.assertEqual(result["caption_count"],
                                 110 if total==480000 else
                                 14 if lang=="hi" else 13)
                self.assertEqual(result["script_scene_count"],
                                 11 if total==480000 else 7)
                self.assertTrue(len(result["expected_words"])>75)
                self.assertTrue(all(len(w[2])>0 for w in result["expected_words"]))
                self.assertEqual(len(result["script_sha256"]),64)
                self.assertEqual(len(result["draft_srt_sha256"]),64)

    def test_three_exact_self_asserted_timed_transcripts_shape_pass_only(self):
        packets=[]
        for ep in ALLOWED:
            outcome=inspect_oct20_untrusted_word_timing(synthetic_claim(ep))
            packets.append(outcome)
            with self.subTest(ep=ep):
                self.assertEqual(
                    outcome["status"],"OCT20_CLAIMED_WORD_TIMING_EDITOR_REVIEW_ONLY")
                self.assertTrue(outcome["exact_script_and_srt_text_shape_matched"])
                self.assertEqual(
                    outcome["largest_outside_estimated_caption_window_ms"],0)
                self.assertFalse(outcome["retime_editor_attention_required"])
                for blocked in (
                    "source_wav_technical_evidence_verified",
                    "word_timings_observed_from_actual_audio",
                    "ASR_provenance_authenticated",
                    "natural_human_speech_verified",
                    "commercial_voice_rights_authenticated",
                    "speaker_consent_authenticated",
                    "spoken_language_pronunciation_verified",
                    "actual_audio_caption_alignment_verified",
                    "ready_for_mux","youtube_upload_authorized",
                    "youtube_publish_authorized",
                ):
                    self.assertFalse(outcome[blocked])
        combined=summarize_oct20_word_timing_batch(tuple(packets))
        self.assertTrue(combined["three_language_episodes_matched"])
        self.assertFalse(combined["real_speech_transcribed_or_recognized"])
        self.assertFalse(combined["real_word_to_audio_alignment_verified"])
        self.assertFalse(combined["youtube_upload_authorized"])
        self.assertEqual(combined["external_network_calls"],0)

    def test_timestamps_retimed_from_estimated_cues_need_editor_attention(self):
        ep="fm_20261020_short_en"
        outcome=inspect_oct20_untrusted_word_timing(
            synthetic_claim(ep,even_across_full_length=True))
        self.assertTrue(outcome["retime_editor_attention_required"])
        self.assertGreater(outcome["largest_outside_estimated_caption_window_ms"],900)
        self.assertFalse(outcome["word_timings_observed_from_actual_audio"])

    def test_devanagari_script_normalization_is_unicode_preserving(self):
        ep="fm_20261020_short_hi"
        candidate=synthetic_claim(ep)
        first=candidate.words[0]
        # Uppercase Latin component is case-insensitive, but original
        # Devanagari combining marks and lexical content are still verified.
        assert first.text=="AI"
        updated=(replace(first,text="ai"),*candidate.words[1:])
        outcome=inspect_oct20_untrusted_word_timing(
            replace(candidate,words=updated))
        self.assertFalse(outcome["actual_audio_caption_alignment_verified"])

    def test_wrong_episode_or_old_csv_script_not_accepted(self):
        original=synthetic_claim("fm_20261020_short_en")
        for episode in ("csv_tutorial_short_en","other","",None):
            with self.subTest(episode=str(episode)):
                with self.assertRaises(WorkflowError):
                    inspect_oct20_untrusted_word_timing(
                        replace(original,episode_id=episode))

    def test_wrong_draft_hash_wav_digest_or_language_denied(self):
        original=synthetic_claim("fm_20261020_short_en")
        changes=(
            {"exact_script_sha256":"a"*64},
            {"exact_estimated_srt_sha256":"a"*64},
            {"claimed_wav_sha256":"bad"},
            {"claimed_wav_sha256":"A"*64},
            {"language":"hi"},
            {"claimed_method":"approved_by_model"},
            {"claimed_method":None},
        )
        for kwargs in changes:
            with self.subTest(mod=kwargs),self.assertRaises(WorkflowError):
                inspect_oct20_untrusted_word_timing(replace(original,**kwargs))

    def test_wrong_word_insertion_deletion_or_word_order_denied(self):
        original=synthetic_claim("fm_20261020_short_en")
        words=list(original.words)
        mutations=(tuple(words[:-1]),
                   tuple((*words,words[-1])),
                   tuple((words[1],words[0],*words[2:])),
                   tuple((replace(words[0],text="UNAUTHENTICATED"),*words[1:])))
        for data in mutations:
            with self.subTest(n=len(data)),self.assertRaises(WorkflowError):
                inspect_oct20_untrusted_word_timing(
                    replace(original,words=data))

    def test_overlap_reverse_or_out_of_bounds_timestamps_denied(self):
        candidate=synthetic_claim("fm_20261020_short_hi")
        for word in (
            replace(candidate.words[3],start_ms=-1),
            replace(candidate.words[3],start_ms=candidate.words[3].end_ms),
            replace(candidate.words[3],start_ms=candidate.words[2].start_ms),
            replace(candidate.words[3],end_ms=44001),
            replace(candidate.words[3],start_ms=True),
            replace(candidate.words[3],end_ms=float(candidate.words[3].end_ms)),
        ):
            changed=list(candidate.words)
            changed[3]=word
            with self.subTest(words=str(word)[:60]),self.assertRaises(WorkflowError):
                inspect_oct20_untrusted_word_timing(
                    replace(candidate,words=tuple(changed)))

    def test_srt_tamper_detected_against_generated_script_without_raw_echo(self):
        ep="fm_20261020_short_en"
        candidate=synthetic_claim(ep)
        from autopilot import oct20_transcript_retime_intake as module
        original=Path.read_bytes
        def changed(path):
            bytes_data=original(path)
            if str(path).endswith(ep+".draft_estimated.srt"):
                return bytes_data.replace(b"Chatbots",b"Impostor")
            return bytes_data
        with patch.object(Path,"read_bytes",autospec=True,side_effect=changed):
            with self.assertRaises(WorkflowError):
                inspect_oct20_untrusted_word_timing(candidate)

    def test_missing_lane_duplicate_lane_and_forged_speech_proof_denied(self):
        good=tuple(inspect_oct20_untrusted_word_timing(
            synthetic_claim(ep)) for ep in ALLOWED)
        with self.assertRaises(WorkflowError):
            summarize_oct20_word_timing_batch(good[:2])
        with self.assertRaises(WorkflowError):
            summarize_oct20_word_timing_batch((good[0],good[0],good[2]))
        forged=dict(good[0],natural_human_speech_verified=True)
        with self.assertRaises(WorkflowError):
            summarize_oct20_word_timing_batch((forged,good[1],good[2]))

    def test_forged_batch_rights_upload_or_word_count_denied(self):
        good=tuple(inspect_oct20_untrusted_word_timing(
            synthetic_claim(ep)) for ep in ALLOWED)
        for field,value in (
            ("youtube_upload_authorized",True),
            ("youtube_publish_authorized",True),
            ("commercial_voice_rights_authenticated",True),
            ("source_wav_technical_evidence_verified",True),
            ("actual_audio_caption_alignment_verified",True),
            ("claimed_word_count",1),
            ("largest_outside_estimated_caption_window_ms",-1),
            ("monthly_recurring_infrastructure_inr",10),
        ):
            with self.subTest(field=field):
                corrupted=dict(good[0],**{field:value})
                with self.assertRaises(WorkflowError):
                    summarize_oct20_word_timing_batch(
                        (corrupted,good[1],good[2]))

    def test_fake_new_authority_field_or_boolean_quota_is_denied(self):
        good=tuple(inspect_oct20_untrusted_word_timing(
            synthetic_claim(ep)) for ep in ALLOWED)
        for field,value in (
            ("human_voice_review_authorized",True),
            ("external_network_calls",False),
            ("monthly_recurring_infrastructure_inr",False),
        ):
            with self.subTest(field=field,value=value):
                forged=dict(good[0],**{field:value})
                with self.assertRaises(WorkflowError):
                    summarize_oct20_word_timing_batch(
                        (forged,good[1],good[2]))

    def test_proposed_candidate_repr_hides_full_transcript_words_hashes(self):
        ep="fm_20261020_short_en"
        candidate=synthetic_claim(ep)
        result=repr(candidate)
        self.assertIn("unverified",result)
        self.assertNotIn(candidate.words[0].text,result)
        self.assertNotIn(candidate.exact_script_sha256,result)
        self.assertNotIn(candidate.claimed_wav_sha256,result)


if __name__=="__main__":
    unittest.main()
