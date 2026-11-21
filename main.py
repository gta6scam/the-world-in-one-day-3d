#!/usr/bin/env python3
"""Hand-in program for 'THE WORLD IN ONE DAY' (news-image-20261120,
@yutulboy, challenger-a2 correction build).

The graded contract: deliver the finished 1024x1024 page committed beside
this file as entry.png into the output directory. This program only copies
that file, so it runs identically anywhere - including the grader's
sandbox, where the repository sits alone and read-only. The generative
builder is preserved as draw.py and is never the hand-in.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    src = os.path.join(HERE, "entry.png")
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)
    # delivery proof: report the byte size actually handed in
    print("entry.png ->", dst, os.path.getsize(dst), "bytes")


if __name__ == "__main__":
    main()
