# 复现与验证

本文记录分析的运行环境、已完成的检查和已知限制。主分析默认读取仓库内的
`data/derived/redblue_teamgames.csv.gz`；从原始数据重建的说明见
[使用说明](../使用说明.md)和[数据来源](../data/raw/README.md)。

## 检查入口

在仓库根目录、安装 `requirements-tested.txt` 中的依赖后运行：

```bash
python -m unittest discover -s tests
python src/audit_data.py
python src/paper_claim_audit.py
```

完整分析与作图使用 `python run_all.py`。
[GitHub 持续集成](https://github.com/CSNOOB6226/lol-blue-side-advantage/actions)
执行单元测试、数据审计和文档结果审计；它不包含完整分析流水线。

## 完整分析验证（2026-10-10）

以下记录来自基于提交 `5642429` 的工作副本，运行环境为 macOS、Python 3.13；
直接依赖版本见 `requirements-tested.txt`。

| 检查 | 结果 |
|---|---|
| 完整分析 `python run_all.py` | 全部通过，75.449 秒 |
| 主仓库单元测试 | 16 项通过，0.153 秒 |
| `make check` | 通过，0.183 秒 |
| README 主要数值与重新生成的结果 | 一致 |
| Elo 嵌套模型 | 满秩并收敛，伪 R² 为 0.0926 |

15 分钟蓝方平均经济领先为 274.61，95% CI [246.26, 302.95]。
该完整流水线记录来自 macOS；完整流水线在 Ubuntu 上的运行尚未验证。

## 数据与补充材料

主数据包含 86,074 条队伍比赛记录，对应 43,037 场比赛。
无损压缩后的 CSV 内容校验值（解压后 SHA-256）为：

```text
99594186fae7af18af0c83711b6eaf2491e8efc98804014c478b07f6686dfe90
```

补充材料位于 `supplementary.zip`，顶层目录为 `supplementary/`，包含 191 个文件。
其中有 64 个 Python 文件和 45 个 JavaScript 模块；连同主分析与测试，共 136 个源码文件。
用途、可选依赖和输入条件见[补充材料说明](../supplementary/README.md)，
完整路径见[源码索引](SOURCE_INDEX.md)。

部分历史文稿的链接目标、Word 模板和原始报告图片未随源码包分发；
相关报告构建代码可能需要自行准备输入文档、图片或系统字体。

## 早期验证记录

| 日期 | 验证范围与结果 |
|---|---|
| 2026-09-24 | 完整主分析 14 个步骤完成；主仓库单元测试 13 项、补充论文材料审计测试 6 项通过；91 个 Python 文件和 45 个 JavaScript 模块语法检查通过。 |
| 2026-10-01 | 单元测试、数据审计和结果审计通过；数据内容与模型设定未变，未重新运行完整分析。 |
| 2026-10-07 | macOS、Python 3.13.12 下，13 项单元测试、数据结构审计及结果与文档一致性审计通过；91 个 Python 文件语法检查通过，数据校验值一致；未重新运行完整分析。 |

## 范围与限制

- 已记录的分析运行使用随包附带的派生数据，没有重新下载或更新原始 CSV，也未执行全量 `--from-raw` 重建。
- `team_strength.py` 的历史运行中出现过一次 `statsmodels` 最大似然未收敛警告。程序完成，已发布结果的回归检查通过；这不等于每个模型都获得了可靠收敛，引用详细模型估计前仍应复核优化诊断。
- 补充研究、Word 构建和演示稿源码经过语法与收录检查，未全部重新生成历史报告或演示稿。额外输入、字体和调用接口见[补充材料说明](../supplementary/README.md)。
