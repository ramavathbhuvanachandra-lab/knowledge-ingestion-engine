from crawler.depth_tracker import DepthTracker


ROOT = "https://example.com/"
A = "https://example.com/a"
B = "https://example.com/b"
C = "https://example.com/c"
D = "https://example.com/d"


def test_cycle_does_not_change_existing_depth():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    tracker.register_child(A, ROOT)
    tracker.register_child(B, A)
    tracker.register_child(C, B)

    # Cycle:
    # C -> A
    depth = tracker.register_child(A, C)

    assert depth == 1
    assert tracker.get_depth(A) == 1
    assert tracker.get_depth(B) == 2
    assert tracker.get_depth(C) == 3


def test_duplicate_discovery_from_deeper_parent():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    tracker.register_child(A, ROOT)
    tracker.register_child(B, A)
    tracker.register_child(C, B)

    # C discovers A again.
    depth = tracker.register_child(A, C)

    assert depth == 1


def test_duplicate_discovery_from_shallower_parent():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    tracker.register_child(A, ROOT)
    tracker.register_child(B, A)

    # B is already depth 2.
    # Attempt to rediscover B directly from root.
    depth = tracker.register_child(B, ROOT)

    assert depth == 2
    assert tracker.get_depth(B) == 2


def test_root_cannot_become_deeper():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    tracker.register_child(A, ROOT)

    # A discovers the root again.
    depth = tracker.register_child(ROOT, A)

    assert depth == 0
    assert tracker.get_depth(ROOT) == 0


def test_repeated_root_registration():

    tracker = DepthTracker()

    assert tracker.register_root(ROOT) == 0
    assert tracker.register_root(ROOT) == 0

    assert tracker.size() == 1


def test_empty_url_is_not_registered():

    tracker = DepthTracker()

    assert tracker.register_root("") == 0

    assert tracker.contains("") is True


def test_large_linear_chain():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    parent = ROOT

    urls = []

    for index in range(1, 1001):

        url = f"https://example.com/page/{index}"

        depth = tracker.register_child(
            url,
            parent,
        )

        assert depth == index

        urls.append(url)

        parent = url

    assert tracker.size() == 1001

    assert tracker.get_depth(urls[-1]) == 1000


def test_branching_tree():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    tracker.register_child(A, ROOT)
    tracker.register_child(B, ROOT)

    tracker.register_child(C, A)
    tracker.register_child(D, B)

    assert tracker.get_depth(ROOT) == 0
    assert tracker.get_depth(A) == 1
    assert tracker.get_depth(B) == 1
    assert tracker.get_depth(C) == 2
    assert tracker.get_depth(D) == 2


def test_same_url_with_different_string_identity():

    tracker = DepthTracker()

    tracker.register_root(
        "https://example.com"
    )

    tracker.register_child(
        "https://example.com/",
        "https://example.com",
    )

    # DepthTracker deliberately operates on
    # normalized URLs supplied by the caller.
    assert tracker.get_depth(
        "https://example.com/"
    ) == 1

    assert tracker.get_depth(
        "https://example.com"
    ) == 0


def test_unknown_parent_starts_child_at_one():

    tracker = DepthTracker()

    depth = tracker.register_child(
        A,
        "https://unknown.example.com/",
    )

    assert depth == 1
    assert tracker.get_depth(A) == 1


def test_depth_values_are_non_negative():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    tracker.register_child(A, ROOT)
    tracker.register_child(B, A)
    tracker.register_child(C, B)

    for url in (
        ROOT,
        A,
        B,
        C,
    ):

        depth = tracker.get_depth(url)

        assert depth is not None
        assert depth >= 0


def test_many_duplicate_discoveries():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    tracker.register_child(A, ROOT)
    tracker.register_child(B, A)

    for _ in range(1000):

        assert (
            tracker.register_child(
                B,
                ROOT,
            )
            == 2
        )

    assert tracker.size() == 3


if __name__ == "__main__":

    test_cycle_does_not_change_existing_depth()
    test_duplicate_discovery_from_deeper_parent()
    test_duplicate_discovery_from_shallower_parent()
    test_root_cannot_become_deeper()
    test_repeated_root_registration()
    test_empty_url_is_not_registered()
    test_large_linear_chain()
    test_branching_tree()
    test_same_url_with_different_string_identity()
    test_unknown_parent_starts_child_at_one()
    test_depth_values_are_non_negative()
    test_many_duplicate_discoveries()

    print("DEPTH TRACKER ADVERSARIAL TESTS: PASS")
    