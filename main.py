#!/usr/bin/env python3
"""Entry program for make.fun bounty news-image-20261120.

Standard library only: copies the pre-rendered entry.png (drawn by draw.py)
to the output directory the harness names.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(os.path.join(HERE, "entry.png"),
                    os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
