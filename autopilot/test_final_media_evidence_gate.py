"""B3d4c2c1 no-network byte-and-caption inventory adversarial tests.

The tiny fake MP4/PNG/WAV signatures below are NOT playable video; they
only exercise this inventory's file hashing and parsing layer. The separate
hosted Kokoro/FFmpeg smoke actually renders and fully decodes real MP4/PNG
files before it runs this same inventory on the exact bytes.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import struct
import unittest

from autopilot.cloud_full_duration_pack import sentence_chunks
from autopilot.computed_demo_storyboards import build_executed_demo
from autopilot.final_media_evidence_gate import (
    FinalMediaEvidenceError,create_unapproved_final_media_inventory,
    require_exact_unapproved_inventory,inspect_three_different_unapproved_media,
)
from autopilot.script_to_preview_bridge import build_signed_preview_plan
from autopilot.test_script_continuity_gate import (
    signed_fixture, NOW, EXCLUDED,
)


RECIPES=("preserve_text_identifiers","validate_iso_dates","review_duplicate_keys")


def _png(width: int,height: int, marker: bytes) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"+b"\x00\x00\x00\rIHDR"
        +struct.pack(">II",width,height)
        +b"\x08\x02\x00\x00\x00"
        +marker
    )


def make_fake_unreviewed_inventory(index: int, root: Path):
    proposal,slot,obs,anchor,registry,seal,_=signed_fixture(index)
    plan=build_signed_preview_plan(
        proposal,slot,obs,seal=seal,anchor_manifest_sha256=anchor,
        registry=registry,excluded_creator_and_publisher_ids=EXCLUDED,
        now=NOW,
    )
    recipe=RECIPES[index]
    demo=build_executed_demo(plan,proposal,recipe)
    folder=root/plan["episode_id"]
    folder.mkdir()
    fake_mp4=(
        b"\x00\x00\x00\x20ftypisom\x00\x00\x00\x00"
        +bytes((index+31,))*240_000
    )
    (folder/"UNAPPROVED_FULL_EDUCATION_TEST.mp4").write_bytes(fake_mp4)
    (folder/"original_voice.wav").write_bytes(
        b"RIFF"+struct.pack("<I",18020)+b"WAVEfmt "
        +bytes((index+21,))*18000
    )
    thumb=_png(1280,720,bytes((index+1,))*35)
    (folder/"UNAPPROVED_THUMBNAIL_TEST.png").write_bytes(thumb)
    (folder/"moving_progress.png").write_bytes(_png(82,14,b"progress"))
    (folder/"scene_order.ffconcat").write_text(
        "ffconcat version 1.0\nfile 'scene_01.png'\n",
        encoding="utf-8",
    )
    width,height=((1080,1920) if index!=1 else (1920,1080))
    for i in range(plan["scene_count"]):
        (folder/f"scene_{i+1:02d}.png").write_bytes(
            _png(width,height,bytes(((i+1+index)%255,))*100)
        )
    chunks=[]
    for row in plan["scene_plan"]:
        chunks.extend(sentence_chunks(row["raw_narration"]))
    srt_blocks=[]
    def stamp(secs):
        return f"00:{secs//60:02d}:{secs%60:02d},000"
    for i,cue in enumerate(chunks,1):
        srt_blocks.extend([
            str(i),f"{stamp(i-1)} --> {stamp(i)}",cue,"",
        ])
    (folder/"scene_captions.srt").write_text(
        "\n".join(srt_blocks)+"\n",encoding="utf-8"
    )
    report={
        "episode":plan["episode_id"],
        "kind":plan["format"],
        "voice":("af_heart","am_michael","bf_emma")[index],
        "scene_count":plan["scene_count"],
        "original_scene_ids":[x["scene_id"] for x in plan["scene_plan"]],
        "script_manifest_sha256":plan["script_manifest_sha256"],
        "full_original_narration_sha256":plan["full_spoken_narration_sha256"],
        "computed_example_evidence_sha256":demo["evidence_packet_sha256"],
        "computed_test_example_executed":True,
        "human_approved_demo_visual_semantics":False,
        "synthetic_data_not_external_factual_support":True,
        "real_provider_generated_script":False,
        "full_actual_mp4_h264_aac_decode_passed":True,
        "actual_kokoro_speech_generated":True,
        "srt_cues_timed_from_generated_pcm":True,
        "human_full_playback_completed":False,
        "human_voice_quality_review_complete":False,
        "factual_accuracy_independently_approved":False,
        "copyright_and_voice_rights_cleared":False,
        "final_video_publishable":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "release_authorized":False,
        "video_sha256":sha256(fake_mp4).hexdigest(),
        "mp4_bytes":len(fake_mp4),
        "original_unreviewed_thumbnail_sha256":sha256(thumb).hexdigest(),
        "narration_cues":len(chunks),
        "seconds":float(len(chunks)+4),
    }
    options={
        "plan":plan,"proposal":proposal,"slot":slot,
        "observations":obs,"seal":seal,
        "external_script_anchor_sha256":anchor,
        "script_registry":registry,
        "excluded_creator_and_publisher_ids":EXCLUDED,
        "report":report,"episode_folder":folder,
        "demo_recipe":recipe,"now":NOW,
    }
    return options,create_unapproved_final_media_inventory(**options)


class FinalMediaEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(prefix="flowminute-c1-hash-unapproved-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.kwargs,self.inventory=make_fake_unreviewed_inventory(0,self.root)

    def test_rebuilt_script_demo_and_all_actual_file_hashes_are_bound(self):
        r=self.inventory
        self.assertEqual(r["status"],
            "EXACT_TEMP_MEDIA_LINEAGE_AND_CAPTIONS_VERIFIED_UNREVIEWED_NO_PUBLISH")
        self.assertEqual(r["signed_original_script_manifest_sha256"],
                         self.kwargs["plan"]["script_manifest_sha256"])
        self.assertEqual(r["asset_count"],self.kwargs["plan"]["scene_count"]+6)
        self.assertEqual(r["srt_text_and_cue_timing"]["cue_count"],
                         self.kwargs["report"]["narration_cues"])
        self.assertTrue(r["srt_text_and_cue_timing"]
                        ["all_spoken_sentences_text_exactly_represented"])
        self.assertTrue(r["all_asset_bytes_rehashed_from_actual_ephemeral_files"])
        self.assertFalse(r["full_human_watch_listen_completed"])
        self.assertFalse(r["all_title_thumbnail_caption_visual_claims_verified"])
        self.assertFalse(r["sound_voice_music_license_rights_checked"])
        self.assertFalse(r["private_immutable_content_ledger_connected"])
        self.assertFalse(r["release_authorized"])
        require_exact_unapproved_inventory(self.inventory,**self.kwargs)

    def test_all_three_different_substantive_computation_recipes_but_not_approved(self):
        inventories=[self.inventory]
        for index in (1,2):
            _,item=make_fake_unreviewed_inventory(index,self.root)
            inventories.append(item)
        r=inspect_three_different_unapproved_media(inventories)
        self.assertTrue(r["three_exact_technical_video_and_thumbnail_hashes_differ"])
        self.assertFalse(r["semantic_originality_approved"])
        self.assertFalse(r["human_fact_and_rights_reviews_complete"])
        self.assertFalse(r["release_authorized"])

    def test_modified_mp4_byte_after_producer_report_does_not_pass(self):
        f=self.kwargs["episode_folder"]/"UNAPPROVED_FULL_EDUCATION_TEST.mp4"
        f.write_bytes(f.read_bytes()+b"tampered")
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**self.kwargs)

    def test_modified_thumbnail_byte_after_producer_report_does_not_pass(self):
        f=self.kwargs["episode_folder"]/"UNAPPROVED_THUMBNAIL_TEST.png"
        f.write_bytes(f.read_bytes()+b"tamper")
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**self.kwargs)

    def test_modified_scene_image_byte_after_report_is_detected_on_recompute(self):
        image=self.kwargs["episode_folder"]/"scene_02.png"
        image.write_bytes(image.read_bytes()+b"attacker")
        changed=create_unapproved_final_media_inventory(**self.kwargs)
        self.assertNotEqual(changed["unapproved_inventory_sha256"],
                            self.inventory["unapproved_inventory_sha256"])
        with self.assertRaises(FinalMediaEvidenceError):
            require_exact_unapproved_inventory(self.inventory,**self.kwargs)

    def test_srt_cue_text_missing_or_changed_denied(self):
        srt=self.kwargs["episode_folder"]/"scene_captions.srt"
        srt.write_text(srt.read_text().replace(" ", "Z",1))
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**self.kwargs)

    def test_srt_wrong_timestamp_backtrack_denied(self):
        srt=self.kwargs["episode_folder"]/"scene_captions.srt"
        s=srt.read_text()
        srt.write_text(s.replace("00:00:01,000 --> 00:00:02,000",
                                 "00:00:00,000 --> 00:00:02,000",1))
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**self.kwargs)

    def test_srt_extra_caption_or_missing_cue_denied(self):
        srt=self.kwargs["episode_folder"]/"scene_captions.srt"
        srt.write_text(srt.read_text()+"900\n00:03:00,000 --> 00:03:01,000\nFake\n\n")
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**self.kwargs)

    def test_removed_voice_or_mp4_denied(self):
        for name in ("original_voice.wav","UNAPPROVED_FULL_EDUCATION_TEST.mp4"):
            with self.subTest(name=name):
                f=self.kwargs["episode_folder"]/name
                b=f.read_bytes()
                f.unlink()
                with self.assertRaises(FinalMediaEvidenceError):
                    create_unapproved_final_media_inventory(**self.kwargs)
                f.write_bytes(b)

    def test_unexpected_data_file_in_render_directory_denied(self):
        extra=self.kwargs["episode_folder"]/"overrides_approval.json"
        extra.write_text('{"release_authorized":true}')
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**self.kwargs)

    def test_symlink_thumbnail_or_scene_denied(self):
        src=self.kwargs["episode_folder"]/"UNAPPROVED_THUMBNAIL_TEST.png"
        real=self.kwargs["episode_folder"]/"legit.png"
        src.rename(real)
        src.symlink_to(real)
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**self.kwargs)

    def test_fake_technical_qa_or_human_approval_in_report_denied(self):
        for field,value in (
            ("actual_kokoro_speech_generated",False),
            ("full_actual_mp4_h264_aac_decode_passed",False),
            ("human_full_playback_completed",True),
            ("factual_accuracy_independently_approved",True),
            ("copyright_and_voice_rights_cleared",True),
            ("release_authorized",True),
            ("youtube_upload_enabled",True),
            ("human_approved_demo_visual_semantics",True),
            ("real_provider_generated_script",True),
        ):
            with self.subTest(field=field):
                kwargs={**self.kwargs,"report":{**self.kwargs["report"],field:value}}
                with self.assertRaises(FinalMediaEvidenceError):
                    create_unapproved_final_media_inventory(**kwargs)

    def test_fake_mp4_digest_or_thumbnail_digest_in_report_denied(self):
        for field in ("video_sha256","original_unreviewed_thumbnail_sha256"):
            with self.subTest(field=field):
                kwargs={**self.kwargs,"report":{**self.kwargs["report"],field:"0"*64}}
                with self.assertRaises(FinalMediaEvidenceError):
                    create_unapproved_final_media_inventory(**kwargs)

    def test_forged_signed_script_title_or_narration_denied(self):
        p=deepcopy(self.kwargs["proposal"])
        p["title"]="Completely different title after signature."
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**{
                **self.kwargs,"proposal":p,
            })
        p=deepcopy(self.kwargs["proposal"])
        p["narration"]+=" Fabricated statement after signing."
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**{
                **self.kwargs,"proposal":p,
            })

    def test_changed_source_response_sha_denied(self):
        x=deepcopy(self.kwargs["observations"])
        x["sources"][0]["response_sha256"]="f"*64
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**{
                **self.kwargs,"observations":x,
            })

    def test_wrong_recipe_or_slot_replay_denied(self):
        for recipe in set(RECIPES)-{"preserve_text_identifiers"}:
            with self.assertRaises(FinalMediaEvidenceError):
                create_unapproved_final_media_inventory(**{
                    **self.kwargs,"demo_recipe":recipe,
                })
        other=deepcopy(self.kwargs["plan"])
        other["episode_id"]="fm_20261105_long"
        with self.assertRaises(FinalMediaEvidenceError):
            create_unapproved_final_media_inventory(**{
                **self.kwargs,"plan":other,
            })

    def test_unapproved_inventory_tamper_rejected_even_when_hash_forged(self):
        changed=deepcopy(self.inventory)
        changed["all_title_thumbnail_caption_visual_claims_verified"]=True
        changed["unapproved_inventory_sha256"]=sha256(
            repr(changed).encode()
        ).hexdigest()
        with self.assertRaises(FinalMediaEvidenceError):
            require_exact_unapproved_inventory(changed,**self.kwargs)

    def test_cross_episode_duplicate_metadata_not_originality_proof(self):
        inventories=[self.inventory]
        for index in (1,2):
            _,item=make_fake_unreviewed_inventory(index,self.root)
            inventories.append(item)
        dup=deepcopy(inventories)
        dup[1]["signed_full_spoken_narration_sha256"]=dup[0][
            "signed_full_spoken_narration_sha256"]
        with self.assertRaises(FinalMediaEvidenceError):
            inspect_three_different_unapproved_media(dup)
        dup=deepcopy(inventories)
        for row in dup[2]["asset_sha256_and_exact_sizes"]:
            if row["file_name"]=="UNAPPROVED_THUMBNAIL_TEST.png":
                row["sha256"]=next(r["sha256"]
                    for r in dup[0]["asset_sha256_and_exact_sizes"]
                    if r["file_name"]=="UNAPPROVED_THUMBNAIL_TEST.png")
        with self.assertRaises(FinalMediaEvidenceError):
            inspect_three_different_unapproved_media(dup)

    def test_three_slots_can_never_invent_human_or_rights_clearance(self):
        rows=[self.inventory]
        for index in (1,2):
            _,item=make_fake_unreviewed_inventory(index,self.root)
            rows.append(item)
        for field in ("human_fact_and_rights_reviews_complete",
                      "semantic_originality_approved",
                      "private_durable_media_store_connected"):
            report=inspect_three_different_unapproved_media(rows)
            self.assertFalse(report[field])


if __name__=="__main__":
    unittest.main()
