# 🎮 Unity 檢測結果 API 使用指南

## 📡 API 端點列表

### 基礎 URL
- **本機：** `http://localhost:8002`
- **Radmin 網絡：** `http://26.86.64.166:8002`

### 主要端點

| 端點 | 方法 | 說明 | Unity 用途 |
|------|------|------|-----------|
| `/detection-results` | GET | 獲取所有檢測結果 | 載入歷史資料 |
| `/detection-results/latest` | GET | 獲取最新檢測結果 | 實時更新顯示 |
| `/detection-results/task/{task_id}` | GET | 獲取特定任務結果 | 播放特定任務 |
| `/detection-results/stats` | GET | 獲取統計資訊 | 顯示總覽 |
| `/health` | GET | 健康檢查 | 連接測試 |

## 🎯 Unity C# 範例代碼

### 1. 基本資料結構

```csharp
[System.Serializable]
public class DetectionResult
{
    public int id;
    public int task_id;
    public int frame_number;
    public string timestamp;
    public string object_type;
    public float confidence;
    public float bbox_x1;
    public float bbox_y1;
    public float bbox_x2;
    public float bbox_y2;
    public float center_x;
    public float center_y;
}

[System.Serializable]
public class DetectionResponse
{
    public string status;
    public int total_count;
    public int returned_count;
    public int limit;
    public int offset;
    public DetectionResult[] data;
}
```

### 2. API 客戶端類別

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using Newtonsoft.Json;

public class YOLOAPIClient : MonoBehaviour
{
    [Header("API 設定")]
    public string apiBaseUrl = "http://26.86.64.166:8002";
    
    [Header("顯示設定")]
    public GameObject detectionPrefab;
    public Transform parentTransform;
    
    private List<DetectionResult> currentDetections = new List<DetectionResult>();
    
    void Start()
    {
        // 測試連接
        StartCoroutine(TestConnection());
        
        // 載入最新檢測結果
        StartCoroutine(LoadLatestDetections());
    }
    
    /// <summary>
    /// 測試 API 連接
    /// </summary>
    public IEnumerator TestConnection()
    {
        string url = $"{apiBaseUrl}/health";
        
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("✅ API 連接成功！");
                Debug.Log($"回應: {request.downloadHandler.text}");
            }
            else
            {
                Debug.LogError($"❌ API 連接失敗: {request.error}");
            }
        }
    }
    
    /// <summary>
    /// 獲取最新檢測結果
    /// </summary>
    public IEnumerator LoadLatestDetections(int limit = 50, string objectType = null)
    {
        string url = $"{apiBaseUrl}/detection-results/latest?limit={limit}";
        
        if (!string.IsNullOrEmpty(objectType))
        {
            url += $"&object_type={objectType}";
        }
        
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                try
                {
                    DetectionResponse response = JsonConvert.DeserializeObject<DetectionResponse>(request.downloadHandler.text);
                    
                    Debug.Log($"📊 載入了 {response.returned_count} 筆檢測結果");
                    
                    currentDetections.Clear();
                    currentDetections.AddRange(response.data);
                    
                    // 在場景中顯示檢測結果
                    DisplayDetections(response.data);
                }
                catch (System.Exception e)
                {
                    Debug.LogError($"JSON 解析失敗: {e.Message}");
                }
            }
            else
            {
                Debug.LogError($"載入失敗: {request.error}");
            }
        }
    }
    
    /// <summary>
    /// 獲取特定任務的檢測結果
    /// </summary>
    public IEnumerator LoadTaskDetections(int taskId, int limit = 100)
    {
        string url = $"{apiBaseUrl}/detection-results/task/{taskId}?limit={limit}";
        
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                try
                {
                    DetectionResponse response = JsonConvert.DeserializeObject<DetectionResponse>(request.downloadHandler.text);
                    
                    Debug.Log($"📊 任務 {taskId} 載入了 {response.returned_count} 筆檢測結果");
                    
                    currentDetections.Clear();
                    currentDetections.AddRange(response.data);
                    
                    // 播放任務檢測序列
                    StartCoroutine(PlayDetectionSequence(response.data));
                }
                catch (System.Exception e)
                {
                    Debug.LogError($"JSON 解析失敗: {e.Message}");
                }
            }
            else
            {
                Debug.LogError($"載入任務失敗: {request.error}");
            }
        }
    }
    
    /// <summary>
    /// 在場景中顯示檢測結果
    /// </summary>
    void DisplayDetections(DetectionResult[] detections)
    {
        // 清除舊的顯示物件
        foreach (Transform child in parentTransform)
        {
            Destroy(child.gameObject);
        }
        
        // 創建新的檢測物件
        foreach (DetectionResult detection in detections)
        {
            CreateDetectionObject(detection);
        }
    }
    
    /// <summary>
    /// 創建單個檢測物件
    /// </summary>
    void CreateDetectionObject(DetectionResult detection)
    {
        if (detectionPrefab == null) return;
        
        GameObject detectionObj = Instantiate(detectionPrefab, parentTransform);
        
        // 設定位置 (需要根據您的座標系統調整)
        Vector3 position = new Vector3(
            detection.center_x / 100f,  // 縮放比例
            detection.center_y / 100f,
            0
        );
        detectionObj.transform.localPosition = position;
        
        // 設定大小
        float width = (detection.bbox_x2 - detection.bbox_x1) / 100f;
        float height = (detection.bbox_y2 - detection.bbox_y1) / 100f;
        detectionObj.transform.localScale = new Vector3(width, height, 1f);
        
        // 設定顏色
        Renderer renderer = detectionObj.GetComponent<Renderer>();
        if (renderer != null)
        {
            renderer.material.color = GetObjectColor(detection.object_type);
        }
        
        // 設定文字標籤
        TextMesh textMesh = detectionObj.GetComponentInChildren<TextMesh>();
        if (textMesh != null)
        {
            textMesh.text = $"{detection.object_type}\n{detection.confidence:F2}";
        }
        
        // 儲存檢測資料到物件
        DetectionDisplay display = detectionObj.GetComponent<DetectionDisplay>();
        if (display == null)
        {
            display = detectionObj.AddComponent<DetectionDisplay>();
        }
        display.detectionData = detection;
    }
    
    /// <summary>
    /// 播放檢測序列
    /// </summary>
    IEnumerator PlayDetectionSequence(DetectionResult[] detections)
    {
        Debug.Log($"🎬 開始播放 {detections.Length} 個檢測序列");
        
        foreach (DetectionResult detection in detections)
        {
            // 清除舊顯示
            foreach (Transform child in parentTransform)
            {
                Destroy(child.gameObject);
            }
            
            // 顯示當前檢測
            CreateDetectionObject(detection);
            
            Debug.Log($"Frame {detection.frame_number}: {detection.object_type} at ({detection.center_x}, {detection.center_y})");
            
            // 等待一段時間 (模擬影片播放)
            yield return new WaitForSeconds(0.1f);
        }
        
        Debug.Log("🎬 序列播放完成");
    }
    
    /// <summary>
    /// 根據物件類型獲取顏色
    /// </summary>
    Color GetObjectColor(string objectType)
    {
        switch (objectType.ToLower())
        {
            case "person": return Color.green;
            case "car": return Color.blue;
            case "truck": return Color.red;
            case "bike": return Color.yellow;
            case "motorcycle": return Color.magenta;
            case "bus": return Color.cyan;
            default: return Color.white;
        }
    }
    
    // GUI 控制按鈕
    void OnGUI()
    {
        GUILayout.BeginArea(new Rect(10, 10, 300, 200));
        
        GUILayout.Label("YOLO 檢測結果控制");
        
        if (GUILayout.Button("載入最新檢測結果"))
        {
            StartCoroutine(LoadLatestDetections(50));
        }
        
        if (GUILayout.Button("載入任務 1 的結果"))
        {
            StartCoroutine(LoadTaskDetections(1));
        }
        
        if (GUILayout.Button("載入任務 2 的結果"))
        {
            StartCoroutine(LoadTaskDetections(2));
        }
        
        if (GUILayout.Button("測試連接"))
        {
            StartCoroutine(TestConnection());
        }
        
        GUILayout.Label($"當前載入: {currentDetections.Count} 筆檢測");
        
        GUILayout.EndArea();
    }
}
```

### 3. 檢測顯示組件

```csharp
using UnityEngine;

public class DetectionDisplay : MonoBehaviour
{
    public DetectionResult detectionData;
    
    void Start()
    {
        // 可以在這裡添加更多的視覺效果
    }
    
    void OnMouseDown()
    {
        // 點擊時顯示詳細資訊
        if (detectionData != null)
        {
            Debug.Log($"檢測詳情:\n" +
                     $"物件: {detectionData.object_type}\n" +
                     $"信心度: {detectionData.confidence:F3}\n" +
                     $"位置: ({detectionData.center_x:F1}, {detectionData.center_y:F1})\n" +
                     $"時間: {detectionData.timestamp}");
        }
    }
}
```

## 🚀 快速開始步驟

### 1. 啟動 API 服務
```bash
# 在 yolo_backend 目錄下
python create_test_data.py  # 創建測試資料
python simple_detection_api.py  # 啟動 API 服務
```

### 2. 在 Unity 中設置
1. 安裝 `Newtonsoft.Json` 套件
2. 創建空的 GameObject 並附加 `YOLOAPIClient` 腳本
3. 設定 `detectionPrefab` (用來顯示檢測結果的 Prefab)
4. 設定 `parentTransform` (檢測物件的父容器)

### 3. 測試 API
訪問以下 URL 確認 API 正常運作：
- http://26.86.64.166:8002/docs (API 文檔)
- http://26.86.64.166:8002/health (健康檢查)
- http://26.86.64.166:8002/detection-results/latest (最新檢測結果)

## 📊 資料格式範例

### API 回應格式
```json
{
  "status": "success",
  "total_count": 500,
  "returned_count": 50,
  "limit": 50,
  "offset": 0,
  "data": [
    {
      "id": 1,
      "task_id": 1,
      "frame_number": 1,
      "timestamp": "2025-08-10T10:30:01.000",
      "object_type": "person",
      "confidence": 0.85,
      "bbox_x1": 100.5,
      "bbox_y1": 150.2,
      "bbox_x2": 200.8,
      "bbox_y2": 350.9,
      "center_x": 150.65,
      "center_y": 250.55
    }
  ]
}
```

這個簡單的 API 現在可以提供檢測結果資料給您的 Unity 專案使用！🎮
