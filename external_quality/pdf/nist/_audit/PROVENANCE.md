NIST PDF audit note

Sample group: external_quality/pdf/nist

Reviewed files:
- samples/papers/pdf_paper_nist_jres_120_011_0001.pdf
- samples/table_heavy/pdf_report_nist_tn2194_0001.pdf
- samples/manuals/pdf_nist_sp800_207_zero_trust_0001.pdf

Evidence retained locally:
- Source-group landing page: https://www.nist.gov/open/license
- Repository source catalog records this group as: "NIST Technical Series public-domain in U.S. with worldwide reprint grant"
- Exact publication URLs reviewed for manifest promotion:
  - https://nvlpubs.nist.gov/nistpubs/jres/120/jres.120.011.pdf
  - https://nvlpubs.nist.gov/nistpubs/TechnicalNotes/NIST.TN.2194.pdf
  - https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf

SP 800-207 intake evidence:
- SHA256: `0290d6ece24874287316f4bf430fef770aa4ec08a2227c8f2c1e5b2ff975e03d`
- Promoted from the main repository showcase without changing bytes.
- The official publication contains 59 pages, 12 base image XObjects, and 6
  soft-mask image XObjects. The soft masks belong to their base images and are
  not independent exported assets.

Review conclusion:
- NIST technical series samples in this repository should remain grouped under the official NIST technical-series licensing page and exact source URLs.
- This note now covers the formal manifest promotion of the retained JRES
  120.011 paper, NIST TN 2194 report, and NIST SP 800-207 real-world indirect
  ColorSpace/ICCBased/Indexed/SMask asset sample.
