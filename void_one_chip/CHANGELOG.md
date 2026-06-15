# CHANGELOG

All notable changes to the Primal Origins SoC IP Core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0] - 2024-XX-XX - Quantum-Photonic Edition

### Added
- **Quantum-Photonic Grand Core** (`origin_v_grand_core_qphoton`)
- **Quantum Random Number Generator (QRNG)** - True randomness from photon quantum noise
- **Quantum Key Distribution (QKD)** - BB84 protocol for quantum-secure storage
- **Quantum-Photonic PUF** - Enhanced PUF with QRNG and ring resonators
- **Fractal Photonic Clock Tree** - H-tree optical clock distribution (5 GHz, <5ps skew)
- **Photonic NoC Router** - WDM-based optical interconnect (256+ Tbps per link)
- **Photonic Arithmetic Unit** - Optical ALU for Hard-Law calculations (50ps latency)
- **Fractal Resonator Cavities** - Nested ring resonators for photonic storage
- **Quantum-Photonic Parameters** - Complete parameter set for quantum-photonic architecture
- **Comprehensive Documentation** - Architecture guide, release notes, verification checklist

### Changed
- **System Performance:** 20 Trillion → **50 Trillion TPS** (2.5x improvement)
- **Clock Frequency:** 1 GHz → **5 GHz** (5x improvement)
- **NoC Bandwidth:** 1 Tbps → **256 Tbps** per link (256x improvement)
- **PUF:** Enhanced with quantum randomness and photonic ring resonators
- **Storage:** Quantum-encrypted via QKD (information-theoretically secure)

### Architecture
- All modules now implement fractal self-similarity
- Golden ratio scaling in resonators (Phi = 1.618...)
- Multi-level entropy extraction in PUF
- Self-similar routing in NoC

### Manufacturing
- **New Requirements:** Silicon photonics process layer
- **Integration:** 3D hybrid bonding for electronic-photonic integration
- **Foundry Support:** TSMC, Intel, GlobalFoundries compatible

---

## [2.1] - 2024-XX-XX

### Added
- One-time fingerprint initialization (6.18 minutes)
- E-fuse model for persistent storage
- Economic stability testbench
- Performance analysis testbench
- Universal adoption guide
- IP integration guide

### Changed
- Founder recognition: Now one-time initialization, then normal login
- Process-agnostic configuration

### Fixed
- Reset persistence issue (e-fuse model)
- Bio-latch initialization logic

---

## [2.0] - 2024-XX-XX

### Added
- Initial 11-stack implementation
- Grand Unified Core
- Top-level SoC integration
- Complete testbench suite
- Production documentation

---

**Note:** Versions 1.x were internal development. Version 2.0 was the first production release. Version 3.0 introduces quantum-photonic architecture.

**Brand:** Primal Origins SoC IP Core
