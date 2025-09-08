# Unity 螢幕座標整合指南

## 🎮 座標系統說明

您的系統現在已經支援 **Unity 螢幕座標格式**！

### 📊 座標轉換對照

| 項目 | 原始像素座標 | Unity 螢幕座標 |
|------|-------------|----------------|
| **原點位置** | 左上角 (0, 0) | 左下角 (0, 0) |
| **Y軸方向** | 向下為正 | 向上為正 |
| **座標單位** | 像素 | 像素 |
| **座標格式** | center_x, center_y | screen_x, screen_y |

### 🔄 轉換範例

```
1920x1080 解析度螢幕中的物件：

原始座標: center_x=320, center_y=240
Unity座標: screen_x=320, screen_y=840

原始座標: center_x=960, center_y=540  (螢幕中心)
Unity座標: screen_x=960, screen_y=540  (螢幕中心)

原始座標: center_x=1600, center_y=840
Unity座標: screen_x=1600, screen_y=240
```

## 🌐 API 使用方式

### 基本搜尋

```
Unity 格式: http://26.86.64.166:8001/api/v1/data/search?keyword=person&coordinate_format=unity
像素格式: http://26.86.64.166:8001/api/v1/data/search?keyword=person&coordinate_format=pixel
```

### 常用 API 端點

1. **搜尋人物 (Unity 格式)**
   ```
   http://26.86.64.166:8001/api/v1/data/search?keyword=person&coordinate_format=unity
   ```

2. **搜尋汽車 (Unity 格式)**
   ```
   http://26.86.64.166:8001/api/v1/data/search?keyword=car&coordinate_format=unity
   ```

3. **取得所有檢測結果 (Unity 格式)**
   ```
   http://26.86.64.166:8001/api/v1/data/search?table=detections&coordinate_format=unity
   ```

## 📝 Unity C# 整合範例

### 資料結構定義

```csharp
[System.Serializable]
public class YOLODetection
{
    public int id;
    public string object_type;
    public string object_chinese;
    public float confidence;
    
    // Unity 螢幕座標 (主要使用)
    public float screen_x;
    public float screen_y;
    
    // 邊界框座標
    public float bbox_screen_x1;
    public float bbox_screen_y1;
    public float bbox_screen_x2;
    public float bbox_screen_y2;
    
    // 尺寸資訊
    public float width;
    public float height;
    
    // 追蹤資訊
    public string track_id;
    public string zone;
}

[System.Serializable]
public class SearchResponse
{
    public YOLODetection[] detections;
    public int total_count;
    public string coordinate_format;
}
```

### API 調用腳本

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;

public class YOLODataClient : MonoBehaviour
{
    [Header("API 設定")]
    public string baseUrl = "http://26.86.64.166:8001/api/v1/data/search";
    public string searchKeyword = "person";
    
    [Header("顯示設定")]
    public GameObject detectionPrefab;
    public Transform parentTransform;
    
    void Start()
    {
        StartCoroutine(FetchDetections());
    }
    
    IEnumerator FetchDetections()
    {
        // 構建 Unity 格式的 API URL
        string url = $"{baseUrl}?keyword={searchKeyword}&coordinate_format=unity&table=detections&limit=50";
        
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                string jsonText = request.downloadHandler.text;
                Debug.Log($"收到資料: {jsonText}");
                
                // 解析 JSON 回應
                var response = JsonUtility.FromJson<SearchResponse>(jsonText);
                
                // 處理檢測結果
                foreach (var detection in response.detections)
                {
                    CreateDetectionObject(detection);
                }
                
                Debug.Log($"成功載入 {response.total_count} 個檢測結果");
            }
            else
            {
                Debug.LogError($"API 調用失敗: {request.error}");
            }
        }
    }
    
    void CreateDetectionObject(YOLODetection detection)
    {
        // 將螢幕座標轉換為世界座標
        Vector3 screenPos = new Vector3(detection.screen_x, detection.screen_y, 0);
        Vector3 worldPos = Camera.main.ScreenToWorldPoint(screenPos);
        
        // 創建檢測物件
        GameObject obj = Instantiate(detectionPrefab, worldPos, Quaternion.identity, parentTransform);
        obj.name = $"{detection.object_chinese}_{detection.id}";
        
        // 設置物件資訊
        var info = obj.GetComponent<DetectionInfo>();
        if (info != null)
        {
            info.SetDetection(detection);
        }
        
        Debug.Log($"創建物件: {detection.object_chinese} 於 Unity 座標 ({detection.screen_x}, {detection.screen_y})");
    }
}
```

### 檢測資訊組件

```csharp
using UnityEngine;
using UnityEngine.UI;

public class DetectionInfo : MonoBehaviour
{
    [Header("UI 元素")]
    public Text labelText;
    public Text confidenceText;
    public Image backgroundImage;
    
    private YOLODetection detectionData;
    
    public void SetDetection(YOLODetection detection)
    {
        detectionData = detection;
        
        // 更新 UI 顯示
        if (labelText != null)
            labelText.text = detection.object_chinese;
        
        if (confidenceText != null)
            confidenceText.text = $"{(detection.confidence * 100):F1}%";
        
        // 根據信心度調整顏色
        if (backgroundImage != null)
        {
            Color color = Color.Lerp(Color.red, Color.green, detection.confidence);
            backgroundImage.color = color;
        }
    }
    
    void Update()
    {
        // 如果需要即時更新位置，可以在這裡實作
    }
}
```

## 🔧 常見問題解決

### Q1: 座標位置不對？
**A:** 確認您使用的是 `screen_x` 和 `screen_y` 欄位，不是原始的 `center_x` 和 `center_y`。

### Q2: Y軸方向相反？
**A:** Unity 螢幕座標的 Y軸向上為正，這已經在轉換中處理了。

### Q3: 需要原始像素座標？
**A:** 使用 `coordinate_format=pixel` 參數或查看回傳資料中的 `original_pixel` 欄位。

## 📞 技術支援

- **API 文件**: http://26.86.64.166:8001/docs
- **測試工具**: 執行 `python test_unity_coordinates.py`
- **座標轉換測試**: 使用上面的測試腳本驗證轉換結果

---

**🎯 現在您的組員可以直接在 Unity 中使用這些座標資料，無需額外轉換！**
