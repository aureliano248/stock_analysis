# Stock Analysis & Backtesting Framework

基于 Python 和 AkShare 的 A 股定投策略回测框架。

## 功能特性

*   **数据源**: 自动获取 AkShare 历史数据并缓存 (支持前复权)。
*   **多策略支持**: 内置多种定投策略，支持策略扩展。
*   **回测引擎**: 模拟逐日交易，计算收益率、总资产、持仓成本等。
*   **可视化**: 自动生成收益率曲线对比图 (PDF)。
*   **配置化**: 通过 `config.py` 集中管理全局参数和策略参数。

## 核心文件

*   `main_v3.py`: **主程序**。根据 `config.py` 中的 `DRAW_STRATEGY_LIST` 批量运行策略，生成对比图和汇总报表。
*   `main_v2.py`: 单策略回测脚本。
*   `strategies.py`: 策略实现类 (策略模式)。
*   `data_loader.py`: 数据获取与预处理。
*   `config.py`: 项目配置文件。

## 支持策略

1.  **FixedInvestment**: 基础定投 (每日/每周/每月固定金额)。
2.  **BenchmarkDropStrategy**: 基准日跌幅加仓 (相比首日跌幅越大买入越多)。
3.  **DynamicBenchmarkDropStrategy**: 动态基准加仓 (相比 MA250 或 60日高点回撤幅度加仓)。
4.  **QuadraticMAStrategy**: 均线偏离度平方加仓 (跌破 MA250 越深，买入倍数呈平方级增加)。
5.  **ProfitRatioStrategy**: 筹码获利比例策略 (基于筹码分布 CYQ 数据动态调整)。

## 使用说明

1.  **环境准备**:
    ```bash
    conda activate stock_analysis
    pip install -r requirements.txt
    ```

2.  **配置策略**:
    修改 `config.py` 设置回测标的 (`SYMBOL`)、时间范围 (`START_DATE`, `END_DATE`) 以及参与对比的策略列表 (`DRAW_STRATEGY_LIST`)。

3.  **运行对比回测**:
    ```bash
    python main_v3.py
    ```
    运行后将在 `figures/` 目录下生成对比图，并在终端打印收益汇总表。
