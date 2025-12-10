# 项目中的三种 Wake Word（唤醒词）实现方式

本项目支持三种不同的唤醒词（Wake Word）检测方式，分别适配不同的硬件平台、算法模型和应用场景。以下分别介绍各自的原理、数据流和适用场景。

---

## 1. AfeWakeWord

**简介**  
AfeWakeWord 基于 ESP-ADF 的 AFE（音频前端）模块，集成了回声消除（AEC）、降噪（NS）、VAD 及唤醒词检测等功能。适用于需要高鲁棒性和复杂前端处理的场景。

**数据流**  
- 外部通过 `Feed(const std::vector<int16_t>& data)` 输入原始 PCM 数据。
- 数据首先送入 AFE 算法，经过前端处理（如降噪、回声消除）。
- 唤醒词检测在 AFE 处理后的数据上进行（`afe_iface_->fetch_with_delay`）。
- 检测到唤醒词后，通过回调通知上层。

**特点**  
- 唤醒词检测与 AFE 前端处理深度集成，适合嘈杂环境和远场语音。
- 支持多通道麦克风阵列。
- 唤醒词模型和参数可灵活配置。

---

## 2. CustomWakeWord

**简介**  
CustomWakeWord 基于 Espressif MultiNet 命令词识别框架，支持自定义唤醒词和命令词。适合需要自定义唤醒词、命令词和多语言支持的场景。

**数据流**  
- 外部通过 `Feed(const std::vector<int16_t>& data)` 输入原始 PCM 数据。
- 若为双通道，自动提取左声道（主麦）。
- 数据直接送入 MultiNet 模型进行命令词/唤醒词检测（`multinet_->detect`）。
- 检测到唤醒词后，通过回调通知上层。

**特点**  
- 支持自定义唤醒词和命令词，配置灵活。
- 支持多语言和多模型切换。
- 适合需要丰富命令词和自定义唤醒词的产品。

---

## 3. EspWakeWord

**简介**  
EspWakeWord 是 Espressif 官方的基础唤醒词检测实现，适用于资源受限或只需基础唤醒功能的场景。

**数据流**  
- 外部通过 `Feed(const std::vector<int16_t>& data)` 输入原始 PCM 数据。
- 数据直接送入唤醒词检测模型（如 wakenet）。
- 检测到唤醒词后，通过回调通知上层。

**特点**  
- 实现简单，资源占用低。
- 适合单麦克风、低成本、对环境适应性要求不高的场景。
- 支持 Espressif 官方提供的标准唤醒词模型。

---

## 总结对比

| 方式            | 数据流入口         | 检测基础         | 适用场景           | 特点                |
|-----------------|-------------------|------------------|--------------------|---------------------|
| AfeWakeWord     | 原始PCM → AFE     | AFE输出          | 远场、嘈杂环境      | 集成前端处理，鲁棒性强 |
| CustomWakeWord  | 原始PCM（主麦）   | MultiNet         | 自定义命令/多语言   | 灵活、支持命令词      |
| EspWakeWord     | 原始PCM           | Wakenet等        | 基础唤醒、低成本    | 简单、资源占用低      |

---

## 参考

- [ESP-ADF AFE 文档](https://docs.espressif.com/projects/esp-adf/zh_CN/latest/api-reference/audio_processing/esp_afe_sr.html)
- [Espressif MultiNet](https://github.com/espressif/esp-sr)
- [Wakenet 唤醒词模型](https://github.com/espressif/esp-sr)

如需切换或定制唤醒词方式，请参考 `AudioService::SetModelsList` 及相关唤醒词类的实现。