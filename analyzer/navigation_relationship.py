def calculate_containment(
    links_a,
    links_b
):

    set_a = set(links_a)
    set_b = set(links_b)

    if not set_a or not set_b:
        return 0.0

    intersection = set_a & set_b

    smaller_size = min(
        len(set_a),
        len(set_b)
    )

    return len(intersection) / smaller_size


def calculate_coverage(
    links_a,
    links_b
):

    set_a = set(links_a)
    set_b = set(links_b)

    if not set_a or not set_b:
        return 0.0

    intersection = set_a & set_b

    larger_size = max(
        len(set_a),
        len(set_b)
    )

    return len(intersection) / larger_size


def determine_relationship(
    links_a,
    links_b
):

    if not links_a or not links_b:
        return "unrelated"

    set_a = set(links_a)
    set_b = set(links_b)

    if set_a == set_b:
        return "duplicate"

    containment = calculate_containment(
        links_a,
        links_b
    )

    coverage = calculate_coverage(
        links_a,
        links_b
    )

    # One candidate is completely contained
    # inside the other.
    if containment == 1.0:
        return "subset"

    # There is meaningful overlap,
    # but neither candidate contains
    # the other completely.
    if coverage > 0.0:
        return "overlap"

    return "unrelated"