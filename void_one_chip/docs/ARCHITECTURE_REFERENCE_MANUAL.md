# ORIGIN-V OMEGA: ARCHITECTURE REFERENCE MANUAL

**Version:** 1.0  
**Status:** Draft  
**For:** SoC Designers and IP Integrators

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [11-Stack Architecture](#11-stack-architecture)
3. [Register Map](#register-map)
4. [Signal Descriptions](#signal-descriptions)
5. [Timing Diagrams](#timing-diagrams)
6. [State Machines](#state-machines)
7. [Programming Model](#programming-model)

---

## OVERVIEW

The Origin-V Omega is an 11-Stack SoC IP Core that implements Hard-Law economic rules directly in silicon. This manual describes the complete architecture for integrators.

---

## 11-STACK ARCHITECTURE

### Stack Hierarchy

**TIER 1: SILICON KERNEL (Physical & Immutable)**
- Stack 01: Physical Sovereignty (SRAM-PUF)
- Stack 02: Hard-Law (SMF Unit - 6.18% economic shunt)
- Stack 03: Bio-Latch (Biological entropy + fingerprint)
- Stack 04: Fractal NoC (4D Hyper-Torus router)

**TIER 2: SOVEREIGN INTERFACE (Hardware Hooks)**
- Stack 05: Sovereign Storage (AES-256 encryption)
- Stack 06: Mesh Network (Excommunication logic)
- Stack 07: Pulse (Velocity accumulator)

**TIER 3: CIVILIZATION FIRMWARE (State & Governance)**
- Stack 08: Assets (Token/NFT register)
- Stack 09: Governance (Merit-based voting)
- Stack 10: Civilization (State broadcast)
- Stack 11: Singularity (Global mesh integration)

---

## REGISTER MAP

### System Fund Registers (Read-Only)

| Address | Name | Width | Description |
|---------|------|-------|-------------|
| 0x0000 | `founder_share` | 128 | 1.00% to Founder |
| 0x0008 | `liquidity_pool` | 128 | 3.00% to Liquidity |
| 0x0010 | `mesh_maintenance` | 128 | 2.18% to Mesh |
| 0x0018 | `public_net` | 128 | 93.82% to User |

### Status Registers

| Address | Name | Width | Description |
|---------|------|-------|-------------|
| 0x0020 | `is_founder` | 1 | Founder status |
| 0x0021 | `core_authorized` | 1 | Core authorization |
| 0x0022 | `mesh_active` | 1 | Mesh connectivity |
| 0x0024 | `civilization_state` | 32 | Node state |
| 0x0028 | `error_code` | 8 | Error status |

### Pulse & Governance

| Address | Name | Width | Description |
|---------|------|-------|-------------|
| 0x0030 | `pulse_balance` | 64 | Pulse currency balance |
| 0x0038 | `governance_weight` | 64 | Voting weight |

---

## SIGNAL DESCRIPTIONS

### Clock and Reset

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `clk` | Input | 1 | System clock (1.0 GHz @ 3nm) |
| `rst_n` | Input | 1 | Active-low reset (asynchronous) |

### Transaction Interface (AXI4-Stream)

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `s_axis_tdata` | Input | 128 | Transaction value (fixed-point) |
| `s_axis_tvalid` | Input | 1 | Transaction valid |
| `s_axis_tready` | Output | 1 | Transaction ready |

### Bio-Entropy Interface

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `bio_entropy_in` | Input | 512 | Biological entropy data |
| `bio_entropy_valid` | Input | 1 | Entropy valid |

### Fingerprint Sensor Interface

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `fp_sensor_active` | Input | 1 | Fingerprint contact detected |
| `fp_sensor_data` | Input | 64 | Fingerprint pattern data |

---

## TIMING DIAGRAMS

### Transaction Flow

```
Clock:     __/‾\__/‾\__/‾\__/‾\__/‾\__/‾\__/‾\__/‾\__
s_axis_tvalid:  ___/‾\___________________
s_axis_tdata:   ___[TX]___________________
s_axis_tready:  __/‾‾‾‾\___________________
founder_share:  ________[1%]_______________
liquidity_pool: ________[3%]_______________
public_net:     ________[93.82%]___________
```

### Founder Recognition (One-Time)

```
Clock:     __/‾\__/‾\__/‾\__/‾\__/‾\__/‾\__/‾\__/‾\__
fp_sensor_active: ___/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\___ (6.18 min)
sys_init_phase1:  _______________________/‾\___
sys_init_phase2:  _________________________/‾\_
founder_init_complete: ______________________/‾\__
is_founder:       _________________________/‾\__
```

---

## STATE MACHINES

### Bio-Latch State Machine

```
[RESET]
   |
   v
[ENTROPY_WAIT] <-- [ENTROPY_TIMEOUT]
   |
   v
[ENTROPY_VALID] --> [FOUNDER_CHECK]
   |                      |
   |                      v
   |              [ONE_TIME_INIT?]
   |                      |
   |                      v
   |              [FINGERPRINT_HOLD (6.18 min)]
   |                      |
   |                      v
   |              [INIT_COMPLETE]
   |                      |
   v                      v
[NORMAL_LOGIN] <--------[FOUNDER_ACTIVE]
```

### SMF Unit State Machine

```
[IDLE]
   |
   v
[TRANSACTION_RECEIVED]
   |
   v
[CALCULATE_SPLITS]
   |  1.00% Founder
   |  3.00% Liquidity
   |  2.18% Mesh
   |  93.82% Public
   |
   v
[INTEGRITY_CHECK]
   |
   |--[PASS]--> [AUTHORIZED] --> [OUTPUT]
   |
   |--[FAIL]--> [BRICK_CHIP] --> [DEAD]
```

---

## PROGRAMMING MODEL

### Transaction Format

```c
typedef struct {
    uint128_t value;      // Transaction value (fixed-point: 10000 = 100.00)
    uint8_t  reserved[16];
} transaction_t;
```

### Response Format

```c
typedef struct {
    uint128_t founder_share;      // 1.00%
    uint128_t liquidity_pool;     // 3.00%
    uint128_t mesh_maintenance;   // 2.18%
    uint128_t public_net;         // 93.82%
    uint8_t   core_authorized;    // 1 if authorized
    uint8_t   error_code;         // Error status
} response_t;
```

### Example Usage

```c
// Send transaction
transaction_t tx;
tx.value = 10000;  // 100.00 units

// Wait for ready
while (!s_axis_tready) { wait(); }

// Send
s_axis_tdata = tx.value;
s_axis_tvalid = 1;

// Wait for response
wait();

// Read outputs
response_t resp;
resp.founder_share = founder_share;
resp.liquidity_pool = liquidity_pool;
resp.mesh_maintenance = mesh_maintenance;
resp.public_net = public_net;
resp.core_authorized = core_authorized;
resp.error_code = error_code;
```

---

## ERROR CODES

| Code | Name | Description |
|------|------|-------------|
| 0x00 | ERR_NONE | No error |
| 0x01 | ERR_UNAUTHORIZED | Unauthorized access |
| 0x02 | ERR_BIO_TIMEOUT | Bio-entropy timeout |
| 0x03 | ERR_INTEGRITY_FAIL | Hard-Law integrity failure |
| 0x04 | ERR_NOC_OVERFLOW | NoC overflow |
| 0x05 | ERR_DOUBLE_SPEND | Double-spend detected |

---

## PERFORMANCE CHARACTERISTICS

### Timing

- **Transaction Latency:** < 10ns (single cycle)
- **Throughput:** 1 Billion TPS (per core @ 1GHz)
- **Pipeline Depth:** 2 stages (SMF unit)

### Area (Estimated)

- **Single Core:** ~0.05 mm² (3nm)
- **4-Core Cluster:** ~0.2 mm² (3nm)

### Power (Estimated)

- **Single Core:** ~0.1 W @ 1GHz (3nm)
- **4-Core Cluster:** ~0.4 W @ 1GHz (3nm)

---

**"Code is Law. Architecture is Enforcement."**

*Origin-V Omega Architecture Reference Manual v1.0*
