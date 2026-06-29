# markitdown-quality-lab

`markitdown-quality-lab` 是 MoonBit `markitdown` 项目的外部质量与性能语料仓。
它不是主仓 runtime，不包含产品代码，也不是主仓构建依赖。主仓必须能在没有本仓的情况下 build、test、run。

本仓用于管理三类不适合直接放进主仓的资产：

* 外部 quality regression 语料
* 外部 performance benchmark 语料
* PDF/layout/model training、审计和实验资产

## 目录结构

```text
markitdown-quality-lab/
  external_quality/
  external_bench/
  pdf_model_training/
  README.md
  LICENSES.md
```

## 目录职责

### external_quality/

`external_quality/` 是外部质量回归语料目录。

* 顶层 `MANIFEST.tsv` 是正式消费入口。
* 顶层 `SOURCE_CATALOG.tsv` 是来源和 license 追溯入口。
* 样例按 `external_quality/<format>/<source>/...` 组织。
* 主仓 `samples/check_quality.sh` 消费这里的 `MANIFEST.tsv`。
* staging、cache、legacy archive 目录不再是正式入口。

正式样例必须由 manifest row 指向。无法确认来源、授权或用途边界的样例不得进入正式 manifest。

### external_bench/

`external_bench/` 是外部性能 benchmark 语料目录。

* 顶层 `MANIFEST.tsv` 是 benchmark 执行入口。
* 样例按 `external_bench/<format>/<size_class>/...` 组织。
* 主仓 `bench v2` 默认消费这里的 `MANIFEST.tsv`。
* 顶层 `README.md` 说明当前策展 benchmark 语料的组织方式。

Benchmark 结果只代表 same-machine / same-corpus / same-parameters 下的方向性反馈，
用于发现本地回归和相对趋势；它不是通用性能承诺。

### pdf_model_training/

`pdf_model_training/` 保存 PDF/layout/model training、审计和实验资产。

* 它不等同于 shipped runtime capability。
* 它不应被主仓 public-only check 依赖。
* 它当前不纳入 `external_quality/` / `external_bench/` 的结构清洗。
* 具体训练、评测、local-only 数据边界由该目录内部 README、manifest 或报告说明。

## 使用方式

推荐将本仓直接放在主仓目录下：

```text
markitdown/
  markitdown-quality-lab/
```

主仓质量检查读取：

```text
markitdown-quality-lab/external_quality/MANIFEST.tsv
```

主仓 benchmark 检查读取：

```text
markitdown-quality-lab/external_bench/MANIFEST.tsv
```

本仓缺失时，主仓 runtime、parser、converter 和常规测试仍应可运行。

## 数据收录规则

* 每个正式样例必须有 manifest row。
* `external_quality/` 的正式 source 必须能在 `external_quality/SOURCE_CATALOG.tsv` 中追溯。
* `external_bench/` 的策展 row 必须在 `MANIFEST.tsv` 中保留 `source_ref` 和必要的来源说明。
* 每个 source 必须有明确 license 和 source origin。
* 不允许 `UNKNOWN`、空 license 或空 source origin 进入正式 catalog。
* 不允许 `.tmp`、cache、local-only、staging 路径进入正式 manifest。
* 无法确认授权、来源、隐私或再分发边界的样例不能进入正式 manifest。
* 样例 license 只描述样例自身，不改变 `markitdown` 项目代码 license。

## Non-goals

* 不承诺 benchmark 的通用性能结论。
* 不把 OCR、PDF、model experimental asset 描述为已 shipped runtime capability。
* 不把本仓作为主仓构建依赖。
* 不保存 private data、本地 cache、临时下载或未授权数据。
* 不用 legacy staging 目录作为正式消费面。

## 维护原则

* 修改 `MANIFEST.tsv` 或 `SOURCE_CATALOG.tsv` 后，必须同步跑 path check 和 license/source check。
* 大规模迁移前先生成 cleanup / migration plan，再执行。
* `external_quality/` 保持 `README + MANIFEST + SOURCE_CATALOG` 结构；
  `external_bench/` 当前是策展 benchmark 语料面。
* 不要在 README 中手写与 manifest 或 catalog 记录矛盾的信息。
* 本仓文档可以总结政策和状态，但不能替代 manifest/catalog 的机器可读约束。
