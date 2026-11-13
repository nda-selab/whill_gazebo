# whill_gazebo

WHILL関連の走行実験に使用する、ROS 2 / Gazebo用のシミュレーションパッケージです。四輪ロボット、IMU・3D LiDAR、障害物を含むワールドと、実験を一括起動するlaunchファイルを提供します。

主な用途は、物理シミュレーションで走行したロボットの軌跡を記録し、別のセンサーモデルで時間反転して再現する「Exact Replay」の検証です。通常走行時と逆再生時のセンサーデータ・真値姿勢を、それぞれrosbagに保存する構成です。

本パッケージはモデルと起動設定を担当します。走行制御、軌跡の記録・逆再生、rosbag記録の実装は、関連する別パッケージにあります。

## ディレクトリ構成

```text
whill_gazebo/
├── CMakeLists.txt
├── package.xml
├── launch/
│   └── exact_replay_experiment.launch.py
├── models/
│   ├── four_wheel_robot/
│   │   ├── model.config
│   │   └── model.sdf
│   ├── exact_replay_rig/
│   │   ├── model.config
│   │   └── model.sdf
│   └── test_environment/
│       ├── model.config
│       └── model.sdf
└── worlds/
    ├── exact_replay_validation.sdf
    └── simple_diff_drive.sdf
```

| ファイル | 内容 |
| --- | --- |
| [exact_replay_experiment.launch.py](launch/exact_replay_experiment.launch.py) | Gazebo、ROSブリッジ、走行制御、記録ノードの一括起動 |
| [four_wheel_robot/model.sdf](models/four_wheel_robot/model.sdf) | 四輪の差動駆動ロボットとセンサー |
| [exact_replay_rig/model.sdf](models/exact_replay_rig/model.sdf) | 軌跡の逆再生用センサーモデルと独自プラグインの設定 |
| [test_environment/model.sdf](models/test_environment/model.sdf) | 地面、壁、2つの箱、円柱からなる静的環境 |
| [exact_replay_validation.sdf](worlds/exact_replay_validation.sdf) | 通常走行モデルと逆再生モデルを配置した実験用ワールド |
| [simple_diff_drive.sdf](worlds/simple_diff_drive.sdf) | 差動二輪とキャスターを備えたロボットの簡易ワールド。標準のlaunchでは使用しません |

`ament_cmake`を使用し、`models/`、`worlds/`、`launch/`をパッケージの共有ディレクトリへインストールします。本パッケージ自身ではC++ノードやプラグインをビルドしません。

## 前提環境と関連パッケージ

以下の手順はROS 2 HumbleとIgnition Gazebo Fortress（Gazebo 6）を前提としています。launchは`ign gazebo`を呼び出し、SDFはIgnition系プラグイン名を使用します。関連するExact Replayプラグインも`ignition-gazebo6`にリンクします。

| パッケージ・ツール | 用途 |
| --- | --- |
| ROS 2 Humble、`colcon`、`ament_cmake` | ビルドとROSノードの実行 |
| Ignition Gazebo Fortress | 物理・センサーシミュレーション |
| `ros_gz_bridge` | GazeboとROS 2間のトピック変換 |
| rosbag2とSQLite3ストレージ | 実験データの記録 |
| `whill_trajectory_control` | `fixed_profile_runner`と走行設定`fixed_profile.yaml` |
| `whill_exact_replay` | Gazeboプラグイン`libwhill_exact_replay.so` |
| `whill_experiment_recorder` | 往路・逆再生のrosbag記録を管理する`bag_recorder` |

標準起動ではGazebo GUIと、Ogre2を使用するGPU LiDARを動かすための描画環境が必要です。

以下では、関連パッケージを同じワークスペースに配置しているものとします。

```text
~/ws_whill_sim/src/
├── whill_gazebo/
├── whill_trajectory_control/
├── whill_exact_replay/
└── whill_experiment_recorder/
```

## ビルドと起動

依存するROS・Gazeboパッケージをインストールした環境で実行します。

```bash
source /opt/ros/humble/setup.bash
cd ~/ws_whill_sim
colcon build --packages-up-to whill_gazebo
source install/setup.bash

ros2 launch whill_gazebo exact_replay_experiment.launch.py
```

ビルド済みの場合は、新しいターミナルで環境を読み込んで起動できます。

```bash
source /opt/ros/humble/setup.bash
source ~/ws_whill_sim/install/setup.bash
ros2 launch whill_gazebo exact_replay_experiment.launch.py
```

launchはモデル検索用の`IGN_GAZEBO_RESOURCE_PATH`と、独自プラグイン検索用の`IGN_GAZEBO_SYSTEM_PLUGIN_PATH`をGazeboプロセスに設定します。通常の起動では手動設定は不要です。

### 実験の進行と終了

起動後は、接続と記録の準備が整うと自動で実験が始まります。

1. Gazeboとの通信ブリッジが接続するまで待機します。
2. 往路用のrosbagを準備し、既定では1秒待って軌跡の記録と走行を開始します。
3. 設定された速度指令に従って走行します。既定の往路は13秒です。
4. 往路の記録を止め、逆再生用のrosbagを準備します。
5. 既定では0.5秒待ち、記録した軌跡を`exact_replay_rig`で逆順に再現します。この間、通常走行側のロボットには停止指令を送ります。
6. 往路の設定時間と終了待機時間（既定1秒）の経過後、実験を完了し、rosbag記録を終了します。

走行・逆再生の時間はシミュレーション時間です。処理負荷によって実時間は長くなる場合があります。

次のログが表示されたら、起動したターミナルで`Ctrl+C`を押して終了してください。実験完了後もGazeboとノードは自動終了しません。

```text
Experiment completed.
All rosbag recording completed.
```

再実験する場合は、一度終了してから同じlaunchコマンドを実行します。

### 進行状況の確認

別のターミナルでROS環境を読み込み、状態トピックを確認できます。

```bash
source /opt/ros/humble/setup.bash
source ~/ws_whill_sim/install/setup.bash
ros2 topic echo /experiment/state std_msgs/msg/String \
  --qos-durability transient_local
```

通常は次の順に状態が変化します。

```text
WAITING → ARMED → FORWARD → PREPARE_REVERSE → EXACT_REPLAY → DONE
```

## 保存データ

既定の保存先は`~/ws_whill_sim/experiment_data/`です。実験ごとに`trial_001`、`trial_002`のような連番ディレクトリが作られます。実際の保存先は起動ログの`Trial directory:`に表示されます。

```text
experiment_data/trial_XXX/
├── forward/               # 往路のrosbag（SQLite3）
├── reverse/               # 逆再生のrosbag（SQLite3）
├── fixed_profile.yaml     # 使用した走行設定のコピー
├── world.sdf              # 使用したワールドのコピー
├── metadata.yaml          # 実験名、作成時刻、記録対象トピックなど
├── forward_recorder.log
└── reverse_recorder.log
```

`world.sdf`に含まれるモデル参照先の`model.sdf`や、プラグインの実装はこのディレクトリへ自動コピーされません。

例えば`trial_001`の記録情報は、以下で確認できます。番号は起動ログに表示されたものへ置き換えてください。

```bash
ros2 bag info ~/ws_whill_sim/experiment_data/trial_001/forward
ros2 bag info ~/ws_whill_sim/experiment_data/trial_001/reverse
```

Exact Replayプラグインは別途`/tmp/forward_exact.csv`へ軌跡を保存します。このファイルは次回の記録で上書きされるため、必要なら実験後に該当する試行ディレクトリへコピーしてください。

## 主なROSトピック

| トピック | 型 | 用途 |
| --- | --- | --- |
| `/clock` | `rosgraph_msgs/msg/Clock` | シミュレーション時刻 |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 通常走行モデルへの速度指令 |
| `/imu` | `sensor_msgs/msg/Imu` | 通常走行側のIMU |
| `/lidar/points` | `sensor_msgs/msg/PointCloud2` | 通常走行側のLiDAR点群 |
| `/ground_truth_pose` | `tf2_msgs/msg/TFMessage` | 通常走行側の真値姿勢 |
| `/exact/imu` | `sensor_msgs/msg/Imu` | 逆再生側のIMU |
| `/exact/lidar/points` | `sensor_msgs/msg/PointCloud2` | 逆再生側のLiDAR点群 |
| `/exact/ground_truth_pose` | `tf2_msgs/msg/TFMessage` | 逆再生側の真値姿勢 |
| `/exact_replay/record` | `std_msgs/msg/Bool` | 軌跡の記録開始 |
| `/exact_replay/stop_record` | `std_msgs/msg/Bool` | 軌跡の記録終了 |
| `/exact_replay/start` | `std_msgs/msg/Bool` | 逆再生開始 |
| `/experiment/state` | `std_msgs/msg/String` | 実験の進行状態 |

記録・逆再生のトリガーは走行制御ノードが自動送信します。

往路のrosbagは`/clock`、`/cmd_vel`、通常走行側のセンサー・真値姿勢、`/experiment/state`を記録します。逆再生のrosbagは`/clock`、逆再生側のセンサー・真値姿勢、`/experiment/state`を記録します。

## モデルとセンサーの設定

四輪ロボットは箱と円柱で構成した簡略モデルです。左右それぞれの前後輪をGazeboの`DiffDrive`プラグインで駆動します。

| 項目 | 既定値 |
| --- | --- |
| 車体サイズ | 0.60 × 0.45 × 0.12 m |
| 車輪半径 / 左右車輪間隔 | 0.10 m / 0.50 m |
| 物理ステップ | 0.001秒 |
| IMU更新レート | 200 Hz |
| LiDAR更新レート | 10 Hz |
| LiDARサンプル数 | 水平512 × 垂直64 |
| LiDAR視野角 | 水平360°、垂直約22.5° |
| LiDAR測距範囲 | 0.3〜50.0 m |
| 真値姿勢の配信レート | 50 Hz |

逆再生モデルは同じセンサー設定と取り付け位置を使用します。衝突形状を持たず、重力を無効化し、独自プラグインで記録済みの運動を再現する構成です。

## 実験条件の変更

### 走行パターン

関連パッケージの`~/ws_whill_sim/src/whill_trajectory_control/config/fixed_profile.yaml`を編集します。以下は`fixed_profile_runner.ros__parameters`配下の既定値の抜粋です。

```yaml
segment_durations: [1.0, 3.0, 2.0, 2.0, 2.0, 2.0, 1.0]
linear_velocities: [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0]
angular_velocities: [0.0, 0.0, 0.20, 0.0, -0.20, 0.0, 0.0]
```

各配列の同じ位置が1区間に対応します。

- `segment_durations`：区間の時間［秒］。すべて正の値にします。
- `linear_velocities`：前進速度［m/s］。
- `angular_velocities`：旋回速度［rad/s］。正が左旋回、負が右旋回です。

3つの配列の要素数を揃えてください。既定では、停止 → 直進 → 左旋回 → 直進 → 右旋回 → 直進 → 停止の順に動作します。

### その他の編集箇所

| 変更内容 | 編集箇所 |
| --- | --- |
| 車体寸法、駆動設定 | `models/four_wheel_robot/model.sdf` |
| センサーの位置・仕様 | `models/four_wheel_robot/model.sdf`と`models/exact_replay_rig/model.sdf` |
| 壁・障害物の配置 | `models/test_environment/model.sdf` |
| モデルの初期位置、物理ステップ | `worlds/exact_replay_validation.sdf` |
| 使用ワールド、走行設定ファイル、rosbag保存先 | `launch/exact_replay_experiment.launch.py` |
| 軌跡CSVの保存先 | `models/exact_replay_rig/model.sdf`の`csv_path` |

launchには現在、これらを切り替えるコマンドライン引数は定義されていません。該当ファイルを編集して変更します。センサー条件を揃えて比較する場合は、通常走行側と逆再生側の両モデルに変更を反映してください。

起動時はインストール先のファイルが読み込まれるため、変更後は再ビルドして起動し直します。

```bash
cd ~/ws_whill_sim
colcon build --packages-up-to whill_gazebo
source install/setup.bash
ros2 launch whill_gazebo exact_replay_experiment.launch.py
```

## トラブルシューティング

| 症状 | 確認箇所 |
| --- | --- |
| `Package ... not found` | ROS環境とワークスペースの`setup.bash`を読み込んだか、関連パッケージをビルドしたか |
| `libwhill_exact_replay.so`を読み込めない | `whill_exact_replay`のビルド結果、Gazebo 6用の依存ライブラリ、launch経由で設定されるプラグイン検索パス |
| `WAITING`から進まない | Gazeboが動いているか、`/clock`が届いているか、ブリッジの起動ログにエラーがないか |
| `ARMED`から進まない | 試行ディレクトリの`forward_recorder.log`。rosbag2の起動やSQLite3ストレージのエラーがないか |
| `PREPARE_REVERSE`から進まない | 試行ディレクトリの`reverse_recorder.log` |
| GUIやLiDARの描画に失敗する | Gazeboのログ、ディスプレイ接続、GPU・Ogre2の描画環境 |
| 編集した設定が反映されない | 再ビルドしたか、正しいワークスペースの`install/setup.bash`を読み込んだか |

接続確認の例です。`ros2 topic hz`は`Ctrl+C`で終了します。

```bash
ros2 topic list
ros2 topic hz /clock
```

## ライセンス

`package.xml`のライセンス宣言は`Apache-2.0`です。
