#!/bin/bash
# anti_freeze.sh — ONE-TIME phone settings so Android stops freezing background Chrome and killing Termux/proot.
# NOT run automatically. George decides. Each line is reversible (settings delete / device_config delete).
# Source: 2026-10-14 deep-research report, sections A and "Concrete commands". Samsung warning below is single-source.
set -x
# 1. Android 14–16 cached-apps freezer OFF. Use the word "disabled", NOT the number 0 (One UI 8.x reported reboot loops with 0).
adb shell settings put global cached_apps_freezer disabled
adb shell device_config put activity_manager_native_boot use_freezer false
# 2. Phantom-process killer OFF (stops signal-9 on Termux + proot children).
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent"
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
adb shell settings put global settings_enable_monitor_phantom_procs false
# 3. Chrome and Termux exempt from Doze / background limits.
adb shell dumpsys deviceidle whitelist +com.android.chrome
adb shell dumpsys deviceidle whitelist +com.termux
adb shell cmd appops set com.android.chrome RUN_IN_BACKGROUND allow
adb shell cmd appops set com.android.chrome RUN_ANY_IN_BACKGROUND allow
adb shell cmd appops set com.termux RUN_IN_BACKGROUND allow
adb shell cmd appops set com.termux RUN_ANY_IN_BACKGROUND allow
# 4. Screen stays on while charging; apps may share the screen (split screen).
adb shell settings put global stay_on_while_plugged_in 7
adb shell settings put global force_resizable_activities 1
adb shell settings put global enable_non_resizable_multi_window 1
