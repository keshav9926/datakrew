import argparse
import glob
import json
import sys

from . import process_file


def main(argv=None):
    ap = argparse.ArgumentParser(prog="assigner",
                                 description="assign damages to car parts, one report per photo")
    ap.add_argument("inputs", nargs="+", help="photo json files (globs are fine)")
    ap.add_argument("--out", default="report.json")
    args = ap.parse_args(argv)

    # expand globs ourselves, the windows shell doesn't
    paths = [p for pattern in args.inputs for p in sorted(glob.glob(pattern))]
    if not paths:
        sys.exit("no input files matched")

    reports = []
    for path in paths:
        try:
            r = process_file(path)
        except (ValueError, json.JSONDecodeError, OSError) as e:
            print(f"skipped {path}: {e}", file=sys.stderr)
            continue
        reports.append(r)
        print(f"{r['image_id']}: {len(r['damages'])} damage(s), "
              f"{len(r['summary'])} part/type pair(s), {len(r['warnings'])} warning(s)")

    with open(args.out, "w") as f:
        json.dump(reports, f, indent=2)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
