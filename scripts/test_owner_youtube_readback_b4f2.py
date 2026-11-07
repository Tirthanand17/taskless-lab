"""B4f2 offline injected YouTube API client tests; never real OAuth or upload."""
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import Mock

from scripts.owner_youtube_readback_b4f2 import (
    OwnerYouTubeReadbackRefused, verify_authenticated_owner_channel,
    verify_processed_private_schedule_and_caption,
)

CHANNEL="UC"+"X"*22
OTHER="UC"+"Y"*22
VIDEO="Abc123Def_9"
CAPTION="caption123abc"
WHEN="2026-11-08T05:30:00Z"
TITLE="Original science educational explainer"
DESC="Research-backed educational narration and visual reference."
LANGUAGE="en"


def youtube_fake(channel=CHANNEL):
    service=Mock()
    service.channels.return_value.list.return_value.execute.return_value={
        "items":[{"id":channel}],"pageInfo":{"totalResults":1},
    }
    service.videos.return_value.list.return_value.execute.return_value={
        "items":[{
            "id":VIDEO,
            "snippet":{"channelId":CHANNEL,"title":TITLE,"description":DESC},
            "status":{"privacyStatus":"private","publishAt":WHEN,
                      "uploadStatus":"processed",
                      "selfDeclaredMadeForKids":False,
                      "containsSyntheticMedia":True},
            "processingDetails":{"processingStatus":"succeeded"},
            "contentDetails":{"hasCustomThumbnail":True},
        }],
    }
    service.captions.return_value.list.return_value.execute.return_value={
        "items":[{"id":CAPTION,
                  "snippet":{"videoId":VIDEO,"language":"en",
                             "status":"serving","isDraft":False}}],
    }
    return service


def check(service,**overrides):
    args=dict(video_id=VIDEO,expected_channel_id=CHANNEL,
              expected_publish_at=WHEN,expected_title=TITLE,
              expected_description=DESC,expected_language=LANGUAGE,
              expected_caption_id=CAPTION,
              expected_synthetic_disclosure=True,expected_made_for_kids=False)
    return verify_processed_private_schedule_and_caption(service,**{**args,**overrides})


class OwnerIdentityBeforeUploadTests(unittest.TestCase):
    def test_exact_authenticated_oauth_channel_success(self):
        service=youtube_fake()
        output=verify_authenticated_owner_channel(service,CHANNEL)
        self.assertEqual(output["authenticated_channel_id"],CHANNEL)
        self.assertFalse(output["videos_insert_executed_by_this_function"])
        service.channels.return_value.list.assert_called_once_with(
            part="id",mine=True,maxResults=2)
        service.videos.assert_not_called()
        service.captions.assert_not_called()

    def test_wrong_channel_must_never_start_insert(self):
        service=youtube_fake(channel=OTHER)
        with self.assertRaises(OwnerYouTubeReadbackRefused):
            verify_authenticated_owner_channel(service,CHANNEL)
        service.videos.assert_not_called()

    def test_no_owner_two_owners_and_pagination_refused(self):
        for response in (
            {"items":[]},
            {"items":[{"id":CHANNEL},{"id":OTHER}]},
            {"items":[{"id":CHANNEL}],"nextPageToken":"other"},
            {"items":[{"id":CHANNEL}],"pageInfo":{"totalResults":2}},
            {"items":[{"id":CHANNEL}],"pageInfo":{"totalResults":True}},
            {"items":[{"id":CHANNEL}],"pageInfo":{"totalResults":"1"}},
            {"items":"not a list"},
            None,
        ):
            service=youtube_fake()
            service.channels.return_value.list.return_value.execute.return_value=response
            with self.subTest(response=response),self.assertRaises(OwnerYouTubeReadbackRefused):
                verify_authenticated_owner_channel(service,CHANNEL)
            service.videos.assert_not_called()

    def test_missing_permission_or_network_failure_refused_without_leaking(self):
        service=youtube_fake()
        service.channels.return_value.list.return_value.execute.side_effect=RuntimeError(
            "OAuth bearer token 123 should not be logged")
        with self.assertRaises(OwnerYouTubeReadbackRefused) as caught:
            verify_authenticated_owner_channel(service,CHANNEL)
        self.assertNotIn("bearer",str(caught.exception).lower())
        service.videos.assert_not_called()


class PostInsertProcessedReadbackTests(unittest.TestCase):
    def test_exact_private_processed_thumbnail_and_uploaded_caption_id(self):
        service=youtube_fake()
        output=check(service)
        self.assertTrue(output["authenticated_video_and_caption_api_readback"])
        self.assertFalse(output["actually_publicly_published"])
        self.assertFalse(output["actual_caption_text_independently_downloaded"])
        self.assertFalse(output["youtube_release_authorized_by_this_function"])
        service.videos.return_value.list.assert_called_once_with(
            part="snippet,status,processingDetails,contentDetails",id=VIDEO)
        service.captions.return_value.list.assert_called_once_with(
            part="snippet",videoId=VIDEO)

    def test_wrong_video_channel_and_future_slot_never_verify(self):
        for loc,bad in (
            ("id","AAAAAAAAAAA"),
            ("channelId",OTHER),
            ("title","Changed title"),
            ("description","Changed description"),
            ("privacyStatus","public"),
            ("privacyStatus","unlisted"),
            ("publishAt","2026-11-08T10:30:00Z"),
        ):
            service=youtube_fake()
            v=service.videos.return_value.list.return_value.execute.return_value["items"][0]
            mapping = v if loc=="id" else (
                v["snippet"] if loc in ("channelId","title","description") else v["status"])
            mapping[loc]=bad
            with self.subTest(loc=loc,bad=bad),self.assertRaises(OwnerYouTubeReadbackRefused):
                check(service)

    def test_uploaded_but_not_processed_or_failed_transcode_blocks_receipt(self):
        for state in ("processing","failed","terminated",None):
            service=youtube_fake()
            v=service.videos.return_value.list.return_value.execute.return_value["items"][0]
            v["processingDetails"]["processingStatus"]=state
            with self.subTest(state=state),self.assertRaises(OwnerYouTubeReadbackRefused):
                check(service)
        service=youtube_fake()
        v=service.videos.return_value.list.return_value.execute.return_value["items"][0]
        v["status"]["uploadStatus"]="uploaded"
        with self.assertRaises(OwnerYouTubeReadbackRefused):
            check(service)

    def test_thumbnail_disclosure_and_kids_mismatch_fail(self):
        for path,value in (
            ("hasCustomThumbnail",False),
            ("hasCustomThumbnail",None),
            ("containsSyntheticMedia",False),
            ("selfDeclaredMadeForKids",True),
        ):
            service=youtube_fake()
            v=service.videos.return_value.list.return_value.execute.return_value["items"][0]
            target=v["contentDetails"] if path=="hasCustomThumbnail" else v["status"]
            target[path]=value
            with self.subTest(path=path,value=value),self.assertRaises(OwnerYouTubeReadbackRefused):
                check(service)

    def test_missing_or_wrong_or_not_serving_caption_id_never_verify(self):
        for status in ("syncing","failed",None):
            service=youtube_fake()
            c=service.captions.return_value.list.return_value.execute.return_value["items"][0]
            c["snippet"]["status"]=status
            with self.subTest(status=status),self.assertRaises(OwnerYouTubeReadbackRefused):
                check(service)
        for key,value in (
            ("id","captionNEW"),
            ("videoId","BBBBBBBBBBB"),
            ("language","hi"),
            ("isDraft",True),
        ):
            service=youtube_fake()
            c=service.captions.return_value.list.return_value.execute.return_value["items"][0]
            (c if key=="id" else c["snippet"])[key]=value
            with self.subTest(key=key),self.assertRaises(OwnerYouTubeReadbackRefused):
                check(service)

    def test_youtube_readback_error_is_redacted_and_no_new_insert(self):
        service=youtube_fake()
        service.captions.return_value.list.return_value.execute.side_effect=RuntimeError(
            "private refresh token leaked")
        with self.assertRaises(OwnerYouTubeReadbackRefused) as caught:
            check(service)
        self.assertNotIn("refresh token",str(caught.exception))
        service.videos.return_value.insert.assert_not_called()

    def test_publisher_orders_identity_before_tag_and_insert(self):
        src=(Path(__file__).resolve().parent/"publish_youtube.py").read_text()
        self.assertLess(src.index("verify_authenticated_owner_channel("),
                        src.index("reserve_github_attempt_before_insert("))
        self.assertLess(src.index("verify_authenticated_owner_channel("),
                        src.index("req=youtube.videos().insert("))
        self.assertLess(src.index("req=youtube.videos().insert("),
                        src.index("verify_processed_private_schedule_and_caption("))
        self.assertIn("expected_caption_id=caption_id",src)
        self.assertIn('status.get("uploadStatus")=="processed"',(Path(
            __file__).resolve().parent/"owner_youtube_readback_b4f2.py").read_text())


if __name__=="__main__":
    unittest.main()
