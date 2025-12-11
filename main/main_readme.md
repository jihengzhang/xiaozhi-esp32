# Xiaozhi-ESP32 主程序架构文档

## 概述

本文档描述了 Xiaozhi-ESP32 项目的主程序入口 `main.cc` 的架构设计，包括头文件依赖关系、核心功能模块以及语音数据流的完整流程。

## 头文件依赖层级

### main.cc Include 层级关系

```mermaid
graph TD
    subgraph ESP-IDF系统层
        A[esp_log.h] --> |日志系统| Main[main.cc]
        B[esp_err.h] --> |错误处理| Main
        C[nvs.h] --> |非易失存储| Main
        D[nvs_flash.h] --> |NVS Flash操作| Main
        E[driver/gpio.h] --> |GPIO驱动| Main
        F[esp_event.h] --> |事件循环| Main
    end

    subgraph FreeRTOS层
        G[freertos/FreeRTOS.h] --> |RTOS内核| Main
        H[freertos/task.h] --> |任务管理| Main
    end

    subgraph 应用层
        I[application.h] --> |应用程序入口| Main
        J[system_info.h] --> |系统信息| Main
    end

    Main --> |启动| App[Application::GetInstance]
```

### Application 模块依赖展开

```mermaid
graph TD
    subgraph Application核心
        App[Application] --> Audio[AudioService]
        App --> Network[NetworkManager]
        App --> Protocol[ProtocolHandler]
        App --> Display[DisplayService]
        App --> LED[LedController]
    end

    subgraph 音频子系统
        Audio --> Codec[AudioCodec]
        Audio --> Processor[AudioProcessor]
        Audio --> WakeWord[WakeWordEngine]
        Audio --> OpusEnc[OpusEncoder]
        Audio --> OpusDec[OpusDecoder]
    end

    subgraph 网络子系统
        Network --> WiFi[WiFiManager]
        Network --> MQTT[MqttClient]
        Network --> WebSocket[WebSocketClient]
    end

    subgraph 协议子系统
        Protocol --> MCP[McpHandler]
        Protocol --> ASR[AsrClient]
        Protocol --> TTS[TtsClient]
    end
```

## 核心功能模块

### 1. 语音处理模块 (Audio Processing)

```mermaid
graph LR
    subgraph 音频前端处理
        Mic[麦克风] --> I2S[I2S驱动]
        I2S --> AEC[回声消除AEC]
        AEC --> NS[噪声抑制]
        NS --> VAD[语音活动检测]
    end

    subgraph 音频编解码
        VAD --> Opus[Opus编码器]
        Opus --> Stream[音频流]
        Stream --> Decode[Opus解码器]
        Decode --> DAC[DAC输出]
    end

    DAC --> Speaker[扬声器]
```

**主要组件：**
- **AudioCodec**: 硬件抽象层，处理 I2S 通信
- **AudioProcessor (AfeAudioProcessor)**: 基于 ESP-ADF 的音频前端处理
- **WakeWord**: 唤醒词检测引擎
- **OpusEncoderWrapper/OpusDecoderWrapper**: 音频编解码

### 2. 语音识别模块 (ASR - Automatic Speech Recognition)

```mermaid
graph TD
    subgraph 本地处理
        Audio[音频输入] --> WW[唤醒词检测]
        WW -->|唤醒成功| Capture[音频采集]
        Capture --> Encode[Opus编码]
    end

    subgraph 云端服务
        Encode -->|WebSocket| Server[ASR服务器]
        Server --> Result[识别结果]
    end

    subgraph 结果处理
        Result -->|JSON| Parse[结果解析]
        Parse --> Intent[意图理解]
        Intent --> Response[响应生成]
    end
```

**工作流程：**
1. 本地唤醒词检测触发语音采集
2. Opus 编码后通过 WebSocket 发送至云端
3. 云端返回识别结果和响应

### 3. MCP (Model Context Protocol) 模块

```mermaid
graph TD
    subgraph MCP客户端
        Client[McpClient] --> Transport[Transport层]
        Transport --> JSON[JSON-RPC]
    end

    subgraph 功能接口
        Client --> Tools[工具调用]
        Client --> Resources[资源访问]
        Client --> Prompts[提示管理]
    end

    subgraph 通信方式
        JSON --> STDIO[标准IO]
        JSON --> SSE[Server-Sent Events]
        JSON --> WebSocket[WebSocket]
    end

    Tools --> |执行| AI[AI模型]
    Resources --> |提供上下文| AI
    AI --> Response[响应]
```

**MCP 特性：**
- 标准化的 AI 模型交互协议
- 支持工具调用、资源访问和提示管理
- 多种传输方式支持

### 4. MQTT 通信模块

```mermaid
graph TD
    subgraph MQTT客户端
        Client[MqttClient] --> Connect[连接管理]
        Client --> Subscribe[订阅管理]
        Client --> Publish[发布消息]
    end

    subgraph 主题设计
        Subscribe --> Cmd[/device/cmd]
        Subscribe --> Config[/device/config]
        Publish --> Status[/device/status]
        Publish --> Event[/device/event]
    end

    subgraph 消息处理
        Cmd --> Handler[命令处理器]
        Handler --> Action[执行动作]
        Action --> Feedback[状态反馈]
        Feedback --> Status
    end

    Broker[MQTT Broker] <--> Client
```

**MQTT 功能：**
- 设备远程控制
- 状态上报
- 配置下发
- OTA 升级触发

## 语音数据流全局框图

### 完整语音交互流程

```mermaid
graph TB
    subgraph 硬件层
        Mic[("🎤 麦克风")] 
        Speaker[("🔊 扬声器")]
    end

    subgraph 音频采集层
        Mic -->|I2S| ADC[AudioCodec ADC]
        ADC -->|Raw PCM| InputTask[AudioInputTask]
    end

    subgraph 音频处理层
        InputTask -->|PCM 16kHz| WakeWord{唤醒词检测}
        WakeWord -->|未唤醒| InputTask
        WakeWord -->|唤醒成功| AfeProcessor[AfeAudioProcessor]
        AfeProcessor -->|AEC+NS+VAD| CleanPCM[清洁PCM]
    end

    subgraph 编码上传层
        CleanPCM --> EncodeQueue[(audio_encode_queue)]
        EncodeQueue --> OpusEnc[OpusEncoder]
        OpusEnc --> SendQueue[(audio_send_queue)]
        SendQueue --> WebSocket[WebSocket Client]
    end

    subgraph 云端处理
        WebSocket <-->|Opus Packets| Cloud((☁️ 云端服务))
        Cloud --> ASR[语音识别]
        ASR --> LLM[大语言模型]
        LLM --> TTS[语音合成]
    end

    subgraph 解码播放层
        Cloud -->|Opus Response| DecodeQueue[(audio_decode_queue)]
        DecodeQueue --> OpusDec[OpusDecoder]
        OpusDec --> PlayQueue[(audio_playback_queue)]
        PlayQueue --> OutputTask[AudioOutputTask]
    end

    subgraph 音频输出层
        OutputTask -->|PCM| DAC[AudioCodec DAC]
        DAC -->|I2S| Speaker
    end

    subgraph 控制层
        App[Application] -.->|控制| InputTask
        App -.->|控制| OutputTask
        App -.->|状态| MQTT[MQTT Client]
        MCP[MCP Handler] -.->|工具调用| App
    end

    style Cloud fill:#87CEEB
    style Mic fill:#90EE90
    style Speaker fill:#FFB6C1
```

### 数据流时序

```mermaid
sequenceDiagram
    participant M as 麦克风
    participant A as AudioService
    participant W as WakeWord
    participant P as AudioProcessor
    participant E as OpusEncoder
    participant C as Cloud
    participant D as OpusDecoder
    participant S as 扬声器

    M->>A: Raw PCM (I2S)
    A->>W: 音频流
    
    alt 唤醒词匹配
        W->>A: 唤醒事件
        A->>P: 开始处理
        loop 语音输入
            M->>A: Raw PCM
            A->>P: 音频处理 (AEC/NS/VAD)
            P->>E: 清洁PCM
            E->>C: Opus Packets
        end
        
        C->>C: ASR + LLM + TTS
        
        loop 语音输出
            C->>D: Opus Response
            D->>A: PCM
            A->>S: 播放
        end
    else 无唤醒
        W->>A: 继续监听
    end
```

## 初始化流程

```mermaid
graph TD
    Start[app_main] --> EventLoop[创建事件循环]
    EventLoop --> NVS[初始化NVS Flash]
    NVS --> |成功| GetApp[Application::GetInstance]
    NVS --> |失败/需擦除| Erase[擦除NVS]
    Erase --> NVS
    
    GetApp --> AppStart[Application::Start]
    
    subgraph Application初始化
        AppStart --> InitAudio[初始化AudioService]
        AppStart --> InitNetwork[初始化NetworkManager]
        AppStart --> InitDisplay[初始化DisplayService]
        AppStart --> InitLED[初始化LedController]
        
        InitAudio --> StartTasks[启动音频任务]
        InitNetwork --> ConnectWiFi[连接WiFi]
        ConnectWiFi --> ConnectServer[连接服务器]
    end
```

## 电源管理

系统实现了智能电源管理以节省能耗：

- **自动休眠**: 音频编解码器在空闲 `AUDIO_POWER_TIMEOUT_MS` 后自动关闭
- **按需唤醒**: 有新的音频输入/输出需求时自动启用
- **定时器监控**: `audio_power_timer_` 定期检查活动状态

## 文件结构

```
main/
├── main.cc              # 程序入口
├── application.h/cc     # 应用程序主类
├── audio/
│   ├── audio_service.h  # 音频服务
│   ├── audio_codec.h    # 编解码器抽象
│   ├── audio_processor.h # 音频处理器
│   └── opus_*.h         # Opus编解码
├── network/
│   ├── mqtt_client.h    # MQTT客户端
│   └── websocket.h      # WebSocket客户端
├── protocol/
│   ├── mcp_handler.h    # MCP协议处理
│   └── asr_client.h     # ASR客户端
└── display/
    └── display_service.h # 显示服务
```
