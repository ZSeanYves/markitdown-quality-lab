PDF.js PDF audit note

Sample group: external_quality/pdf/pdfjs

Reviewed files added in this batch:
- 90ms_rksj_h_sample.pdf
- Embedded_font.pdf
- bug_jpx.pdf
- ccitt_EndOfBlock_false.pdf
- cid_cff.pdf
- jbig2_file_header.pdf
- jbig2_symbol_offset.pdf
- noembed-eucjp.pdf
- noembed-sjis.pdf
- issue11555.pdf
- issue2128r.pdf
- issue6286.pdf
- vertical.pdf
- cidfont_cmap_overflow.pdf

Evidence retained locally:
- Source-group catalog entry: `pdfjs_tests` in `external_quality/SOURCE_CATALOG.tsv`
- License mirror: `external_quality/pdf/pdfjs/LICENSE-pdfjs.txt`
- Upstream repository root: https://github.com/mozilla/pdf.js
- Exact upstream fixture URLs:
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/90ms_rksj_h_sample.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/Embedded_font.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/bug_jpx.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/ccitt_EndOfBlock_false.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/cid_cff.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/jbig2_file_header.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/jbig2_symbol_offset.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/noembed-eucjp.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/noembed-sjis.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/issue11555.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/issue2128r.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/issue6286.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/vertical.pdf
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/cidfont_cmap_overflow.pdf

Review conclusion:
- These files are official Apache-2.0 PDF.js test fixtures copied from the upstream `test/pdfs` tree.
- The repository already approves `pdfjs_tests` as a checked-in external regression fixture source group.
- This note closes the per-batch provenance gap for the newly promoted JPX, CCITT, JBIG2, embedded-font, GBK-EUC, UniJIS-UCS2, 90ms-RKSJ, vertical-writing, and CID/CMap fixtures.
