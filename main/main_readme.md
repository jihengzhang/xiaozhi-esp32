# Main Entry Point Architecture

This document describes the architecture of the Xiaozhi-ESP32 project starting from `main.cc`.

## Include Hierarchy

The following diagram illustrates the dependency relationships of the main entry point:

```mermaid
graph TD
    subgraph ESP-IDF Core
        esp_log[esp_log.h]
        esp_err[esp_err.h]
        esp_event[esp_event.h]
    end

    subgraph NVS Storage
        nvs[nvs.h]
        nvs_flash[nvs_flash.h]
    end

    subgraph Hardware Drivers
        gpio[driver/gpio.h]
    end

    subgraph FreeRTOS
        freertos[freertos/FreeRTOS.h]
        task[freertos/task.h]
        freertos --> task
    end

    subgraph Application Layer
        app[application.h]
        sys_info[system_info.h]
    end

    main[main.cc] --> esp_log
    main --> esp_err
    main --> esp_event
    main --> nvs
    main --> nvs_flash
    main --> gpio
    main --> freertos
    main --> task
    main --> app
    main --> sys_info
```

## Application Module Hierarchy

```mermaid
graph TD
    subgraph Application
        App[Application]
    end

    subgraph Audio Module
        AudioService[AudioService]
        AudioCodec[AudioCodec]
        AudioProcessor[AudioProcessor]
        WakeWord[WakeWord]
        OpusEncoder[OpusEncoderWrapper]
        OpusDecoder[OpusDecoderWrapper]
        
        AudioService --> AudioCodec
        AudioService --> AudioProcessor
        AudioService --> WakeWord
        AudioService --> OpusEncoder
        AudioService --> OpusDecoder
    end

    subgraph Network Module
        MQTT[MQTT Client]
        WebSocket[WebSocket]
        Protocol[Protocol Handler]
    end

    subgraph MCP Module
        MCP[MCP Server]
        Tools[MCP Tools]
    end

    App --> AudioService
    App --> MQTT
    App --> WebSocket
    App --> Protocol
    App --> MCP
    MCP --> Tools
```

## Key Functional Modules

### 1. Audio Processing (语音处理)

The audio processing module handles real-time audio capture and playback:

| Component | Description |
|-----------|-------------|
| **AudioCodec** | Hardware abstraction layer for I2S communication |
| **AudioProcessor** | AEC (Acoustic Echo Cancellation), noise suppression, VAD |
| **OpusEncoder/Decoder** | High-efficiency audio compression for network streaming |
| **WakeWord** | Keyword detection engine (e.g., "你好小智", "Hi ESP") |

### 2. Speech Recognition (语音识别)

Speech recognition is handled via cloud services:

- Local VAD detects speech activity
- Audio is encoded in Opus format and streamed to cloud
- Cloud ASR returns transcription results
- Results are processed by the application for intent handling

### 3. MCP (Model Context Protocol)

MCP provides tool execution capabilities:

| Feature | Description |
|---------|-------------|
| **Tool Registration** | Dynamic registration of callable tools |
| **Tool Execution** | Execute tools based on AI model requests |
| **Context Management** | Maintain conversation and execution context |

### 4. MQTT Communication

MQTT handles device-cloud messaging:

- Device status reporting
- Remote configuration updates
- Command reception and execution
- OTA update notifications

## Global Voice Data Flow

```mermaid
graph TD
    subgraph Input Pipeline [Input Pipeline - ESP32S3]
        Mic[("🎤 Microphone")] -->|I2S| Codec1[AudioCodec<br/>audio_codec.cc]
        Codec1 -->|Raw PCM| InputTask[AudioInputTask<br/>audio_service.cc]
        InputTask -->|16kHz PCM| WW{WakeWord?}
        
        WW -->|Not Detected| WakeEngine[WakeWord Engine<br/>wake_word.cc]
        WakeEngine -->|Wake Event| App1[Application<br/>application.cc]
        
        WW -->|Detected/Active| Processor[AudioProcessor<br/>afe_audio_processor.cc]
        Processor -->|Clean PCM| EncQueue[Encode Queue<br/>audio_service.cc]
    end

    subgraph Encoding [Encoding - ESP32S3]
        EncQueue --> OpusEnc[Opus Encoder<br/>opus_encoder_wrapper.cc]
        OpusEnc -->|Opus Packets| SendQueue[Send Queue<br/>audio_service.cc]
    end

    subgraph Network [Network Layer]
        SendQueue --> Protocol[Protocol Layer<br/>protocol.cc - ESP32S3]
        Protocol -->|WebSocket| Cloud((☁️ Cloud Server))
        Cloud -->|ASR Result| Protocol
        Cloud -->|TTS Audio| Protocol
        Protocol --> DecQueue[Decode Queue<br/>audio_service.cc - ESP32S3]
    end

    subgraph CloudServices [Cloud Services - 云端]
        Cloud --> ASR[语音识别 ASR]
        ASR --> LLM[大语言模型 LLM]
        LLM --> TTS[语音合成 TTS]
        TTS --> Cloud
    end

    subgraph Decoding [Decoding - ESP32S3]
        DecQueue --> OpusDec[Opus Decoder<br/>opus_decoder_wrapper.cc]
        OpusDec -->|PCM| PlayQueue[Playback Queue<br/>audio_service.cc]
    end

    subgraph Output Pipeline [Output Pipeline - ESP32S3]
        PlayQueue --> OutputTask[AudioOutputTask<br/>audio_service.cc]
        OutputTask --> Codec2[AudioCodec<br/>audio_codec.cc]
        Codec2 -->|I2S| Speaker[("🔊 Speaker")]
    end

    subgraph Application Logic [Application Logic - ESP32S3]
        App1[Application<br/>application.cc] --> StateManager[State Manager<br/>application.cc]
        StateManager -->|Start Listening| InputTask
        StateManager -->|Stop Listening| InputTask
        Cloud -->|Intent/Response| App1
        App1 -->|Execute| MCP[MCP Tools<br/>mcp_server.cc]
    end
```

### Source File Reference Table

| Component | Source File | Location | Description |
|-----------|-------------|----------|-------------|
| **AudioCodec** | `main/audio/audio_codec.cc` | ESP32S3 | I2S hardware abstraction |
| **AudioInputTask** | `main/audio/audio_service.cc` | ESP32S3 | Audio capture task |
| **AudioOutputTask** | `main/audio/audio_service.cc` | ESP32S3 | Audio playback task |
| **AudioProcessor** | `main/audio/afe_audio_processor.cc` | ESP32S3 | AEC, VAD, noise suppression |
| **WakeWord** | `main/audio/wake_word.cc` | ESP32S3 | Keyword detection |
| **OpusEncoder** | `main/audio/opus_encoder_wrapper.cc` | ESP32S3 | PCM to Opus encoding |
| **OpusDecoder** | `main/audio/opus_decoder_wrapper.cc` | ESP32S3 | Opus to PCM decoding |
| **Protocol** | `main/protocols/protocol.cc` | ESP32S3 | WebSocket/MQTT communication |
| **Application** | `main/application.cc` | ESP32S3 | Main application logic |
| **MCP Server** | `main/mcp/mcp_server.cc` | ESP32S3 | Tool execution framework |
| **ASR** | Cloud Service | ☁️ Cloud | Speech-to-text recognition |
| **LLM** | Cloud Service | ☁️ Cloud | Large Language Model inference |
| **TTS** | Cloud Service | ☁️ Cloud | Text-to-speech synthesis |

## Startup Sequence

```mermaid
sequenceDiagram
    participant Main as main.cc
    participant Event as ESP Event Loop
    participant NVS as NVS Flash
    participant App as Application

    Main->>Event: esp_event_loop_create_default()
    Main->>NVS: nvs_flash_init()
    alt NVS Corrupted
        Main->>NVS: nvs_flash_erase()
        Main->>NVS: nvs_flash_init()
    end
    Main->>App: GetInstance()
    Main->>App: Start()
    App->>App: Initialize WiFi
    App->>App: Initialize Audio Service
    App->>App: Connect to Cloud
    App->>App: Start Main Loop
```

## Task Priority Model

| Task | Priority | Description |
|------|----------|-------------|
| AudioInputTask | High | Real-time audio capture |
| AudioOutputTask | High | Real-time audio playback |
| OpusCodecTask | Medium-High | Audio encoding/decoding |
| NetworkTask | Medium | Network communication |
| ApplicationTask | Normal | Business logic processing |

## Memory Management

- Audio buffers use pre-allocated ring buffers
- Opus codec uses static memory allocation
- Queue-based inter-task communication prevents memory fragmentation
