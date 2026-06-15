# ORIGIN-V OMEGA: API REFERENCE

**Complete Interface Documentation**

---

## MODULE: origin_v_grand_core

### Module Declaration

```systemverilog
module origin_v_grand_core #(
    parameter [511:0] FOUNDER_ROOT_KEY = 512'h0_REPLACE_WITH_YOUR_KEY,
    parameter int NUM_CORES = 1
)(
    // See signal descriptions below
);
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `FOUNDER_ROOT_KEY` | [511:0] | 512'h0 | Founder's bio-entropy key |
| `NUM_CORES` | int | 1 | Number of cores (for multi-core) |

### Ports

#### Clock and Reset

| Port | Direction | Width | Description |
|------|-----------|-------|-------------|
| `clk` | Input | 1 | System clock |
| `rst_n` | Input | 1 | Active-low reset |

#### Transaction Interface (AXI4-Stream)

| Port | Direction | Width | Description |
|------|-----------|-------|-------------|
| `s_axis_tdata` | Input | 128 | Transaction value |
| `s_axis_tvalid` | Input | 1 | Transaction valid |
| `s_axis_tready` | Output | 1 | Transaction ready |

#### Bio-Entropy Interface

| Port | Direction | Width | Description |
|------|-----------|-------|-------------|
| `bio_entropy_in` | Input | 512 | Biological entropy |
| `bio_entropy_valid` | Input | 1 | Entropy valid |

#### Fingerprint Interface

| Port | Direction | Width | Description |
|------|-----------|-------|-------------|
| `fp_sensor_active` | Input | 1 | Fingerprint contact |
| `fp_sensor_data` | Input | 64 | Fingerprint data |

#### System Fund Outputs

| Port | Direction | Width | Description |
|------|-----------|-------|-------------|
| `founder_share` | Output | 128 | 1.00% to Founder |
| `liquidity_pool` | Output | 128 | 3.00% to Liquidity |
| `mesh_maintenance` | Output | 128 | 2.18% to Mesh |
| `public_net` | Output | 128 | 93.82% to User |

#### Status Outputs

| Port | Direction | Width | Description |
|------|-----------|-------|-------------|
| `is_founder` | Output | 1 | Founder status |
| `core_authorized` | Output | 1 | Authorization status |
| `mesh_active` | Output | 1 | Mesh connectivity |
| `civilization_state` | Output | 32 | Node state |
| `error_code` | Output | 8 | Error code |

---

## USAGE EXAMPLES

### Basic Transaction

```systemverilog
// Setup
reg [127:0] tx_value = 128'd10000;  // 100.00 units
reg tx_valid = 1'b0;

// Send transaction
always @(posedge clk) begin
    if (s_axis_tready && !tx_valid) begin
        s_axis_tdata <= tx_value;
        tx_valid <= 1'b1;
    end else if (tx_valid) begin
        tx_valid <= 1'b0;
    end
end
```

### Reading System Funds

```systemverilog
// System funds are available on outputs
wire [127:0] founder = founder_share;
wire [127:0] liquidity = liquidity_pool;
wire [127:0] mesh = mesh_maintenance;
wire [127:0] user = public_net;
```

### Checking Status

```systemverilog
// Check authorization
if (core_authorized && mesh_active) begin
    // System is operational
end

// Check founder status
if (is_founder) begin
    // Founder privileges active
end

// Check error
if (error_code != 8'h00) begin
    // Handle error
    case (error_code)
        8'h01: // ERR_UNAUTHORIZED
        8'h02: // ERR_BIO_TIMEOUT
        8'h03: // ERR_INTEGRITY_FAIL
        // ...
    endcase
end
```

---

**"Complete API for Complete Control"**

*Origin-V Omega API Reference v1.0*
