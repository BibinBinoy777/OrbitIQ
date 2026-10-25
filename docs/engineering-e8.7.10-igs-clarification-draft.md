# E8.7.10 — IGS technical clarification draft

**UNSENT LOCAL DRAFT.** No message was sent and no provider response is recorded.
Intended routing: IGS Analysis Center Coordinator / ERP product-format maintainer;
verify the current public contact route before sending. No contact address or
private attachment is supplied here.

Subject: Epoch scale, zero fields and interpolation conventions for week-2295 IGS final ERP

Dear IGS ERP/product-format team,

We are qualifying a historical reference product for a proposed retrospective
comparison of SGP4/TEME calculated states with IGS final orbit coordinates:

`IGS0OPSFIN_20233650000_07D_01D_ERP.ERP.gz`

It was retrieved anonymously from
`https://igs.bkg.bund.de/root_ftp/IGS/products/2295/IGS0OPSFIN_20233650000_07D_01D_ERP.ERP.gz`
with HTTPS 200, completed **2026-10-25T07:29:00.340641Z**. Compressed size is
**419 bytes**, SHA-256
`2a201026f27e1265e77b9af8b81636bca0b0dfbf425ca4de0797ee5e587b1fd3`.
The associated orbit reference is
`IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz`, declaring IGS20/GPS.

The ERP begins `version 2` / `EOP  SOLUTION`, with seven daily MJD tags
`60309.50` through `60315.50`. We consulted IGSMAIL-1943, the official
`erp.txt`, the IGS products page (final daily integrations at 12 UTC), and the
week-2295 combination summary. We distinguish that operational sampling guidance
from an explicit definition of this file's MJD independent variable.

Could you clarify, with an applicable product-era reference where possible:

1. **Epoch scale:** what time scale applies to the MJD tags in this exact
   operational final product? Does the fractional field represent that scale
   directly, so `.50` denotes noon on that scale? Are these tags solution
   reference epochs, daily-arc midpoints or another convention? How should they
   relate to the filename's nominal midnight start and the SP3 GPS-time epochs?
   We have not inferred UTC solely from the `UT1-UTC` quantity label.
2. **Fields and zeros:** all seven rows have zero `UTsig`, `Nr`, `Nf`, `Nt`,
   `dpsi` and `deps`. Are these estimated numerical zeros, unavailable/unestimated
   fields, placeholders or something else? Please identify the definition and
   angular units/reference model for the extra `dpsi/deps` columns; the final
   unit token is only `10**-6`. The count columns are not being described as
   optional merely because they contain zeros.
3. **Interpolation and time handling:** what adjacent-sample interpolation,
   pole-rate/LOD use, leap-discontinuity treatment and boundary policy are
   recommended for this product? Does `LOD` use precisely the convention and
   `0.1 us/day` scaling printed in the header/specification? We intend to retain
   the fractional tags and prohibit extrapolation, rather than shifting noon
   records to midnight.
4. **Regularization/subdaily conventions:** which ocean-tide, diurnal/semidiurnal
   libration and long-period terms are removed, retained or expected to be
   restored in these 2024 ERP values? Please identify exact model/routine versions
   and time arguments, and the relationship to the associated final orbit/SINEX
   solution. We want to prevent double counting and distinguish the 2009 IGS
   guide / approved IERS Conventions (2010) from exact operational settings.
5. **Terrestrial alignment/TIO:** our existing Astropy **7.2.3** TEME→ITRS path
   follows Vallado, using GMST82(UT1), polar motion and zero TIO locator s′.
   Is there an authoritative product-era reference that helps qualify the TIO
   and terrestrial-convention treatment for comparison with IGS20? We are seeking
   the required conventions, not assuming that a matched ERP file validates or
   endorses this software chain.

No real-input propagation, spacecraft transformation, real ERP interpolation,
residual calculation or scientific uncertainty estimate has been performed.
The study remains BLOCKED while these and other essential qualifications are
unresolved. A separate prototype has been tested only on invented values on an
abstract fractional-MJD axis; it is not connected to our active EOP path.

Thank you for any clarification or references.
