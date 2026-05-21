# markitdown-quality-lab

External quality corpus payloads and PDF layout-classifier training/eval assets
for `markitdown`.

This sibling working tree is not a release artifact of the main repository.
The main repo reads it through:

* `MARKITDOWN_QUALITY_LAB`
* `MARKITDOWN_QUALITY_CORPUS`
* `MARKITDOWN_LAYOUT_LAB`
* `MARKITDOWN_LAYOUT_MODEL`

Normal conversion runtime does not depend on this tree.

Preferred local deployment is repo-local:

```bash
cd /path/to/markitdown
git clone git@github.com:ZSeanYves/markitdown-quality-lab.git markitdown-quality-lab
```

For external-quality manifests, canonical payload references should use
corpus-root-relative `sources/...` paths. See
[corpus/README.md](./corpus/README.md) for migration policy and examples.
