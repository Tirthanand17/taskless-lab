"""Synthetic offline voice source/human review readiness; never real audio."""
from copy import deepcopy
from hashlib import sha256
import json
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase2r3_authored_pack_audit import SOURCE, SECTIONS
from autopilot.phase3_voice_acquisition_readiness import (
    build_voice_acquisition_readiness_packet, REQUIRED_EVIDENCE,
)


class VoiceReadinessPacketTests(unittest.TestCase):
    def test_exact_three_original_episodes_and_human_source_requirements(self):
        x = build_voice_acquisition_readiness_packet()
        self.assertEqual(x["status"], "SOURCE_LOCKED_VOICE_ASSET_REQUEST_ONLY_NOT_RECEIVED")
        self.assertEqual(len(x["episodes"]), 3)
        self.assertEqual(
            {e["episode_id"] for e in x["episodes"]},
            {row[2] for row in SECTIONS}
        )
        self.assertEqual(
            {e["original_language"] for e in x["episodes"] if e["kind"] == "short"},
            {"hi", "en"},
        )
        self.assertEqual(len({e["planned_narrator_id"] for e in x["episodes"]}), 3)
        self.assertEqual(sum(e["planned_duration_seconds"] for e in x["episodes"]), 516)
        self.assertEqual(
            [e["authored_scene_count"] for e in x["episodes"]], [4, 4, 24]
        )
        self.assertEqual(x["authored_markdown_sha256"],
                         sha256(SOURCE.read_bytes()).hexdigest())
        for ep in x["episodes"]:
            with self.subTest(episode=ep["episode_id"]):
                for key in ("spoken_script_sha256", "source_section_sha256",
                            "estimated_draft_srt_sha256"):
                    self.assertRegex(ep[key], r"^[a-f0-9]{64}$")
                self.assertEqual(ep["evidence_required_not_collected"],
                                 REQUIRED_EVIDENCE)
                self.assertEqual(ep["caption_timing_state"],
                                 "SCRIPT_ESTIMATE_NOT_SPEECH_ALIGNED")
                self.assertFalse(ep["source_wav_received"])
                self.assertFalse(ep["language_and_voice_listening_verified"])
                self.assertFalse(ep["actual_spoken_caption_alignment_verified"])
                self.assertFalse(ep["approved_for_render_or_mux"])
                self.assertFalse(ep["approved_for_upload_or_publish"])

    def test_stable_digest_bound_to_complete_source_and_language_pack(self):
        a=build_voice_acquisition_readiness_packet()
        b=build_voice_acquisition_readiness_packet()
        self.assertEqual(a,b)
        summary={k:v for k,v in a.items() if k!="packet_sha256"}
        actual=sha256(json.dumps(
            summary,sort_keys=True,separators=(",",":"),
            ensure_ascii=True,allow_nan=False,
        ).encode("utf-8")).hexdigest()
        self.assertEqual(a["packet_sha256"],actual)
        self.assertEqual(b["packet_sha256"],actual)
        self.assertNotIn("## SHORT 1",str(a))
        self.assertNotIn("00:00–00:10",str(a))

    def test_text_mutation_changes_hash_or_fails_closed(self):
        raw=SOURCE.read_text(encoding="utf-8")
        new=raw.replace(
            "क्या आपको Excel जैसी CSV फ़ाइल का डेटा जल्दी समझना है?",
            "क्या आपको Excel जैसी CSV फ़ाइल का डेटा बहुत जल्दी समझना है?", 1
        )
        self.assertNotEqual(raw,new)
        try:
            x=build_voice_acquisition_readiness_packet(markdown=new)
        except WorkflowError:
            pass  # A changed preapproved script can also be refused.
        else:
            self.assertNotEqual(x["packet_sha256"],
                                build_voice_acquisition_readiness_packet()["packet_sha256"])
            self.assertFalse(x["publishing_authorized"])

    def test_language_substitution_breaks_source_lock(self):
        raw=SOURCE.read_text(encoding="utf-8")
        start=raw.index("## SHORT 1")
        stop=raw.index("## SHORT 2")
        changed=raw[:start]+raw[start:stop].replace("क्या", "This",1)+raw[stop:]
        self.assertNotEqual(raw,changed)
        with self.assertRaises(WorkflowError):
            build_voice_acquisition_readiness_packet(markdown=changed)

    def test_wrong_scene_time_rejected_not_silently_replaced(self):
        raw=SOURCE.read_text(encoding="utf-8")
        old="00:00–00:10"
        self.assertIn(old,raw)
        with self.assertRaises(WorkflowError):
            build_voice_acquisition_readiness_packet(
                markdown=raw.replace(old,"00:00–00:11",1)
            )

    def test_no_false_asset_rights_or_production_permission(self):
        x=build_voice_acquisition_readiness_packet()
        for key in (
            "voice_provider_or_model_connected",
            "legal_or_human_editor_authenticated",
            "separate_owner_authorization_for_new_model_or_service_obtained",
            "authenticity_or_naturalness_verified",
            "real_audio_caption_alignment_verified",
            "release_or_production_ready", "publishing_authorized",
        ):
            with self.subTest(key=key):
                self.assertIs(x[key],False)
        self.assertEqual(x["network_calls"],0)
        self.assertEqual(x["files_written"],0)
        self.assertEqual(x["recurring_infrastructure_budget_inr"],0)
        self.assertEqual(x["real_voice_assets_available_in_this_packet"],0)
        self.assertEqual(x["independently_verified_voice_assets"],0)

    def test_user_mutations_cannot_alter_independent_regenerated_packet(self):
        report=build_voice_acquisition_readiness_packet()
        mutated=deepcopy(report)
        mutated["episodes"][0]["approved_for_upload_or_publish"]=True
        mutated["publishing_authorized"]=True
        self.assertNotEqual(mutated["packet_sha256"],sha256(json.dumps(
            {k:v for k,v in mutated.items() if k!="packet_sha256"},
            sort_keys=True,separators=(",",":"),ensure_ascii=True
        ).encode("utf-8")).hexdigest())
        self.assertFalse(build_voice_acquisition_readiness_packet()["publishing_authorized"])

    def test_no_actual_recording_file_model_or_owned_account_reference(self):
        x=build_voice_acquisition_readiness_packet()
        visible=str(x)
        for forbidden in ("C:\\Users", "youtube.com/watch?v=", ".wav_path",
                          "sk-", "Bearer ", "private_key", "api_token"):
            self.assertNotIn(forbidden,visible)
        self.assertEqual(len(x["permitted_paths_to_examine_after_separate_owner_authorization"]),2)


if __name__ == "__main__":
    unittest.main()
