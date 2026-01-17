class SchemaService:

    @staticmethod
    def to_internal_schema(raw: dict):
        segments = []

        sentiment_map = { }
        if "sentiment_analysis_results" in raw:
            for s in raw["sentiment_analysis_results"]:
                sentiment_map[(s["start"], s["end"])] = s["sentiment"]

        if "words" in raw:
            # Assembly AI gives word-level timestamps
            # We aggregate to sentence-level segments
            segment_text = []
            seg_start = None
            seg_end = None

            for w in raw["words"]:
                text = w["text"]
                start = w["start"]
                end = w["end"]

                if seg_start is None:
                    seg_start = start

                segment_text.append(text)
                seg_end = end

                if text.endswith((".", "?", "!")):
                    sentiment = None
                    for (s_start, s_end), s_val in sentiment_map.items():
                        if seg_start >= s_start and seg_end <= s_end:
                            sentiment = s_val
                            break

                    segments.append({
                        "text": " ".join(segment_text),
                        "start": seg_start,
                        "end": seg_end,
                        "sentiment": sentiment
                    })

                    segment_text = []
                    seg_start = None
                    seg_end = None

        return {"segments": segments}
