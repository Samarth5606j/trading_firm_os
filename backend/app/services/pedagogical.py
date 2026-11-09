import numpy as np

def generate_dual_mode_analysis(ticker: str, market_data: dict, audited_decision: dict) -> dict:
    df = market_data['df']
    curr = market_data['currency_symbol']
    action = audited_decision['final_action']
    
    returns = df['Close'].pct_change().dropna()
    realized_volatility = float(returns.std() * np.sqrt(252) * 100)
    
    risk_free_rate = 0.05
    excess_returns = returns - (risk_free_rate / 252)
    sharpe_ratio = float(np.sqrt(252) * excess_returns.mean() / (returns.std() + 1e-9))
    
    downside_returns = returns[returns < 0]
    sortino_ratio = float(np.sqrt(252) * excess_returns.mean() / (downside_returns.std() + 1e-9))
    
    cum_returns = (1 + returns).cumprod()
    peak = cum_returns.cummax()
    max_drawdown = float(((cum_returns - peak) / peak).min() * 100)

    base_inv = 10000.0 if curr == "₹" else 1000.0
    buffer_pct = 0.025
    
    if action == "BUY":
        target_gain = round(base_inv * (buffer_pct * 1.5), 2)
        max_loss = round(base_inv * buffer_pct, 2)
        scenario_text = (
            f"If testing this setup with {curr}{int(base_inv):,}: "
            f"Expected Target Profit is +{curr}{target_gain:,} (Balance reaches {curr}{int(base_inv + target_gain):,}), "
            f"while your disciplined Safety Stop cuts any loss at -{curr}{max_loss:,} (Balance will never drop below {curr}{int(base_inv - max_loss):,})."
        )
    elif action == "SELL":
        scenario_text = "The committee advises taking profits or exiting. Keeping funds safe in cash is recommended."
    else:
        scenario_text = "The committee recommends holding cash. No immediate edge detected; capital preservation is priority."

    if market_data['rsi'] > 70:
        plain_risk = "The stock is overheating (RSI > 70). Professional traders may take profits shortly, creating downside risk for late buyers."
    elif market_data['rsi'] < 30:
        plain_risk = "Heavy panic selling detected (RSI < 30). While a bargain bounce is possible, buying requires disciplined stop losses."
    else:
        plain_risk = "Momentum is balanced. Risk is strictly confined to general market volatility."

    return {
        "quant_metrics": {
            "realized_volatility_pct": round(realized_volatility, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
        },
        "beginner_guidance": {
            "plain_risk_warning": plain_risk,
            "tangible_currency_scenario": scenario_text,
        }
    }