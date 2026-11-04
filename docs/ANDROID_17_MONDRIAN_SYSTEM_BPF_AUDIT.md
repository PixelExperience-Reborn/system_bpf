# P1 — system/bpf Android 17 source and mondrian kernel compatibility audit

Date: 2026-11-04. **Source-only audit, not an Android17 BPF port, kernel build or device test.**

## Historical PE source and verified upstream

- Archived PixelExperience-Reborn `system_bpf` branch `seventeen`, SHA `4f894f92daf252f4988ac22a530065f054ae1277`, merges official **Android14 r21**, 2024-01-30. No production source from `seventeen` is modified by this audit.
- Official Android17 r1 `platform/system/bpf` exact Git tree `a02aa20523909870e9c3874931604ea061f2badb`. Source: https://android.googlesource.com/platform/system/bpf/+/refs/tags/android-17.0.0_r1/
- Official Android17 r1 separate `platform/system/bpfprogs` Git tree `238924255acb29e72d0204ca66d4ea0792b84abb`. Source: https://android.googlesource.com/platform/system/bpfprogs/+/refs/tags/android-17.0.0_r1/
- AOSP17 manifest already selects **both** official projects `system/bpf` and `system/bpfprogs`, plus official `system/netd` and `packages/modules/Connectivity`. Neither platform source is replaced by PE.

## Soong, init and executable divergence

**Archived Android14 PE:**
- `bpfloader/Android.bp`: C++ `cc_binary { name: "bpfloader" }`, `srcs: ["BpfLoader.cpp"]`, `libbpf_android`, `libbpf_bcc`, `libnetdutils`, `init_rc: ["bpfloader.rc"]`, `required: ["btfloader", "timeInState.o"]`, debug `bpfRingbufProg.o`.
- `libbpf_android/Android.bp`: C++ `cc_library { name: "libbpf_android" }` with `libbpf_bcc`, `libbpf_minimal` and historic ELF/BPF loading APIs.
- `progs/Android.bp`: old `bpf { name: "bpfRingbufProg.o" }`; this is a **debug/test helper**, not a production network optimization.
- `bpfloader/bpfloader.rc` documents early-init ordering: mount `/sys/fs/bpf`, initialize APEX, load programs and set readiness before `netd`. Its comments explicitly warn failure may lead to `netd`/system-server crash loops.

**Official Android17:**
- Root `Android.bp` exposes `android_bpf_defs`, `bpf_prog_platform_headers`, and `bpf_cc_defaults`; old `bpf_defaults` is not equivalent.
- `loader/Android.bp` now defines `libbpf_android` and a **Rust** `rust_binary { name: "bpfloader" }`, using `bpfloader.rs`, Rust libbpf-rs/libbpf-sys, Rust bindgen, `libandroid_bpfprogs_flags`, logging and `libbackstage_power_flags_rust`.
- Rust loader's `required` BPF programs include `kernelWakelockDuration.bpf`, `timeInState.bpf`, `dmabufIter.bpf`, `bpfLockContention.bpf` and additional debug programs; its kernel-version filters and critical-boot decisions are not equivalent to old metadata.
- Modern `system/bpfprogs` owns `timeInState.c`, `fuseMedia.c`, `dmabufIter.c` and `libbpf_prog` modules plus `android_bpfprogs_flags` AConfig declarations. These are not present in the archived `system_bpf` source under the same ownership.
- The Rust loader's `BpfFileDesc` carries paths, permission bits, owner/group, `critical`, `skip_on_user`, `allow_missing`, `min_kver`/`max_kver` and maps/programs per object; *replacing this with the old C++ loader risks early boot and network failure*.
- Sources: https://android.googlesource.com/platform/system/bpf/+/refs/tags/android-17.0.0_r1/loader/Android.bp ; https://android.googlesource.com/platform/system/bpf/+/refs/tags/android-17.0.0_r1/loader/bpfloader.rs ; https://android.googlesource.com/platform/system/bpfprogs/+/refs/tags/android-17.0.0_r1/Android.bp .

## Historical PE delta reviewed

Commit `9f7c2410317ddd8e7e24d998a40456635514d208`, "Partially revert bpfloader - remove dead code", modifies `libbpf_android/Loader.cpp`, retains a kernel **4.9** map-expectations bypass and DEVMAP approximation for pre-4.14 kernels. Its comment says old `bpfGetFd...` interfaces need kernel >=4.14. The mondrian kernel is based on **Linux 5.10**, but its actual configuration/ABI/backports have not yet been validated for the planned PE-Reborn build. This old 4.9 compatibility revert is **REJECTED** for direct Android17 port and should not override modern map validation or loader errors. Most other sampled history is upstream AOSP cherry-pick/merge lineage and does not justify replacing upstream Android17.

## Kernel 5.10 / mondrian requirements

**Reference-only**: the current LF52406 mondrian kernel, modules and device trees were developed for a LineageOS-based device configuration; new PixelExperience-Reborn Android17 device + common trees must be created independently.

Before a device bring-up:
1. Pin actual kernel source commit/defconfig and kernel modules/devicetrees. Check real Kconfig values for `CONFIG_BPF`, `CONFIG_BPF_SYSCALL`, `CONFIG_BPF_JIT`, `CONFIG_CGROUP_BPF`, `CONFIG_DEBUG_INFO_BTF`, relevant verifier/features/map types and expected tracepoints. **Not all are implied by version 5.10**.
2. Compare `bpfloader.rs` object list and kernel minimums with actual built `*.bpf` programs and `system/bpfprogs`; confirm required/critical vs optional behavior. For example, some extra tracepoints are gated behind 6.1 checks and must **not** be assumed usable on 5.10.
3. Verify mount/pin namespace `/sys/fs/bpf`, APEX readiness, init trigger, map SELinux labels and ownership, `bpf.progs_loaded` behavior and `netd` startup. Do not bypass loader errors with a hardcoded success property.
4. Ensure build graph is consistent for `system/bpf`, `system/bpfprogs`, `system/netd` and Connectivity/Tethering Mainline. Check `netd` BPF stats, policy routing, tethering, traffic permissions, battery/CPU accounting and FUSE/media BPF uses.
5. Test boot, LTE/Wi-Fi DNS/routing/tethering/VPN, per-UID traffic counters, stats/battery, MediaProvider FUSE, and reliable reboot/persistence on **independent PE-Reborn mondrian** product.

## Status / explicit release gates

- [x] Old PE source SHA, Android14 loader/Soong and historical 4.9 patch reviewed.
- [x] Official AOSP17 source trees and Rust loader + separate bpfprogs design identified.
- [x] Host-only archive consistency test added.
- [x] Independent official AOSP17 r1 **tagged source Git trees** fetched and pinned for `system/bpf` and `system/bpfprogs`; Rust loader, Soong and object-file markers verified in [CI PASS #41791055533](https://github.com/PixelExperience-Reborn/system_bpf/actions/runs/41791055533). This is **not** the manifest's repo-sync test or an Android17 build.
- [ ] Staged manifest **joint repo sync** for `system/bpf` and `system/bpfprogs`; new manifest workflow exists but its run is not confirmed.
- [ ] Full AOSP17 Rust/Soong and eBPF compiler verification.
- [ ] Actual kernel 5.10 config, BTF/verifier tracepoints and SELinux labels validated.
- [ ] Physical mondrian boot, `bpfloader`/netd/Connectivity behavior, CTS/VTS and OTA tests.

**Integration decision:** retain the two official AOSP17 repositories. **No old C++ bpfloader, DEVMAP fallback or network/SELinux bypass** is applied. Source audit CI is not evidence of a working BPF stack.
