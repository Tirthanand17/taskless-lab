"""No secrets, cloud access or media render: 90-video capacity falsification."""
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from math import inf,nan
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_capacity_admission import (
    DAYS,FPS,LANES,FullLengthTrial,ZeroRupeeCapacity,
    evaluate_capacity,workload_manifest,
)

NOW=datetime(2026,10,19,9,tzinfo=timezone.utc)


def valid_trials():
    return tuple(
        FullLengthTrial(
            lane=x.lane,duration_s=x.duration_s,frames=x.duration_s*FPS,
            width=x.width,height=x.height,
            wall_seconds=(24 if x.duration_s==42 else 315),
            final_bytes=(9_000_000 if x.duration_s==42 else 94_000_000),
            peak_memory_mib=(1500 if x.duration_s==42 else 2800),
            video_codec="h264",audio_codec="aac",
            full_decode_passed=True,
            narration_and_caption_qa_passed=True,
            rights_review_passed=True,
            measured_at=NOW-timedelta(hours=5),
        )
        for x in LANES
    )


def claimed_free_capacity():
    return ZeroRupeeCapacity(
        backend="private-verified-zero-overage-worker",
        monthly_render_seconds_available=50_000,
        private_storage_bytes_available=10_000_000_000,
        available_worker_ram_mib=4096,
        monthly_base_cost_inr=0,
        automatic_overage_disabled=True,
        privately_stored_media=True,
        persistent_storage_verified=True,
        free_allowance_independently_verified=True,
        valid_until=NOW+timedelta(days=10),
    )


class ZeroBudgetCapacityTests(unittest.TestCase):
    def test_baseline_month_has_90_full_hd_jobs_not_synthetic_samples(self):
        demand=workload_manifest()
        self.assertEqual(demand["days"],30)
        self.assertEqual(demand["monthly_videos"],90)
        self.assertEqual(demand["monthly_media_seconds"],15480)
        self.assertEqual(demand["monthly_native_hd_frames"],371520)
        self.assertEqual([x["monthly_videos"] for x in demand["lanes"]],
                         [30,30,30])
        self.assertFalse(demand["publishing_authorized"])

    def test_missing_evidence_is_blocked_and_does_not_invent_cost_or_storage(self):
        out=evaluate_capacity((),None,now=NOW)
        self.assertEqual(out["status"],"NO_VERIFIED_ZERO_COST_CAPACITY")
        self.assertEqual(out["assumed_estimate_render_seconds_with_25_percent_headroom"],None)
        self.assertEqual(out["assumed_estimate_private_storage_bytes_two_copies_with_headroom"],None)
        self.assertIn("PROVIDER_ZERO_OVERAGE_CONTRACT_MISSING",out["blocking_reasons"])
        self.assertEqual(len(out["blocking_reasons"]),4)

    def test_full_length_hypothetical_fit_is_not_production_authorization(self):
        out=evaluate_capacity(valid_trials(),claimed_free_capacity(),now=NOW)
        self.assertEqual(out["status"],"HYPOTHETICAL_RESOURCE_FIT_NOT_AUTHORIZED")
        self.assertEqual(out["blocking_reasons"],())
        self.assertGreater(out["assumed_estimate_render_seconds_with_25_percent_headroom"],0)
        self.assertGreater(out["assumed_estimate_private_storage_bytes_two_copies_with_headroom"],0)
        for field in (
            "full_hd_publishing_capacity_verified",
            "licensed_voice_or_rights_verified_by_software",
            "independent_provider_authority_verified_by_software",
            "new_service_connection_authorized",
            "youtube_upload_authorized","publishing_authorized","cloud_deployed",
        ):
            self.assertFalse(out[field])

    def test_short_single_second_frames_do_not_launder_capacity(self):
        cases=list(valid_trials())
        cases[0]=replace(cases[0],duration_s=1,frames=24)
        out=evaluate_capacity(tuple(cases),claimed_free_capacity(),now=NOW)
        self.assertIn("short_en:NOT_FULL_LENGTH_NATIVE_HD",out["blocking_reasons"])
        self.assertFalse(out["publishing_authorized"])

    def test_cloudflare_free_cannot_act_as_native_hd_renderer(self):
        p=replace(claimed_free_capacity(),backend="cloudflare-workers-free")
        out=evaluate_capacity(valid_trials(),p,now=NOW)
        self.assertIn("CLOUDFLARE_FREE_CPU_INSUFFICIENT_FOR_VIDEO_ENCODING",
                      out["blocking_reasons"])
        self.assertFalse(out["full_hd_publishing_capacity_verified"])
        self.assertEqual(out["cloudflare_workers_free_invocation_cpu_ms"],10)

    def test_public_standard_ci_cannot_satisfy_private_upload_storage(self):
        p=replace(claimed_free_capacity(),backend="github-public-standard-ci")
        out=evaluate_capacity(valid_trials(),p,now=NOW)
        self.assertIn("PUBLIC_CI_NOT_AUTHORIZED_FOR_PRIVATE_MEDIA_AND_OAUTH",
                      out["blocking_reasons"])

    def test_paid_overage_missing_private_storage_and_unverified_credits_block(self):
        p=replace(claimed_free_capacity(),
                  monthly_base_cost_inr=25,
                  automatic_overage_disabled=False,
                  privately_stored_media=False,
                  persistent_storage_verified=False,
                  free_allowance_independently_verified=False,
                  valid_until=NOW-timedelta(days=1))
        got=evaluate_capacity(valid_trials(),p,now=NOW)
        self.assertIn("NONZERO_COST_OR_BILLABLE_OVERAGE_NOT_DISABLED",
                      got["blocking_reasons"])
        self.assertIn("ACCOUNT_SPECIFIC_FREE_CAPACITY_NOT_VERIFIED",
                      got["blocking_reasons"])
        self.assertIn("PRIVATE_DURABLE_MEDIA_STORAGE_NOT_VERIFIED",
                      got["blocking_reasons"])

    def test_monthly_render_and_retained_bytes_and_peak_ram_must_fit(self):
        cap=replace(claimed_free_capacity(),
                    monthly_render_seconds_available=1,
                    private_storage_bytes_available=1,
                    available_worker_ram_mib=100)
        issues=evaluate_capacity(valid_trials(),cap,now=NOW)["blocking_reasons"]
        self.assertIn("MONTHLY_RENDER_RUNTIME_ALLOWANCE_INSUFFICIENT",issues)
        self.assertIn("MONTHLY_PRIVATE_STORAGE_ALLOWANCE_INSUFFICIENT",issues)
        self.assertIn("WORKER_PEAK_RAM_ALLOWANCE_INSUFFICIENT",issues)

    def test_trial_freshness_codec_audio_rights_and_captions_fail_closed(self):
        original=valid_trials()
        for update,expected in (
            ({"measured_at":NOW-timedelta(days=15)},"TRIAL_TOO_OLD_OR_FUTURE"),
            ({"measured_at":NOW+timedelta(days=1)},"TRIAL_TOO_OLD_OR_FUTURE"),
            ({"audio_codec":"none"},"FULL_AV_DECODE_NOT_VERIFIED"),
            ({"full_decode_passed":False},"FULL_AV_DECODE_NOT_VERIFIED"),
            ({"narration_and_caption_qa_passed":False},
             "NARRATION_CAPTION_RIGHTS_NOT_VERIFIED"),
            ({"rights_review_passed":False},
             "NARRATION_CAPTION_RIGHTS_NOT_VERIFIED"),
        ):
            with self.subTest(update=update):
                values=(replace(original[0],**update),)+original[1:]
                result=evaluate_capacity(values,claimed_free_capacity(),now=NOW)
                self.assertIn("short_en:"+expected,result["blocking_reasons"])

    def test_duplicate_unknown_invalid_measurements_and_timestamps_refused(self):
        originals=valid_trials()
        wrong=replace(originals[0],lane="new_lane")
        for trials in (
            originals+(originals[0],),
            (originals[0],originals[0],originals[2]),
            (wrong,)+originals[1:],
            list(originals),
        ):
            with self.subTest(value=str(type(trials))),self.assertRaises(WorkflowError):
                evaluate_capacity(trials,claimed_free_capacity(),now=NOW)
        for value in (nan,inf,-inf,True,0,-1):
            with self.subTest(value=value),self.assertRaises(WorkflowError):
                evaluate_capacity(
                    (replace(originals[0],wall_seconds=value),)+originals[1:],
                    claimed_free_capacity(),now=NOW,
                )
        with self.assertRaises(WorkflowError):
            evaluate_capacity(originals,None,now=NOW.replace(tzinfo=None))

    def test_invalid_provider_contract_is_not_silently_coerced(self):
        for changed in (
            {"monthly_base_cost_inr":True},
            {"monthly_render_seconds_available":-1},
            {"available_worker_ram_mib":1.1},
            {"valid_until":NOW.replace(tzinfo=None)},
            {"backend":"unapproved-provider"},
        ):
            with self.subTest(changed=changed),self.assertRaises(WorkflowError):
                evaluate_capacity(
                    valid_trials(),replace(claimed_free_capacity(),**changed),
                    now=NOW,
                )


if __name__=="__main__":
    unittest.main()
