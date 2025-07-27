# Copilot Instructions for intraday_trading

## 项目架构与核心组件

- **main_strategy.py**：主策略入口，负责策略初始化、主循环、信号融合、下单、风控和日志。调用各类信号检测器和风控模块，实现自动化交易。
- **indicators/**：技术指标与信号检测模块。
  - `peak_valley_detector.py`：分时顶底信号检测，含均线、RSI等指标计算。
  - `second_level_detector.py`：秒级信号检测。
  - `multi_timeframe_fusion.py`：多时间框架信号融合。
- **utils/**：工具与风控模块。
  - `risk_manager.py`：仓位管理、止损止盈、买卖数量计算。
  - `data_manager.py`：历史数据、tick数据、实时指标的获取与处理。
  - `tick_data_processor.py`：tick数据处理与缓存。
- **config.py**：策略参数配置，集中管理股票池、参数、交易时间等。
- **requirements.txt/environment.yml**：依赖管理，部分包需用 pip 安装。

## 关键开发与运行流程

- **环境准备**：优先用 conda 创建 Python 3.8~3.11 环境，主流依赖用 conda 安装，特殊包（如 mgquant、supermind）用 pip 安装。
- **回测/实盘**：策略主循环通过 `handle_bar(context, bar_dict)` 驱动，信号检测与风控解耦。部分交易API（如 supermind）需查阅其文档或用 `dir()`/`help()` 交互探索。
- **日志与异常**：统一用 `logging` 记录，异常捕获后写日志，便于调试和回测复盘。
- **信号融合**：分钟级、秒级、多时间框架信号通过融合器统一输出最终信号。
- **风控与下单**：风控逻辑独立于信号检测，所有下单前均需风控校验。

## 项目约定与模式

- **技术指标计算**：均线、RSI等指标均用 pandas/numpy 实现，返回与输入等长的数组，前部为 NaN。
- **数据流**：数据获取、信号检测、风控、下单严格分层，便于扩展和测试。
- **异常处理**：所有主流程均用 try/except 包裹，防止单只股票异常影响全局。
- **依赖管理**：requirements.txt 仅供 pip 使用，conda 安装需手动拆分。
- **代理与镜像**：如需加速 pip，可用阿里/清华镜像，SSR 需配置 user-rule.txt 代理 PyPI 相关域名。

## 典型用法示例

- 获取移动均线：`_calculate_ma(prices, period)`
- 获取 RSI：`_calculate_rsi(prices, period=14)`
- 获取 tick 数据：`get_tick_data(stock, context, lookback_minutes=10)`
- 策略主循环：`handle_bar(context, bar_dict)`

## 外部依赖与集成

- 依赖 `supermind`、`mgquant` 等第三方包，部分接口需用 `dir()`/`help()` 交互探索。
- 交易API与数据API解耦，便于切换底层实现。

---
如需补充或有不清楚的地方，请反馈具体需求或问题。
