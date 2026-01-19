# Analog-Layout-Constraint-Extractor

一個基於圖論 (Graph Theory) 的類比電路佈局約束自動提取工具，支援 ALIGN 格式。

此工具能夠讀取 SPICE Netlist，將其轉換為圖形結構，並自動識別常見的類比電路結構（如差動對 Differential Pairs、電流鏡 Current Mirrors），最後輸出對應的佈局約束檔案。

## 功能特色
- **SPICE 解析**: 使用 `PySpice` 解析標準 Netlist。
- **圖形引擎**: 使用 `NetworkX` 建立 Bipartite Graph (Device-Net)。
- **自動識別**:
    - Differential Pairs (同型號、同尺寸、共源極)。
    - Current Mirrors (共閘極、Diode-connected)。
- **ALIGN 支援**: 輸出符合 ALIGN 工具格式的 JSON 約束檔。

## 安裝

需要 Python 3.8+ 環境。

```bash
# 安裝相依套件
pip install PySpice networkx matplotlib
```

注意：`PySpice` 可能需要安裝底層 SPICE 引擎（如 Ngspice）。

## 快速開始

### 1. 準備 Netlist
準備一個 `.sp` 檔案，例如 `amplifier.sp`。

### 2. 執行提取工具
(需自行撰寫或呼叫 `AnalogConstraintExtractor` 類別)

```python
from analog_constraint_extractor import AnalogConstraintExtractor

extractor = AnalogConstraintExtractor()
extractor.read_netlist("amplifier.sp")

# 執行識別
extractor.identify_diff_pairs()
extractor.identify_current_mirrors()

# 輸出結果
extractor.export_constraints("amplifier_constraints.json")
```

## 測試
專案包含自動化測試腳本：

```bash
python3 -m unittest tests/test_extractor.py
```
