from analyzer.segment_analyzer import SegmentAnalyzer
from models.hierarchy import Hierarchy
from models.url_structure import URLStructure


class HierarchyAnalyzer:

    def __init__(self):
        self.segment_analyzer = SegmentAnalyzer()

    def analyze(
        self,
        url_structure: URLStructure
    ) -> Hierarchy:

        # Normalize URL segments
        segments = self.segment_analyzer.analyze(
            url_structure.segments
        )

        # Handle homepage
        if not segments:

            return Hierarchy(
                root="home",
                entity="home",
                section="home",
                language="",
                leaf="home",
                depth=0
            )

        # Root folder
        root = segments[0]

        # Main entity
        entity = root

        # Language (if present)
        language = ""

        if len(segments) >= 2:
            if segments[1] in ["en", "hi", "fr", "de"]:
                language = segments[1]

        # Section
        if len(segments) >= 3:
            section = segments[-1]

        elif len(segments) == 2:
            section = segments[-1]

        else:
            section = "overview"

        # Last URL segment
        leaf = segments[-1]

        return Hierarchy(
            root=root,
            entity=entity,
            section=section,
            language=language,
            leaf=leaf,
            depth=url_structure.depth
        )