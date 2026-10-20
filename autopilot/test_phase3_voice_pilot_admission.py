"""Phase 3R1 3-voice pilot policy tests; **NO** genuine narrator data.

Synthetic WAV tones and fabricated license text demonstrate how easy a
technically valid but speech/legally unverified pilot can be forged.
No models, accounts, network, media files or permissions leave the runner.
"""
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import math
import struct
import tempfile
import unittest
import wave

from autopilot.agent_org import WorkflowError
from autopilot.phase3_voice_pilot_admission import (
    VoiceSample,EXPECTED,review_offline_voice_pilot,
    _first_authored_utterance_hash
)

NOW=datetime(2026,10,18,2,0,tzinfo=timezone.utc)


def fake_tone(path:Path, frequency:int, seconds:float=1) -> None:
    rate=16000
    with wave.open(str(path),"wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(rate)
        sound.writeframes(b"".join(
            struct.pack("<h",round(2800*math.sin(2*math.pi*frequency*i/rate)))
            for i in range(int(rate*seconds))
        ))


def sha(path:Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


class AudioPilotAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.doc=root/"fabricated_not_a_real_license.txt"
        self.doc.write_text(
            "Synthetic test declaration of commercial and adaptation rights. "
            "This is NOT a genuine legal license or speaker consent.",
            encoding="utf-8"
        )
        specs=[]
        for i,ep in enumerate(sorted(EXPECTED)):
            sample_path=root/(ep+".wav")
            fake_tone(sample_path,180+i*90)
            plan=EXPECTED[ep]
            specs.append(VoiceSample(
                episode_id=ep,narrator_id=plan["narrator_id"],
                language=plan["language"],
                wav_path=sample_path,expected_seconds=1.0,
                wav_sha256=sha(sample_path),
                bound_text_sha256=_first_authored_utterance_hash(ep),
                source_kind="owned_recording",
                claimed_license_spdx="owned-recording-contract",
                rights_document_path=self.doc,
                rights_document_sha256=sha(self.doc),
                commercial_use_claimed=True,
                adaptations_allowed_claimed=True,
                attribution_prepared=True,
                consent_claimed=True,
            ))
        self.specs=specs

    def review(self, samples=None):
        return review_offline_voice_pilot(
            self.specs if samples is None else samples,now=NOW)

    def variant(self,i,**changes):
        result=list(self.specs)
        result[i]=replace(result[i],**changes)
        return result

    def test_fake_wav_and_fake_contracts_cannot_grant_voice_approval(self):
        result=self.review()
        self.assertEqual(result["status"],"THREE_VOICE_SAMPLES_TECHNICALLY_BOUND_UNVERIFIED")
        self.assertEqual(len(result["episodes"]),3)
        self.assertFalse(result["independent_human_listening_verified"])
        self.assertFalse(result["hindi_pronunciation_verified"])
        self.assertFalse(result["license_legality_authenticated"])
        self.assertFalse(result["captions_word_aligned_to_speech"])
        self.assertFalse(result["youtube_upload_authorized"])
        self.assertFalse(result["publishing_authorized"])
        self.assertEqual(result["network_calls"],0)
        self.assertEqual(result["spend_inr"],0)
        self.assertNotIn("Synthetic test declaration",str(result))

    def test_permutation_does_not_change_output(self):
        self.assertEqual(self.review(),self.review(list(reversed(self.specs))))

    def test_source_episode_language_binding_from_actual_script(self):
        for record in self.specs:
            self.assertEqual(record.bound_text_sha256,
                             _first_authored_utterance_hash(record.episode_id))
            self.assertEqual(len(record.bound_text_sha256),64)

    def test_same_identical_sound_file_not_twice(self):
        first=self.specs[0]
        repeated=self.variant(1,wav_path=first.wav_path,wav_sha256=first.wav_sha256)
        with self.assertRaises(WorkflowError):
            self.review(repeated)

    def test_duplicate_narrator_episode_denied(self):
        modified=self.variant(1,episode_id=self.specs[0].episode_id)
        with self.assertRaises(WorkflowError):
            self.review(modified)

    def test_mismatched_language_denied(self):
        with self.assertRaises(WorkflowError):
            self.review(self.variant(1,language="es"))

    def test_wrong_narrator_id_denied(self):
        with self.assertRaises(WorkflowError):
            self.review(self.variant(0,narrator_id="narrator_unapproved"))

    def test_modified_script_hash_denied(self):
        with self.assertRaises(WorkflowError):
            self.review(self.variant(0,bound_text_sha256="0"*64))

    def test_audio_replaced_after_hash_record_denied(self):
        sound=self.specs[0].wav_path
        fake_tone(sound,700)
        with self.assertRaises(WorkflowError):
            self.review()

    def test_license_doc_modified_after_hash_denied(self):
        self.doc.write_text("Changed mock license!",encoding="utf-8")
        with self.assertRaises(WorkflowError):
            self.review()

    def test_noncommercial_license_denied(self):
        for label in ("CC-BY-NC-4.0","CC-BY-NC-SA-4.0","MIT", "unknown"):
            with self.subTest(label=label),self.assertRaises(WorkflowError):
                self.review(self.variant(0,claimed_license_spdx=label))

    def test_commercial_adaptation_and_consent_claims_mandatory(self):
        for field in ("commercial_use_claimed","adaptations_allowed_claimed",
                      "attribution_prepared","consent_claimed"):
            with self.subTest(field=field),self.assertRaises(WorkflowError):
                self.review(self.variant(0,**{field:False}))

    def test_symlink_audio_or_document_denied(self):
        path=Path(self.tmp.name)/"linked_audio.wav"
        path.symlink_to(self.specs[0].wav_path)
        with self.assertRaises(WorkflowError):
            self.review(self.variant(0,wav_path=path))
        doclink=Path(self.tmp.name)/"license_link.txt"
        doclink.symlink_to(self.doc)
        with self.assertRaises(WorkflowError):
            self.review(self.variant(0,rights_document_path=doclink))

    def test_model_source_must_be_exactly_pinned_with_safe_format(self):
        model=replace(
            self.specs[0],source_kind="offline_tts",
            claimed_license_spdx="Apache-2.0",
            model_label="hexgrad/Kokoro-82M",
            model_git_revision="1"*40,
            model_weights_sha256="2"*64,
            voice_style_sha256="3"*64,
            model_artifact_format="safetensors",
            consent_claimed=False,
        )
        specs=self.variant(0,**{
            key:getattr(model,key) for key in (
                "source_kind","claimed_license_spdx","model_label",
                "model_git_revision","model_weights_sha256",
                "voice_style_sha256","model_artifact_format",
                "consent_claimed")
        })
        result=self.review(specs)
        self.assertFalse(result["model_weights_downloaded"])
        self.assertFalse(result["model_deserialization_performed"])
        self.assertFalse(result["license_legality_authenticated"])

    def test_unsafe_pytorch_pickle_source_denied(self):
        model={
            "source_kind":"offline_tts",
            "claimed_license_spdx":"Apache-2.0",
            "model_label":"hexgrad/Kokoro-82M",
            "model_git_revision":"1"*40,
            "model_weights_sha256":"2"*64,
            "voice_style_sha256":"3"*64,
            "model_artifact_format":"pth",
        }
        with self.assertRaises(WorkflowError):
            self.review(self.variant(0,**model))

    def test_unpinned_model_revision_denied(self):
        model={
            "source_kind":"offline_tts",
            "claimed_license_spdx":"Apache-2.0",
            "model_label":"hexgrad/Kokoro-82M",
            "model_git_revision":"main",
            "model_weights_sha256":"2"*64,
            "voice_style_sha256":"3"*64,
            "model_artifact_format":"safetensors",
        }
        with self.assertRaises(WorkflowError):
            self.review(self.variant(0,**model))

    def test_paid_tts_provider_or_unknown_source_denied(self):
        with self.assertRaises(WorkflowError):
            self.review(self.variant(0,source_kind="external_tts"))

    def test_missing_rights_doc_denied(self):
        with self.assertRaises(WorkflowError):
            self.review(self.variant(0,rights_document_path=Path(self.tmp.name)/"missing.pdf"))

    def test_wrong_review_clock_denied(self):
        with self.assertRaises(WorkflowError):
            review_offline_voice_pilot(self.specs,now=NOW.replace(tzinfo=None))

    def test_technical_pcm_silence_denied(self):
        fake_tone(self.specs[0].wav_path,0)
        # Frequency zero makes a zero-valued silent WAV.
        adjusted=self.variant(0,wav_sha256=sha(self.specs[0].wav_path))
        with self.assertRaises(WorkflowError):
            self.review(adjusted)


if __name__=="__main__":
    unittest.main()
