"""Download the four datasets (SDMBench h5ad files on figshare) into data/."""
import os
import urllib.request

from common import DATA, FILES

URLS = {
    "dlpfc": "https://ndownloader.figshare.com/files/40016365",    # Visium DLPFC 151673 (Maynard et al. 2021)
    "smi": "https://ndownloader.figshare.com/files/40016455",      # CosMx SMI lung tumour, slice global_z0 (He et al. 2022)
    "merfish": "https://ndownloader.figshare.com/files/40038532",  # MERFISH hypothalamus, Bregma -0.14 (Moffitt et al. 2018)
    "starmap": "https://ndownloader.figshare.com/files/40038637",  # STARmap mouse cortex, BZ5 (Wang et al. 2018)
}

if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    for name, url in URLS.items():
        path = os.path.join(DATA, FILES[name])
        if os.path.exists(path):
            print("have", path)
            continue
        print("downloading", name, "from", url)
        urllib.request.urlretrieve(url, path)
