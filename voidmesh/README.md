# VoidMesh Platform & Web Portal

This directory houses the specifications and portal assets for **VoidMesh** (publicly branded as **"Void"**)—the decentralized peer-to-peer social networking platform and web portal of the Void Ecosystem.

## Directory Structure
- **[voidmesh.logos](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidmesh/voidmesh.logos)**: The core peer-to-peer connection protocol, sliding-window network frame sync, and neural network weight-slice consensus logic.
- **[manifest.yaml](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidmesh/manifest.yaml)**: YAML declaration of PWA (Progressive Web Application) install metadata.
- **[vtp_config.yaml](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidmesh/vtp_config.yaml)**: Configuration options for the Virtual Threshold Portal (VTP) edge servers.
- **[void_portal_icon.png](file:///c:/Users/voidi/OneDrive/Desktop/VOID%20Empire/voidmesh/void_portal_icon.png)**: The official gold portal wordmark icon used for client identification.

## Architectural Integration with VoidOS
VoidMesh coordinates network frames and synchronizes cognitive attention weights across edge nodes, while **VoidOS** (the supervisor operating system) schedules task slices and manages low-level hardware memory registers. This ensures absolute independence from centralized cloud APIs.

* **Connection Protocol**: Pre-handshake challenge-response authentication occurs at the socket level. Nodes solve verification checks before accessing sliding-window buffers.
* **Weight Consensus**: Attention weight updates are distributed across active peers. Node responses must match a majority consensus before state mutations are committed.

## Sovereign Client Portal Downloads

| Download Target | Target Architecture | File Path | Compilation Engine | Features / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **Truth Desktop Client Engine** | Win32 Standalone x64 | `voidos/app_targets/truth_desktop.exe` | `logosc_v3.exe` | Zero-dependency, native Win32 window surface mapping, hardware accelerated. |
| **Truth Mobile Client Core** | Android APK (ARM64) | `voidos/app_targets/truth.apk` | `logosc_v3.exe` | Freestanding mobile client, OpenGL ES rendering, local TLI execution. |
| **VoidStudio Native IDE** | Win32 Standalone x64 | `logos/ide/voidstudio.exe` | `logosc_v3.exe` | Full-scale editor, TextMate token grammar parser, concurrent inline AST diagnostics. |

> [!NOTE]
> All distributed executables and application packages are 100% autonomous, zero-dependency, native binaries generated directly by the local self-hosting compilation engine (`logosc_v3.exe`) running under VoidOS. No browser runtime overhead or corporate web engine wrappers are bundled.
