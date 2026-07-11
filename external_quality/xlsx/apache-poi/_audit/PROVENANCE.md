# Apache POI XLSX image fixture audit

Sample group: `external_quality/xlsx/apache-poi`

The following files are official Apache POI test fixtures copied from the
upstream `test-data/spreadsheet` directory. Apache POI is licensed under
Apache-2.0; the existing local license mirror is
`external_quality/xlsx/apache-poi/LICENSE-apache-poi.txt`, and the approved
source-group record is `apache_poi_tests` in
`external_quality/SOURCE_CATALOG.tsv`.

| File | Exact upstream URL | SHA256 |
| --- | --- | --- |
| `picture.xlsx` | https://github.com/apache/poi/blob/trunk/test-data/spreadsheet/picture.xlsx | `fea2f13189e87d06297d7b5313abca4d0b6cd8747d5ca450e4db11273b265279` |
| `WithDrawing.xlsx` | https://github.com/apache/poi/blob/trunk/test-data/spreadsheet/WithDrawing.xlsx | `97b1ab359d6aecbe37864f30c85106e386f0a19bea8f290103927362a2701066` |
| `picture-and-shape-same-size.xlsx` | https://github.com/apache/poi/blob/trunk/test-data/spreadsheet/picture-and-shape-same-size.xlsx | `0a5262599a8f5ba12db065ce89bfa3fe16b19ae1a97ece449021c188eda00437` |

Review conclusion: the files are redistributable official regression
fixtures from an already approved source group. They cover package media,
multiple drawing images, mixed JPEG/PNG payloads, and a picture adjacent to a
non-picture shape.
