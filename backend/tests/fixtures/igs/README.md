# E8 deterministic format controls

These are **synthetic test fixtures**, not NASA/IGS products or observations.
`synthetic-final.sp3` has two invented position epochs and two GPS identifiers.
Its fixed-column structure follows the public SP3-c specification and the inspected
`IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz` layout. It is not an excerpt of that
product. The short grid is deliberately incomplete for the nominal daily product.
No test can promote it to scientific approval. Its P records deliberately retain
80 columns, including trailing blanks for flags. The per-file `.gitattributes`
rule records this format requirement; do not trim those columns.

The satellite metadata control uses public identifier facts plus an explicitly
synthetic file header. Tests construct GP format controls from the existing public
Vallado fixture, label them synthetic, and never propagate those inputs. Test-only
positions/sigmas do not constitute an uncertainty estimate or real ephemeris.

Sources: [SP3-c](https://files.igs.org/pub/data/format/sp3c.txt),
[SP3-d field explanations](https://files.igs.org/pub/data/format/sp3d.pdf),
[Metadata SINEX 1.10](https://files.igs.org/pub/resource/working_groups/multi_gnss/Metadata_SINEX_1.10.pdf).

Full acquired products, genuine GP JSON, processing summaries, current ANTEX,
source captures and per-epoch inspection outputs stay under ignored
`data/e8-nasa-igs/` in the E8 worktree. They are absent from Git, Docker contexts
and routine CI. The safe public evidence contains acquisition metadata/hashes and
aggregate qualification facts, without ephemeris coordinates or full GP records.
