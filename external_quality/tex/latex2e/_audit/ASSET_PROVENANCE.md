# LaTeX2e PNG graphics fixture audit

- Minimal document: `graphics-png-minimal.tex`
- Upstream test basis: https://github.com/latex3/latex2e/blob/develop/required/graphics/testfiles/braces-compat-01.lvt
- Sidecar: `foo.bar.png`
- Exact sidecar URL: https://github.com/latex3/latex2e/blob/develop/required/graphics/testfiles/support/foo.bar.png
- Sidecar SHA256: `5c932cf2400fc8da2f1ac52f772d016f8db244e0c4d16067db71271e92613114`
- Source catalog id: `latex2e_samples`
- License: LPPL-1.3c
- Local license mirror: `external_quality/tex/latex2e/LICENSE-latex2e.txt`

The minimal `.tex` file isolates one supported `includegraphics` branch from
the official graphics test while retaining the exact official PNG payload.
