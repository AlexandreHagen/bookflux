import json

from bookflux.output_utils import FormattingIssue, FormattingIssueReport, write_formatting_report


def test_write_formatting_report(tmp_path) -> None:
    report = FormattingIssueReport(
        run_id="run-1",
        issues=[
            FormattingIssue(
                page_number=1,
                issue_type="truncation",
                description="Text truncated.",
                severity="high",
            )
        ],
        summary={"truncation": 1},
    )
    output_path = tmp_path / "report.json"
    write_formatting_report(report, str(output_path))

    data = json.loads(output_path.read_text())
    assert data["run_id"] == "run-1"
    assert data["summary"]["truncation"] == 1
    assert data["issues"][0]["severity"] == "high"


def test_formatting_report_deterministic(tmp_path) -> None:
    issues = [
        FormattingIssue(
            page_number=2,
            issue_type="font_scaled_down",
            description="Font size reduced.",
            severity="medium",
        ),
        FormattingIssue(
            page_number=1,
            issue_type="truncation",
            description="Text truncated.",
            severity="high",
        ),
    ]
    report_a = FormattingIssueReport(
        run_id="run-a",
        issues=issues,
        summary={"font_scaled_down": 1, "truncation": 1},
    )
    report_b = FormattingIssueReport(
        run_id="run-a",
        issues=issues,
        summary={"truncation": 1, "font_scaled_down": 1},
    )

    path_a = tmp_path / "report-a.json"
    path_b = tmp_path / "report-b.json"
    write_formatting_report(report_a, str(path_a))
    write_formatting_report(report_b, str(path_b))

    assert path_a.read_text() == path_b.read_text()
