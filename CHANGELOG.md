# Changelog

All notable changes to the Asymmetric Grid Bot will be documented in this file.

## [2.1.1] - 2026-02-08

### 🚀 Major Update: Asymmetric Grid + Compounding

**New Features:**
- ✅ Asymmetric grid strategy (1% buy / 1.5% sell)
- ✅ True compounding (trade sizes grow with portfolio)
- ✅ Enhanced logging with trade size growth tracking
- ✅ Improved dashboard showing compounding metrics

**Performance:**
- 50% more profit per sell vs symmetric grid
- Exponential growth through compounding
- Proven in 13.5h live trading (+0.6-1.0% profit)

**Technical:**
- Dynamic trade size calculation (5% of current portfolio)
- Trade size growth tracking and logging
- Enhanced status display with compounding metrics

### Testing:
- ✅ Paper trading: 9.5 hours (4 trades, +1.29% growth)
- ✅ Live trading: 13.5 hours (5 trades, profitable)
- ✅ Zero errors, 100% uptime

---

## [2.1.0] - 2026-02-07

### Initial Dual Trigger Implementation

**Features:**
- Dual trigger mode (buy and sell active simultaneously)
- Symmetric grid (1% buy / 1% sell)
- Fixed trade sizes
- Paper and live trading modes
- Rich TUI dashboard
- Interactive setup wizard

**Issues Found:**
- Fee death spiral in downtrends
- Fixed trade sizes (no compounding)
- Symmetric triggers not optimal for profit

**Status:** Deprecated - replaced by v2.1.1

---

## Upcoming

### [2.2.0] - Planned
- Multiple trading pairs
- Portfolio rebalancing
- Advanced analytics
- Performance metrics

### [3.0.0 - APEX] - In Development
- 7 trading strategies
- ML-powered regime detection
- Multi-timeframe analysis
- Web dashboard
- Dynamic capital allocation

---

## Version History

- **v2.1.1** - Current (Asymmetric + Compounding) ✅
- **v2.1.0** - Deprecated (Symmetric, fixed sizes)
- **v2.0.x** - Early experiments
- **v1.x** - Prototype phase
