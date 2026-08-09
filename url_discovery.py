from urllib.parse import urljoin, urlparse

from crawler.url_normalizer import normalize_url
from crawler.url_validator import is_valid_url
from crawler.url_classifier import classify_url
from models.navigation import NavigationCandidate, NavigationNode
from models.url import URLInfo


class URLDiscovery:

    def discover(
        self,
        candidates: list[NavigationCandidate],
        source_url: str,
    ) -> list[URLInfo]:

        discovered: list[URLInfo] = []
        seen: set[str] = set()

        base_domain = urlparse(source_url).netloc

        for candidate in candidates:

            for node in candidate.tree:

                self._collect_node(
                    node=node,
                    source_url=source_url,
                    base_domain=base_domain,
                    discovered=discovered,
                    seen=seen,
                )

        return discovered

    def _collect_node(
        self,
        node: NavigationNode,
        source_url: str,
        base_domain: str,
        discovered: list[URLInfo],
        seen: set[str],
    ) -> None:

        raw_href = node.href.strip()

        if raw_href:

            # Ignore non-navigation links before URL resolution.
            if not (
                raw_href == "#"
                or raw_href.startswith(
                    (
                        "javascript:",
                        "mailto:",
                        "tel:",
                    )
                )
            ):

                absolute_url = urljoin(
                    source_url,
                    raw_href,
                )

                normalized = normalize_url(
                    absolute_url,
                )

                if is_valid_url(normalized):

                    url_info = classify_url(
                        raw_url=raw_href,
                        normalized_url=normalized,
                        base_domain=base_domain,
                        discovered_from=source_url,
                    )

                    if normalized not in seen:

                        discovered.append(
                            url_info
                        )

                        seen.add(
                            normalized
                        )

        # Always process children, even if the
        # current navigation node has an invalid href.
        for child in node.children:

            self._collect_node(
                node=child,
                source_url=source_url,
                base_domain=base_domain,
                discovered=discovered,
                seen=seen,
            )