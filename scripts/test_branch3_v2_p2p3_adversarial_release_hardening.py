"""Additional adversarial P2/P3 creator-rights tests; strictly offline, no outreach."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import unittest

from scripts.test_branch3_v2_p2p3_pilot_owner_review import inputs, draft, NOW
from scripts.branch3_v2_p2p3_pilot_owner_review import (
    PilotDenied, validate_owner_packet, validate_public_route_audit,
    production_contact_license_or_clip,
)


class AdversarialReleaseHardening(unittest.TestCase):
    def test_deferred_prospect_cannot_gain_download_or_upload_authority(self):
        watch, audit, policy, registry = inputs()
        original = draft()
        for field, value in (
            ("allow_contact", True),
            ("allow_source_download", True),
            ("allow_upload", True),
            ("commercial_youtube_license_granted", True),
            ("actual_signatory_authorized", True),
            ("recipient_address", "injected@example.invalid"),
            ("rights_checklist_pending_count", 0),
        ):
            with self.subTest(field=field):
                packet = copy.deepcopy(original)
                packet["deferred_or_format_only_options"][0][field] = value
                with self.assertRaises(PilotDenied):
                    validate_owner_packet(packet, watchlist=watch,
                                          public_audit=audit, policy=policy,
                                          registry=registry, now=NOW)

    def test_any_prospect_cannot_rebind_to_another_creator(self):
        watch, audit, policy, registry = inputs()
        baseline = draft()
        for group in ("owner_review_first_options",
                      "deferred_or_format_only_options"):
            with self.subTest(group=group):
                forged = copy.deepcopy(baseline)
                forged[group][0]["prospect_id"] = "ankitt_ps5" if group.startswith("deferred") else "caseoh_format"
                with self.assertRaises(PilotDenied):
                    validate_owner_packet(forged, watchlist=watch,
                                          public_audit=audit, policy=policy,
                                          registry=registry, now=NOW)

    def test_provenance_digest_and_research_expiration_cannot_be_forged(self):
        watch, audit, policy, registry = inputs()
        baseline = draft()
        for field, value in (
            ("source_watchlist_sha256", "0" * 64),
            ("public_route_audit_sha256", "f" * 64),
            ("route_research_expires_after_days", 3650),
            ("research_observed_utc", "2030-01-01T00:00:00Z"),
            ("next_step", "AUTO_CONTACT_AND_PUBLISH"),
        ):
            with self.subTest(field=field):
                forged = copy.deepcopy(baseline)
                forged[field] = value
                with self.assertRaises(PilotDenied):
                    validate_owner_packet(forged, watchlist=watch,
                                          public_audit=audit, policy=policy,
                                          registry=registry, now=NOW)

    def test_public_audit_rejects_unknown_fields_and_bools_as_counts(self):
        watch, audit, _, _ = inputs()
        for key, value in (
            ("creator_replies_received", True),
            ("authenticated_commercial_rights_grants", False),
            ("youtube_uploads", False),
            ("route_review_expires_after_days", True),
        ):
            with self.subTest(field=key):
                forged = copy.deepcopy(audit)
                forged[key] = value
                with self.assertRaises(PilotDenied):
                    validate_public_route_audit(forged, watch, now=NOW)
        forged = copy.deepcopy(audit)
        forged["options"][4]["license_approved_by_ai"] = True
        with self.assertRaises(PilotDenied):
            validate_public_route_audit(forged, watch, now=NOW)

    def test_expired_route_stays_blocked_even_if_other_fields_unchanged(self):
        watch, audit, _, _ = inputs()
        with self.assertRaises(PilotDenied):
            validate_public_route_audit(audit, watch, now=NOW + timedelta(days=31))
        with self.assertRaises(PilotDenied):
            validate_public_route_audit(audit, watch,
                                        now=datetime(2026, 11, 13, tzinfo=timezone.utc))

    def test_production_contact_download_and_publish_entrypoint_is_closed(self):
        for kwargs in (
            {"outreach": True},
            {"license_accepted": True, "signed": True},
            {"source_url": "https://example.invalid/media.mp4", "download": True},
            {"privacy": "public", "publish": True},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(PilotDenied):
                production_contact_license_or_clip(**kwargs)


if __name__ == "__main__":
    unittest.main()
