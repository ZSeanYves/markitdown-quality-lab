PDF.js PDF audit note

Sample group: external_quality/pdf/pdfjs

Reviewed files added in this batch:
- images.pdf
- images_1bit_grayscale.pdf
- cmykjpeg.pdf
- smaskdim.pdf
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
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/images.pdf
    - SHA256: `f7a44ca650d951cfea007440cda297dabbf2cf0c8f77a948a580cc0e99496725`
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/images_1bit_grayscale.pdf
    - SHA256: `afbed07b9fe25563b2604b81cd7186c91d4356e5428a05322b8b7eae88301e24`
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/cmykjpeg.pdf
    - SHA256: `659d6b19912f63db988b0b26b9bde0e6d8100667ef162051a4a84ea8e5b90272`
  - https://github.com/mozilla/pdf.js/blob/master/test/pdfs/smaskdim.pdf
    - SHA256: `e03b8359f8b64e1a18a795aa9376bc98d98dca89a828ec20c49a4ac2f36a3d82`
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
