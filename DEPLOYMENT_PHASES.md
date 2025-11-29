# 🚀 AiNex Deployment Phases - Architecture & Flow

**Version:** 2.1.0  
**Status:** ✅ Phase 1 Implementation Complete  
**Timeline:** Phase 1 → Phase 2 → Phase 3

---

## OVERVIEW

AiNex operates in three distinct deployment phases, each with specific checks, safeguards, and capabilities:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │  PHASE 1: PREFLIGHT CHECK 🛡️                      │ │
│  │  Status: ACTIVE                                   │ │
│  │  Duration: ~8 seconds                             │ │
│  │  Progression: AUTO (on dashboard load)            │ │
│  │  Entry Point: Dashboard.tsx (top of viewport)     │ │
│  │  Exit Criteria: All 5 checks PASS ✅              │ │
│  └────────────────────────────────────────────────────┘ │
│                          ↓                             │
│  ┌────────────────────────────────────────────────────┐ │
│  │  PHASE 2: SIMULATION MODE ⚡                      │ │
│  │  Status: READY (awaiting Phase 1 completion)      │ │
│  │  Duration: 15-60 minutes (user configurable)      │ │
│  │  Progression: USER INITIATED                      │ │
│  │  Entry Point: "START SIMULATION MODE" button      │ │
│  │  Exit Criteria: Confidence >= 85%                 │ │
│  └────────────────────────────────────────────────────┘ │
│                          ↓                             │
│  ┌────────────────────────────────────────────────────┐ │
│  │  PHASE 3: LIVE MODE 🔥                            │ │
│  │  Status: LOCKED (requires Phase 2 + Confidence)   │ │
│  │  Duration: Unlimited (until manual stop)          │ │
│  │  Progression: USER INITIATED (with safety lock)   │ │
│  │  Entry Point: "SWITCH TO LIVE MODE" button        │ │
│  │  Exit Criteria: Manual withdrawal or stop         │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## PHASE 1: PREFLIGHT CHECK 🛡️

### Purpose
Validate system readiness before any trading operations. Ensures all critical dependencies are operational.

### Status Indicators
```
✓ PASS  (Green - #00FF9D)   → System ready
⚠ PENDING (Yellow)         → Currently checking
✗ FAIL  (Red)              → Manual intervention required
```

### Checks Performed

| # | Check | Duration | What It Tests | Pass Criteria |
|---|-------|----------|---------------|---------------|
| 1 | **Blockchain** | 1.5s | Network connection to ETH RPC | Connected + responsive |
| 2 | **Wallet** | 1.5s | Valid Ethereum address | Valid address format |
| 3 | **Memory** | 1.0s | Available system memory | 512MB+ available |
| 4 | **Security** | 1.5s | Security protocols active | All enabled |
| 5 | **Network** | 1.0s | Latency to blockchain | < 200ms ping |
| | **TOTAL** | **~8s** | | **All 5 pass** |

### UI Components

**Preflight Collapsed (Default State)**
```
┌────────────────────────────────────────────┐
│ ✓ ⬇ 🛡️ ✓ PREFLIGHT OK        5/5        │
└────────────────────────────────────────────┘
```

**Preflight Expanded (Details)**
```
┌────────────────────────────────────────────────────┐
│ ⬆ 🛡️ ✓ PREFLIGHT OK               5/5           │
├────────────────────────────────────────────────────┤
│ ✓ 📡 BLOCKCHAIN    Blockchain connection OK  ████ │
│ ✓ 💰 WALLET        Wallet address validated  ████ │
│ ✓ 💾 MEMORY        Memory available: 512MB+  ████ │
│ ✓ 🔐 SECURITY      Security protocols active ████ │
│ ✓ ⚡ NETWORK       Network latency: 45ms    ████ │
├────────────────────────────────────────────────────┤
│            [ RE-RUN CHECKS ]                       │
└────────────────────────────────────────────────────┘
```

### Implementation Details

**Component:** `PreflightCheck.tsx`
```typescript
interface PreflightCheckProps {
  onComplete?: (passed: boolean) => void;
}

// Auto-runs on mount
// Can be re-run manually
// Emits completion status to parent
```

**Flow:**
1. Component mounts → Auto-run preflight
2. Each check runs sequentially (1.5-2.5s total delay)
3. Results update in real-time with progress bars
4. On completion → `onComplete(true/false)` callback
5. User can expand/collapse for details
6. User can manually re-run if needed

### Failure Handling

If any check fails:
```
┌────────────────────────────────────────────┐
│ ⚠ 🛡️ ⚠ PREFLIGHT FAILED      3/5       │
├────────────────────────────────────────────┤
│ ✗ 📡 BLOCKCHAIN    Connection timeout     │
│ ✗ 💰 WALLET        Invalid address        │
│ ✓ 💾 MEMORY        Memory available       │
│ ⚠ 🔐 SECURITY      Warning: TLS disabled  │
│ ✓ ⚡ NETWORK       Network latency: 45ms  │
├────────────────────────────────────────────┤
│            [ RE-RUN CHECKS ]               │
└────────────────────────────────────────────┘
```

**User Actions on Failure:**
- Expand details to see error messages
- Fix issue (reconnect wallet, restart service, etc.)
- Click "RE-RUN CHECKS"
- Once all pass → Proceed to Phase 2

---

## PHASE 2: SIMULATION MODE ⚡

### Purpose
Test trading strategy in risk-free simulation using real market data. Build confidence before live trading.

### Activation

**Prerequisites:**
- ✅ Phase 1 Preflight: **PASSED**
- User clicks "START SIMULATION MODE" button (bottom center, blue glow)

**Button State:**
```
PHASE 1 PASSED:
┌─────────────────────────────────────┐
│  ⚡ START SIMULATION MODE ⚡         │
│   (animated bounce, clickable)       │
└─────────────────────────────────────┘

PHASE 1 FAILED:
┌─────────────────────────────────────┐
│  ⚡ AWAITING PREFLIGHT (0%) ⚡       │
│   (disabled, grayed out)             │
└─────────────────────────────────────┘
```

### Simulation Metrics

Real-time dashboard updates:

| Metric | Refresh | Source |
|--------|---------|--------|
| Profit/Hour | Real-time | SimulationEngine |
| Profit/Trade | Real-time | SimulationEngine |
| Trade Frequency | Real-time | Mock data |
| Confidence % | Every 5s | AIOptimizer |
| Strategy Weights | Every 5s | AIOptimizer weights |

### Confidence Progression

```
Time 0s:    0% ░░░░░░░░░░░░░░░░░░░░
Time 60s:  15% ███░░░░░░░░░░░░░░░░
Time 5m:   42% ████████░░░░░░░░░░░
Time 10m:  68% ██████████████░░░░░
Time 15m:  92% ████████████████░░ ← UNLOCKS PHASE 3
Time 20m:  98% ██████████████████░
```

### Safety Interlocks

**Confidence Lock:**
- If confidence < 85% → "SWITCH TO LIVE MODE" disabled
- Button shows: "AWAITING CONFIDENCE (42%)" in gray
- Button re-enabled automatically when confidence ≥ 85%

**UI State:**
```
CONFIDENCE < 85%:
┌──────────────────────────────────────┐
│  ⚡ AWAITING CONFIDENCE (42%) ⚡      │
│  (disabled, 50% opacity)             │
└──────────────────────────────────────┘

CONFIDENCE ≥ 85%:
┌──────────────────────────────────────┐
│  ⚡ SWITCH TO LIVE MODE ⚡            │
│  (enabled, green glow, bounce)       │
└──────────────────────────────────────┘
```

### Exit Criteria

Advance to Phase 3 when:
- ✅ Confidence ≥ 85%
- ✅ User clicks "SWITCH TO LIVE MODE"
- ✅ Self-healing checks pass

---

## PHASE 3: LIVE MODE 🔥

### Purpose
Execute real trading on blockchain with real capital. Maximum performance + maximum risk.

### Activation

**Prerequisites:**
- ✅ Phase 1: Preflight **PASSED**
- ✅ Phase 2: Simulation **COMPLETED** (Confidence ≥ 85%)
- ✅ User confirms: "SWITCH TO LIVE MODE"

**Confirmation Modal:**
```
┌────────────────────────────────────────┐
│  ⚠️  ENTERING LIVE MODE                │
│                                        │
│  You are about to execute REAL trades  │
│  with REAL capital.                    │
│                                        │
│  • Trading will begin immediately     │
│  • Losses are your responsibility      │
│  • You can stop at any time            │
│                                        │
│  [ CONFIRM & GO LIVE ]  [ CANCEL ]     │
└────────────────────────────────────────┘
```

### Live Trading Safeguards

| Safeguard | Mechanism | Trigger |
|-----------|-----------|---------|
| **Stop Loss** | Auto-halt if loss > 10% | Monitor on-chain |
| **Position Size** | Max 5% of balance per trade | Execution layer |
| **Slippage Check** | Reject if > 0.2% | Pre-trade validation |
| **Rate Limit** | Max 10 trades/minute | Executor bot |
| **Emergency Stop** | User button (red) | Manual override |

### Live Mode Indicators

**Active State:**
```
┌─────────────────────────────────────┐
│ 🟢 LIVE MODE ACTIVE                 │
│                                     │
│ ⚡ PROFIT/HOUR: 0.0245 ETH          │
│ 💰 BALANCE: 1.2345 ETH              │
│ 📊 CONFIDENCE: 98%                  │
│ 🎯 TRADES TODAY: 342                │
│                                     │
│  [ WITHDRAW ] [ STOP TRADING ]       │
└─────────────────────────────────────┘
```

### Exit from Phase 3

User can exit by:
1. **Withdraw Funds** → Partial exit, stay in LIVE mode
2. **Stop Trading** → Halt new trades, cash out position
3. **Emergency Stop** (red button) → Immediate halt (may incur losses)

---

## PHASE PROGRESSION DIAGRAM

```
                    ┌──────────────────┐
                    │  PHASE 1: CHECK  │
                    │  🛡️ Preflight   │
                    │  Duration: 8s    │
                    │  Status: Active  │
                    └────────┬─────────┘
                             │
                    ✓ ALL CHECKS PASS
                    (Auto or Re-run)
                             │
                             ▼
                    ┌──────────────────┐
                    │ PHASE 2: SIMULATE│
                    │ ⚡ Test Mode     │
                    │ Duration: 15-60m │
                    │ Status: Ready    │
                    └────────┬─────────┘
                             │
                    ✓ CONFIDENCE ≥ 85%
                    (Real-time updates)
                             │
                             ▼
                    ┌──────────────────┐
                    │ PHASE 3: LIVE    │
                    │ 🔥 Real Trading  │
                    │ Duration: ∞      │
                    │ Status: Locked   │
                    └──────────────────┘
```

---

## CRITICAL STATE MANAGEMENT

### EngineContext State Machine

```typescript
type EngineState = 
  | 'IDLE'        // Waiting for user to start
  | 'BOOTING'     // Phase 1 running
  | 'READY'       // Phase 1 passed, waiting for Phase 2
  | 'SIMULATION'  // Phase 2 active
  | 'TRANSITION'  // Moving from Phase 2 to Phase 3
  | 'LIVE'        // Phase 3 active
```

### State Transitions

```
IDLE
  ├─ User clicks INITIATE
  └─→ BOOTING
       ├─ Phase 1 running
       │  └─ Preflight checks execute
       └─→ READY (if all checks pass)
            ├─ User clicks "START SIMULATION"
            └─→ SIMULATION
                 ├─ Phase 2 running
                 │  └─ AI learns + confidence builds
                 └─→ TRANSITION (when confidence ≥ 85%)
                      ├─ User confirms LIVE
                      └─→ LIVE
                           └─ Phase 3: real trading
```

---

## DASHBOARD LAYOUT BY PHASE

### Phase 1: Preflight Check Focus
```
┌─────────────────────────────────────────┐
│ [Sidebar]  [PREFLIGHT CHECK - EXPANDED] │
│            [Blockchain OK] ✓            │
│            [Wallet OK] ✓                │
│            [Memory OK] ✓                │
│            [Security OK] ✓              │
│            [Network OK] ✓               │
│            [RE-RUN CHECKS]              │
│                                         │
│            [INITIATE button] (enabled)  │
└─────────────────────────────────────────┘
```

### Phase 2: Simulation Active
```
┌──────────────────────────────────────────┐
│ [Sidebar]  [PREFLIGHT CHECK - COLLAPSED]│
│            [✓ PREFLIGHT OK  5/5]        │
│                                         │
│            [Metrics Grid - LIVE UPDATING]
│            [Profit Velocity] [Max]...   │
│            [Confidence: 42%] [progress] │
│            [Strategy Weights]           │
│                                         │
│  [START SIMULATION - DISABLED]          │
│  [AWAITING CONFIDENCE (42%)]            │
└──────────────────────────────────────────┘
```

### Phase 3: Live Mode Active
```
┌──────────────────────────────────────────┐
│ [Sidebar]  [PREFLIGHT CHECK - COLLAPSED]│
│            [✓ PREFLIGHT OK  5/5]        │
│                                         │
│            [🟢 LIVE MODE ACTIVE]        │
│            [Metrics Grid - REAL-TIME]   │
│            [Profit/Hour: 0.0245 ETH]    │
│            [Confidence: 98%]            │
│                                         │
│  [WITHDRAW] [STOP TRADING] [EMERGENCY]  │
└──────────────────────────────────────────┘
```

---

## MONITORING & LOGGING

### Phase 1 Logs
```
[PREFLIGHT] Starting system checks...
[BLOCKCHAIN] ✓ Connected to Ethereum mainnet (45ms latency)
[WALLET] ✓ Address 0x742d... validated
[MEMORY] ✓ 1024MB available
[SECURITY] ✓ All protocols active
[NETWORK] ✓ RPC latency: 45ms
[PREFLIGHT] ✅ All checks passed
```

### Phase 2 Logs
```
[SIMULATION] Starting simulation mode...
[SIMULATION] Boot complete, confidence: 0%
[SIMULATION] Trade #1: +0.00234 ETH profit
[SIMULATION] AI update: weights adjusted
[SIMULATION] Confidence updated: 15% → 28%
[SIMULATION] Trade #150: System is confident
[SIMULATION] Confidence: 85% → UNLOCKING PHASE 3
```

### Phase 3 Logs
```
[LIVE] ✅ Entering live trading mode
[LIVE] Position size: 0.5 ETH
[LIVE] Trade #1: +0.00512 ETH (real capital)
[LIVE] Profit/hour: 0.0245 ETH
[LIVE] Total profit: 1.2345 ETH (cumulative)
[LIVE] Emergency stop requested
[LIVE] Halting trades immediately
[LIVE] Position: CLOSED
```

---

## ROLLBACK PROCEDURES

### Phase 2 → Phase 1 (Confidence Drop)
```
If confidence drops < 70% during Phase 2:
└─ Alert: "Confidence declining - consider pausing"
└─ User can reset and re-run Phase 1
```

### Phase 3 → Phase 2 (Error Detected)
```
If critical error in Phase 3:
└─ Emergency stop activates
└─ Close all positions
└─ Return to READY state
└─ Allow Phase 2 restart
```

### Complete Reset
```
If catastrophic failure:
└─ Return to IDLE
└─ Reset all metrics
└─ Allow fresh Phase 1 start
└─ Preserve historical logs
```

---

## SUMMARY TABLE

| Aspect | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| **Name** | Preflight Check | Simulation | Live Trading |
| **Icon** | 🛡️ | ⚡ | 🔥 |
| **Duration** | ~8s | 15-60m | ∞ |
| **Risk** | None | None | Real Capital |
| **Trigger** | Auto | User + Phase1 | User + Confidence |
| **Real Capital** | ✗ | ✗ | ✓ |
| **Exit** | Auto | Confidence ≥85% | Manual |
| **Safeguards** | 5 checks | Confidence lock | Stop loss + monitoring |
| **Status** | ✅ ACTIVE | Ready | Locked (Phase 2 prerequisite) |

---

**This three-phase system ensures safe, confident progression from system validation through strategy testing to live deployment.**
