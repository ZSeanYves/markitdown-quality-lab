# OCR provenance audit

This note records the local provenance and license review for the OCR source
groups listed in `external_quality/SOURCE_CATALOG.tsv`.

## ocr_src_0020

Source group: IRS forms and publications

Local files reviewed:
- `external_quality/ocr/irs/samples/pdf_page_image/ocr_pdf_page_image_irs_fw4_0001.pdf`
- `external_quality/ocr/irs/samples/structured/ocr_structured_irs_fw9_0001.pdf`
- `external_quality/ocr/irs/samples/language/ocr_language_irs_fw4zht_0001.pdf`
- `external_quality/ocr/irs/samples/language/ocr_language_irs_fw9sp_0001.pdf`

Evidence:
- Source-group landing page: `https://www.irs.gov/FormsPubs`
- Local PDF front matter identifies `Department of the Treasury` and
  `Internal Revenue Service`
- The retained PDFs are official IRS forms and translations matching the W-4 /
  W-9 family naming visible in the local filenames and front matter

Conclusion:
- Retain as official IRS government-public source material with per-file review
  recorded locally.

## ocr_src_0022

Source group: Wikimedia Commons File:Photo enforced traffic light sign.JPG

Local file reviewed:
- `external_quality/ocr/commons/samples/negative/ocr_negative_commons_sign_0001.jpg`

Evidence:
- Commons file page:
  `https://commons.wikimedia.org/wiki/File:Photo_enforced_traffic_light_sign.JPG`
- Commons summary records `Source: Own work`
- Commons licensing records that the uploader released the work into the public
  domain worldwide

Conclusion:
- Retain as Commons public-domain-dedicated material.

## ocr_src_0023

Source group: Wikimedia Commons File:Ledger-sm2.jpg

Local file reviewed:
- `external_quality/ocr/commons/samples/historical/ocr_historical_commons_ledger_0001.jpg`

Evidence:
- Commons file page: `https://commons.wikimedia.org/wiki/File:Ledger-sm2.jpg`
- Commons licensing records `PD-USGov`
- Commons page also records Creative Commons Public Domain Mark 1.0

Conclusion:
- Retain as Commons historical public-domain material with the Commons file page
  kept as the provenance anchor.

## ocr_src_0025

Source group: Wikimedia Commons File:The menu... (39980813130).jpg

Local file reviewed:
- `external_quality/ocr/commons/samples/scene_text/ocr_scene_text_commons_menu_0001.jpg`

Evidence:
- Commons file page:
  `https://commons.wikimedia.org/wiki/File:The_menu..._(39980813130).jpg`
- Commons summary records Flickr source and author `Stig Nygaard`
- Commons licensing records `Creative Commons Attribution 2.0`
- Commons page records Flickr review confirmation for `cc-by-2.0`

Conclusion:
- Retain as CC-BY-2.0 Commons/Flickr material; attribution must be preserved in
  repo documentation and downstream publication context.

## ocr_src_0027

Source group: Project-owned synthetic OCR seed pages

Local files reviewed:
- `external_quality/ocr/self_synthetic/samples/degradation/ocr_degradation_self_blur_0001.png`
- `external_quality/ocr/self_synthetic/samples/language/ocr_language_self_arabic_0001.png`
- `external_quality/ocr/self_synthetic/samples/layout/ocr_layout_self_heading_paragraph_0001.png`
- `external_quality/ocr/self_synthetic/samples/layout/ocr_layout_self_multi_column_0001.png`
- `external_quality/ocr/self_synthetic/samples/plain_print/ocr_plain_print_self_dense_smallfont_0001.png`
- `external_quality/ocr/self_synthetic/samples/structured/ocr_structured_self_table_0001.png`

Evidence:
- `local-generated` source marker
- Files are project-owned synthetic OCR fixtures retained directly inside this
  repository

Conclusion:
- Retain as project-owned synthetic material.

## ocr_src_0028

Source group: Wikimedia Commons File:Image 579x817 from 0,8 to 7224,10200.jpg

Local file reviewed:
- `external_quality/ocr/commons/samples/layout/ocr_layout_commons_daily_exchange_0001.jpg`

Evidence:
- Commons file page:
  `https://commons.wikimedia.org/wiki/File:Image_579x817_from_0,8_to_7224,10200.jpg`
- Commons licensing records the image as public domain in the United States
  because copyright expired / publication predates current protection

Conclusion:
- Retain as Commons public-domain historical material with the Commons file page
  retained as provenance anchor.

## ocr_src_0029

Source group: Wikimedia Commons File:SCC1.jpg

Local file reviewed:
- `external_quality/ocr/commons/samples/historical/ocr_historical_commons_scc1_0001.jpg`

Evidence:
- Commons file page: `https://commons.wikimedia.org/wiki/File:SCC1.jpg`
- Commons licensing records U.S. federal-government public-domain status
- Commons page also records Creative Commons Public Domain Mark 1.0

Conclusion:
- Retain as Commons public-domain historical material.

## ocr_src_0030

Source group: Wikimedia Commons File:Arabic newspaper declare formation of the UAR, 1958.jpg

Local file reviewed:
- `external_quality/ocr/commons/samples/language/ocr_language_commons_uar_0001.jpg`

Evidence:
- Commons file page:
  `https://commons.wikimedia.org/wiki/File:Arabic_newspaper_declare_formation_of_the_UAR,_1958.jpg`
- Commons licensing records the work as public domain in Syria and acceptable
  for Commons hosting in the United States
- Commons page notes the public-domain basis includes daily-news / official
  document treatment under the cited Syrian law

Conclusion:
- Retain as Commons public-domain historical news material with the Commons file
  page retained as provenance anchor.

## ocr_src_0031

Source group: Wikimedia Commons File:Typewriter-writed paper.jpg

Local file reviewed:
- `external_quality/ocr/commons/samples/degradation/ocr_degradation_commons_typewriter_photo_0001.jpg`

Evidence:
- Commons file page:
  `https://commons.wikimedia.org/wiki/File:Typewriter-writed_paper.jpg`
- Commons summary records `Source: Own work`
- Commons licensing records `CC0 1.0 Universal Public Domain Dedication`

Conclusion:
- Retain as Commons CC0 material.

## ocr_src_0032

Source group: Wikimedia Commons File:Lat Pau (Chinese newspaper).jpg

Local file reviewed:
- `external_quality/ocr/commons/samples/language/ocr_language_commons_lat_pau_0001.jpg`

Evidence:
- Commons file page:
  `https://commons.wikimedia.org/wiki/File:Lat_Pau_(Chinese_newspaper).jpg`
- Commons licensing records the work as public domain because copyright expired
  in Singapore

Conclusion:
- Retain as Commons public-domain historical newspaper material with the Commons
  file page retained as provenance anchor.
