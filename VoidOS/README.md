# VoidOS Microkernel
**VoidOS** is the bare-metal, non-silicon operating system that drives the VoidOne hardware.

## System Defense
- **Thermodynamic Scheduler**: Applications must clear their hardcoded 6.18% thermal debt limit within a designated wave cycle. 
- **Page Faults**: Failure to manage thermal debt results in an immediate hardware-level thread execution halt to protect system integrity.
- **Memory Footprint**: The microkernel scheduler is entirely self-contained within a strict 4096-byte hardware pagemap.
