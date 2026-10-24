# E8 — NASA/IGS reference-data feasibility plan

Baseline: verified E7 `309aa02826bc0ca36ce82ed31d14fb76dbeecbfb`.
Branch: `engineering-e8-nasa-igs-feasibility`, separate worktree
`/workspace/OrbitIQ-nasa-igs`. The initial pasted request named E6/E7; the updated
E8 request supplies this corrected baseline. The original E7 worktree/branches,
real archive, private Swarm inputs and previous reports remain untouched.

Study ID: **ORBITIQ-IGS-GPS-RETRO-001**. Question: can a documented IGS combined
final GNSS orbit support a future, carefully limited retrospective comparison with
an exact compatible CelesTrak GP input through the unchanged SGP4/WGS72 engine?
No residual, propagation run, state subtraction or comparison implementation is
part of this phase. ESA Swarm-A remains a preserved, inactive alternative
workstream with its existing PARTIAL/BLOCKED status. NASA/IGS feasibility has its
own evidence and protocol, without waiting for ESA clarification.

## Investigation and implementation boundary

1. Read current NASA Earthdata, IGS products/frame/SP3 and CelesTrak format
   documentation; retain acquisition times, status, source URLs and hashes.
2. Verify actual CDDIS access, without printing/discovering credentials or treating
   an HTML login response as a product. Inspect official IGS data-centre mirrors
   as explicit alternatives, never as a claim of authenticated NASA acquisition.
3. Acquire at most a narrowly scoped final candidate and its processing summary;
   preserve original bytes privately outside source/CI. Inspect actual headers,
   cadence, identifiers, exclusions and quality fields.
4. Examine a bounded genuine CelesTrak GPS response, schema/mode compatibility and
   official time-dependent PRN/SVN/COSPAR/NORAD mapping. Prove or reject temporal
   overlap within the existing inclusive seven-day engine guard.
5. Add only an offline metadata/eligibility inspector where required, not a new
   orbital engine, API, storage migration or runnable comparison. Use exact source
   time arithmetic and the existing local leap/EOP facilities for diagnostics.
   Unsupported/ambiguous metadata and missing resources fail closed. No scientific
   gate can be enabled by a command-line approval switch.
6. Use tiny explicitly synthetic, specification-derived fixtures for deterministic
   tests. Verify the inspector separately on the genuine private candidate. Never
   substitute fixtures after acquisition/qualification failure.
7. Produce separately scoped qualification evidence, protocol and verification
   report. Conclusions are VERIFIED/PARTIALLY VERIFIED/UNVERIFIED/BLOCKED and end
   in an explicit candidate decision. A demonstrated BLOCKED result is valid E8
   feasibility completion; it does not establish scientific qualification.

## Acceptance

- Documentation/actual-acquisition claims have retained source evidence.
- Product hashes, SP3 declarations, exact epochs and exclusions are inspected.
- Identity mapping, existing GP schema/deep-space mode and temporal eligibility
  are tested without computing positions.
- Time conversion resources are pinned; frame identity, geocentre/reference point,
  quality, uncertainty and statistical dependence are assessed independently.
- No invented frame transform, uncertainty budget or accuracy acceptance threshold.
- Protocol predeclares future epoch/GP selection, sign convention, sampling,
  exclusions, diagnostics and permitted conclusions; residual code is absent.
- Appropriate backend, numerical, frontend/build and CI regression checks actually
  execute. All E1–E7 coverage, old reports, private files and branches remain intact.
- Publish only reviewed non-sensitive source/synthetic fixtures/docs to this E8
  branch under the existing investigation publication authorization, then verify
  exact-SHA CI. No merge, production deployment or private product upload.

E4 remains **OPEN**. Phase 11.3.1 remains **PARTIAL**; scientific evaluation
**BLOCKED**. Stop after feasibility reporting and await explicit user approval
before any real comparison implementation or residual calculations.
