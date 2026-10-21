# Corrected historical GP export — submitted, awaiting response

**SUBMITTED — user-reported in the interim milestone request.** The user reports
manually emailing CelesTrak for the corrected export. The submission timestamp
was not supplied and remains unknown. This task did not send email, submit a form,
complete CAPTCHA or authenticate to a provider. The corrected attachment is
**AWAITING RESPONSE**; the private intake inventory still contains only the
original rejected attachment. Real replacement reconciliation is **NOT STARTED**,
and scientific qualification remains **PARTIAL**, with evaluation blocked.

The prepared wording below is retained as a record. Submission is recorded from
the user's statement, not independently authenticated email headers. No private
email contents or contact details are included. The original historical request's
timestamp below identifies that earlier request, not this correction submission.

Identify the existing request as **2026-10-21T06:10:16Z**, SWARM A, NORAD **39452**,
international designator **2013-067B**, period **2013-12-30 through 2014-01-02**.
Expected count: **three**, subject to provider confirmation. Original filename:
`sat000039452.json`, 1,227 bytes, SHA-256
`c55dc4cbb2331a162014833a1a354e6f62ff4572d5238954b8108f69cae3053c`.
The original remains private and unchanged. Do not paste correspondence or contact
details into Git. Use personal contact information only in the provider's workflow.

Suggested message:

> Thank you for fulfilling my historical GP request submitted on 21 October 2026
> at 06:10:16 UTC, for SWARM A, NORAD 39452 / 2013-067B, covering 30 December 2013
> through 2 January 2014. Your summary reported three historical element sets.
>
> The received `sat000039452.json` file contains nine numeric literals missing the
> leading zero before a decimal point. Strict JSON parsing fails at line 1,
> column 129. The affected fields are ECCENTRICITY, BSTAR and MEAN_MOTION_DOT
> across the three reported records. I have preserved the original attachment
> without editing it.
>
> Please resend the same historical source records in standards-compliant JSON,
> preserving their original numerical values and precision, epochs, element-set
> identifiers, record order where possible, and all source metadata. Please
> explain any differences, additional or removed records rather than silently
> substituting another dataset. Three records are expected, subject to your
> confirmation. No current GP dataset, propagated positions or wider historical
> range is requested.
>
> Please retain any available source creation, publication or archive-availability
> timestamps, their meaning/time scale, source provenance and applicable reuse or
> attribution conditions. If those details are unavailable, please leave them
> unknown rather than deriving availability from the orbital epochs.

The correction request has been submitted according to the user; wait for the
provider response rather than repeatedly resubmitting. When the corrected file
arrives, upload the **original unedited attachment** and
any non-sensitive provenance/availability information supplied. Its actual email
receipt time may be supplied if known; do not use the request time or filesystem
storage time as a substitute. Preserve it as a new capture with its own filename,
hash and size. Never replace the existing original.
