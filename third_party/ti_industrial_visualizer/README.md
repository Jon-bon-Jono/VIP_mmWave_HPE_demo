# Texas Instruments Industrial Visualizer Integration

This directory contains a project-local copy of the Texas Instruments (TI) Industrial Visualizer source code used for TI mmWave radar demo tools.

The Industrial Visualizer is included here as a **donor/reference codebase** for the VIP mmWave HPE runtime. It is useful for understanding how TI's host-side tools connect to a radar, send configuration commands, parse UART packets, and render point clouds/tracked objects. It should **not** become the architecture of the final runtime system.

The final runtime architecture should remain ROS 2-centred:

```text
radar source / replay source / camera source
    -> canonical ROS topics
        -> inference / sync / logging / visualisation sinks
```

Qt should be used for GUI rendering and user interaction. ROS 2 should remain the system backbone.

---

## Environment setup

TI's Visualizer dependency stack is old. The recommended Python version is **Python 3.8**, because TI's pinned `numpy==1.19.4` and `PySide2==5.15.2.1` are more reliable there than on newer Python versions.

To run the visualizer, create the environment from the supplied environment file:

```bash
conda env create -f ti_industrial_viz.yml
conda activate ti_industrial_viz
```

## Running the Industrial Visualizer from source
Run:

```bash
conda activate ti_industrial_viz
cd Industrial_Visualizer
python gui_main.py
```

## Environment compatibility warning

The `ti_industrial_viz` environment is only intended for running the Industrial Visualizer source code as a standalone reference/debugging tool. It is not an official runtime environment for this project. Any code borrowed from the Industrial Visualizer and integrated into the ROS 2 runtime must work in the project runtime environment defined by `vip_ros2_jazzy_dev.yml`. New runtime dependencies may be introduced (e.g. Qt), but developers must choose versions that are compatible with `vip_ros2_jazzy_dev.yml` and update the runtime environment file accordingly. Code should not rely on package versions that only work in the standalone TI visualizer environment.

## Suggested repository workflow

The integration branch for this work is:

```text
feature/ti-industrial-visualiser
```

General rule:

```text
If a change is generally useful to the project and does not depend on the TI integration:
    branch from main → PR to main

If a change depends on the TI integration branch:
    branch from feature/ti-industrial-visualiser → PR back into feature/ti-industrial-visualiser
```

Do not rebase the shared integration branch after people have branched from it. Students may rebase their own small feature branches if they know what they are doing, but the shared integration branch should keep stable history.

Whenever useful work lands in `main`, regularly merge `main` into the integration branch:

```bash
git checkout feature/ti-industrial-visualiser
git pull
git merge origin/main
git push
```

This should be done at least weekly and after any major PR into `main`. Do not wait until the end of the integration effort.

### Example workflow: independent logging work

```bash
git checkout main
git pull
git checkout -b feature/logging-runtime-core
# make changes
git push -u origin feature/logging-runtime-core
```

Open a PR into `main`.

After it merges, the integration branch owner should pull `main` into the TI integration branch:

```bash
git checkout feature/ti-industrial-visualiser
git pull
git merge origin/main
git push
```

### Example workflow: TI integration work

```bash
git checkout feature/ti-industrial-visualiser
git pull
git checkout -b feature/ti-driver-refactor
# make changes
git push -u origin feature/ti-driver-refactor
```

Open a PR into `feature/ti-industrial-visualiser`, not directly into `main`.


## Intended role of this code

The Industrial Visualizer is a standalone Python/Qt application. In TI's original workflow, the GUI owns the full runtime:

```text
Industrial Visualizer
    -> opens CLI/data serial ports
    -> sends a radar .cfg file
    -> starts/stops the radar
    -> reads binary UART frames
    -> parses TLVs
    -> renders point cloud and tracked objects
```

In `vip_hpe_runtime`, that responsibility must be split differently:

```text
IWR6843 / MMWAVEICBOOST
    -> ROS 2 radar source node
        -> /radar/points and related diagnostics
            -> runtime GUI / model inference / logging / replay tools
```

Use this third-party code for:

- understanding TI configuration flow;
- understanding UART packet framing and TLV parsing;
- borrowing visualisation ideas for point clouds, tracks, boundary boxes, and diagnostics;
- comparing our ROS output against a known TI-style visualiser;
- running a standalone debugging tool when needed.

Do **not** use this third-party code as the top-level runtime architecture.

---

## Current radar assumptions

The current project radar is an IWR6843-based radar connected through MMWAVEICBOOST. It appears to be running a 'TI 3D People Counting' style firmware that performs onboard detection and tracking, then streams point cloud and tracked-object information to the host over UART.

Important working assumptions:

- We will avoid reflashing the radar with updated/custom firmware unless there is a clear reason to do so.
- The currently flashed firmware does **not** recognise the newer `presenceBoundaryBox` command.
- The checked-in Industrial Visualizer source should be treated as the current working baseline for this branch.
- Students should not change low-level serial settings, parser assumptions, or radar configuration commands unless their task explicitly requires it and the change is documented.
- The example radar config file  `Industrial_Visualizer/ODS_LivingLab_Corner.cfg` file is a runtime configuration file sent to the radar by the host. It is not firmware.
- The example radar config file was used for an internal dataset we collected (the same dataset which the 07_SW.pickle replay file is from). The `staticBoundaryBox`, `boundaryBox` and `sensorPosition` have been configured based on the size of the lab and placement of the radar.

The radar host workflow is:

```text
CLI/control UART:
    host sends configuration commands and start/stop commands

Data UART:
    radar streams binary frame packets containing point cloud / tracking output
```

In the ROS runtime, the **radar source/driver** should own both serial ports. GUI widgets, loggers, and downstream processing nodes should consume ROS topics or call ROS services/actions. They should not open the radar COM ports directly.

---

## Existing runtime design to preserve

The current ROS runtime already has the right design direction:

- `vip_hpe_msgs` defines canonical messages such as `RadarFrame`, `RadarPoint`, and `PersonPose3DArray`.
- `vip_hpe_runtime/config/sessions/*.yaml` defines session-level configuration.
- `vip_hpe_runtime/launch/session.launch.py` launches a session from YAML.
- `vip_hpe_runtime/launching/builders.py` maps session config entries to ROS nodes.
- `RadarReplayNode` currently publishes replayed radar frames to `/radar/points`.
- `AnimatedPlotNode` currently acts as a lightweight Matplotlib visualisation sink.

The live radar integration should extend this pattern. It should not introduce a separate TI-shaped runtime path.

The target direction should support these options:

```text
sources:
  radar:
    kind: replay
```

and:

```text
sources:
  radar:
    kind: live_iwr6843_ti_people_counting
```

Both should result in the same topic contract:

```text
/radar/points  ->  vip_hpe_msgs/RadarFrame
```

Downstream pose inference, synchronisation, logging, and visualisation should not need to know whether the radar data came from replay or live hardware.

---

## Proposed runtime architecture

### Core idea

Replace the source-specific `RadarReplayNode` pattern with a generic `RadarSourceNode` pattern.

```text
RadarSourceNode  (ROS 2 node)
    owns one RadarSource implementation, e.g.:
        ReplayRadarSource
        Iwr6843PeopleCountingRadarSource
        future radar source implementations
```

The ROS node handles:

- ROS parameters;
- publishers;
- diagnostics;
- services/actions for runtime control;
- session lifecycle and shutdown;
- conversion from project-level Python objects to ROS messages.

The `RadarSource` implementation handles:

- opening/closing the data source;
- configuration;
- start/stop;
- reading frames;
- parsing device-specific data;
- returning project-level Python frame objects.

`RadarSource` subclasses should **not** depend on `rclpy`. This keeps them testable without launching ROS.

### Suggested `RadarSource` interface

A small abstract base class or protocol is likely useful:

```text
RadarSource
    open()
    configure()
    start()
    read_frame()
    stop()
    close()
```

This interface should stay small. Do not force all future radars to expose identical low-level capabilities. The runtime only needs to know whether a source can be opened, configured, started, read from, stopped, and closed.

A replay source can implement this interface by wrapping the existing replay code, such as `LivingLabSubjectReplay` and `ReplayCursor`. A live radar driver can implement the same interface by owning serial ports and parsing binary radar frames.

### Driver ownership rules

The live radar driver/source should be the only object that owns the corresponding radar serial ports.

```text
Iwr6843PeopleCountingRadarSource
    owns CLI serial port
    owns data serial port
    sends config/start/stop commands
    reads and parses binary data stream
```

No Qt widget, logger, recorder, parser test, or visualisation component should directly share those serial ports during an active session.

The GUI may request actions such as `start`, `stop`, `restart`, or `load profile`, but those actions should go through ROS services/actions exposed by the radar node.

---

## Suggested file structure

This is a suggested structure, not a fixed requirement. It is intended to keep ROS code, parser code, GUI code, and third-party vendor code separated.

```text
src/vip_hpe_runtime/vip_hpe_runtime/
    radar_sources/
        base.py                  # RadarSource interface/protocol and shared dataclasses
        replay.py                # ReplayRadarSource wrapping current replay classes
        registry.py              # maps kind -> RadarSource factory
        ti_people_counting.py    # live IWR6843/TI People Counting source
        ti_protocol.py           # TI packet framing, frame headers, TLV parsing
        ti_config.py             # config/profile loading and validation

    nodes/
        radar_source_node.py     # generic ROS node owning a RadarSource
        qt_runtime_gui_node.py   # Qt GUI ROS entry point, if implemented as ROS executable
        animated_plot_node.py    # legacy/simple visualiser; may be phased out
        ...

    gui/
        app.py                   # QApplication creation and top-level wiring
        main_window.py           # QMainWindow with stacked pages
        home_page.py             # session setup / YAML builder page
        session_page.py          # main runtime visualisation page
        radar_view_widget.py     # pyqtgraph/OpenGL point cloud + pose visualisation
        diagnostics_panel.py     # runtime status, topic rates, parser/driver state
        ros_bridge.py            # ROS subscriptions/services bridged into Qt safely
        session_config_builder.py
        session_launcher.py

    launching/
        builders.py              # extend builders for radar_source_node and Qt GUI
        validation.py            # validate live/replay radar config variants
        config.py                # session config loading helpers
```

Avoid creating a separate ROS package such as `vip_ti_iwr6843` at this stage unless the integration grows large enough to justify it. A separate package may become useful later, but for now it would encourage one package per radar and fragment the runtime design.

If a future split is needed, prefer a generic package name such as `vip_hpe_radar_drivers` rather than a package named after one specific radar.

---

## Session configuration direction

The session YAML (e.g. `src/vip_hpe_runtime/config/sessions/replay_pc_gt_pose_visualize.yaml`) should remain the main orchestration format. The homepage/lander GUI should build the same session config structure that developers can also provide directly.

Example replay radar source:

```yaml
sources:
  radar:
    enabled: true
    kind: replay
    params:
      pickle_path: data/ll_replay/07_SW.pickle
      start_index: 35000
      end_index: -1
      playback_hz: 10.0
      loop: true
      gtrack_filtering: true
```

Example live radar source:

```yaml
sources:
  radar:
    enabled: true
    kind: live_iwr6843_ti_people_counting
    params:
      profile_name: living_lab_corner
      cfg_path: config/radar/ODS_LivingLab_Corner.cfg
      cli_port: COM3
      data_port: COM4
      frame_id: radar_link
      auto_start: true
```

To make dynamic testing more efficient, developers should continue to be able to bypass the homepage/lander GUI and launch directly from YAML:

```bash
ros2 launch vip_hpe_runtime session.launch.py session_config:=path/to/session.yaml
```

The GUI homepage should therefore be a session config builder, not a separate hidden configuration system.

---

## Front-end / GUI direction

`AnimatedPlotNode` can be phased out as the main visualiser. It may still be useful as a small lightweight debugging visualiser if students want a simple 3D pose + point cloud plot during development.

The main GUI should be Qt-based and structured around one top-level window:

```text
RuntimeGuiApp
    QApplication
    MainWindow(QMainWindow)
        QStackedWidget
            HomePage(QWidget)
            SessionPage(QWidget)
    GuiRosBridge / QtRosBridge
```

### Homepage / lander

The homepage should handle session setup:

- choose replay vs live radar mode;
- choose radar profile;
- select radar `.cfg` file;
- select relevant ports or runtime options;
- choose pose mode;
- choose logging/recording options;
- validate required files and fields;
- generate a session YAML/data structure;
- optionally launch the session using the existing launch path.

The homepage may perform lightweight preflight checks, but it should not become the long-running owner of the radar serial ports. The radar source node owns the radar during an active session.

### Main session page

The main session page should replace the runtime visualisation role currently played by `AnimatedPlotNode`.

It should:

- subscribe to `/radar/points`;
- subscribe to `/pose/people`;
- optionally subscribe to radar tracks/diagnostics if those topics are added;
- render point cloud, pose, coordinate axes, room bounds, and optional tracked targets;
- show status such as frame rate, dropped frames, parser errors, and runtime state;
- request actions through ROS services/actions rather than directly operating hardware.

### Qt and ROS threading

Qt widgets should live on the Qt main thread. ROS callbacks should not directly mutate Qt widgets.

Use a bridge pattern:

```text
ROS callback
    -> stores message in cache or emits Qt signal
        -> Qt main thread updates widgets/render state
```

A `QTimer`-based render loop is preferred over redrawing immediately on every ROS message:

```text
ROS messages arrive at sensor/runtime rate
    -> latest state cache updated
Qt render timer fires at display rate
    -> render latest available state
```

---

## What can be reused from the Industrial Visualizer

Good reuse targets:

- serial configuration flow as a behavioural reference;
- packet framing and TLV parsing logic as a parser reference;
- point-cloud rendering ideas;
- tracked-target rendering ideas;
- boundary box / field-of-view display ideas;
- GUI status and diagnostics ideas;
- config/profile selection ideas for development/debug mode.

Avoid copying:

- GUI ownership of radar serial ports;
- parser code buried inside Qt widgets;
- TI demo selection as the project runtime model;
- direct widget updates from stream/parser callbacks;
- untracked modifications to vendor code.

Project-owned code should live under `src/vip_hpe_runtime`. Vendor/reference code should remain under `third_party/ti_industrial_visualizer`.

---

## Suggested work packages

These work packages are suggestions. They are deliberately concrete enough to guide implementation, but students should still keep PRs small and preserve the existing runtime architecture.

### WP1 — RadarSource abstraction and replay refactor

Goal: replace the current source-specific radar replay node pattern with a generic radar source pattern.

Suggested implementation targets:

- introduce a `RadarSource` interface/protocol;
- introduce a project-level `RadarFrameData` or similar internal Python data structure if useful;
- implement `ReplayRadarSource` by wrapping the existing replay classes (`LivingLabSubjectReplay` and `ReplayCursor`);
- implement a registry/factory that maps `sources.radar.kind` to a source implementation;
- replace or adapt `RadarReplayNode` into `RadarSourceNode`.

Suggested files/classes:

```text
radar_sources/base.py
    RadarSource
    RadarFrameData

radar_sources/replay.py
    ReplayRadarSource

radar_sources/registry.py
    create_radar_source(kind, params)

nodes/radar_source_node.py
    RadarSourceNode
```

(can be somewhat similar to builder pattern used in `vip_hpe_core/preprocessing`)

Expected outcome:

- `kind: replay` still publishes `vip_hpe_msgs/RadarFrame` to `/radar/points`;
- downstream nodes behave exactly as before;
- replay logic is no longer tied to a replay-specific ROS node class.

### WP2 — Live IWR6843/TI People Counting source

Goal: implement a live radar source that satisfies the same `RadarSource` lifecycle as replay. 

Suggested implementation targets:

- implement a live source/driver for the currently supported IWR6843 TI People Counting setup;
- keep serial ownership inside the source/driver;
- keep ROS/rclpy out of the source class;
- make radar configuration/start/stop part of the driver lifecycle;
- return project-level frame objects that can be converted to `RadarFrame`.

Suggested files/classes:

```text
radar_sources/ti_people_counting.py
    Iwr6843PeopleCountingRadarSource

radar_sources/ti_config.py
    TiRadarProfile
    TiConfigLoader
    TiConfigApplier

radar_sources/ti_protocol.py
    TiPacketFramer
    TiTlvParser
    TiFrameAdapter
```

Expected outcome:

- `kind: live_iwr6843_ti_people_counting` can be selected in session YAML;
- the same `RadarSourceNode` publishes live frames to `/radar/points`;
- no GUI component opens the radar serial ports.

### WP3 — TI packet parser isolation and tests

Goal: isolate byte-stream parsing from ROS and Qt so it can be tested independently. 

Suggested implementation targets:

- parse complete binary frames from a byte stream;
- parse frame headers and TLVs;
- convert parsed packets into project-level frame objects;
- handle malformed frames, incomplete frames, and unknown TLVs gracefully;
- either add tests using short captured or synthetic byte streams or save raw byte streams at the serial transport/parser boundary to serve as testing data so that parser behaviour can be tested without physical radar access.

Suggested files/classes:

```text
radar_sources/ti_protocol.py
    TiPacketFramer
    TiFrameHeader
    TiTlv
    TiTlvParser
    TiFrameAdapter

tests/runtime/
    parser tests for valid/incomplete/malformed frames
```

Expected outcome:

- parser logic can be tested without ROS, Qt, or physical radar hardware;
- parser errors are explicit and diagnosable;
- future parser changes are less likely to silently break live operation.

### WP4 — Session config support for live radar

Goal: make live radar operation fit the same YAML-driven session model as replay.

Suggested implementation targets:

- extend session validation for multiple radar source kinds;
- extend launch builders so `sources.radar.kind` selects the generic radar source node;
- add example session YAMLs for replay and live radar;
- keep the same `/radar/points` output topic regardless of source.

Suggested files/classes:

```text
launching/validation.py
    validate radar source variants

launching/builders.py
    build_radar_source_node(...)
    RADAR_BUILDERS or source registry support

config/sessions/
    example replay session
    example live radar session
```

Expected outcome:

- developers can launch replay or live radar by changing YAML;
- downstream pose/visualisation nodes do not change;
- session config remains the single source of runtime truth.

### WP5 — Message contract review

Goal: decide whether the current `vip_hpe_msgs/RadarFrame` message is sufficient for live TI output.

Suggested implementation targets:

- compare current replay point fields with live radar point fields;
- decide how to represent target IDs or tracker association if available;
- decide whether tracked targets need a generic project message;
- avoid overfitting messages to one TI firmware version.

Possible message additions:

```text
vip_hpe_msgs/msg/TrackedTarget.msg
vip_hpe_msgs/msg/TrackedTargetArray.msg
vip_hpe_msgs/msg/RadarStatus.msg
```

Expected outcome:

- `RadarFrame` remains stable for point cloud consumers;
- tracked targets are represented generically if they are useful;
- downstream code is not tied to TI-specific TLV names.

### WP6 — Qt runtime GUI replacement for AnimatedPlotNode

Goal: replace the current Matplotlib visualisation sink with a Qt/pyqtgraph-based GUI.

Suggested implementation targets:

- create one top-level `QMainWindow` with stacked pages;
- implement a homepage/session setup page;
- implement a main runtime session page;
- render radar point cloud and pose data from ROS topics;
- optionally render tracked targets, boundary boxes, axes, and diagnostics;
- keep rendering independent of message arrival using cached latest state and a Qt timer.

Suggested files/classes:

```text
gui/app.py
    RuntimeGuiApp

gui/main_window.py
    MainWindow

gui/home_page.py
    HomePage

gui/session_page.py
    SessionPage

gui/radar_view_widget.py
    RadarViewWidget

gui/diagnostics_panel.py
    DiagnosticsPanel

nodes/qt_runtime_gui_node.py
    optional ROS executable entry point for the GUI
```

Expected outcome:

- `AnimatedPlotNode` is no longer the main visualiser;
- the new GUI subscribes to the same canonical runtime topics;
- a lightweight Matplotlib visualiser may remain only as a debugging tool if students find it useful.

### WP7 — GUI ROS bridge and safe Qt/ROS threading

Goal: connect the Qt GUI to ROS topics/services without making ROS callbacks directly mutate widgets.

Suggested implementation targets:

- implement a bridge object that owns the GUI's ROS node/subscriptions/service clients;
- use Qt signals, queues, or controlled polling to move data into the GUI thread;
- keep the GUI responsive under live radar load;
- support clean shutdown when the GUI closes.

Suggested files/classes:

```text
gui/ros_bridge.py
    GuiRosBridge
    RosWorker
```

Expected outcome:

- GUI receives `/radar/points` and `/pose/people` safely;
- ROS callbacks do not directly update Qt widgets;
- session page rendering remains smooth and debuggable.

### WP8 — Homepage/session builder

Goal: make the GUI homepage build the same session config structure used by direct YAML launch (e.g. `src/vip_hpe_runtime/config/sessions/replay_pc_gt_pose_visualize.yaml`).

Suggested implementation targets:

- create a session config builder object independent of Qt widgets;
- support replay and live radar modes;
- support selecting radar profile and `.cfg` path;
- support selecting pose mode, visualisation mode, logging mode, and output directory;
- validate required fields before launching;
- save generated YAML so runs are reproducible.

Suggested files/classes:

```text
gui/session_config_builder.py
    SessionConfigBuilder
    SessionConfigValidationResult

gui/home_page.py
    HomePage

gui/session_launcher.py
    SessionLauncher
```

Expected outcome:

- users can start from a GUI homepage;
- developers can skip the homepage and pass YAML directly;
- homepage does not become a hidden second runtime configuration system.

### WP9 — Radar diagnostics and runtime status

Goal: make live radar failures visible to developers and users.

Suggested implementation targets:

- expose radar source state: disconnected, configured, streaming, stopped, error;
- track frame rate, dropped frames, parse failures, unknown TLVs, no-data timeouts, and command failures;
- publish diagnostics/status through ROS;
- display status in the GUI.

Suggested files/classes:

```text
radar_sources/base.py
    RadarSourceStatus

nodes/radar_source_node.py
    diagnostics/status publishing

gui/diagnostics_panel.py
    status display
```

Expected outcome:

- failures are not hidden in terminal output;
- GUI can distinguish connection, configuration, streaming, and parser problems;
- logs contain enough information to debug hardware/runtime issues.

### WP10 — Logging and replay compatibility

Goal: ensure live radar output can be recorded and later replayed through the same runtime path.

Suggested implementation targets:

- record canonical ROS topics such as `/radar/points` and `/pose/people`;
- optionally record raw radar frames for parser debugging, if appropriate;
- record session metadata such as config path, profile, source kind, frame ID, and runtime settings;
- ensure recorded live data can be replayed without the physical radar connected.

Expected outcome:

- live sessions can become replay sessions;
- parser/runtime bugs can be reproduced offline;
- logging does not depend on the GUI owning hardware.

---

## Documentation for working with the radar

### 3D People Counting Demo Software Implementation Guide — Rev 1.0

Main technical reference for the relevant TI demo family. It explains the host/radar setup, configuration flow, onboard detection/tracking architecture, task model, and UART output format.

https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/1023/3D_5F00_people_5F00_counting_5F00_demo_5F00_implementation_5F00_guide.pdf

### Detection Layer Parameter Tuning Guide for the 3D People Counting Demo — Rev 1.0

Explains configurable detection-layer parameters and points to the implementation guide for lower-level details. Verify commands against the actual device and current project config before changing runtime settings.

https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/1023/3D_5F00_people_5F00_counting_5F00_detection_5F00_layer_5F00_tuning_5F00_guide.pdf

### Group Tracker Parameter Tuning Guide for the 3D People Counting Demo — Rev 1.0/1.1

Explains the group tracker/GTRACK layer, including boundary boxes, sensor position, gating, allocation, state transitions, acceleration limits, and tracking configuration. The tracker can be useful for coarse person localisation and filtering, but it should not be treated as high-accuracy pose estimation.

https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/1023/3D_5F00_people_5F00_counting_5F00_tracker_5F00_layer_5F00_tuning_5F00_guide.pdf

### Design Guide: TIDEP-01000 — People Tracking and Counting Reference Design Using mmWave Radar Sensor

High-level reference design document for the IWR6843 people-counting application. It covers IWR6843ISK, IWR6843ISK-ODS, AOP variants, and the onboard Capon beamforming plus tracking architecture.

https://www.ti.com/lit/ug/tidue71d/tidue71d.pdf

### mmWave SDK User Guide — SDK 3.5.x / 3.6.x

Useful if we eventually need to understand SDK-level build, flashing, DPM/DPC/DPU architecture, or firmware source code. Secondary for current work because the plan is to avoid reflashing/reprogramming unless necessary.

https://dr-download-cdn.ti.com/software-development/software-development-kit-sdk/MD-PIrUeCYr3X/03.06.00.00-LTS/mmwave_sdk_user_guide.pdf

### 60 GHz mmWave Sensor EVM User Guide

Useful for board setup, switches/jumpers, ports, and power considerations.

https://www.ti.com/lit/ug/swru546e/swru546e.pdf

### mmWaveICBoost and Antenna Module User Guide

Useful for MMWAVEICBOOST-specific setup, antenna module mounting, SOP mode, power, and interface details.

https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/1023/0753.swru546c_2D002D002D002D00_mmWaveICBoost-and-Antenna-Module.pdf

---
