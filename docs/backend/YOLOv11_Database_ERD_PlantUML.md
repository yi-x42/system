# YOLOv11 數位雙生分析系統 - PlantUML ERD

```plantuml
@startuml YOLOv11_Database_ERD

!define ENTITY entity
!define WEAK weak entity
!define RELATIONSHIP diamond

' 設定樣式
!theme plain
skinparam backgroundColor white
skinparam entity {
  BackgroundColor lightblue
  BorderColor black
}

' === 核心分析表 ===

entity "ANALYSIS_RECORDS" as ar {
  * id : UUID <<PK>>
  --
  camera_id : VARCHAR
  video_path : VARCHAR
  status : VARCHAR
  created_at : TIMESTAMP
  updated_at : TIMESTAMP
  start_time : TIMESTAMP
  end_time : TIMESTAMP
  total_frames : INTEGER
  processed_frames : INTEGER
  metadata : JSON
  error_message : TEXT
}

entity "DETECTION_RESULTS" as dr {
  * id : UUID <<PK>>
  --
  * analysis_id : UUID <<FK>>
  frame_number : INTEGER
  object_class : VARCHAR
  confidence : FLOAT
  x_min : FLOAT
  y_min : FLOAT
  x_max : FLOAT
  y_max : FLOAT
  detected_at : TIMESTAMP
  additional_data : JSON
}

entity "BEHAVIOR_EVENTS" as be {
  * id : UUID <<PK>>
  --
  * analysis_id : UUID <<FK>>
  event_type : VARCHAR
  severity : VARCHAR
  description : TEXT
  start_frame : INTEGER
  end_frame : INTEGER
  event_time : TIMESTAMP
  event_data : JSON
  is_active : BOOLEAN
}

' === 系統管理表 ===

entity "USERS" as u {
  * id : UUID <<PK>>
  --
  * username : VARCHAR <<UK>>
  * email : VARCHAR <<UK>>
  password_hash : VARCHAR
  role : VARCHAR
  is_active : BOOLEAN
  created_at : TIMESTAMP
  last_login : TIMESTAMP
  preferences : JSON
}

entity "CAMERAS" as c {
  * id : VARCHAR <<PK>>
  --
  name : VARCHAR
  type : VARCHAR
  connection_string : VARCHAR
  location : VARCHAR
  status : VARCHAR
  configuration : JSON
  created_at : TIMESTAMP
  updated_at : TIMESTAMP
  created_by : UUID <<FK>>
}

entity "YOLO_MODELS" as ym {
  * id : UUID <<PK>>
  --
  name : VARCHAR
  version : VARCHAR
  file_path : VARCHAR
  model_type : VARCHAR
  class_names : JSON
  hyperparameters : JSON
  is_active : BOOLEAN
  created_at : TIMESTAMP
  created_by : UUID <<FK>>
}

entity "SYSTEM_CONFIGURATIONS" as sc {
  * key : VARCHAR <<PK>>
  --
  category : VARCHAR
  value : TEXT
  description : TEXT
  data_type : VARCHAR
  updated_at : TIMESTAMP
  updated_by : UUID <<FK>>
}

entity "SYSTEM_LOGS" as sl {
  * id : UUID <<PK>>
  --
  level : VARCHAR
  component : VARCHAR
  message : TEXT
  context : JSON
  created_at : TIMESTAMP
  ip_address : VARCHAR
  user_id : UUID <<FK>>
}

entity "FILE_UPLOADS" as fu {
  * id : UUID <<PK>>
  --
  original_name : VARCHAR
  stored_name : VARCHAR
  file_path : VARCHAR
  mime_type : VARCHAR
  file_size : BIGINT
  checksum : VARCHAR
  upload_type : VARCHAR
  created_at : TIMESTAMP
  uploaded_by : UUID <<FK>>
}

' === 關聯關係 ===

' 一對多關係
ar ||--o{ dr : "contains"
ar ||--o{ be : "generates"

' 使用者關聯
u ||--o{ ar : "creates"
u ||--o{ c : "manages"
u ||--o{ ym : "uploads"
u ||--o{ sc : "configures"
u ||--o{ sl : "logs"
u ||--o{ fu : "uploads"

' 多對一關係
ar }o--|| c : "uses"
ar }o--|| ym : "processed_by"
ar }o--|| fu : "analyzes"

@enduml
```

## 🎨 PlantUML 使用說明

### 線上工具
- PlantUML Online: http://www.plantuml.com/plantuml/
- 複製上面的 PlantUML 代碼貼上即可生成圖表

### 本地工具
```bash
# 安裝 PlantUML
npm install -g node-plantuml
# 或使用 Java 版本
java -jar plantuml.jar diagram.puml
```

### VS Code 擴展
- PlantUML: 支援即時預覽
- Markdown Preview Enhanced: 支援 PlantUML 渲染
