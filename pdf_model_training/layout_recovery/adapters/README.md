# Layout Recovery Adapters

Adapter work here should convert public layout datasets into parser-facing
region and layout-recovery rows.

Initial target:

```text
DocLayNet page/region annotations -> layout_recovery labels
```

Do not emit convert-layer block semantics such as `paragraph`, `list_item`, or
`heading` as final layout-recovery targets. Text-bearing region information is
allowed only as parser-side region context.
