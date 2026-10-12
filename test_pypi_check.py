from pypi_check import Result, format_report, parse_requirements, summarize


def test_parse_summarize_format():
    pins, warnings = parse_requirements(
        "# comment\n\nrequests==2.32.5  # inline\nflask>=2\nsix[x]==1.10.0 ; python_version<'4'\n-r other.txt\nfoo===1\n"
    )
    assert pins == [("requests", "2.32.5"), ("six", "1.10.0")]
    assert len(warnings) == 2 and "flask>=2" in warnings[0] and "foo===1" in warnings[1]

    results = [
        Result("requests", "2.32.5", "ok", "2025-08-18T00:00:00"),
        Result("six", "1.10.0", "ok", "2015-10-07T00:00:00"),
        Result("nope", "1.0", "missing_package"),
        Result("requests", "99.0", "missing_version"),
        Result("empty", "1.0", "ok", None),
    ]
    assert format_report(summarize(results)) == (
        "Dependencies checked: 5\n"
        "Packages not on PyPI: 1\n"
        "Version not on PyPI: 1\n"
        "Oldest pinned release: six==1.10.0 (2015)"
    )


if __name__ == "__main__":
    test_parse_summarize_format()
    print("ok")
