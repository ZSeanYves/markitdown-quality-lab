# PDF Text Block Roadmap

## Stage 0 Done

Completed already:

* `DocLayNet` smoke and pilot acquisition
* `baseline_v3` feature work
* offline `HGB` teacher training
* teacher quality beyond the original distillation gate
  * `pilot3000_v1 baseline_v3 HGB heldout macro F1 = 0.8097`

Main conclusion from Stage 0:

* continuing to scale `DocLayNet` pages with only the old logistic baseline was
  misleading
* the stronger offline teacher is good enough to justify distillation work

## Stage 1 Current

Current target:

* HGB teacher artifact audit
* HGB feature-importance and error-bucket audit
* `PubTables` specialist scaffold
* distillation policy hardening
* distillation v0 high-confidence hint export

Deliverables:

* local-only teacher audit reports
* tracked `distillation_policy.md`
* tracked `PubTables` specialist adapter skeleton
* tracked roadmap and specialist notes
* tracked hint-export script plus local-only v0 eval

Stage 1 status:

* teacher audit done
* `PubTables` scaffold done
* distillation v0 hint export done
* next step is moving from export to gated hint design, not runtime hookup

## Stage 2 Next

Next target:

* tiny real `PubTables` local-only adapter smoke
* narrow `table_like` / weak `caption` specialist experiment
* teacher + specialist evaluation on boundary slices
* explicit source-separated evaluation
* v1 rule-gated hint design for stable labels

Rules for Stage 2:

* do not pollute `DocLayNet` gold heldout
* keep `PubTables` as specialist-only
* treat `caption` as weak/specialist until proven stable

## Stage 3 Distillation

Distillation target:

* high-confidence routing thresholds
* rule candidates for stable buckets
* compact decision-table candidates
* possible small model candidates if speed and closure stay controlled

Primary buckets to distill first:

* `footer_header_noise`
* `table_like`
* `heading`
* `keep_as_text`
* high-confidence `paragraph`
* high-confidence `list_item`

Buckets that still need caution:

* `caption`
* patent/legal short-numbered lines
* address / affiliation rows
* form-like short rows

## Stage 4 Runtime Preconditions

Only after distillation evidence is mature should runtime be discussed.

Required gates:

* external PDF quality evaluation
* `bash samples/check.sh`
* `bash samples/check_quality.sh --format pdf`
* `bash samples/bench.sh`
* speed regression review
* binary / closure review
* fail-closed behavior review

Only then:

* propose convert-layer gated integration
* keep deterministic rules primary
* keep model influence optional and reversible
