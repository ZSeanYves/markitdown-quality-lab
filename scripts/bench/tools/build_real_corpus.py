#!/usr/bin/env python3
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests


LAB_ROOT = Path(__file__).resolve().parents[3]
ROOT = LAB_ROOT / "external_bench"
PAYLOAD_ROOT = ROOT
CACHE = LAB_ROOT / ".tmp" / "bench" / "cache"
FETCH_PLAN_DIR = LAB_ROOT / "scripts" / "bench"
LICENSES = LAB_ROOT / "licenses" / "bench"
MAX_BYTES = 500 * 1024 * 1024
HEAD_TIMEOUT = (10, 20)
GET_TIMEOUT = (15, 45)
USER_AGENT = "markitdown-external-bench-real-corpus/0.2"

PARSER_FORMATS = {"html", "txt", "csv", "tsv", "json", "yaml", "xml"}
COMPARE_FORMATS = {"pdf", "docx", "pptx", "xlsx", "html", "txt", "csv", "json", "xml"}

LICENSES_BY_GROUP = {
    "irs_publications": ("LicenseRef-US-Gov-Public-Domain", "https://www.usa.gov/government-copyright", "no"),
    "nist_publications": ("LicenseRef-US-Gov-Public-Domain", "https://www.usa.gov/government-copyright", "no"),
    "govinfo": ("LicenseRef-US-Gov-Public-Domain", "https://www.usa.gov/government-copyright", "no"),
    "opendatani": ("OGL-UK-3.0", "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/", "yes"),
    "govuk_orgcharts": ("OGL-UK-3.0", "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/", "yes"),
    "nhs_digital": ("CC-BY-4.0", "https://creativecommons.org/licenses/by/4.0/", "yes"),
    "ons": ("OGL-UK-3.0", "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/", "yes"),
    "w3c_specs": ("LicenseRef-W3C-Document-2023", "https://www.w3.org/copyright/document-license-2023/", "yes"),
    "gutenberg_books": ("LicenseRef-Project-Gutenberg", "https://www.gutenberg.org/policy/license.html", "yes"),
    "rfc_editor": ("LicenseRef-IETF-Trust", "https://trustee.ietf.org/license-info/", "yes"),
    "usgs_feeds": ("LicenseRef-US-Gov-Public-Domain", "https://www.usa.gov/government-copyright", "no"),
    "owid_grapher": ("CC-BY-4.0", "https://ourworldindata.org/how-to-use-our-world-in-data", "yes"),
    "uniprot_api": ("CC-BY-4.0", "https://www.uniprot.org/help/license", "yes"),
    "worldbank_api": ("CC-BY-4.0", "https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets", "yes"),
    "spdx_data": ("CC0-1.0", "https://github.com/spdx/license-list-data/blob/main/LICENSE", "no"),
    "wikidata": ("CC0-1.0", "https://www.wikidata.org/wiki/Wikidata:Licensing", "no"),
    "github_yaml": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", "yes"),
    "census_tiger": ("LicenseRef-US-Gov-Public-Domain", "https://www.usa.gov/government-copyright", "no"),
}


@dataclass
class Candidate:
    bench_id: str
    format: str
    source_group: str
    size_class: str
    filename: str
    source_url: str
    landing_url: str
    enabled_tier: str = "disabled"
    review_status: str = "reviewed_candidate"
    notes: str = ""
    license_spdx: Optional[str] = None
    license_url: Optional[str] = None
    attribution_required: Optional[str] = None
    source_version: str = "current"
    download: bool = True
    github_repo: Optional[str] = None
    github_branch: Optional[str] = None
    github_path: Optional[str] = None
    terms_url: str = ""
    resolved_url: str = ""

    def rel_path(self) -> str:
        return f"{self.format}/{self.source_group}/{self.size_class}/{self.filename}"

    def bench_layers(self) -> str:
        layers = []
        if self.format in PARSER_FORMATS:
            layers.append("parser")
        layers.extend(["convert", "cli"])
        if self.format in COMPARE_FORMATS:
            layers.append("compare")
        return ";".join(layers)

    def parser_stages(self) -> str:
        return "parse" if self.format in PARSER_FORMATS else ""


def candidate(
    bench_id,
    fmt,
    group,
    size,
    filename,
    source_url,
    landing_url,
    enabled=False,
    download=True,
    review_status="reviewed_candidate",
    notes="",
    license_spdx=None,
    license_url=None,
    attribution_required=None,
    source_version="current",
    terms_url="",
):
    lic = LICENSES_BY_GROUP.get(group, ("NOASSERTION", "", "yes"))
    return Candidate(
        bench_id=bench_id,
        format=fmt,
        source_group=group,
        size_class=size,
        filename=filename,
        source_url=source_url,
        landing_url=landing_url,
        enabled_tier="smoke" if enabled else "disabled",
        review_status=review_status,
        notes=notes,
        license_spdx=license_spdx or lic[0],
        license_url=license_url or lic[1],
        attribution_required=attribution_required or lic[2],
        source_version=source_version,
        download=download,
        terms_url=terms_url,
    )


def github_yaml(bench_id, repo, branch, path, size, enabled=False, license_spdx="Apache-2.0"):
    filename = bench_id + ".yaml"
    return Candidate(
        bench_id=bench_id,
        format="yaml",
        source_group="github_yaml",
        size_class=size,
        filename=filename,
        source_url=f"https://raw.githubusercontent.com/{repo}/{branch}/{path}",
        landing_url=f"https://github.com/{repo}/blob/{branch}/{path}",
        enabled_tier="smoke" if enabled else "disabled",
        review_status="reviewed_candidate",
        notes="GitHub raw URL is resolved to a commit SHA before download.",
        license_spdx=license_spdx,
        license_url="https://www.apache.org/licenses/LICENSE-2.0" if license_spdx == "Apache-2.0" else "https://opensource.org/license/mit/",
        attribution_required="yes",
        github_repo=repo,
        github_branch=branch,
        github_path=path,
    )


def build_candidates():
    c = []
    c += [
        candidate("pdf_irs_p17", "pdf", "irs_publications", "medium", "p17.pdf", "https://www.irs.gov/pub/irs-pdf/p17.pdf", "https://www.irs.gov/forms-pubs/about-publication-17", enabled=True),
        candidate("pdf_irs_f1040", "pdf", "irs_publications", "small", "f1040.pdf", "https://www.irs.gov/pub/irs-pdf/f1040.pdf", "https://www.irs.gov/forms-pubs/about-form-1040"),
        candidate("pdf_irs_p15", "pdf", "irs_publications", "medium", "p15.pdf", "https://www.irs.gov/pub/irs-pdf/p15.pdf", "https://www.irs.gov/forms-pubs/about-publication-15"),
        candidate("pdf_nist_800_53r5", "pdf", "nist_publications", "large", "NIST.SP.800-53r5.pdf", "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf", "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final"),
        candidate("pdf_nist_800_61r2", "pdf", "nist_publications", "medium", "NIST.SP.800-61r2.pdf", "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf", "https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final"),
        candidate("pdf_nist_800_171r3", "pdf", "nist_publications", "medium", "NIST.SP.800-171r3.pdf", "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-171r3.pdf", "https://csrc.nist.gov/publications/detail/sp/800-171/rev-3/final"),
        candidate("pdf_nist_800_207", "pdf", "nist_publications", "medium", "NIST.SP.800-207.pdf", "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf", "https://csrc.nist.gov/publications/detail/sp/800-207/final"),
        candidate("pdf_nist_800_218", "pdf", "nist_publications", "medium", "NIST.SP.800-218.pdf", "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf", "https://csrc.nist.gov/publications/detail/sp/800-218/final"),
        candidate("pdf_nist_ai_rmf", "pdf", "nist_publications", "medium", "NIST.AI.100-1.pdf", "https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf", "https://www.nist.gov/itl/ai-risk-management-framework"),
        candidate("pdf_govinfo_budget_2025", "pdf", "govinfo", "large", "BUDGET-2025-BUD.pdf", "https://www.govinfo.gov/content/pkg/BUDGET-2025-BUD/pdf/BUDGET-2025-BUD.pdf", "https://www.govinfo.gov/app/details/BUDGET-2025-BUD", download=False, notes="Catalog only for now; large govinfo PDF left out of default download."),
    ]

    c += [
        candidate("docx_rail_cif_notes", "docx", "opendatani", "medium", "rail-cif-file-supplementary-notes.docx", "https://admin.opendatani.gov.uk/dataset/e41b1057-b0bd-4419-95eb-77057c8ad6b0/resource/00dc6365-8b56-434f-8889-a39582a2eec6/download/rail-cif-file-supplementary-notes.docx", "https://www.data.gov.uk/dataset/e41b1057-b0bd-4419-95eb-77057c8ad6b0/nir20160126v2"),
        candidate("docx_ulsterbus_cif_notes", "docx", "opendatani", "small", "ulsterbus-cif-file-supplementary-notes.docx", "https://admin.opendatani.gov.uk/dataset/c1acee5b-a400-46bd-a795-9bf7637ff879/resource/7b195748-c3f9-4970-b0fb-90a194f7e3b3/download/bus-cif-file-supplementary-notes.docx", "https://www.data.gov.uk/dataset/c1acee5b-a400-46bd-a795-9bf7637ff879/ulsterbus-and-goldline-timetable-data-from-28-june-31-august-2016"),
        candidate("docx_metro_cif_notes", "docx", "opendatani", "small", "metro-cif-file-supplementary-notes.docx", "https://admin.opendatani.gov.uk/dataset/6d9677cf-8d03-4851-985c-16f73f7dd5fb/resource/1a72b4c1-48a4-4dd9-a1ee-2de4bba281bc/download/bus-cif-file-supplementary-notes.docx", "https://www.data.gov.uk/dataset/6d9677cf-8d03-4851-985c-16f73f7dd5fb/metro-timetable-data-valid-from-18-june-until-31-august-2016"),
        candidate("docx_bus_stop_defs", "docx", "opendatani", "tiny", "definitions-of-headings-of-translink-bus-stop-list-table.docx", "https://admin.opendatani.gov.uk/dataset/495c6964-e8d2-4bf1-9942-8d950b3a0ceb/resource/169d8ffa-79bd-46bd-b6be-931cd46d6842/download/definitions-of-headings-of-translink-bus-stop-list-table.docx", "https://www.data.gov.uk/dataset/495c6964-e8d2-4bf1-9942-8d950b3a0ceb/translink-bus-stop-list"),
        candidate("docx_dvla_user_guide", "docx", "opendatani", "medium", "driving-licence-data-user-guide-sep-2017.docx", "https://data.dft.gov.uk/driving-licence-data/driving-licence-data-user-guide-sep-2017.docx", "https://www.data.gov.uk/dataset/d0be1ed2-9907-4ec4-b552-c048f6aec16a/driving-licence-data", enabled=True),
        candidate("docx_manchester_parking_metadata", "docx", "opendatani", "small", "parking_spaces_2018_metadata.docx", "http://www.manchester.gov.uk/open/download/downloads/id/562/parking_spaces_2018_metadata.docx", "https://www.data.gov.uk/dataset/79c34ee5-b548-4461-800c-c6b3ce6865bb/http-www-manchester-gov-uk-open-download-downloads-id-712-parking_spaces_2017-csv"),
        candidate("docx_trade_union_2020", "docx", "opendatani", "small", "trade_union_facility_time_2020_metadata.docx", "http://open.manchester.gov.uk/download/downloads/id/928/trade_union_facility_time_2020_metadata.docx", "https://www.data.gov.uk/dataset/6ed20c3e-f8be-4ad4-b49c-9c655daab4ae/public-sector-facility-time-publication"),
        candidate("docx_trade_union_2022", "docx", "opendatani", "small", "trade_union_facility_time_2022.docx", "https://www.manchester.gov.uk/open/downloads/download/163/trade_union_facility_time", "https://www.data.gov.uk/dataset/6ed20c3e-f8be-4ad4-b49c-9c655daab4ae/public-sector-facility-time-publication"),
        candidate("docx_trade_union_2023", "docx", "opendatani", "small", "trade_union_facility_time_2023.docx", "https://open.manchester.gov.uk/downloads/file/1160/trade_union_facility_time_2023", "https://www.data.gov.uk/dataset/6ed20c3e-f8be-4ad4-b49c-9c655daab4ae/public-sector-facility-time-publication"),
        candidate("docx_trade_union_2024", "docx", "opendatani", "small", "trade_union_facility_time_2024.docx", "https://www.manchester.gov.uk/open/downloads/download/187/trade_union_facility_time_2024", "https://www.data.gov.uk/dataset/6ed20c3e-f8be-4ad4-b49c-9c655daab4ae/public-sector-facility-time-publication"),
    ]

    c += [
        candidate("pptx_staff_officer", "pptx", "opendatani", "medium", "staff-officer-irc241559-final.pptx", "https://admin.opendatani.gov.uk/dataset/e7d8e911-bf68-472b-bf9c-3a337cf152e0/resource/fd6e9f25-0ecf-4268-a47c-89d21ed26f54/download/staff-officer---irc241559---final.pptx", "https://www.data.gov.uk/dataset/e7d8e911-bf68-472b-bf9c-3a337cf152e0/irc241559-staff-officer-so-external-recruitment-campaign-section-75-data"),
        candidate("pptx_deputy_principal", "pptx", "opendatani", "medium", "deputy-principal-irc241560.pptx", "https://admin.opendatani.gov.uk/dataset/e0ccb98b-a255-43c0-b4a2-3ea3a473fdd1/resource/bbde7f56-53e5-4a8f-beb4-6704335f9375/download/deputy-principal---irc241560.pptx", "https://www.data.gov.uk/dataset/e0ccb98b-a255-43c0-b4a2-3ea3a473fdd1/irc241560-deputy-principal-dp-external-recruitment-campaign-data"),
        candidate("pptx_skills_academy", "pptx", "opendatani", "medium", "skills-academy-so-competition-irc284906.pptx", "https://admin.opendatani.gov.uk/dataset/90fbe621-d564-48db-a1c4-3e9070b6d5ca/resource/e418a83e-5db1-4d47-b16f-10a3262a4c3f/download/skills-academy-so-competition-irc284906-.pptx", "https://www.data.gov.uk/dataset/90fbe621-d564-48db-a1c4-3e9070b6d5ca/irc284906-skills-academy-so-competition-external-recruitment-campaign-data"),
        candidate("pptx_student_placement_2022", "pptx", "opendatani", "medium", "student-placement-irc-275819.pptx", "https://admin.opendatani.gov.uk/dataset/beb9ee30-d015-43e3-8ae7-cb33a1de626b/resource/e974733b-46ec-4cdb-882f-299b1c3b054e/download/student-placement-competition--irc-275819.pptx", "https://www.data.gov.uk/dataset/beb9ee30-d015-43e3-8ae7-cb33a1de626b/nics-student-placement-external-recruitment-campaign-data-irc-275819"),
        candidate("pptx_operational_apprentice", "pptx", "opendatani", "medium", "operational-delivery-apprentice.pptx", "https://www.opendatani.gov.uk/dataset/e0c7d95f-6589-4f63-a5aa-bda297be0895/resource/c1fd7c08-93d7-45bb-ba35-ff32424beeb2/download/completed-stages-of-operational-delivery-apprentice-comp---with-tables--extra-offer.pptx", "https://www.data.gov.uk/dataset/e0c7d95f-6589-4f63-a5aa-bda297be0895/irc269650-nics-operational-delivery-apprentice-scheme-external-recruitment-campaign-data"),
        candidate("pptx_so_275969", "pptx", "opendatani", "medium", "so-completed-stages-with-tables.pptx", "https://www.opendatani.gov.uk/dataset/e1bd774e-bda7-42dc-bd49-0b38caef283b/resource/560f8a2a-8c86-475d-ba07-d0abee6f087d/download/so---completed-stages-with-tables.pptx", "https://www.data.gov.uk/dataset/e1bd774e-bda7-42dc-bd49-0b38caef283b/irc275969-staff-officer-so-external-recruitment-campaign-data"),
        candidate("pptx_eo_265817", "pptx", "opendatani", "medium", "completed-stages-of-eoi-and-eoii.pptx", "https://www.opendatani.gov.uk/dataset/f458b041-ab57-413a-a925-ad0953138d3a/resource/dad7b2ce-e37b-483a-90d9-db8d6fcf05b8/download/completed-stages-of-eoi-and-eoii.pptx", "https://www.data.gov.uk/dataset/f458b041-ab57-413a-a925-ad0953138d3a/irc265817-executive-officer-2"),
        candidate("pptx_nhs_diabetes", "pptx", "nhs_digital", "large", "NDA_DPP_MainReport_1718_1.1.pptx", "https://files.digital.nhs.uk/A6/CD0E5A/NDA_DPP_MainReport_1718_1.1.pptx", "https://www.data.gov.uk/dataset/314fb958-a5b9-43b2-95aa-38113a5e52d3/national-diabetes-audit-diabetes-prevention-programme-2017-18-diagnoses-and-demographics"),
        candidate("pptx_ao_2019", "pptx", "opendatani", "medium", "completed-stages-of-ao-with-tables.pptx", "https://www.opendatani.gov.uk/dataset/52f3bf19-6073-48b5-bf5f-1260bb7ae7a9/resource/eb2b492b-900b-4740-a6a3-88dcac799915/download/completed-stages-of-ao---with-tables.pptx", "https://www.data.gov.uk/dataset/52f3bf19-6073-48b5-bf5f-1260bb7ae7a9/irc240709-administrative-officer-ao-external-recruitment-2019-20"),
        candidate("pptx_ecgd_orgchart", "pptx", "govuk_orgcharts", "small", "ecgd-structure-chart-march-2012.pptx", "https://www.gov.uk/government/uploads/system/uploads/attachment_data/file/190928/ecgd-structure-chart-march-2012.pptx", "https://www.data.gov.uk/dataset/c06fa044-eafc-4ed8-8941-426c5ad03a6f/staff-organograms-and-pay-ecgd", enabled=True),
    ]

    ons_urls = [
        ("xlsx_ons_mye24", "mye24tablesuk.xlsx", "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2024/mye24tablesuk.xlsx", True),
        ("xlsx_ons_myeb_2011_2024", "myebtablesuk20112024.xlsx", "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2011tomid2024/myebtablesuk20112024.xlsx", False),
        ("xlsx_ons_ukpop_1838_2024", "ukpopulationestimates18382024.xlsx", "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/ukpopulationestimates1838to2024/ukpopulationestimates18382024.xlsx", False),
        ("xlsx_ons_mye23", "mye23tablesuk.xlsx", "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2023/mye23tablesuk.xlsx", False),
        ("xlsx_ons_ukpop_1838_2023", "ukpopulationestimates183820231.xlsx", "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/ukpopulationestimates1838to2023/ukpopulationestimates183820231.xlsx", False),
        ("xlsx_ons_myeb_2011_2022", "myebtablesuk20112022.xlsx", "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2011tomid2022/myebtablesuk20112022.xlsx", False),
        ("xlsx_ons_mye22", "mye22final.xlsx", "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2022/mye22final.xlsx", False),
        ("xlsx_ons_regional_1971_2020", "regionalpopestimatesenglandandwales19712020.xlsx", "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2001tomid2020detailedtimeseries/regionalpopestimatesenglandandwales19712020.xlsx", False),
        ("xlsx_ons_ukpop_1838_2020", "ukpopulationestimates18382020.xlsx", "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2001tomid2020detailedtimeseries/ukpopulationestimates18382020.xlsx", False),
        ("xlsx_ons_ukpop_1838_2019", "ukpopulationestimates18382019.xlsx", "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2001tomid2019detailedtimeseries/ukpopulationestimates18382019.xlsx", False),
    ]
    for bid, filename, uri, enabled in ons_urls:
        c.append(candidate(bid, "xlsx", "ons", "medium", filename, "https://www.ons.gov.uk/file?uri=" + uri, "https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland", enabled=enabled))

    for bid, url, size, enabled in [
        ("html_w3c_wcag22", "https://www.w3.org/TR/WCAG22/", "medium", True),
        ("html_w3c_svg2", "https://www.w3.org/TR/SVG2/", "large", False),
        ("html_w3c_css_color4", "https://www.w3.org/TR/css-color-4/", "medium", False),
        ("html_w3c_css_grid2", "https://www.w3.org/TR/css-grid-2/", "medium", False),
        ("html_w3c_webaudio", "https://www.w3.org/TR/webaudio/", "large", False),
        ("html_w3c_uievents", "https://www.w3.org/TR/uievents/", "medium", False),
        ("html_w3c_html_aria", "https://www.w3.org/TR/html-aria/", "medium", False),
        ("html_w3c_accname", "https://www.w3.org/TR/accname-1.2/", "medium", False),
        ("html_w3c_wai_aria", "https://www.w3.org/TR/wai-aria-1.2/", "large", False),
        ("html_w3c_payment_request", "https://www.w3.org/TR/payment-request/", "medium", False),
    ]:
        c.append(candidate(bid, "html", "w3c_specs", size, bid.replace("html_w3c_", "") + ".html", url, url, enabled=enabled))

    for bid, pgid, slug, size, enabled in [
        ("epub_gutenberg_moby_dick", "2701", "moby-dick", "small", False),
        ("epub_gutenberg_pride", "1342", "pride-and-prejudice", "medium", False),
        ("epub_gutenberg_frankenstein", "84", "frankenstein", "small", False),
        ("epub_gutenberg_dracula", "345", "dracula", "small", False),
        ("epub_gutenberg_sherlock", "1661", "sherlock-holmes", "small", False),
        ("epub_gutenberg_alice", "11", "alice", "small", True),
        ("epub_gutenberg_tale_two_cities", "98", "tale-of-two-cities", "small", False),
        ("epub_gutenberg_dorian_gray", "174", "dorian-gray", "small", False),
        ("epub_gutenberg_war_and_peace", "2600", "war-and-peace", "medium", False),
        ("epub_gutenberg_ulysses", "4300", "ulysses", "medium", False),
    ]:
        c.append(candidate(bid, "epub", "gutenberg_books", size, f"pg{pgid}-images-3.epub", f"https://www.gutenberg.org/cache/epub/{pgid}/pg{pgid}-images-3.epub", f"https://www.gutenberg.org/ebooks/{pgid}", enabled=enabled, notes="Project Gutenberg file retained with license/header context."))

    for bid, rfc, size, enabled in [
        ("txt_rfc9110", "9110", "large", True),
        ("txt_rfc9111", "9111", "medium", False),
        ("txt_rfc9112", "9112", "medium", False),
        ("txt_rfc8446", "8446", "large", False),
        ("txt_rfc8259", "8259", "small", False),
        ("txt_rfc3986", "3986", "medium", False),
        ("txt_rfc4180", "4180", "tiny", False),
        ("txt_rfc9000", "9000", "large", False),
        ("txt_rfc5280", "5280", "large", False),
        ("txt_rfc7231", "7231", "large", False),
    ]:
        c.append(candidate(bid, "txt", "rfc_editor", size, f"rfc{rfc}.txt", f"https://www.rfc-editor.org/rfc/rfc{rfc}.txt", f"https://www.rfc-editor.org/rfc/rfc{rfc}", enabled=enabled))

    for bid, url, landing, group, size, enabled in [
        ("csv_usgs_all_day", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.csv", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/", "usgs_feeds", "small", True),
        ("csv_usgs_all_week", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.csv", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/", "usgs_feeds", "medium", False),
        ("csv_usgs_all_month", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.csv", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/", "usgs_feeds", "large", False),
        ("csv_usgs_significant_month", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.csv", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/", "usgs_feeds", "small", False),
        ("csv_usgs_45_month", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.csv", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/", "usgs_feeds", "small", False),
        ("csv_usgs_25_month", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.csv", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/", "usgs_feeds", "medium", False),
        ("csv_usgs_10_month", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/1.0_month.csv", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/", "usgs_feeds", "large", False),
        ("csv_owid_co2", "https://ourworldindata.org/grapher/annual-co2-emissions-per-country.csv", "https://ourworldindata.org/grapher/annual-co2-emissions-per-country", "owid_grapher", "medium", False),
        ("csv_owid_life_expectancy", "https://ourworldindata.org/grapher/life-expectancy.csv", "https://ourworldindata.org/life-expectancy", "owid_grapher", "medium", False),
        ("csv_owid_population", "https://ourworldindata.org/grapher/population.csv", "https://ourworldindata.org/population-growth", "owid_grapher", "medium", False),
    ]:
        c.append(candidate(bid, "csv", group, size, bid + ".csv", url, landing, enabled=enabled))

    uniprot_queries = [
        ("tsv_uniprot_reviewed", "reviewed:true", True),
        ("tsv_uniprot_human", "organism_id:9606 AND reviewed:true", False),
        ("tsv_uniprot_mouse", "organism_id:10090 AND reviewed:true", False),
        ("tsv_uniprot_ecoli", "organism_id:562 AND reviewed:true", False),
        ("tsv_uniprot_yeast", "organism_id:559292 AND reviewed:true", False),
        ("tsv_uniprot_arabidopsis", "organism_id:3702 AND reviewed:true", False),
        ("tsv_uniprot_drosophila", "organism_id:7227 AND reviewed:true", False),
        ("tsv_uniprot_brca1", "gene:BRCA1", False),
        ("tsv_uniprot_kinase", "keyword:Kinase", False),
        ("tsv_uniprot_membrane", "keyword:Transmembrane", False),
    ]
    for bid, query, enabled in uniprot_queries:
        url = "https://rest.uniprot.org/uniprotkb/search?query=" + quote(query) + "&format=tsv&fields=accession,id,protein_name,organism_name,length&size=500"
        c.append(candidate(bid, "tsv", "uniprot_api", "medium", bid + ".tsv", url, "https://www.uniprot.org/help/license", enabled=enabled))

    for bid, url, landing, group, size, enabled in [
        ("json_wb_population", "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&per_page=20000", "https://data.worldbank.org/indicator/SP.POP.TOTL", "worldbank_api", "large", True),
        ("json_wb_gdp", "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.CD?format=json&per_page=20000", "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD", "worldbank_api", "large", False),
        ("json_wb_life", "https://api.worldbank.org/v2/country/all/indicator/SP.DYN.LE00.IN?format=json&per_page=20000", "https://data.worldbank.org/indicator/SP.DYN.LE00.IN", "worldbank_api", "large", False),
        ("json_wb_co2", "https://api.worldbank.org/v2/country/all/indicator/EN.ATM.CO2E.KT?format=json&per_page=20000", "https://data.worldbank.org/indicator/EN.ATM.CO2E.KT", "worldbank_api", "large", False),
        ("json_wb_internet", "https://api.worldbank.org/v2/country/all/indicator/IT.NET.USER.ZS?format=json&per_page=20000", "https://data.worldbank.org/indicator/IT.NET.USER.ZS", "worldbank_api", "large", False),
        ("json_wb_unemployment", "https://api.worldbank.org/v2/country/all/indicator/SL.UEM.TOTL.ZS?format=json&per_page=20000", "https://data.worldbank.org/indicator/SL.UEM.TOTL.ZS", "worldbank_api", "large", False),
        ("json_usgs_all_month", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/", "usgs_feeds", "large", False),
        ("json_spdx_licenses", "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json", "https://github.com/spdx/license-list-data", "spdx_data", "medium", False),
        ("json_spdx_exceptions", "https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions.json", "https://github.com/spdx/license-list-data", "spdx_data", "small", False),
        ("json_wikidata_q42", "https://www.wikidata.org/wiki/Special:EntityData/Q42.json", "https://www.wikidata.org/wiki/Wikidata:Licensing", "wikidata", "small", False),
    ]:
        c.append(candidate(bid, "json", group, size, bid + ".json", url, landing, enabled=enabled))

    c += [
        github_yaml("yaml_swagger_petstore", "swagger-api/swagger-petstore", "master", "src/main/resources/openapi.yaml", "small"),
        github_yaml("yaml_k8s_deployment", "kubernetes/website", "main", "content/en/examples/application/deployment.yaml", "tiny", enabled=True),
        github_yaml("yaml_k8s_simple_pod", "kubernetes/website", "main", "content/en/examples/pods/simple-pod.yaml", "tiny"),
        github_yaml("yaml_k8s_load_balancer", "kubernetes/website", "main", "content/en/examples/service/load-balancer-example.yaml", "small"),
        github_yaml("yaml_bitnami_nginx_values", "bitnami/charts", "main", "bitnami/nginx/values.yaml", "medium"),
        github_yaml("yaml_bitnami_postgresql_values", "bitnami/charts", "main", "bitnami/postgresql/values.yaml", "large"),
        github_yaml("yaml_prometheus_values", "prometheus-community/helm-charts", "main", "charts/prometheus/values.yaml", "large"),
        github_yaml("yaml_actions_node", "actions/starter-workflows", "main", "ci/node.js.yml", "tiny", license_spdx="MIT"),
        github_yaml("yaml_actions_python", "actions/starter-workflows", "main", "ci/python-app.yml", "tiny", license_spdx="MIT"),
        github_yaml("yaml_grafana_values", "grafana/helm-charts", "main", "charts/grafana/values.yaml", "large"),
    ]

    wb_xml = [
        ("xml_wb_population", "SP.POP.TOTL", True),
        ("xml_wb_gdp", "NY.GDP.MKTP.CD", False),
        ("xml_wb_co2", "EN.ATM.CO2E.KT", False),
        ("xml_wb_school", "SE.PRM.ENRR", False),
        ("xml_wb_health", "SH.XPD.CHEX.GD.ZS", False),
        ("xml_wb_forest", "AG.LND.FRST.ZS", False),
        ("xml_wb_electricity", "EG.USE.ELEC.KH.PC", False),
        ("xml_wb_unemployment", "SL.UEM.TOTL.ZS", False),
        ("xml_wb_internet", "IT.NET.USER.ZS", False),
        ("xml_wb_life", "SP.DYN.LE00.IN", False),
    ]
    for bid, indicator, enabled in wb_xml:
        c.append(candidate(bid, "xml", "worldbank_api", "large", bid + ".xml", f"https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=xml&per_page=20000", f"https://data.worldbank.org/indicator/{indicator}", enabled=enabled))

    for bid, pgid, size, enabled in [
        ("zip_gutenberg_moby_dick_html", "2701", "medium", False),
        ("zip_gutenberg_frankenstein_html", "84", "small", False),
        ("zip_gutenberg_dracula_html", "345", "small", False),
        ("zip_gutenberg_sherlock_html", "1661", "small", True),
        ("zip_gutenberg_alice_html", "11", "small", False),
    ]:
        c.append(candidate(bid, "zip", "gutenberg_books", size, f"pg{pgid}-h.zip", f"https://www.gutenberg.org/cache/epub/{pgid}/pg{pgid}-h.zip", f"https://www.gutenberg.org/ebooks/{pgid}", enabled=enabled, notes="ZIP archive audited before manifest write."))
    for bid, path in [
        ("zip_census_state", "STATE/tl_2024_us_state.zip"),
        ("zip_census_county", "COUNTY/tl_2024_us_county.zip"),
        ("zip_census_place", "PLACE/tl_2024_us_place.zip"),
        ("zip_census_zcta", "ZCTA520/tl_2024_us_zcta520.zip"),
        ("zip_census_roads_autauga", "ROADS/tl_2024_01001_roads.zip"),
    ]:
        c.append(candidate(bid, "zip", "census_tiger", "medium", Path(path).name, f"https://www2.census.gov/geo/tiger/TIGER2024/{path}", "https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html", download=False, notes="Catalog only: Census host returned 403 to this environment during HEAD probes."))
    return c


def write_tsv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: str(row.get(k, "")) for k in fieldnames})


def resolve_github_pin(candidate):
    if not candidate.github_repo:
        candidate.resolved_url = candidate.source_url
        return
    api = f"https://api.github.com/repos/{candidate.github_repo}/commits/{candidate.github_branch}"
    r = requests.get(api, timeout=HEAD_TIMEOUT, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    r.raise_for_status()
    sha = r.json()["sha"]
    candidate.source_version = sha
    candidate.source_url = f"https://raw.githubusercontent.com/{candidate.github_repo}/{sha}/{candidate.github_path}"
    candidate.landing_url = f"https://github.com/{candidate.github_repo}/blob/{sha}/{candidate.github_path}"
    candidate.resolved_url = candidate.source_url


def sniff_magic(fmt, path):
    data = path.read_bytes()
    head = data[:4096]
    if fmt == "pdf":
        return head.startswith(b"%PDF"), "expected %PDF"
    if fmt in {"docx", "pptx", "xlsx", "epub", "zip"}:
        return head.startswith(b"PK\x03\x04") or head.startswith(b"PK\x05\x06") or head.startswith(b"PK\x07\x08"), "expected ZIP magic"
    text = data[:65536]
    try:
        sample = text.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            sample = text.decode("latin-1")
        except UnicodeDecodeError:
            return False, "text decode failed"
    stripped = sample.lstrip()
    if fmt == "json":
        try:
            json.loads(data.decode("utf-8-sig"))
            return True, "json parsed"
        except Exception as exc:
            return False, f"json parse failed: {exc}"
    if fmt == "xml":
        return stripped.startswith("<"), "expected XML-like leading <"
    if fmt == "html":
        lowered = stripped[:1000].lower()
        return "<html" in lowered or lowered.startswith("<!doctype"), "expected html doctype/html"
    if fmt in {"txt", "csv", "tsv", "yaml"}:
        return True, "text decoded"
    return True, "no format-specific sniff"


def audit_zip(path):
    with zipfile.ZipFile(path) as zf:
        infos = zf.infolist()
        total = 0
        for info in infos:
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or re.match(r"^[A-Za-z]:/", name):
                raise ValueError(f"unsafe absolute member path: {info.filename}")
            parts = [part for part in name.split("/") if part]
            if ".." in parts:
                raise ValueError(f"unsafe parent member path: {info.filename}")
            total += info.file_size
            if total > MAX_BYTES:
                raise ValueError(f"expanded zip size exceeds limit: {total}")
        if len(infos) > 10000:
            raise ValueError(f"too many zip entries: {len(infos)}")
        return len(infos), total


def size_class_from_bytes(n):
    if n < 100 * 1024:
        return "tiny"
    if n < 1024 * 1024:
        return "small"
    if n < 10 * 1024 * 1024:
        return "medium"
    if n < 100 * 1024 * 1024:
        return "large"
    return "xlarge"


def download(candidate):
    dest = PAYLOAD_ROOT / candidate.rel_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT}
    head_meta = {
        "content_length": "",
        "content_type": "",
        "last_modified": "",
        "etag": "",
    }
    if dest.exists() and dest.stat().st_size > 0:
        ok, magic_note = sniff_magic(candidate.format, dest)
        if not ok:
            raise ValueError(magic_note)
        archive_members = 0
        archive_uncompressed = 0
        if candidate.format in {"docx", "pptx", "xlsx", "epub", "zip"}:
            archive_members, archive_uncompressed = audit_zip(dest)
        data = dest.read_bytes()
        return {
            **head_meta,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "media_type": default_media_type(candidate.format),
            "final_url": candidate.source_url,
            "archive_member_count": archive_members,
            "archive_uncompressed_bytes": archive_uncompressed,
            "actual_size_class": size_class_from_bytes(len(data)),
            "magic_ok": "yes",
            "download_status": "reused",
            "download_error": "",
        }
    try:
        h = requests.head(candidate.source_url, timeout=HEAD_TIMEOUT, allow_redirects=True, headers=headers)
        head_meta["content_length"] = h.headers.get("Content-Length", "")
        head_meta["content_type"] = h.headers.get("Content-Type", "")
        head_meta["last_modified"] = h.headers.get("Last-Modified", "")
        head_meta["etag"] = h.headers.get("ETag", "")
    except Exception as exc:
        head_meta["head_error"] = str(exc)

    with requests.get(candidate.source_url, timeout=GET_TIMEOUT, stream=True, allow_redirects=True, headers=headers) as r:
        r.raise_for_status()
        final_url = r.url
        content_type = r.headers.get("Content-Type", "")
        total = 0
        partial = dest.with_suffix(dest.suffix + ".partial")
        sha = hashlib.sha256()
        with partial.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_BYTES:
                    partial.unlink(missing_ok=True)
                    raise ValueError(f"download exceeds {MAX_BYTES} bytes")
                sha.update(chunk)
                f.write(chunk)
        if total == 0:
            partial.unlink(missing_ok=True)
            raise ValueError("zero-byte download")
        ok, magic_note = sniff_magic(candidate.format, partial)
        if not ok:
            partial.unlink(missing_ok=True)
            raise ValueError(magic_note)
        archive_members = 0
        archive_uncompressed = 0
        if candidate.format in {"docx", "pptx", "xlsx", "epub", "zip"}:
            archive_members, archive_uncompressed = audit_zip(partial)
        partial.replace(dest)
        return {
            **head_meta,
            "bytes": total,
            "sha256": sha.hexdigest(),
            "media_type": content_type.split(";")[0] or default_media_type(candidate.format),
            "final_url": final_url,
            "archive_member_count": archive_members,
            "archive_uncompressed_bytes": archive_uncompressed,
            "actual_size_class": size_class_from_bytes(total),
            "magic_ok": "yes",
            "download_status": "downloaded",
            "download_error": "",
        }


def default_media_type(fmt):
    return {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "html": "text/html",
        "epub": "application/epub+zip",
        "txt": "text/plain",
        "csv": "text/csv",
        "tsv": "text/tab-separated-values",
        "json": "application/json",
        "yaml": "application/yaml",
        "xml": "application/xml",
        "zip": "application/zip",
    }.get(fmt, "application/octet-stream")


def row_for_candidate(candidate, status):
    return {
        "bench_id": candidate.bench_id,
        "format": candidate.format,
        "source_group": candidate.source_group,
        "rel_path": candidate.rel_path(),
        "target_rel_path": candidate.rel_path(),
        "size_class": candidate.size_class,
        "actual_size_class": status.get("actual_size_class", ""),
        "bytes": status.get("bytes", ""),
        "sha256": status.get("sha256", ""),
        "media_type": status.get("media_type", default_media_type(candidate.format)),
        "compression": "zip-container" if candidate.format in {"docx", "pptx", "xlsx", "epub", "zip"} else "none",
        "archive_member_count": status.get("archive_member_count", "0"),
        "archive_uncompressed_bytes": status.get("archive_uncompressed_bytes", "0"),
        "source_url": candidate.source_url,
        "landing_url": candidate.landing_url,
        "license_spdx": candidate.license_spdx,
        "license_id": candidate.license_spdx,
        "license_url": candidate.license_url,
        "terms_url": candidate.terms_url,
        "attribution_required": candidate.attribution_required,
        "redistributable": "yes" if candidate.review_status != "pending_review" else "pending_review",
        "fetch_method": "requests-stream",
        "fetched_at": status.get("fetched_at", ""),
        "final_url": status.get("final_url", ""),
        "content_length": status.get("content_length", ""),
        "content_type": status.get("content_type", ""),
        "last_modified": status.get("last_modified", ""),
        "etag": status.get("etag", ""),
        "source_version": candidate.source_version,
        "workload_tags": "real_world;external_bench",
        "parser_stages": candidate.parser_stages(),
        "bench_layers": candidate.bench_layers(),
        "bench_profile": "default",
        "enabled_tier": candidate.enabled_tier,
        "review_status": candidate.review_status,
        "magic_ok": status.get("magic_ok", ""),
        "download_status": status.get("download_status", "planned"),
        "download_error": status.get("download_error", ""),
        "notes": candidate.notes,
    }


def write_license_notes():
    LICENSES.mkdir(parents=True, exist_ok=True)
    text = """# External Bench Source License Notes

This directory records license review anchors for the generated real-world
external_bench corpus. Payload-specific provenance is in MANIFEST.tsv and
SOURCE_CATALOG.tsv.

* US government public-domain guidance: https://www.usa.gov/government-copyright
* UK Open Government Licence v3.0: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
* W3C Document License 2023: https://www.w3.org/copyright/document-license-2023/
* Project Gutenberg license/terms: https://www.gutenberg.org/policy/license.html
* IETF Trust license information: https://trustee.ietf.org/license-info/
* World Bank dataset terms: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets
* Our World in Data reuse policy: https://ourworldindata.org/how-to-use-our-world-in-data
* UniProt license: https://www.uniprot.org/help/license
* Wikidata licensing: https://www.wikidata.org/wiki/Wikidata:Licensing
* SPDX license-list-data license: https://github.com/spdx/license-list-data/blob/main/LICENSE
"""
    (LICENSES / "source_notes.md").write_text(text, encoding="utf-8")


def main():
    candidates = build_candidates()
    blocked_fragments = (
        "admin.opendatani.gov.uk",
        "www.opendatani.gov.uk/dataset/",
        "manchester.gov.uk/open/download",
        "open.manchester.gov.uk/download",
    )
    for cand in candidates:
        if any(fragment in cand.source_url for fragment in blocked_fragments):
            cand.download = False
            cand.enabled_tier = "disabled"
            cand.notes = (cand.notes + " FETCH_BLOCKED in this environment; kept as catalog candidate.").strip()
    for path in (CACHE, FETCH_PLAN_DIR, LICENSES):
        path.mkdir(parents=True, exist_ok=True)

    rows = []
    fetched_rows = []
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for cand in candidates:
        try:
            resolve_github_pin(cand)
        except Exception as exc:
            cand.review_status = "pending_review"
            cand.enabled_tier = "disabled"
            status = {"download_status": "failed", "download_error": f"github pin failed: {exc}", "fetched_at": fetched_at}
            rows.append(row_for_candidate(cand, status))
            print(f"FAIL_PIN\t{cand.bench_id}\t{exc}", flush=True)
            continue
        if not cand.download:
            status = {"download_status": "catalog_only", "download_error": "", "fetched_at": fetched_at}
            rows.append(row_for_candidate(cand, status))
            print(f"CATALOG\t{cand.bench_id}", flush=True)
            continue
        try:
            status = download(cand)
            status["fetched_at"] = fetched_at
            row = row_for_candidate(cand, status)
            rows.append(row)
            fetched_rows.append(row)
            print(f"FETCHED\t{cand.bench_id}\t{row['bytes']}\t{row['sha256']}", flush=True)
            time.sleep(0.2)
        except Exception as exc:
            cand.enabled_tier = "disabled"
            status = {"download_status": "failed", "download_error": str(exc), "fetched_at": fetched_at}
            rows.append(row_for_candidate(cand, status))
            print(f"FAILED\t{cand.bench_id}\t{exc}", flush=True)

    source_fields = [
        "bench_id", "format", "source_group", "source_url", "landing_url", "license_spdx",
        "license_url", "terms_url", "redistributable", "enabled_tier", "review_status",
        "target_rel_path", "size_class", "actual_size_class", "download_status",
        "download_error", "source_version", "notes",
    ]
    plan_fields = [
        "bench_id", "format", "source_group", "size_class", "target_rel_path", "landing_url",
        "source_url", "license_id", "license_url", "terms_url", "bench_layers",
        "enabled_tier", "review_status", "download_status", "notes",
    ]
    manifest_fields = [
        "bench_id", "format", "source_group", "rel_path", "size_class", "actual_size_class",
        "bytes", "sha256", "media_type", "compression", "archive_member_count",
        "archive_uncompressed_bytes", "source_url", "landing_url", "license_spdx",
        "license_url", "terms_url", "attribution_required", "redistributable",
        "fetch_method", "fetched_at", "final_url", "content_length", "content_type",
        "last_modified", "etag", "source_version", "workload_tags", "parser_stages",
        "bench_layers", "bench_profile", "enabled_tier", "review_status", "magic_ok", "notes",
    ]
    header_fields = ["bench_id", "format", "source_group", "content_length", "content_type", "last_modified", "etag", "final_url", "download_status", "download_error"]

    write_tsv(ROOT / "SOURCE_CATALOG.tsv", source_fields, rows)
    write_tsv(FETCH_PLAN_DIR / "FETCH_PLAN.tsv", plan_fields, rows)
    write_tsv(ROOT / "MANIFEST.tsv", manifest_fields, fetched_rows)
    write_tsv(CACHE / "http_metadata.tsv", header_fields, rows)
    write_license_notes()

    print(f"SUMMARY\tcandidates={len(rows)}\tfetched={len(fetched_rows)}\tmanifest={ROOT / 'MANIFEST.tsv'}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
