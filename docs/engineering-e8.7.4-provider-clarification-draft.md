# E8.7.4 — Provider clarification draft

**UNSENT LOCAL DRAFT.** No email account accessed, message sent or attachment
uploaded. No personal sender/contact details are included. Full GP values and
original XML remain private; the table contains the identifying metadata needed
to ask about the exact pairs. `REV_AT_EPOCH` is revolution metadata, not a
revision-ranking field.

**To:** Dr. T. S. Kelso, CelesTrak

**Subject:** Historical GP XML for NORAD 35752: empty headers and same-epoch revolution values

Dear Dr. Kelso,

Thank you for fulfilling the historical GP request for NORAD **35752**,
NAVSTAR 64 (USA 206), COSPAR **2009-043A**, for **25–31 December 2023**.
The request was submitted on **24 October 2026 at 18:08:31 UTC**.

The received `sat000035752.xml` contains ten OMM messages, matching the
fulfillment count. The unchanged file is 10,072 bytes, SHA-256:

`c398ecdc707013d0c9bf245b9eeb1894aef1f2a7bafd60f9a687ce797e0a0828`.

All messages contain `<CREATION_DATE/>` and `<ORIGINATOR/>`, present-empty
without `xsi:nil`. The file passes the exact SANA NDM/XML 2.0.0 schema named
by its schema hint. We understand that schema acceptance does not establish
creation history or source provenance.

Direct comparison found two same-epoch pairs:

| Local record ordinal (zero-based index) | EPOCH, explicit TIME_SYSTEM=UTC | NORAD / OBJECT_ID | ELEMENT_SET_NO | REV_AT_EPOCH |
| --------------------------------------- | ------------------------------- | ----------------- | -------------- | ------------ |
| 1 (0)                                   | `2023-12-25T21:13:18.902784`    | 35752 / 2009-043A | `999`          | `10520`      |
| 2 (1)                                   | `2023-12-25T21:13:18.902784`    | 35752 / 2009-043A | `999`          | `10522`      |
| 4 (3)                                   | `2023-12-28T04:47:54.504096`    | 35752 / 2009-043A | `999`          | `10524`      |
| 5 (4)                                   | `2023-12-28T04:47:54.504096`    | 35752 / 2009-043A | `999`          | `10527`      |

These indices identify source order locally, not provider archive IDs. Within
each pair, all other raw fields and XML fragment bytes match, including the
mean elements, drag terms, element-set number, identity and empty headers.
Both members remain preserved; neither has been preferred or merged.

Could you please clarify:

1. Are these two present-empty header fields expected for historical GP XML
   exports of this kind?
2. What do the empty fields mean for message/file creation history and source
   provenance? In particular, how should the export originator be distinguished
   from the underlying element-set producer?
3. If retained, is an authoritative creation timestamp, originator designation,
   underlying archival element record or other record-level provenance available?
   We understand creation timestamps may not be retained; confirmation of that
   limitation is sufficient. Please do not estimate or reconstruct unavailable metadata.
4. What explains the differing `REV_AT_EPOCH` values in these exact same-epoch
   pairs?
5. Should each member be interpreted as a distinct historical element set or
   archive entry, and is any retained identifier or archive metadata available
   to distinguish them?

Our scope is a proposed retrospective comparison of estimated orbit products,
not a historical forecasting or independent-accuracy claim. No propagation or
residual calculation has been performed. We are seeking interpretation of the
original records, not assuming either member is incorrect or requesting new
fitted elements.

Thank you for your guidance.
