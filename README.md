# evoeng

Digital Extreme Evolution Engine tools.


## cache_extract.py

Extracts a `.cache` and `.toc` file pair.

Example usage:

    $ python cache_extract.py H.Misc.cache

In that instance, the corresponding file `H.Misc.toc` must be in the same directory.
That command will extract and decompress all files in `H.Misc.cache` into a `H.Misc/` directory.

NOTE: Evolution cache files sometimes have conflicting filenames and directory names.
In such instances, a `~` character is appended to the filename.

Example from Warframe:

```
TennoShield
├── ShieldDown
│   ├── ShieldDown
│   ├── ShieldDownLocal
│   ├── TennoHealthPulse
│   ├── TennoHealthPulse.wav
│   └── TennoShieldDown.wav
├── ShieldRecharge
│   ├── ShieldRecharges
│   ├── ShieldRechargesLocal
│   └── TennoShieldUp.wav
├── ShieldRecharge~
└── ShieldRecharge.wav
```
