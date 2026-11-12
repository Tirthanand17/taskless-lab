"""Clivox A3: adversarial tests for private-media boundary, deny-by-default."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.branch3_media_storage_preflight import (
    POLICY,MANIFEST,CREATOR_PERMS,CHANNEL_STATE,
    StorageDenied,read_json,inspect_private_repo_metadata,
    validate_public_paths,validate_policy,check_no_upload_side_effects,
    BRANDING_ALLOWLIST
)

class MediaStoragePreflightTests(unittest.TestCase):
    def setUp(self):
        self.policy=read_json(POLICY)
        self.manifest=read_json(MANIFEST)
        self.perms=read_json(CREATOR_PERMS)
        self.channel=read_json(CHANNEL_STATE)

    def validate(self):
        return validate_policy(self.policy,self.manifest,self.perms,self.channel)

    def test_unprovisioned_plan_is_correctly_blocked(self):
        result=self.validate()
        self.assertEqual(result["creator_grants"],0)
        self.assertFalse(result["source_download_authorized"])
        self.assertFalse(result["private_media_vault_provisioned"])
        self.assertFalse(result["youtube_upload_authorized"])

    def test_user_repo_public_paths_are_limited_to_safe_text_and_brand_png(self):
        paths=[str(x.relative_to(POLICY.parents[2])).replace("\\","/")
               for x in (POLICY.parents[2]/"branch3").rglob("*") if x.is_file()]
        x=validate_public_paths(paths,allowed_visuals=sorted(BRANDING_ALLOWLIST))
        self.assertFalse(x["licensed_media_detected"])
        self.assertEqual(x["allowed_original_visuals_present"],2)

    def test_reject_public_source_video_and_private_documents(self):
        for file in (
            "branch3/footage/creator.mp4",
            "branch3/rights_cases/creator_contract.pdf",
            "branch3/media_storage/clip.wav",
            "branch3/screenshots/podcast.png",
            "branch3/media_storage/raw_contract.json",
            "branch3/media_storage/oauth.json",
            "branch3/media_storage/private_agreement.md",
            "branch3/media_storage/../secrets.txt",
            "branch3/media_storage\\clip.mp4",
        ):
            with self.subTest(file=file),self.assertRaises(StorageDenied):
                validate_public_paths([file],allowed_visuals=sorted(BRANDING_ALLOWLIST))

    def test_deny_premature_storage_activation(self):
        for flag in (
            "private_vault_repository_identity_verified","private_vault_owner_approved",
            "identity_and_access_review_complete","owner_contract_scope_reviewed",
            "github_production_environment_protection_verified","media_fetch_enabled",
            "media_write_enabled","media_render_enabled","youtube_upload_enabled",
        ):
            self.policy=read_json(POLICY)
            self.policy[flag]=True
            with self.subTest(flag=flag),self.assertRaises(StorageDenied):
                self.validate()

    def test_deny_public_artifacts_lfs_repo_or_contracts(self):
        for key,value in self.policy["data_policy"].items():
            self.policy=read_json(POLICY)
            self.policy["data_policy"][key]=not value
            with self.subTest(key=key),self.assertRaises(StorageDenied):
                self.validate()

    def test_deny_forged_media_and_rights_checks(self):
        for field in (
            "source_creator_rights_grant_verified",
            "commercial_youtube_reuse_verified",
            "music_visuals_guests_and_publisher_rights_cleared",
            "permission_active_reverified","contract_owner_reviewed",
        ):
            self.manifest=read_json(MANIFEST)
            self.manifest["permission"][field]=True
            with self.subTest(field=field),self.assertRaises(StorageDenied):
                self.validate()
        self.manifest=read_json(MANIFEST)
        self.manifest["permission"]["source_creator_rights_grant_fingerprint_sha256"]="a"*64
        with self.assertRaises(StorageDenied):self.validate()

    def test_no_cross_channel_or_source_scope(self):
        self.policy["target_channel_id"]="UCCcL9Q_jqVq6LJmnYUSAFZA"
        with self.assertRaises(StorageDenied):self.validate()
        self.policy=read_json(POLICY)
        self.manifest["source"]["canonical_url"]="https://youtu.be/i6pmnpaOaZQ?token=private"
        with self.assertRaises(StorageDenied):self.validate()

    def test_storage_object_identifiers_cannot_be_faked(self):
        for key,val in (
            ("private_repository","Tirthanand17/taskless-lab"),
            ("asset_id",12345678),
            ("release_tag","raw-season-1"),
            ("expected_sha256","0"*64),
            ("expected_bytes",2000000),
            ("privacy_rechecked_with_authenticated_api",True)
        ):
            self.manifest=read_json(MANIFEST)
            self.manifest["vault"][key]=val
            with self.subTest(key=key),self.assertRaises(StorageDenied):
                self.validate()

    def test_empty_permission_allowlist_required(self):
        self.perms["creators"]=[{"creator_id":"not_authorized"}]
        with self.assertRaises(StorageDenied):self.validate()

    def test_public_controller_repository_not_valid_private_vault(self):
        repo={
            "full_name":"Tirthanand17/taskless-lab","private":False,
            "visibility":"public","owner":{"login":"Tirthanand17"},
            "archived":False,"disabled":False
        }
        with self.assertRaises(StorageDenied):
            inspect_private_repo_metadata(repo,expected_full_name=repo["full_name"])

    def test_private_repo_metadata_shape_is_not_rights_approval(self):
        repo={
            "full_name":"Tirthanand17/clivox-media-vault",
            "private":True,"visibility":"private",
            "owner":{"login":"Tirthanand17"},
            "archived":False,"disabled":False
        }
        r=inspect_private_repo_metadata(repo,expected_full_name=repo["full_name"])
        self.assertTrue(r["vault_metadata_shape_checked"])
        self.assertFalse(r["can_download_copyrighted_media"])
        self.assertFalse(r["owner_approval_verified"])
        self.assertFalse(r["access_control_verified_with_live_api"])
        for change in (
            {"private":False},{"visibility":"public"},
            {"archived":True},{"disabled":True},
            {"full_name":"UnknownOwner/clivox-media-vault"},
        ):
            copy_repo=copy.deepcopy(repo)
            copy_repo.update(change)
            with self.subTest(change=change),self.assertRaises(StorageDenied):
                inspect_private_repo_metadata(copy_repo,
                    expected_full_name=repo["full_name"])

    def test_storage_actions_not_implemented(self):
        with self.assertRaises(StorageDenied):
            check_no_upload_side_effects()

if __name__=="__main__":
    unittest.main()
