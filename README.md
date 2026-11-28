# TuiHub datasets

本仓库包含了 TuiHub 项目中使用的数据集。

---

This repository contains the datasets used in the TuiHub project.

**TOC**

- [Game Detection Rules](#game-detection-rules)
- [Game ID List](#game-id-list)
- [VNDB ID Connector](#vndb-id-connector)

## Game Detection Rules

提供本地游戏目录的离线识别规则，覆盖常见商店安装清单（Steam、GOG）与游戏引擎目录结构（Unity、Unreal、Ren’Py、RPG Maker、KiriKiri、Godot 等），用于定位安装目录、查找启动文件、提取标题及外部平台 ID 线索。
规则基于常见发行包的目录特征编写，无法覆盖所有打包变体，出现漏判或误判属于预期现象，如果你发现问题可以提交 issue。

---

Provides offline detection rules for local game directories, covering store installation manifests (Steam, GOG) and common game engine layouts (Unity, Unreal, Ren’Py, RPG Maker, KiriKiri, Godot, etc.) to locate installations, find launch files, extract titles, and read external platform ID hints.  
The rules match common release layouts and have not been verified against every packaging variant. Missed or false matches are expected; if you find any problems, you can submit an issue.

### Usage

完整规则下载地址：[https://datasets.tuihub.org/game_detection_rules.json](https://datasets.tuihub.org/game_detection_rules.json)  
JSON Schema 地址：[https://datasets.tuihub.org/schemas/game_detection_rules_schema.json](https://datasets.tuihub.org/schemas/game_detection_rules_schema.json)  
规则文件包含以下顶层字段：
- traversal: 对象，遍历时跳过的目录名匹配模式
- defaults: 对象，默认忽略的启动文件名模式与通用文件名词干
- storeManifests: 数组，商店安装清单识别规则（支持游戏目录内清单与库级 `.acf` 清单）
- engines: 数组，各引擎的目录布局、启动文件与标题提取规则
- hints: 数组，识别游戏目录后提取外部平台 ID 线索的规则

规则仅依据本地文件特征匹配，`hints` 提取的 ID 仅作关联线索，不代表商店归属确认。跨语言实现所需的执行语义、测试样本与 Python 参考实现见 [src/game_detection_rules](https://github.com/tuihub/tuihub-datasets/tree/master/src/game_detection_rules)。

如果你需要自动化更新规则，可以利用版本文件检测更新：[https://datasets.tuihub.org/build.json](https://datasets.tuihub.org/build.json)

---

Download address of the complete rules: [https://datasets.tuihub.org/game_detection_rules.json](https://datasets.tuihub.org/game_detection_rules.json)  
JSON Schema address: [https://datasets.tuihub.org/schemas/game_detection_rules_schema.json](https://datasets.tuihub.org/schemas/game_detection_rules_schema.json)  
The rule file contains the following top-level fields:
- traversal: object, directory name patterns skipped during traversal
- defaults: object, default ignored entry patterns and generic filename stems
- storeManifests: array, store installation manifest rules (covering both directory-local manifests and library-level `.acf` manifests)
- engines: array, per-engine directory layouts, launch entries, and title extractors
- hints: array, rules that extract external platform ID hints after a game root is identified

Rules match local file signatures only; IDs extracted by `hints` are unverified correlation hints rather than confirmed store installations. Execution semantics, conformance cases, and the Python reference implementation live in [src/game_detection_rules](https://github.com/tuihub/tuihub-datasets/tree/master/src/game_detection_rules).

If you need to automatically update the rules, you can use the version file to detect updates: [https://datasets.tuihub.org/build.json](https://datasets.tuihub.org/build.json)

## Game ID List

WIP

## VNDB ID Connector

[![Run vndb_id_connector](https://github.com/tuihub/tuihub-datasets/actions/workflows/vndb_id_connector.yml/badge.svg)](https://github.com/tuihub/tuihub-datasets/actions/workflows/vndb_id_connector.yml)
[![Dynamic JSON Badge](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Ftuihub%2Ftuihub-datasets%2Factions%2Fworkflows%2Fvndb_id_connector.yml%2Fruns%3Fstatus%3Dcompleted%26per_page%3D1&query=%24.workflow_runs%5B0%5D.run_started_at&label=Update%20at)](https://github.com/tuihub/tuihub-datasets/actions/workflows/vndb_id_connector.yml)

目前提供视觉小说在 [VNDB](https://vndb.org/)，[Bangumi](https://bgm.tv/) 和 [Steam](https://store.steampowered.com/)
三个平台上的 ID 对应关系。
数据集由脚本辅助生成，没有经过完全的人工校对，出现缺漏错误都是预期内的现象，如果你发现问题可以提交 issue。  
计划至少每个月更新一次，但我们不提供任何持续更新的承诺。

本数据集遵循 [CC0](https://creativecommons.org/publicdomain/zero/1.0/deed.zh) 协议。这代表任何使用了本数据集的项目都**无需**注明数据来源，且自行承担因使用本数据集而产生的法律责任。

---

Currently, the ID correspondence between visual novels on [VNDB](https://vndb.org/), [Bangumi](https://bgm.tv/)
and [Steam](https://store.steampowered.com/) is provided.  
The dataset is generated with the help of scripts, and has not been fully manually verified. Missing and errors are
expected. If you find any problems, you can submit an issue.  
We plan to update at least once a month, but we do not provide any guarantee of continuous updates.

This dataset is licensed under the [CC0](https://creativecommons.org/publicdomain/zero/1.0/deed.en) license. This means
that any project that uses this dataset **does not** need to indicate the source of the data and assumes the legal
responsibility for using this dataset.

### Usage

*目前仅提供完整数据集下载，如果你需要在线查询请提交 issue 请求*  

完整数据集下载地址：[https://datasets.tuihub.org/vndb_id_connector.json](https://datasets.tuihub.org/vndb_id_connector.json)  
数据集每个条目包含以下字段：
- vndb: 字符串，VNDB 的 vid，不存在时为空字符串
- bangumi: 字符串，Bangumi 的条目 id，不存在时为空字符串
- steam: 字符串，Steam 的 app id，不存在时为空字符串
- names: 字符串数组，包含中英日三种语言的多种版本的游戏名称，至少包含一条

由于存在各种特例，数据集中三种平台的 ID 及游戏名称均有可能重复出现，这不是错误，在要求唯一性时请自行处理。

如果你需要自动化更新数据集，可以利用版本文件检测更新：[https://datasets.tuihub.org/build.json](https://datasets.tuihub.org/build.json) 

---

*Currently, only the complete dataset is provided for download. If you need to query online, please submit an issue*

Download address of the complete dataset: [https://datasets.tuihub.org/vndb_id_connector.json](https://datasets.tuihub.org/vndb_id_connector.json)  
Each entry in the dataset contains the following fields:
- vndb: string, VNDB vid, empty string when it does not exist
- bangumi: string, Bangumi entry id, empty string when it does not exist
- steam: string, Steam app id, empty string when it does not exist
- names: string array, contains multiple versions of game names in Chinese, English and Japanese, at least one

Due to various special cases, the IDs and game names of the three platforms may appear repeatedly in the dataset. This
is not an error. Please handle it yourself when uniqueness is required.

If you need to automatically update the dataset, you can use the version file to detect updates: [https://datasets.tuihub.org/build.json](https://datasets.tuihub.org/build.json)
