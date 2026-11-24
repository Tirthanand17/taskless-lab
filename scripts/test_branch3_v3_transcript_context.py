import unittest

from scripts.branch3_v3_transcript_context import fixture_rows, propose_transcript, refine_candidate, validate


class TranscriptContextTests(unittest.TestCase):
    def test_two_complete_disjoint_proposals(self):
        rows = fixture_rows()
        p = propose_transcript(rows, 80000)
        self.assertEqual([(x["start_ms"],x["end_ms"]) for x in p], [(0,24000),(50000,74000)])
        self.assertTrue(all(x["word_timing_observed"] and not x["quote_verified"]
                            and not x["render_authorized"] and not x["youtube_upload_authorized"]
                            for x in p))

    def test_missing_words_and_no_candidates(self):
        rows = fixture_rows()
        for r in rows:
            r["words"] = []
        self.assertEqual(propose_transcript(rows,80000),[])
        self.assertEqual(propose_transcript([],80000),[])

    def test_context_refine_keeps_anchor(self):
        r = refine_candidate({"start_ms":0,"end_ms":32000,"anchor_ms":12000},fixture_rows(),80000)
        self.assertEqual(r["end_ms"],24000)
        self.assertIsNone(refine_candidate({"start_ms":24000,"end_ms":48000,"anchor_ms":32000},
                                            fixture_rows(),80000))

    def test_invalid_word_times_and_schema(self):
        for key,value in [("end_ms",True),("start_ms",-1),("text",""),("approved",True)]:
            rows = fixture_rows()
            rows[0]["words"][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate(rows,80000)

    def test_invalid_segment_overlap(self):
        rows=fixture_rows()
        rows[1]["start_ms"]=5999
        with self.assertRaises(ValueError):
            validate(rows,80000)

    def test_incomplete_boundaries(self):
        rows=fixture_rows()
        for row in rows:
            row["text"]=row["text"].rstrip(".?")
        self.assertEqual(propose_transcript(rows,80000),[])


if __name__ == "__main__":
    unittest.main()
