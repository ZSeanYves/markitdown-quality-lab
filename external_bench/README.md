# Curated External Bench Corpus

`external_bench/` 是当前给主仓 `bench v2` 使用的正式 benchmark 语料面。

当前目录只保留 runner 直接消费的策展 payload：

```text
external_bench/
  README.md
  MANIFEST.tsv
  FORMAT_MATRIX.md
  <format>/
    <size_class>/
      <file>
```

说明：

* 主仓默认读取 `external_bench/MANIFEST.tsv`。
* `rel_path` 直接指向本目录下的策展 payload。
* `source_ref` 保留来源锚点；每一行的来源说明以 `MANIFEST.tsv` 为准。
* 主仓必须能在没有这个目录的情况下完成 build、unit test 和 repo-local regression。

这个目录描述的是“正式 benchmark 消费面”，不是“所有外部原始来源池”。
