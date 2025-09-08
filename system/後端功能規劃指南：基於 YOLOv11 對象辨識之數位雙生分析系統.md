<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# 後端功能規劃指南：基於 YOLOv11 對象辨識之數位雙生分析系統

本報告提出一套完整的後端功能藍圖，協助你把 YOLOv11 偵測結果轉化為可持續擴充、能與 Unity 數位雙生即時同步的資料服務。內容涵蓋模型端擴充、資料庫結構、API 與串流策略、事件分析、效能監控與開發流程等面向，並輔以最新業界實務與研究文獻。

## 系統整體架構概觀

1. **感知層 (YOLOv11 + 推論伺服器)**
    - GPU 推論服務接受影音串流，輸出「偵測框、類別、信心值」等原始結果[^1][^2]。
    - 以 gRPC/REST 方式封裝，方便水平擴充。
2. **邏輯層 (Python 微服務群)**
    - 追蹤、計數、熱點圖、事件規則等延伸分析模組[^1][^3][^4]。
    - 每個功能獨立 Docker 服務，經由佇列 (如 RabbitMQ) 串接。
3. **資料層 (時序 + 關聯式 + 物件儲存)**
    - 偵測結果進入 TimescaleDB 作為時序資料；目標靜態屬性留在 PostgreSQL；影像切片存入 MinIO。
    - 事件告警寫入 Redis 以支援即時推播。
4. **呈現層 (Unity 數位雙生)**
    - Unity 定時透過 REST/WebSocket/WebRTC 拉取 JSON 或 ProtoBuf 資料流[^5][^6]。
    - 以場景物件映射資料庫主鍵，實現真實-虛擬同步[^7][^8]。

## YOLOv11 偵測端功能擴充

### 1. 多目標追蹤 (MOT)

| 追蹤器 | 特點 | FPS | 參考來源 |
| :-- | :-- | :-- | :-- |
| BoT-SORT | 姿態與速度共同估計 | 30FPS[^1] | 1 |
| ByteTrack | 低遮擋誤配率 | 35FPS[^2] | 6 |

- 於推論後呼叫 `model.track(tracker="bytetrack.yaml")` 即可取得 `track_id` 對應[^2]。
- 建議欄位：`uuid, frame_id, track_id, class, bbox, confidence, timestamp`.


### 2. 人流／車流計數

- 透過「跨線計數」或「區域停留統計」策略累加 ID，常用於閘門或車道分析[^3][^9]。
- 建議在資料庫中額外紀錄 `enter_time, exit_time, dwell_seconds`。


### 3. 熱點圖 (Heatmap) 產生

- 將偵測中心點落在 2D 網格，以高斯核累積熱度，傳回 1,024×1,024 矩陣供前端著色[^4][^10]。
- 可設定滑動時間窗 (例如 5分鐘) 平滑人潮變化，避免瞬時尖峰[^4]。


### 4. 異常事件偵測

| 事件類型 | 規則示例 | 欄位 | 優先級 |
| :-- | :-- | :-- | :-- |
| 逾時逗留 | `dwell_seconds > 600` | track_id | 高 |
| 人員闖入 | `class == person` 且 `roi_id == restricted_zone` | frame_id | 高 |
| 車行逆向 | 以向量角度反判 | track_id | 中 |
| 無物品區放置 | `class == bag` 且 3,600秒未移動 | track_id | 低 |

- 事件觸發時寫入 `alert_event` 表，並透過 WebSocket 推播給 Unity[^11][^12]。


### 5. 複合任務

- 若需細粒度輪廓可切換 YOLOv11 Seg 模型 (`task='segment'`) 進行實體拆解[^13]。
- 亦可串接 Pose/OBB 任務，提高工業組件對位精度[^13]。


## 資料庫模式設計

| 表名 | 關鍵欄位 | 說明 |
| :-- | :-- | :-- |
| detection_log | `uuid`, `frame_id`, `bbox`, `confidence`, `class`, `track_id` | 原始偵測記錄[^1][^2] |
| track_meta | `track_id`, `first_seen`, `last_seen`, `avg_speed`, `dwell_seconds` | 聚合統計 |
| heatmap_grid | `grid_id`, `heat_value`, `updated_at` | 熱點圖最新值[^4] |
| alert_event | `alert_id`, `type`, `severity`, `payload`, `created_at` | 異常事件 |

> 若使用 TimescaleDB，可對 `detection_log` 建立時間分區，並對 `track_id` 建置 Hyper-Log-Log 估計唯一值，加速聚合。

## API 與串流層

### REST API

| 路徑 | 方法 | 功能 | 回傳格式 |
| :-- | :-- | :-- | :-- |
| `/api/v1/detections` | GET | 分頁查詢偵測 | JSON/ProtoBuf |
| `/api/v1/tracks/{id}` | GET | 取得個別追蹤軌跡 | GeoJSON |
| `/api/v1/heatmap` | GET | 取得最新熱點圖 | Base64 PNG |
| `/api/v1/alerts/subscribe` | WS | 訂閱異常事件 | JSON Stream |

- 建議使用 FastAPI 以 async/await 撰寫；內建 WebSocket 支援[^12]。


### WebSocket / WebRTC 實時畫面

- 若 Unity 需低延遲視覺資料，可用 aiortc 建立 WebRTC channel[^6]。
- 方案：感知伺服器發布 H264 RTP → Signaling Server → Unity Peer Connection。


## 與 Unity 數位雙生整合

1. **資料拉取方式**
    - 使用 `UnityWebRequest` 或第三方 RESTClient/REST Express 套件[^5][^14]。
    - 解析後以 `JsonUtility.FromJson` 或 `MessagePack` 反序列化。
2. **場景映射**
    - `track_id` ↔ Unity `GameObject` 同名子節點。
    - 對象位置=資料庫 `bbox` 中心點 × 比例係數，對應到世界座標。
3. **動態熱點顯示**
    - 收到 Heatmap PNG 後轉為 `Texture2D`；貼附至地面 Mesh。
    - 每隔 30秒 更新一次以平衡 FPS 與即時性[^10]。
4. **事件可視化**
    - WebSocket 推播 → Unity 協程 → UI 頻道跳出警示框[^11]。
    - 音效或粒子特效指向異常物件。

## DevOps、測試與監控

| 項目 | 建議工具 | 要點 | 來源 |
| :-- | :-- | :-- | :-- |
| CI/CD | GitHub Actions | GPU 容器快照、模型版本標籤 | 18 |
| 容器化 | Docker Compose/K8s | 拆分推論、API、DB、訊息匯流排 | 5 |
| 監控 | Prometheus + Grafana | GPU 使用率、平均延遲、事件頻率 | 37 |
| 端對端測試 | Postman → REST Express 自動生成 Unity 測試腳本 | 減少手寫 API 誤差 | 39 |

## 安全與權限管理

- JWT 驗證 + RBAC：區分「管理員、檢視者、裝置」權限。
- 影像資料如涉隱私，依 ISO/IEC 27701 對人臉進行遮罩或只存哈希。
- WebSocket 訂閱層加入分組推送，僅回傳授權 ROI。


## 功能優先級與里程碑建議

| 階段 | 關鍵交付 | 期限 | 依賴 |
| :-- | :-- | :-- | :-- |
| P0 | YOLOv11 基礎偵測 + REST `/detections` | 第1月 | GPU 節點 |
| P1 | 多目標追蹤 + 計數 API | 第2月 | P0 |
| P2 | Heatmap 生成 + Unity 可視化 | 第3月 | P1 |
| P3 | 異常事件規則引擎 + WebSocket 推播 | 第4月 | P2 |
| P4 | WebRTC 串流 + 手機端 XR | 第6月 | P3 |

## 常見挑戰與對策

| 挑戰 | 原因 | 對策 |
| :-- | :-- | :-- |
| 在高流量場館 FPS 急降 | 追蹤器匹配計算量大 | 依物件類別分流、動態切換 nms_thres |
| 資料庫暴增 | 長時熱點資料佔用 | 只保留 24h 原始偵測，匯總寫回 HDF5 |
| Unity 畫面延遲 | REST 輪詢不及時 | 搭配 WebSocket 差量推送 |

## 結語

透過上列後端模組，你可在 YOLOv11 推論之上快速疊代出「追蹤、計數、熱點、異常告警」等核心分析，並將資料以低延遲管道送達 Unity 數位雙生場景。循序落實 P0–P4 里程碑，即能打造一套可水平擴充、易維運、並具備實時可視化能力的完整 Computer Vision 服務。

<div style="text-align: center">⁂</div>

[^1]: https://docs.ultralytics.com/modes/track/

[^2]: https://pyimagesearch.com/2024/06/17/object-tracking-with-yolov8-and-python/

[^3]: https://typeset.io/pdf/a-novel-yolo-based-real-time-people-counting-approach-3o35xcyw62.pdf

[^4]: https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123700222.pdf

[^5]: https://github.com/Unity3dAzure/RESTClient

[^6]: https://modal.com/docs/examples/webrtc_yolo

[^7]: https://unity.com/topics/digital-twin-definition

[^8]: https://learn.unity.com/tutorial/introduction-to-digital-twins-with-unity

[^9]: https://www.semanticscholar.org/paper/A-novel-YOLO-Based-real-time-people-counting-Ren-Fang/8a79f302ef20e04ccd018921e92594031edfd58e

[^10]: https://www.youtube.com/watch?v=J2QwUv-enBg

[^11]: https://github.com/ultralytics/yolov5/issues/11042

[^12]: https://www.youtube.com/watch?v=1H9qUzmSm_M

[^13]: https://docs.ultralytics.com/reference/data/dataset/

[^14]: https://dev.to/aqaddoura/revolutionizing-unity-api-integration-from-postman-to-production-in-minutes-with-rest-express-5577

[^15]: https://www.toolify.ai/ai-news/build-a-powerful-object-detection-api-with-yolo-and-flask-2053088

[^16]: https://www.geeksforgeeks.org/machine-learning/yolo-you-only-look-once-real-time-object-detection/

[^17]: https://www.classcentral.com/course/youtube-build-a-flask-backend-for-real-time-weed-detection-with-yolov8-full-stack-ai-tutorial-421532

[^18]: https://e-space.mmu.ac.uk/619410/1/YOLO-PC-revised.pdf

[^19]: https://www.youtube.com/watch?v=9BnubSbXnRM

[^20]: https://docs.ultralytics.com/datasets/detect/

[^21]: https://labelstud.io/tutorials/yolo

[^22]: https://www.youtube.com/watch?v=vi2K3NmKHfA

[^23]: https://www.youtube.com/watch?v=rapWRxOYYUw

[^24]: https://pjreddie.com/darknet/yolo/

[^25]: https://www.youtube.com/watch?v=eJbuC0AH10A

[^26]: https://www.ultralytics.com/blog/how-to-use-ultralytics-yolo11-for-object-tracking

[^27]: https://github.com/Deepchavda007/People-Count-using-YOLOv8

[^28]: https://www.toolify.ai/tw/ai-news-tw/使用yolo和flask建立物件辨識api-2063076

[^29]: https://universe.roboflow.com/peter-malak-j25xh/yolo-augmentation-basic-database/dataset/1

[^30]: https://www.koyeb.com/tutorials/using-yolo-for-real-time-ai-image-detection-with-koyeb-gpus

[^31]: https://github.com/opendatalab/DocLayout-YOLO

[^32]: https://unity.com/resources/unity-digital-twin-solutions-video

[^33]: https://stackoverflow.com/questions/58594235/yolo-training-yolo-with-own-dataset/59943154

[^34]: https://www.youtube.com/watch?v=iPpCgFF0of0

[^35]: https://openreview.net/forum?id=nibW47kUvt

[^36]: https://www.youtube.com/watch?v=dGrgy2dAvSI

[^37]: https://arxiv.org/html/2411.15653v1

[^38]: https://www.youtube.com/watch?v=GXvJ1RddsfQ

[^39]: https://www.unity-consulting.com/en/consulting-services/digital-twin/

