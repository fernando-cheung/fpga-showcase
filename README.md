# fpga-showcase

**最近更新**：2026-10-20 —— 首页改成“双 Feature”：`s05.html`（整机 DUC → DDC 回环）+ `showcase.html`（零件级验证），下面再列 s01–s04 四篇原理页。

Fernando Cheung 的 FPGA 基带数据通路笔记站。纯静态页面，无构建步骤、无 CDN、无外部字体；直接打开 `index.html` 或部署到 GitHub Pages 即可。

## 页面结构

| 文件 | 内容 |
|---|---|
| `index.html` | 首页：两个大 Feature（整机 / 零件验证）+ s01–s04 四张原理卡 + 两条阅读线 |
| `showcase.html` | **零件级验证**：s01–s04 四个单模块实验台，6 张 ILA 截图 + 5 份 CSV 逐点对账（原首页） |
| `s01.html` | NCO 原理：相位累加器、查表、相位截断、正交本振 + FPGA 实现 |
| `s02.html` | 复数混频原理：和频/差频、I/Q、CONJ、定点舍入饱和 + FPGA 实现 |
| `s03.html` | FIR 原理：卷积、窗函数、线性相位、Q1.15 + FPGA 实现 |
| `s04.html` | 2× 半带插值/抽取：镜像、半带约束、多相分解、抗混叠 + FPGA 实现 |
| `s05.html` | s05+s06 集成：DUC（FIR → 混频 → 2× 插值）→ DDC 回环、LO_DLY 14/23、2:1 并串定帧 + 上板 ILA |

每篇原理页固定分成「通信原理」和「FPGA 实现」两部分，末尾是验证证据与记忆锚点；
`s05.html` 是「整机篇」，重点在系统顺序、位宽/相位和上板波形；
`showcase.html` 是「零件验证」，只回答“每个模块自己跑起来是什么样”。

## 目录

```
assets/site.css          共享样式（深色绿/琥珀，沿用原展示页配色）
assets/img/*.svg         原理页图表（由真实系数生成）
assets/img/s05-ila-duc.png  s05 DUC 上板 ILA 截图（1870×803）
assets/img/s06-ila-ddc.png  s06 DUC→DDC 回环 ILA 截图（1339×810）
assets/data/*.mem        从 fpga-lab 复制的系数表，供图表生成脚本读取
assets/favicon.svg       favicon
tools/make_figs.py       图表生成脚本（只依赖 numpy；输出 assets/img/*.svg）
```

## 重新生成图表

```bash
python3 tools/make_figs.py
```

脚本读取 `assets/data/fir_coef.mem`（s03 的 47 抽头）和 `assets/data/hb_odd.mem`
（s04 的 30 个奇系数），画出系数、幅频、相位、冲激响应、镜像与混叠示意图。
图表是手写 SVG，不依赖 matplotlib。

## 内容来源

正文数字来自 `fpga-lab` 仓库的 `s01_nco/`–`s06_ddc/` 任务书、`docs/进度.md`、
`docs/学习备忘.md`，以及 2026-10-18/19/20 的 ILA 截图与 CSV。
`s05.html` 用的是 s05 / s06 的 ILA 截图；上板展示页保留原始 base64 内嵌 PNG，
单文件可离线打开。
