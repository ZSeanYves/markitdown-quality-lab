# ODF Toolkit ODS drawing fixture audit

- File: `drawing_import_xml_MSO15.ods`
- Exact upstream URL: https://github.com/tdf/odftoolkit/blob/master/odfdom/src/test/resources/test-input/drawing_import_xml_MSO15.ods
- Upstream repository: https://github.com/tdf/odftoolkit
- Source catalog id: `odf_toolkit_tests`
- License: Apache-2.0
- Local license mirror: `external_quality/ods/odf-toolkit/LICENSE-odf-toolkit.txt`
- SHA256: `d5640d131ad34de4aed184629f5eed8e294cab8ccf47e168fcd6fb05ec3e568d`

Review conclusion: this official Apache-2.0 test document is redistributable
and contains a broad set of package media referenced from spreadsheet drawing
frames, including PNG, JPEG, GIF, TIFF, EMF, and WMF payloads.

The additional ODS boundary files were captured from revision
`cfd3a9fbbda351fad38aad5e112e3598d08e23f0` through the GitHub Contents API.
They are public official test documents with no personal or sensitive data;
their payload hashes and sizes are recorded in `AUDIT.json`.
