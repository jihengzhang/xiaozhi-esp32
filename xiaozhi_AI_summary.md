# XiaoZhi AI Summary

## Architecture
- Entry (`main/main.cc`) boots ESP-IDF default event loop/NVS and calls the singleton `Application::Start()`.
- `Application` orchestrates state, audio, and connectivity: initializes display/audio, checks assets/OTA, chooses MQTT or WebSocket protocol based on OTA config, registers MCP tools, and drives a main event loop that reacts to scheduled tasks, wake-word hits, VAD changes, audio send queue, clock ticks, and protocol errors.
- Audio pipeline is handled by `AudioService` (capture, encode/decode OPUS, VAD, wake-word detection, AEC modes). It feeds audio packets to the selected `Protocol` and plays incoming TTS packets; wake-word events raise `MAIN_EVENT_WAKE_WORD_DETECTED`.
- Protocol layer (`MqttProtocol` / `WebsocketProtocol`) streams audio and JSON frames; `Application::OnIncomingJson` updates UI, speech state, MCP dispatch, and reacts to system commands (e.g., reboot).
- Hardware abstraction lives in `Board` and per-board implementations under `main/boards/` (codec/display/LED/network/power-save setup, buttons, optional camera/backlight). Boards can add MCP tools for their peripherals.
- MCP server (`main/mcp_server.cc`) registers common tools (device status, volume, brightness, theme, camera, reboot/upgrade, etc.) and routes MCP payloads from the cloud back into device APIs.
- Settings/OTA/Assets/System: `Settings` wraps NVS, `Ota` handles version check/activation/upgrade, `Assets` downloads & applies language/fonts/emojis, `SystemInfo` exposes metrics used in UI/MCP.

## Source Tree (trimmed)
```
.
├─ main/              firmware entry + app logic
│  ├─ main.cc         IDF entry -> Application
│  ├─ application.*   state machine, event loop, audio/protocol wiring
│  ├─ mcp_server.*    MCP tool registration + dispatch
│  ├─ protocol/       MQTT/WebSocket transports, audio/json framing
│  ├─ audio_service.* audio capture/encode/decode, wake-word, VAD, AEC
│  ├─ boards/         board-specific init, buttons, power, peripherals
│  ├─ display/        OLED/LCD abstraction and themes
│  ├─ assets/         fonts/emojis/lang strings, asset management
│  ├─ ota.*, settings.*, system_info.*, device_state_event.*
├─ components/        extra components (e.g., esp-ml307, codecs)
├─ managed_components/IDF component manager downloads
├─ docs/              protocol & hardware docs
├─ partitions/        partition tables (v1/v2)
├─ scripts/           helper scripts
├─ sdkconfig*         build-time config
└─ build/             generated artifacts
```

## Dialogue Control (wake word / command / button)
- **Wake word**: `AudioService` raises `MAIN_EVENT_WAKE_WORD_DETECTED`; `Application::OnWakeWordDetected()` encodes the wake word, opens the audio channel if needed, then sets listening mode (auto-stop or realtime). When speaking, a wake word triggers `AbortSpeaking` to cut TTS. Wake-word detection is enabled in idle state (`SetDeviceState(kDeviceStateIdle)` turns it on).
- **Command phrase (e.g., "exit")**: The firmware does not currently key off the literal text "exit". To add this, hook in `Application::OnIncomingJson` when `type == "stt"` (or in your protocol layer) to detect the phrase and call `Application::StopListening()` or `AbortSpeaking(...)` via `Schedule(...)`. You can also add a new `type == "system"` command branch alongside the existing "reboot" handler to stop/close the audio channel.
- **Button control**: Board files wire physical inputs. Example `main/boards/xmini-c3/xmini_c3_board.cc` `InitializeButtons()`:
  - Click → `Application::ToggleChatState()` (opens/closes audio; toggles idle/listening/speaking).
  - Press-to-talk mode (PressToTalkMcpTool enabled) → press down calls `StartListening()`, release calls `StopListening()`; click is ignored in that mode.
  - Buttons also wake the power-save timer. Other boards follow the same pattern—update their button handlers to call `ToggleChatState`, `StartListening`, or `StopListening` to customize behavior.
- **Other stop paths**: `StopListening()` sends a stop to the server and returns to idle; closing the audio channel (`OnAudioChannelClosed`) resets UI and state. A wake word during TTS also stops speech via `AbortSpeaking`.

## Multinet v7 退出命令（"ok, exit"）完整实现方案

### 1. 模型配置 (assets/index.json)
在 assets 的 `index.json` 文件中的 `multinet_model.commands` 数组添加新命令：

```json
{
  "command": "ok_exit",
  "text": "ok, exit",
  "action": "exit"
}
```

阈值和持续时间参数保持与现有 wake 命令一致。

### 2. 识别层改动 (main/audio/wake_words/custom_wake_word.cc)

**当前问题**: 只有 `action == "wake"` 时才触发回调。

**修改方案**: 
- 在检测到任何命令时都保存到 `last_detected_wake_word_`
- 对 `action == "exit"` 同样触发回调
- 可选：修改回调签名传递 action 字符串，或在 `command.text` 中携带标识

```cpp
// 示例代码片段
if (command.action == "wake" || command.action == "exit") {
    last_detected_wake_word_ = command.text;
    if (on_wake_word_detected_) {
        on_wake_word_detected_(command.action);  // 传递 action
    }
}
```

### 3. 应用层处理 (Application::OnWakeWordDetected)

在 `OnWakeWordDetected` 方法中添加退出命令判断逻辑：

```cpp
void Application::OnWakeWordDetected() {
    std::string wake_word = audio_service_.GetLastWakeWord();
    
    // 检测退出命令
    if (wake_word == "ok, exit" || wake_word == "ok_exit") {
        HandleExitCommand();
        return;  // 不执行唤醒流程
    }
    
    // 正常唤醒流程
    // ...existing wake word handling...
}

void Application::HandleExitCommand() {
    switch (device_state_) {
        case kDeviceStateSpeaking:
            // 立即停止播放
            AbortSpeaking(kAbortReasonNone);
            SetDeviceState(kDeviceStateIdle);
            break;
            
        case kDeviceStateListening:
            // 停止监听
            StopListening();
            break;
            
        default:
            // 其他状态忽略或记录日志
            break;
    }
}
```

**关键要点**:
- 不需要调用 `EncodeWakeWord()` - 退出命令不发送音频
- 不需要打开音频通道 - 直接执行停止动作
- 区分大小写和空格 - 确保匹配 assets 中定义的文本

### 4. 事件流程图

```
用户说 "ok, exit"
    ↓
CustomWakeWord 检测到命令 (action="exit")
    ↓
保存到 last_detected_wake_word_
    ↓
触发回调 → MAIN_EVENT_WAKE_WORD_DETECTED
    ↓
Application::OnWakeWordDetected()
    ↓
检测到退出命令文本
    ↓
根据当前状态执行:
  - Speaking → AbortSpeaking + 回到 Idle
  - Listening → StopListening
  - 其他 → 忽略
```

### 5. 调试建议

- 启用日志确认命令被正确识别：`ESP_LOGI(TAG, "Detected command: %s, action: %s", text, action)`
- 验证 `last_detected_wake_word_` 是否正确保存退出命令文本
- 检查事件是否正确投递到主循环
- 测试不同状态下的退出行为（空闲/监听/播放）

### 6. 可选增强

- **超时保护**: 退出命令后自动清除状态，避免误触发
- **用户反馈**: 播放简短提示音或显示退出图标
- **多语言支持**: 在 assets 中为不同语言添加对应的退出命令
- **权限控制**: 某些状态下可能需要禁用退出功能

## 本地命令 vs 网络命令处理分析

### 命令处理路径对比

#### 1. 本地识别命令（离线处理）
**处理文件**: `main/audio/wake_words/custom_wake_word.cc`

- **识别引擎**: Multinet v7 本地模型
- **配置来源**: `assets/index.json` → `multinet_model.commands[]`
- **处理流程**:
  ```
  音频输入 → Multinet引擎 → 命令匹配
      ↓
  CustomWakeWord::Detect()
      ↓
  匹配 action == "wake" 或 "exit"
      ↓
  on_wake_word_detected_() 回调
      ↓
  MAIN_EVENT_WAKE_WORD_DETECTED
      ↓
  Application::OnWakeWordDetected()
  ```

- **特点**:
  - 完全离线，不依赖网络
  - 延迟极低（< 500ms）
  - 命令词有限（assets 配置的几个固定词）
  - 仅支持唤醒和简单控制命令

**关键代码位置**:
```cpp
// main/audio/wake_words/custom_wake_word.cc
void CustomWakeWord::Detect(int16_t* data, int len) {
    // Multinet 识别
    esp_mn_state_t state = esp_mn_process(model_, data, len, &result);
    
    if (state == ESP_MN_STATE_DETECTED) {
        Command command = GetCommand(result.command_id);
        if (command.action == "wake") {
            last_detected_wake_word_ = command.text;
            on_wake_word_detected_();  // 触发本地回调
        }
    }
}
```

#### 2. 网络 AI 命令（在线处理）
**处理文件**: `main/application.cc` + `main/protocol/mqtt_protocol.cc` / `websocket_protocol.cc`

- **识别引擎**: 云端 AI 模型（通过 MQTT/WebSocket）
- **配置来源**: 远程服务器配置
- **处理流程**:
  ```
  音频输入 → AudioService 编码
      ↓
  Protocol::SendAudio() → MQTT/WebSocket 上传
      ↓
  云端 STT + NLU 处理
      ↓
  Protocol::OnIncomingJson() 接收结果
      ↓
  Application::OnIncomingJson() 分发处理
      ↓
  根据 type 执行: stt/tts/tool/system
  ```

- **特点**:
  - 需要 WiFi + MQTT/WebSocket 连接
  - 延迟较高（网络 RTT + 云端处理）
  - 支持自然语言理解
  - 功能强大（对话、工具调用、系统控制）

**关键代码位置**:
```cpp
// main/application.cc
void Application::OnIncomingJson(const cJSON* json) {
    const char* type = cJSON_GetStringValue(cJSON_GetObjectItem(json, "type"));
    
    if (strcmp(type, "stt") == 0) {
        // 语音转文字结果
        const char* text = cJSON_GetStringValue(cJSON_GetObjectItem(json, "text"));
        // 显示在 UI，可在此拦截特定命令
    }
    else if (strcmp(type, "tts") == 0) {
        // TTS 音频播放
        audio_service_.Play(audio_data, audio_len);
    }
    else if (strcmp(type, "tool") == 0) {
        // MCP 工具调用
        mcp_server_.Handle(json);
    }
    else if (strcmp(type, "system") == 0) {
        // 系统命令（reboot 等）
        const char* command = cJSON_GetStringValue(cJSON_GetObjectItem(json, "command"));
    }
}

// main/protocol/mqtt_protocol.cc
void MqttProtocol::SendAudio(const uint8_t* data, size_t len) {
    // 上传音频到 MQTT topic
    esp_mqtt_client_publish(client_, audio_topic_, data, len, 0, 0);
}
```

### 临时禁止联网连接 AI 模型的方法

#### 方案 1: 代码级禁用（推荐用于开发调试）

**修改文件**: `main/application.cc`

```cpp
// filepath: main/application.cc
void Application::Start() {
    // ...existing code...
    
    // 禁用网络协议初始化
    #if 0  // 临时禁用
    if (use_mqtt) {
        protocol_ = std::make_unique<MqttProtocol>(...);
    } else {
        protocol_ = std::make_unique<WebsocketProtocol>(...);
    }
    protocol_->Start();
    #endif
    
    // ...existing code...
}

void Application::OnWakeWordDetected() {
    // ...existing code...
    
    // 跳过音频上传
    #if 0  // 禁用云端交互
    if (protocol_ && protocol_->IsConnected()) {
        protocol_->SendAudio(...);
    }
    #endif
    
    // 仅保留本地命令处理
    std::string wake_word = audio_service_.GetLastWakeWord();
    if (wake_word == "ok, exit") {
        HandleExitCommand();
    }
}
```

#### 方案 2: 配置级禁用（推荐用于测试模式）

**修改文件**: `main/settings.h` + `main/application.cc`

1. 添加设置项:
```cpp
// main/settings.h
class Settings {
public:
    // ...existing code...
    bool GetOfflineMode() const;
    void SetOfflineMode(bool enabled);
};
```

2. 应用层检查:
```cpp
// main/application.cc
void Application::OnWakeWordDetected() {
    if (settings_->GetOfflineMode()) {
        // 仅执行本地命令
        HandleLocalCommand();
        return;
    }
    
    // 正常云端交互流程
    // ...existing code...
}
```

3. 通过 MCP 工具或 NVS 设置 offline_mode:
```cpp
// 添加 MCP 工具控制
mcp_server_.RegisterTool("set_offline_mode", [](const cJSON* params) {
    bool enabled = cJSON_GetObjectItem(params, "enabled")->valueint;
    settings_->SetOfflineMode(enabled);
});
```

#### 方案 3: WiFi 禁用（最简单但影响范围大）

**修改文件**: Board 实现文件（如 `main/boards/xmini-c3/xmini_c3_board.cc`）

```cpp
// main/boards/xmini-c3/xmini_c3_board.cc
void XminiC3Board::InitializeNetwork() {
    #if 0  // 临时禁用 WiFi
    esp_netif_init();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    // ...wifi setup...
    #endif
    
    ESP_LOGW(TAG, "Network disabled for offline testing");
}
```

**副作用**: OTA、资源下载、时间同步等功能也会失效。

#### 方案 4: 协议层拦截（细粒度控制）

**修改文件**: `main/protocol/mqtt_protocol.cc`

```cpp
// main/protocol/mqtt_protocol.cc
void MqttProtocol::SendAudio(const uint8_t* data, size_t len) {
    #ifdef OFFLINE_MODE  // 编译时开关
    ESP_LOGW(TAG, "Offline mode: audio not sent");
    return;
    #endif
    
    // ...existing code...
}
```

通过 `sdkconfig` 添加 `CONFIG_OFFLINE_MODE=y` 控制。

### 推荐实现策略

**开发阶段**: 使用方案 2（配置级），通过 NVS 或 MCP 工具动态切换，方便测试本地命令和网络命令对比。

**生产部署**: 
- 保留网络功能，仅在唤醒时判断 WiFi 状态
- 离线时自动降级到本地命令模式
- 显示离线图标提示用户

```cpp
void Application::OnWakeWordDetected() {
    if (!IsNetworkConnected()) {
        // 离线模式：仅处理本地命令
        HandleLocalCommand();
        display_->ShowOfflineIcon();
        return;
    }
    
    // 在线模式：完整 AI 交互
    // ...existing code...
}
```

### 本地命令扩展建议

如需增强离线功能，可在 assets 配置更多本地命令：

```json
{
  "commands": [
    {"command": "ok_wake", "text": "ok, xiaozhi", "action": "wake"},
    {"command": "ok_exit", "text": "ok, exit", "action": "exit"},
    {"command": "volume_up", "text": "volume up", "action": "volume_up"},
    {"command": "volume_down", "text": "volume down", "action": "volume_down"},
    {"command": "brightness_up", "text": "brighter", "action": "brightness_up"}
  ]
}
```

然后在 `Application::OnWakeWordDetected()` 中处理这些 action，调用对应的本地 API（音量、亮度等）。
