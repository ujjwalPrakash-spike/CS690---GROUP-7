"""Download the two sections used here into data/.

STARmap BZ5, BZ9 and BZ14 (mouse mPFC, Wang et al. 2018) as shipped in the LLMiniST repository,
and the MERFISH Bregma -0.14 section (mouse hypothalamic preoptic area, Moffitt et al. 2018) as an h5ad.
"""
import os
import urllib.request

from common import DATA

STARMAP_URL = "https://raw.githubusercontent.com/wJDKnight/LLMiniST/main/examples/starmap/{}/{}.csv"
MERFISH_URL = "https://ndownloader.figshare.com/files/40038532"


def get(url, path):
    if os.path.exists(path):
        print("have", path)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print("downloading", url)
    urllib.request.urlretrieve(url, path)


if __name__ == "__main__":
    for sample in ("BZ5", "BZ9", "BZ14"):
        for part in ("celltype", "pos", "domain", "data"):
            get(STARMAP_URL.format(sample, part), os.path.join(DATA, "starmap", sample, f"{part}.csv"))
    get(MERFISH_URL, os.path.join(DATA, "merfish.h5ad"))
