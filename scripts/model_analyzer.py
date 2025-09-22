"""
YOLOv11 模型資訊提取工具
分析模型文件的詳細資訊
"""
import torch
import os
from pathlib import Path
import json

def extract_model_info(model_path):
    """提取 YOLO 模型的詳細資訊"""
    try:
        model_path = Path(model_path)
        if not model_path.exists():
            return {"error": f"模型文件不存在: {model_path}"}
        
        print(f"📁 分析模型文件: {model_path}")
        print(f"📊 文件大小: {model_path.stat().st_size / (1024*1024):.1f} MB")
        
        # 載入模型檢查點 (處理 YOLO 模型的安全載入)
        try:
            # 嘗試安全載入
            checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
        except Exception as e1:
            print(f"⚠️ 標準載入失敗: {e1}")
            try:
                # 嘗試允許 ultralytics 全域
                import torch.serialization
                torch.serialization.add_safe_globals(['ultralytics.nn.tasks.DetectionModel'])
                checkpoint = torch.load(model_path, map_location='cpu')
            except Exception as e2:
                print(f"⚠️ 安全載入失敗: {e2}")
                # 最後嘗試不安全載入 (僅用於分析)
                checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
        
        model_info = {
            "file_size_mb": round(model_path.stat().st_size / (1024*1024), 1),
            "file_path": str(model_path)
        }
        
        print(f"🔍 檢查點類型: {type(checkpoint)}")
        
        if isinstance(checkpoint, dict):
            print(f"📋 檢查點包含的鍵: {list(checkpoint.keys())}")
            
            # 模型架構資訊
            if 'model' in checkpoint:
                model = checkpoint['model']
                print(f"🏗️ 模型類型: {type(model)}")
                
                # 計算參數量
                if hasattr(model, 'parameters'):
                    total_params = sum(p.numel() for p in model.parameters())
                    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
                    model_info['total_parameters'] = total_params
                    model_info['trainable_parameters'] = trainable_params
                    model_info['parameters_m'] = f"{total_params/1e6:.1f}M"
                    print(f"⚙️ 總參數量: {total_params:,} ({total_params/1e6:.1f}M)")
                    print(f"🎯 可訓練參數: {trainable_params:,}")
                
                # 類別資訊
                if hasattr(model, 'names') and model.names:
                    model_info['class_names'] = model.names
                    model_info['num_classes'] = len(model.names)
                    print(f"🏷️ 類別數量: {len(model.names)}")
                    print(f"📝 類別名稱: {list(model.names.values())[:10]}..." if len(model.names) > 10 else f"📝 類別名稱: {list(model.names.values())}")
                
                # 模型配置
                if hasattr(model, 'yaml'):
                    model_info['yaml_config'] = model.yaml
                    print(f"📄 YAML 配置: 可用")
                
                if hasattr(model, 'model') and hasattr(model.model, '__len__'):
                    model_info['num_layers'] = len(model.model)
                    print(f"🔗 層數: {len(model.model)}")
            
            # 訓練資訊
            if 'epoch' in checkpoint:
                model_info['trained_epochs'] = checkpoint['epoch']
                print(f"📈 訓練週期: {checkpoint['epoch']}")
            
            if 'best_fitness' in checkpoint:
                model_info['best_fitness'] = float(checkpoint['best_fitness'])
                print(f"🏆 最佳適應度: {checkpoint['best_fitness']}")
            
            # 性能指標
            metrics_keys = ['metrics', 'results', 'best_fitness']
            for key in metrics_keys:
                if key in checkpoint:
                    model_info[key] = checkpoint[key]
                    print(f"📊 {key}: 可用")
            
            # 元數據
            metadata_keys = ['date', 'version', 'license', 'docs', 'imgsz', 'task']
            for key in metadata_keys:
                if key in checkpoint:
                    model_info[key] = checkpoint[key]
                    print(f"ℹ️ {key}: {checkpoint[key]}")
        
        return model_info
        
    except Exception as e:
        return {"error": f"載入模型時發生錯誤: {str(e)}"}

def main():
    print("=" * 60)
    print("🔍 YOLOv11n 模型詳細資訊分析")
    print("=" * 60)
    
    model_path = r"D:\project\system\yolo11n.pt"
    info = extract_model_info(model_path)
    
    print("\n" + "=" * 60)
    print("📋 分析結果總結")
    print("=" * 60)
    
    if "error" in info:
        print(f"❌ 錯誤: {info['error']}")
    else:
        # 整理關鍵資訊
        print(f"📁 文件大小: {info.get('file_size_mb', 'N/A')} MB")
        print(f"⚙️ 參數量: {info.get('parameters_m', 'N/A')}")
        print(f"🏷️ 類別數: {info.get('num_classes', 'N/A')}")
        print(f"🔗 層數: {info.get('num_layers', 'N/A')}")
        print(f"📈 訓練週期: {info.get('trained_epochs', 'N/A')}")
        print(f"🏆 最佳適應度: {info.get('best_fitness', 'N/A')}")
        
        # 保存詳細資訊到 JSON
        output_file = "yolov11n_model_info.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 詳細資訊已保存到: {output_file}")

if __name__ == "__main__":
    main()
