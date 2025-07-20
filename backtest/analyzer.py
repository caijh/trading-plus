import pandas as pd


def analyze_results(records):
    df = pd.DataFrame(records, columns=['entry_time', 'exit_time', 'entry_price', 'exit_price', 'reason'])
    df['return_pct'] = (df['exit_price'] - df['entry_price']) / df['entry_price'] * 100
    # df['holding_days'] = (df['exit_time'] - df['entry_time']).dt.days

    print("==== 回测统计结果 ====")
    total_trades = len(df)
    win_rate = (df['return_pct'] > 0).mean() * 100 if total_trades > 0 else 0
    avg_return = df['return_pct'].mean() if total_trades > 0 else 0
    max_drawdown = df['return_pct'].min() if total_trades > 0 else 0
    max_return = df['return_pct'].max() if total_trades > 0 else 0
    print(f"总交易次数: {total_trades}")
    print(f"胜率: {win_rate:.2f}%")
    print(f"平均收益: {avg_return:.2f}%")
    print(f"最大回撤: {max_drawdown:.2f}%")
    print(f"最大收益: {max_return:.2f}%")
    result = {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "average_return_pct": round(avg_return, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "max_return_pct": round(max_return, 2),
    }
    return result
