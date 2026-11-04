"""B3d4c2d1: adversarial standard-library-only S3 emulator and physical fake assets.

All bytes are synthetic deliberately NONPLAYABLE. It simulates only the
request/readback contract: it is NOT actual Amazon S3, IAM, Object Lock,
owner approval, rights review or immutable cross-account storage. A separate
GitHub Actions Moto HTTP service job tests SDK command compatibility.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from autopilot.primary_sourced_storyboards import build_story,canonical
from autopilot.primary_claim_surface_docket import make_unapproved_claim_surface_docket
from autopilot.private_versioned_media_escrow import (
    EscrowError, ReviewRequiredStorageIntent,prepare_exact_private_escrow,
    escrow_once_and_readback, _check_plan, _read_exact_file,
)

NOW=datetime(2026,11,4,16,0,0,tzinfo=timezone.utc)
KMS="arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000"
CONFIG=ReviewRequiredStorageIntent(
    bucket="flowminute-simulated-private-lock-test",
    region="us-east-1",kms_key_arn=KMS,retention_days=7,
)


def fixture(folder:Path,slot:str="short_am"):
    story=build_story(slot)
    ep=folder/story["episode_id"]
    ep.mkdir(mode=0o700)
    names={
        "original_voice.wav","scene_captions.srt",
        "UNAPPROVED_FULL_EDUCATION_TEST.mp4",
        "UNAPPROVED_THUMBNAIL_TEST.png",
        "scene_order.ffconcat","animated_frames.ffconcat",
        "moving_progress.png",
    }
    for i in range(story["scene_count"]):
        names.add(f"scene_{i+1:02d}.png")
        for j in range(5):
            names.add(f"moving_{i+1:02d}_{j:02d}.png")
    for name in sorted(names):
        (ep/name).write_bytes(
            (f"SYNTHETIC NONPLAYABLE STORED-FILE CONTRACT ONLY | {story['episode_id']} | {name} | ").encode()*3
        )
    video=(ep/"UNAPPROVED_FULL_EDUCATION_TEST.mp4").read_bytes()
    thumb=(ep/"UNAPPROVED_THUMBNAIL_TEST.png").read_bytes()
    producer={
        "video_sha256":sha256(video).hexdigest(),
        "mp4_bytes":len(video),
        "original_unreviewed_thumbnail_sha256":sha256(thumb).hexdigest(),
        "original_source_story_draft_sha256":story["draft_sha256"],
        "actual_full_encoded_h264_aac_with_captions_and_animation":True, # MOCK ATTESTATION
        "actual_narration_text_and_srt_matched":True, # MOCK ATTESTATION
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
    return story,ep,producer


class FakeS3:
    """Strictly local disposable in-memory model, not cloud vendor semantics."""
    def __init__(self):
        self.objects={}
        self.put_calls=0
        self.fail_after=None
        self.break_get=False
        self.omit_version=False
        self.forget_kms=False
        self.weaken_lock=False

    def put_object(self,**kwargs):
        self.put_calls+=1
        if self.fail_after is not None and self.put_calls>=self.fail_after:
            raise IOError("Synthetic transient timeout; could have stored object")
        key=kwargs["Key"]
        assert kwargs["IfNoneMatch"]=="*"
        assert kwargs["ServerSideEncryption"]=="aws:kms"
        assert kwargs["ObjectLockMode"]=="COMPLIANCE"
        if key in self.objects:
            raise IOError("S3 412 PreconditionFailed replay")
        raw=kwargs["Body"]
        assert isinstance(raw,bytes)
        assert len(raw)==kwargs["ContentLength"]
        assert base64.b64encode(sha256(raw).digest()).decode()==kwargs["ChecksumSHA256"]
        version=f"mock/immutable_version_{len(self.objects)+1:04d}"
        self.objects[key]=dict(
            raw=raw,version=version,
            metadata=kwargs["Metadata"],
            kms=kwargs["SSEKMSKeyId"],
            lock=kwargs["ObjectLockMode"],
            retain_until=kwargs["ObjectLockRetainUntilDate"],
        )
        return {} if self.omit_version else {"VersionId":version}

    def head_object(self,**kwargs):
        row=self.objects[kwargs["Key"]]
        if kwargs["VersionId"]!=row["version"]:
            raise IOError("Wrong S3 object version")
        return {
            "VersionId":row["version"],
            "ContentLength":len(row["raw"]),
            "Metadata":row["metadata"],
            "ServerSideEncryption":"aws:kms",
            "SSEKMSKeyId":"bad-other-region" if self.forget_kms else row["kms"],
            "ObjectLockMode":"GOVERNANCE" if self.weaken_lock else row["lock"],
            "ObjectLockRetainUntilDate":row["retain_until"],
            "ChecksumSHA256":base64.b64encode(sha256(row["raw"]).digest()).decode(),
        }

    def get_object(self,**kwargs):
        row=self.objects[kwargs["Key"]]
        if kwargs["VersionId"]!=row["version"]:
            raise IOError("Wrong version read")
        b=row["raw"]+b"tampered" if self.break_get else row["raw"]
        return {
            "VersionId":row["version"],
            "Body":io.BytesIO(b),
            "ChecksumSHA256":base64.b64encode(sha256(row["raw"]).digest()).decode(),
        }


class S3ExactEscrowTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(prefix="flowminute-escrow-synthetic-")
        self.addCleanup(self.temp.cleanup)
        self.story,self.folder,self.report=fixture(Path(self.temp.name))
        self.plan=prepare_exact_private_escrow(
            story=self.story,folder=self.folder,producer_report=self.report,
            config=CONFIG,
        )
        self.s3=FakeS3()

    def run_escrow(self,**args):
        d=dict(s3=self.s3,plan=self.plan,folder=self.folder,config=CONFIG,now=NOW)
        d.update(args)
        return escrow_once_and_readback(**d)

    def test_full_43_objects_and_manifest_staged_by_version_specific_readback(self):
        result=self.run_escrow()
        self.assertEqual(self.plan["object_count"],43)
        self.assertEqual(result["original_versioned_object_count"],43)
        self.assertEqual(result["total_object_count_including_final_manifest"],44)
        self.assertEqual(len(self.s3.objects),44)
        self.assertEqual(self.s3.put_calls,44)
        self.assertTrue(result["all_object_versions_independently_read_back"])
        self.assertTrue(result["all_object_versions_compliance_retention_proved_by_adapter"])
        self.assertFalse(result["real_cloud_account_identity_and_bucket_iam_verified"])
        self.assertFalse(result["real_owner_approved_storage_cost_and_retention"])
        self.assertFalse(result["actual_independent_factual_voice_rights_and_owner_review"])
        self.assertFalse(result["release_authorized"])
        manifest_keys=[x for x in self.s3.objects if "/escrow-manifest/" in x]
        self.assertEqual(len(manifest_keys),1)
        self.assertEqual(
            self.s3.objects[manifest_keys[0]]["raw"],
            canonical({
                "schema_version":1,
                "status":"ALL_EXACT_ORIGINAL_VERSIONED_OBJECTS_STORED_UNAPPROVED",
                "episode_id":self.story["episode_id"],
                "unapproved_escrow_plan_sha256":self.plan["unapproved_escrow_plan_sha256"],
                "original_media_inventory_sha256":self.plan["original_producer_media_inventory_sha256"],
                "source_claim_docket_sha256":self.plan["unapproved_claim_surface_docket_sha256"],
                "object_versions":[
                    {
                        "object_version_id":x["version"],"key":key,
                        "sha256":sha256(x["raw"]).hexdigest(),
                        "exact_bytes":len(x["raw"]),
                        "s3_version_id_readback_passed":True,
                        "sha256_entire_returned_object_confirmed":True,
                        "object_lock_compliance_mode_returned":True,
                        "specific_customer_kms_key_returned":True,
                    } for key,x in self.s3.objects.items()
                    if "/escrow-manifest/" not in key
                ],
                "object_count":43,
                "real_owner_workload_iam_and_cost_terms_confirmed":False,
                "real_review_and_final_playback_completed":False,
                "youtube_upload_enabled":False,
                "release_authorized":False,
            }),
        )

    def test_three_original_story_versions_have_43_127_43_asset_fingerprints(self):
        for slot,count in (("short_am",43),("long",127),("short_pm",43)):
            with self.subTest(slot=slot):
                root=Path(self.temp.name)/slot
                root.mkdir()
                story,folder,report=fixture(root,slot)
                plan=prepare_exact_private_escrow(
                    story=story,folder=folder,producer_report=report,config=CONFIG,
                )
                self.assertEqual(plan["object_count"],count)
                docket=make_unapproved_claim_surface_docket(slot)
                self.assertEqual(
                    plan["unapproved_claim_surface_docket_sha256"],
                    docket["unapproved_claim_surface_docket_sha256"],
                )
                self.assertFalse(plan["release_authorized"])
                self.assertFalse(plan["production_bucket_iam_versioning_and_lock_verified"])

    def test_changed_source_claim_docket_rehashed_cannot_be_escrowed(self):
        altered=deepcopy(self.plan)
        altered["unapproved_claim_surface_docket_sha256"]="0"*64
        original={k:v for k,v in altered.items() if k!="unapproved_escrow_plan_sha256"}
        altered["unapproved_escrow_plan_sha256"]=sha256(canonical(original)).hexdigest()
        with self.assertRaises(EscrowError):
            self.run_escrow(plan=altered)
        self.assertEqual(self.s3.put_calls,0)

    def test_wrong_legal_kms_scope_region_and_retention_preflight_rejected(self):
        for change in (
            {"bucket":"bad/file"},
            {"region":"eu-west-2"},
            {"kms_key_arn":"arn:aws:kms:us-east-1:123:key/nope"},
            {"retention_days":0},
            {"retention_days":31},
            {"retention_days":True},
            {"prefix":"../../escape"},
        ):
            c=ReviewRequiredStorageIntent(**{**CONFIG.__dict__,**change})
            with self.subTest(change=change),self.assertRaises(EscrowError):
                prepare_exact_private_escrow(story=self.story,folder=self.folder,
                                             producer_report=self.report,config=c)

    def test_metadata_rights_or_real_owner_forgery_blocked(self):
        for flag in (
            "youtube_upload_enabled","release_authorized",
        ):
            report={**self.report,flag:True}
            with self.subTest(flag=flag),self.assertRaises(EscrowError):
                prepare_exact_private_escrow(story=self.story,folder=self.folder,
                                             producer_report=report,config=CONFIG)
        for flag in (
            "youtube_upload_enabled","release_authorized",
            "real_human_fact_rights_disclosure_and_full_watch_approvals",
            "production_bucket_iam_versioning_and_lock_verified",
        ):
            altered=deepcopy(self.plan)
            altered[flag]=True
            altered["unapproved_escrow_plan_sha256"]=sha256(canonical({
                k:v for k,v in altered.items() if k!="unapproved_escrow_plan_sha256"
            })).hexdigest()
            with self.subTest(flag=flag),self.assertRaises(EscrowError):
                self.run_escrow(plan=altered)

    def test_exact_byte_tamper_before_put_rejected_and_zero_objects_stored(self):
        for name in ("UNAPPROVED_FULL_EDUCATION_TEST.mp4",
                     "UNAPPROVED_THUMBNAIL_TEST.png","scene_captions.srt",
                     "moving_01_02.png","original_voice.wav"):
            path=self.folder/name
            raw=path.read_bytes()
            path.write_bytes(raw+b"tampered")
            with self.subTest(file=name),self.assertRaises(EscrowError):
                self.run_escrow()
            self.assertEqual(self.s3.put_calls,0)
            path.write_bytes(raw)

    def test_unknown_extra_file_or_missing_asset_blocks_all_write(self):
        extra=self.folder/"forged_hidden.txt"
        extra.write_text("not original asset",encoding="utf8")
        with self.assertRaises(EscrowError):
            self.run_escrow()
        extra.unlink()
        original=(self.folder/"scene_01.png").read_bytes()
        (self.folder/"scene_01.png").unlink()
        with self.assertRaises(EscrowError):
            self.run_escrow()
        self.assertEqual(self.s3.put_calls,0)
        (self.folder/"scene_01.png").write_bytes(original)

    def test_symlink_under_video_folder_rejected(self):
        path=self.folder/"scene_01.png"
        raw=path.read_bytes()
        path.unlink()
        path.symlink_to(self.folder/"scene_02.png")
        with self.assertRaises(EscrowError):
            self.run_escrow()
        self.assertEqual(self.s3.put_calls,0)
        path.unlink()
        path.write_bytes(raw)

    def test_no_retry_after_ambiguous_put_or_duplicate_key(self):
        self.s3.fail_after=5
        with self.assertRaisesRegex(EscrowError,"DO NOT retry|do NOT retry"):
            self.run_escrow()
        self.assertEqual(self.s3.put_calls,5)
        self.assertEqual(len(self.s3.objects),4)
        self.assertFalse(any("/escrow-manifest/" in x for x in self.s3.objects))
        self.s3.fail_after=None
        with self.assertRaises(EscrowError):
            self.run_escrow()
        self.assertFalse(any("/escrow-manifest/" in x for x in self.s3.objects))

    def test_missing_version_id_after_server_write_is_ambiguous_no_retry(self):
        self.s3.omit_version=True
        with self.assertRaises(EscrowError):
            self.run_escrow()
        self.assertEqual(self.s3.put_calls,1)
        self.assertEqual(len(self.s3.objects),1)

    def test_remote_body_tamper_wrong_kms_or_weaker_retention_fails(self):
        for option in ("break_get","forget_kms","weaken_lock"):
            f=FakeS3()
            setattr(f,option,True)
            with self.subTest(fault=option),self.assertRaises(EscrowError):
                self.run_escrow(s3=f)
            self.assertEqual(f.put_calls,1)
            self.assertFalse(any("/escrow-manifest/" in k for k in f.objects))

    def test_duplicate_successful_manifest_cannot_be_replaced_on_replay(self):
        receipt=self.run_escrow()
        first_count=len(self.s3.objects)
        with self.assertRaises(EscrowError):
            self.run_escrow()
        self.assertEqual(len(self.s3.objects),first_count)
        self.assertEqual(receipt["original_versioned_object_count"],43)

    def test_no_cloud_client_constructed_from_unreviewed_plan(self):
        import autopilot.private_versioned_media_escrow as code
        for name in ("create_aws_account","get_aws_secret",
                     "fetch_billing_api","create_real_s3_client",
                     "deploy_cloud","upload_to_youtube","sign_as_owner"):
            self.assertFalse(hasattr(code,name))


if __name__=="__main__":
    unittest.main()
