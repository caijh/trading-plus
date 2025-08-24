import numpy as np
import pandas as pd


def evaluate_strategy(records, risk_free_rate=0.0):
    """
    根据回测交易记录评价策略优劣

    参数：
        records: list of tuples
            每笔交易记录，格式：(entry_time, exit_time, entry_price, exit_price, reason)
        risk_free_rate: float
            无风险收益率，默认0，可用于计算夏普比率

    返回：
        dict: 策略各指标和综合评分
    """
    if not records:
        print("无交易记录，无法评价策略")
        return {}

    df = pd.DataFrame(records, columns=['entry_time', 'exit_time', 'entry_price', 'exit_price', 'reason'])

    # 计算收益率和持仓天数
    df['return_pct'] = (df['exit_price'] - df['entry_price']) / df['entry_price'] * 100
    df['holding_days'] = (df['exit_time'] - df['entry_time']).dt.days

    total_trades = len(df)
    wins = df[df['return_pct'] > 0]
    losses = df[df['return_pct'] <= 0]

    # 基本收益指标
    avg_return = df['return_pct'].mean()  # 平均每笔收益
    win_rate = len(wins) / total_trades * 100  # 胜率
    avg_win = wins['return_pct'].mean() if not wins.empty else 0  # 平均盈利
    avg_loss = losses['return_pct'].mean() if not losses.empty else 0  # 平均亏损
    profit_loss_ratio = -avg_win / avg_loss if avg_loss != 0 else np.inf  # 盈亏比

    # 风险指标
    max_return = df['return_pct'].max()
    max_drawdown = df['return_pct'].min()
    avg_holding_days = df['holding_days'].mean()

    # 夏普比率（年化假设252交易日）
    daily_returns = df['return_pct'] / df['holding_days'].replace(0, 1)  # 避免除0
    if len(daily_returns) > 1:
        sharpe_ratio = (daily_returns.mean() - risk_free_rate / 252) / daily_returns.std() * np.sqrt(252)
    else:
        sharpe_ratio = np.nan

    # 综合评分（可自定义权重）
    score = 0
    # 盈利能力权重
    score += avg_return * 0.3
    score += profit_loss_ratio * 10 * 0.3  # 放大盈亏比权重
    score += win_rate * 0.1
    # 风险控制权重
    score += (0 if max_drawdown < 0 else 100) * 0.1  # 最大回撤越低越好
    score += (sharpe_ratio if not np.isnan(sharpe_ratio) else 0) * 0.2

    result = {
        "total_trades": total_trades,  # 总交易次数
        "win_trades": len(wins),
        "win_rate": round(win_rate, 2),  # 胜率 %
        "average_return_pct": round(avg_return, 2),  # 平均收益率 %
        "avg_win_pct": round(avg_win, 2),  # 平均盈利 %
        "avg_loss_pct": round(avg_loss, 2),  # 平均亏损 %
        "profit_loss_ratio": round(profit_loss_ratio, 2),  # 盈亏比
        "max_return_pct": round(max_return, 2),  # 最大单笔收益 %
        "max_drawdown_pct": round(max_drawdown, 2),  # 最大回撤 %
        "avg_holding_days": round(avg_holding_days, 2),  # 平均持仓天数
        "sharpe_ratio": round(sharpe_ratio, 2),  # 夏普比率
        "score": round(score, 2),  # 综合评分
    }

    print("==== 策略评价结果 ====")
    for k, v in result.items():
        print(f"{k}: {v}")

    return result
