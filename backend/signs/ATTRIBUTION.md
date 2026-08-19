# Attribution & data sources

This product uses the following third-party dataset and code assets:

## INCLUDE: A Large Scale Dataset for Indian Sign Language Recognition

* **Authors:** Advaith Sridhar, Rohith Gandhi Ganesan, Pratyush Kumar,
  Mitesh M. Khapra (IIT Madras / AI4Bharat)
* **Paper:** DOI [10.1145/3394171.3413528](https://doi.org/10.1145/3394171.3413528) (ACM Multimedia 2020)
* **Dataset:** [Zenodo record 4010759](https://zenodo.org/records/4010759)
* **License:** [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
* **Sub-set used:** Greetings, Animals, Colours, Pronouns, Days and Time,
  Seasons, Home categories.

Per the CC-BY-4.0 terms, end-users of this app see the following credit
in the footer of the playback screen:

> Sign clips courtesy of the INCLUDE dataset
> (Sridhar et al., ACM MM 2020) — licensed CC-BY-4.0.

The dictionary build script in `signs/build_sign_dictionary.py` is
the only place where the dataset is fetched; nothing is hardcoded
inline.

## spaCy

* **Model:** `en_core_web_sm` 3.8.0
* **License:** MIT
* **Used for:** tokenization, sentence segmentation, lemmatization
  only — no reordering or translation.

## No other third-party data

No webcam-derived data, no user uploads are persisted server-side.
Uploaded story files are parsed in memory and discarded.
