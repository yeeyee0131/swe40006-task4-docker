import argparse
import csv
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


def read_sessions(path):
    sessions = []
    errors = []

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"date", "subject", "hours"}

        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                "CSV must contain these columns: date, subject, hours."
            )

        for line, row in enumerate(reader, start=2):
            try:
                session_date = date.fromisoformat(
                    (row.get("date") or "").strip()
                )
                subject = (row.get("subject") or "").strip()
                hours_text = (row.get("hours") or "").strip()

                if not subject or len(subject) > 60:
                    raise ValueError(
                        "Subject must contain 1 to 60 characters."
                    )

                try:
                    hours = Decimal(hours_text)
                except InvalidOperation:
                    raise ValueError("Hours must be a number.")

                if not hours.is_finite() or not Decimal("0") < hours <= 24:
                    raise ValueError(
                        "Hours must be greater than 0 and at most 24."
                    )

                sessions.append({
                    "date": session_date.isoformat(),
                    "subject": subject,
                    "hours": hours,
                })
            except ValueError as error:
                errors.append(f"Line {line}: {error}")

    if errors:
        raise ValueError(
            "Input validation failed:\n" + "\n".join(errors)
        )

    if not sessions:
        raise ValueError("CSV must contain at least one study session.")

    return sessions


def summarize(sessions):
    totals = {}
    counts = {}

    for session in sessions:
        subject = session["subject"]
        totals[subject] = totals.get(subject, Decimal("0")) + session["hours"]
        counts[subject] = counts.get(subject, 0) + 1

    subjects = [
        {
            "subject": subject,
            "sessions": counts[subject],
            "total_hours": float(hours),
        }
        for subject, hours in sorted(
            totals.items(), key=lambda item: (-item[1], item[0])
        )
    ]

    total_hours = sum(
        (session["hours"] for session in sessions), Decimal("0")
    )

    return {
        "session_count": len(sessions),
        "subject_count": len(subjects),
        "total_hours": float(total_hours),
        "average_session_hours": float(
            round(total_hours / len(sessions), 2)
        ),
        "date_range": {
            "first": min(session["date"] for session in sessions),
            "last": max(session["date"] for session in sessions),
        },
        "subjects": subjects,
    }


def print_summary(summary):
    print("\nTHONGYEE / STUDY HOURS ANALYZER")
    print("SWE40006 - Task 4.4")
    print("=" * 72)
    print(
        f"Period: {summary['date_range']['first']} "
        f"to {summary['date_range']['last']}"
    )
    print(
        f"Sessions: {summary['session_count']}  |  "
        f"Subjects: {summary['subject_count']}  |  "
        f"Total hours: {summary['total_hours']:.2f}"
    )
    print(
        f"Average session: {summary['average_session_hours']:.2f} hours"
    )
    print("-" * 72)
    print(f"{'SUBJECT':<44} {'SESSIONS':>8} {'HOURS':>10}")

    for subject in summary["subjects"]:
        print(
            f"{subject['subject']:<44} "
            f"{subject['sessions']:>8} "
            f"{subject['total_hours']:>10.2f}"
        )

    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze study sessions and export a JSON summary."
    )
    parser.add_argument(
        "--input", required=True, type=Path,
        help="CSV file containing date, subject, hours."
    )
    parser.add_argument(
        "--output", required=True, type=Path,
        help="Destination JSON summary."
    )
    args = parser.parse_args()

    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Input and output must be different files.")

        sessions = read_sessions(args.input)
        summary = summarize(sessions)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        print_summary(summary)
        print(f"JSON summary saved to: {args.output}")
        return 0

    except (OSError, ValueError, csv.Error) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())