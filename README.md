# TuiHub datasets

本仓库包含了 TuiHub 项目中使用的数据集。

---

This repository contains the datasets used in the TuiHub project.

**TOC**

- [Game ID List](#game-id-list)
- [VNDB ID Connector](#vndb-id-connector)

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
