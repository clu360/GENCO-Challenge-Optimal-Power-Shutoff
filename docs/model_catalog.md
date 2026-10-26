# Model Catalog

Actual catalog entries; no native G500 success is inferred from saved epochs.
Weights are acquired from the separate checksum-bound local model bundle.
Texas demo graphs are private pending source permissions. Historical PF models
are represented by recorded Stage L results, not bundled as new fine-tunes.

| Model ID | Family | Role/status | SHA-256 |
|---|---|---|---|
| texas2k.genco_opf.G100 | genco_opf | PASS | `d952811fc2fd329d2ab7c076987dec094c99c6b89036e3053b818afbcc0c4adb` |
| texas2k.genco_opf.G100_to_R400 | genco_opf | PASS | `e64b22da3c8fa92a6c959f355e269e815d2c422bc3809fefa33db47ab11c8bcd` |
| texas2k.genco_opf.G100_to_W400 | genco_opf | PASS | `b4af8c9e6383ff75168b08967a0d7c125653b5dbc432328b53912e7b9aa3da74` |
| texas2k.genco_opf.G500 | genco_opf | PASS | `1e664defde395b77b97e4829bf8e22c3828cbb05da87082aab4b3916a4411ad4` |
| texas2k.opengridsfm.G100 | opengridsfm | PASS | `e45ed36e3956eeb7750d2e396737e0cc3ccd58990aae84b65a6af9d1fdad06d5` |
| texas2k.opengridsfm.G100_to_R400 | opengridsfm | PASS | `0ce7ad4538598f439fff4b59a72e33272f1de193ecaa3dae521c0e3eaceb0cbd` |
| texas2k.opengridsfm.G100_to_W400 | opengridsfm | PASS | `406bb6e4c23c42f1bdf1a682e4213bb64f5fe71f105feebf54b8c6f06508ae0e` |
| texas2k.genco_opf.base | genco_opf | RELEASED_BASE | `158520c976c5a97dbf251cfbd21c985982b3d3cb0e11bbbe96112214bc981343` |
| texas2k.opengridsfm.base | opengridsfm | RELEASED_BASE | `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831` |
| goc500.ft0 | opengridsfm | SMOKE_ONLY | `cf72e0f6036d1e37fb5a298eb3db5e69a6524f48bc7b0b8b5cd34e758ddfe4a2` |
| goc500.m1 | opengridsfm | PUBLISHED_ADAPTATION | `a1378fdaf38af6b317f172c27df7c0f14a23138143d65dfe5e1c46c613e119ad` |
| goc500.m2 | opengridsfm | PUBLISHED_ADAPTATION | `08eda70270f787db42c48b751becc9da2062b0482550a5c2a761b4eba0c94ff6` |
| goc500.m3 | opengridsfm | PUBLISHED_ADAPTATION | `4ec89d36de80081be2fc26c14a1bc5a5369d7423b557d71b9dd4a254462f302d` |
| goc500.base | opengridsfm | RELEASED_BASE | `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831` |
| texas2k.opengridsfm.G500 | opengridsfm | PASS | `2e4911c452dd4a2c80e17ab6f7dc5764150ae6615e3a16404ed9fb82bdeee170` |

Original research checkpoint: `346058115d35b3da234146067e675f31e74d5fae`.

Native G500: certified PASS; native final OPS/AC: pending. Phase II held.
CPU loader/parity evidence and separate fresh-checkout evidence must not be conflated.
