"""Phase 4E.5: synthetic uploads playlist vs videos.list completeness tests."""
from copy import deepcopy
import unittest

from autopilot.core import CHANNEL_ID
from autopilot.phase4b_readonly_audit import AuditBlocked
from autopilot.phase4e5_upload_playlist_crosscheck import (
    assemble_untrusted_uploads_with_video_details as join,
)
from autopilot.phase4e2_signed_snapshot_bridge import _checked_youtube

UP="UU1234567890abcde"
V1="abc123def45"
V2="abc123def46"
CHAN={"items":[{"id":CHANNEL_ID,
                "contentDetails":{"relatedPlaylists":{"uploads":UP}},
                "snippet":{"title":"PRIVATE CHANNEL"}}]}

def pli(vid):
    return {"contentDetails":{"videoId":vid},
            "snippet":{"channelId":CHANNEL_ID,"title":"PRIVATE PLAYLIST TITLE"}}

def detail(vid):
    return {"id":vid,
            "snippet":{"channelId":CHANNEL_ID,"title":"PRIVATE VIDEO"},
            "status":{"privacyStatus":"private"},
            "processingDetails":{"processingStatus":"succeeded"},
            "description":"PRIVATE DESCRIPTION"}

def pl(ids,*,req=None,nxt=None,playlist=UP):
    response={"items":[pli(i) for i in ids]}
    if nxt is not None:response["nextPageToken"]=nxt
    return {"playlist_id":playlist,"requested_page_token":req,"response":response}

def batch(ids,items=None):
    return {"requested_video_ids":list(ids),
            "response":{"items":[detail(i) for i in ids] if items is None else items}}

def audit(pages=None,batches=None,channel=None):
    return join(channel_response=CHAN if channel is None else channel,
                playlist_pages=[pl([V1])] if pages is None else pages,
                video_detail_batches=[batch([V1])] if batches is None else batches)


class UploadedVideoCrosswalkTests(unittest.TestCase):
    def test_exact_one_video_and_compatible_signed_bridge_shape(self):
        r=audit()
        self.assertEqual(r["video_count"],1)
        self.assertTrue(r["pagination_complete"])
        self.assertEqual(_checked_youtube(r),(1,0,False))
        for secret in (UP,"PRIVATE CHANNEL","PRIVATE PLAYLIST TITLE",
                       "PRIVATE VIDEO","PRIVATE DESCRIPTION"):
            self.assertNotIn(secret,str(r))
        self.assertFalse(r["saw_authenticated_provider_request"])
        self.assertFalse(r["publication_authorized"])
        self.assertEqual(r["network_calls"],0)
        self.assertEqual(r["production_writes"],0)

    def test_two_pages_and_two_batches_out_of_order(self):
        r=audit(pages=[pl([V1],nxt="p2"),pl([V2],req="p2")],
                batches=[batch([V2]),batch([V1])])
        self.assertEqual([x["youtube_id"] for x in r["videos"]],[V1,V2])
        self.assertEqual(_checked_youtube(r),(2,0,False))

    def test_single_batch_of_multiple_video_ids(self):
        r=audit(pages=[pl([V1,V2])],batches=[batch([V2,V1])])
        self.assertEqual(r["video_count"],2)

    def test_empty_uploads_is_not_authenticated_proof(self):
        r=audit(pages=[pl([])],batches=[])
        self.assertEqual(_checked_youtube(r),(0,0,False))
        self.assertFalse(r["saw_authenticated_provider_request"])

    def test_missing_last_page_fails(self):
        with self.assertRaisesRegex(AuditBlocked,"Incomplete uploads"):
            audit(pages=[pl([V1],nxt="next")])

    def test_reordered_duplicate_or_terminal_pages_fail(self):
        bad=[
            [pl([V1],nxt="next"),pl([V2],req="different")],
            [pl([V1],nxt="next"),pl([V2],req="next",nxt="next")],
            [pl([V1]),pl([V2])],
            [pl([V1],nxt="next"),pl([V1],req="next")],
        ]
        for pages in bad:
            with self.subTest(pages=pages),self.assertRaises(AuditBlocked):
                audit(pages=pages)

    def test_missing_deleted_private_video_detail_fails(self):
        with self.assertRaisesRegex(AuditBlocked,"Missing, deleted"):
            audit(batches=[batch([V1],items=[])])

    def test_extra_detail_id_not_uploaded_fails(self):
        with self.assertRaises(AuditBlocked):
            audit(batches=[batch([V2])])
        with self.assertRaises(AuditBlocked):
            audit(batches=[batch([V1],items=[detail(V2)])])

    def test_missing_batch_from_uploaded_set_fails(self):
        with self.assertRaisesRegex(AuditBlocked,"not fully reconciled"):
            audit(pages=[pl([V1,V2])],batches=[batch([V1])])

    def test_duplicate_requested_batches_fail(self):
        with self.assertRaises(AuditBlocked):
            audit(batches=[batch([V1]),batch([V1])])

    def test_unexpected_channel_in_channel_or_playlist_fails(self):
        wrong=deepcopy(CHAN)
        wrong["items"][0]["id"]="wrong"
        with self.assertRaises(AuditBlocked):audit(channel=wrong)
        with self.assertRaises(AuditBlocked):
            audit(pages=[pl([V1],playlist="UU9999999999abcde")])
        broken=pli(V1)
        broken["snippet"]["channelId"]="wrong"
        with self.assertRaises(AuditBlocked):
            audit(pages=[{"playlist_id":UP,"requested_page_token":None,
                          "response":{"items":[broken]}}])

    def test_wrong_video_owner_fails(self):
        v=detail(V1)
        v["snippet"]["channelId"]="wrong"
        with self.assertRaises(AuditBlocked):
            audit(batches=[batch([V1],items=[v])])

    def test_missing_upload_playlist_id_fails(self):
        c=deepcopy(CHAN)
        del c["items"][0]["contentDetails"]
        with self.assertRaises(AuditBlocked):audit(channel=c)

    def test_oversized_input_fails(self):
        with self.assertRaises(AuditBlocked):
            audit(pages=[pl([V1]*51)])
        with self.assertRaises(AuditBlocked):
            audit(batches=[batch([V1]*51)])

    def test_13_page_chain_fails(self):
        pages=[pl([],req=None if i==0 else f"tok_{i}",
                  nxt=None if i==12 else f"tok_{i+1}") for i in range(13)]
        with self.assertRaises(AuditBlocked):audit(pages=pages)

    def test_unknown_processing_fails_open_as_uncertainty_not_approval(self):
        v=detail(V1)
        del v["processingDetails"]
        result=audit(batches=[batch([V1],items=[v])])
        self.assertEqual(_checked_youtube(result),(1,1,False))
        self.assertFalse(result["publication_authorized"])

    def test_secret_bearing_batch_wrapper_rejected(self):
        bad=batch([V1])
        bad["refresh_token"]="secret"
        with self.assertRaises(AuditBlocked):audit(batches=[bad])

    def test_fake_provider_validation_flag_ignored(self):
        pages=[pl([V1])]
        pages[0]["response"]["verified"]=True
        result=audit(pages=pages)
        self.assertFalse(result["saw_authenticated_provider_request"])

    def test_deterministic_redacted_snapshot(self):
        self.assertEqual(audit(),audit(pages=deepcopy([pl([V1])]),
                                       batches=deepcopy([batch([V1])])))

if __name__=="__main__":
    unittest.main()
