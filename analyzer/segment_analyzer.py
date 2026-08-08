class SegmentAnalyzer:

    def analyze(self, segments):

        cleaned = []

        for segment in segments:

            cleaned.append(
                segment
                .lower()
                .replace("-", "_")
                .replace("%20", "_")
            )

        return cleaned