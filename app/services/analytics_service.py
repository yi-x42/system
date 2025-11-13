"""
分析統計服務
提供檢測結果的統計分析和數據視覺化支持
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, desc, text, or_

from app.core.logger import api_logger
from app.models.database import DetectionResult, AnalysisTask

class AnalyticsService:
    """分析統計服務"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5分鐘緩存
    
    async def get_analytics_data(
        self,
        period: str = "24h",
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """獲取分析統計數據"""
        try:
            # 檢查緩存
            cache_key = f"analytics_{period}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 根據時間段設定查詢範圍
            time_range = self._get_time_range(period)
            
            if db:
                # 從數據庫獲取真實數據
                data = await self._get_database_analytics(time_range, db)
            else:
                # 生成模擬數據
                data = self._generate_mock_analytics(period)
            
            # 更新緩存
            self.cache[cache_key] = {
                "data": data,
                "timestamp": datetime.now()
            }
            
            return data
            
        except Exception as e:
            api_logger.error(f"獲取分析數據失敗: {e}")
            # 返回模擬數據作為備用
            return self._generate_mock_analytics(period)
    
    def _get_time_range(self, period: str) -> Dict[str, datetime]:
        """根據時間段字符串返回時間範圍"""
        now = datetime.now()
        
        if period == "1h":
            start_time = now - timedelta(hours=1)
        elif period == "24h":
            start_time = now - timedelta(hours=24)
        elif period == "7d":
            start_time = now - timedelta(days=7)
        elif period == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)  # 預設24小時
        
        return {"start": start_time, "end": now}
    
    async def _get_database_analytics(
        self,
        time_range: Dict[str, datetime],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """從數據庫獲取真實的分析數據"""
        try:
            start_time = time_range["start"]
            end_time = time_range["end"]
            
            # 檢測總數統計
            detection_counts = await self._get_detection_counts(start_time, end_time, db)
            
            # 小時趨勢數據
            hourly_trend = await self._get_hourly_trend(start_time, end_time, db)
            
            # 類別分布統計
            category_distribution = await self._get_category_distribution(start_time, end_time, db)
            
            # 時段分析
            time_period_analysis = await self._get_time_period_analysis(start_time, end_time, db)
            
            return {
                "detection_counts": detection_counts,
                "hourly_trend": hourly_trend,
                "category_distribution": category_distribution,
                "time_period_analysis": time_period_analysis
            }
            
        except Exception as e:
            api_logger.error(f"從數據庫獲取分析數據失敗: {e}")
            raise
    
    async def _get_detection_counts(
        self,
        start_time: datetime,
        end_time: datetime,
        db: AsyncSession
    ) -> Dict[str, int]:
        """獲取檢測數量統計"""
        try:
            # 總檢測數
            total_query = select(func.count(DetectionResult.id)).where(
                and_(
                    DetectionResult.frame_timestamp >= start_time,
                    DetectionResult.frame_timestamp <= end_time
                )
            )
            total_result = await db.execute(total_query)
            total_detections = total_result.scalar() or 0
            
            # 人員檢測數
            person_query = select(func.count(DetectionResult.id)).where(
                and_(
                    DetectionResult.object_type == "person",
                    DetectionResult.frame_timestamp >= start_time,
                    DetectionResult.frame_timestamp <= end_time
                )
            )
            person_result = await db.execute(person_query)
            person_count = person_result.scalar() or 0
            
            # 車輛檢測數
            vehicle_query = select(func.count(DetectionResult.id)).where(
                and_(
                    DetectionResult.object_type.in_(["car", "truck", "bus", "motorcycle"]),
                    DetectionResult.frame_timestamp >= start_time,
                    DetectionResult.frame_timestamp <= end_time
                )
            )
            vehicle_result = await db.execute(vehicle_query)
            vehicle_count = vehicle_result.scalar() or 0
            
            # 異常事件（高信心度的檢測）
            alert_query = select(func.count(DetectionResult.id)).where(
                and_(
                    DetectionResult.confidence > 0.9,
                    DetectionResult.frame_timestamp >= start_time,
                    DetectionResult.frame_timestamp <= end_time
                )
            )
            alert_result = await db.execute(alert_query)
            alert_count = alert_result.scalar() or 0
            
            return {
                "total_detections": total_detections,
                "person_count": person_count,
                "vehicle_count": vehicle_count,
                "alert_count": alert_count
            }
            
        except Exception as e:
            api_logger.error(f"獲取檢測數量統計失敗: {e}")
            return {"total_detections": 0, "person_count": 0, "vehicle_count": 0, "alert_count": 0}
    
    async def _get_hourly_trend(
        self,
        start_time: datetime,
        end_time: datetime,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """獲取小時趨勢數據"""
        try:
            # 使用簡化的 SQL 查詢
            query = text("""
                SELECT 
                    EXTRACT(hour FROM timestamp) as hour,
                    object_type,
                    COUNT(*) as count
                FROM detection_results 
                WHERE timestamp >= :start_time AND timestamp <= :end_time
                GROUP BY EXTRACT(hour FROM timestamp), object_type
                ORDER BY hour
            """)
            
            result = await db.execute(query, {
                "start_time": start_time,
                "end_time": end_time
            })
            
            # 處理查詢結果
            hourly_data = {}
            for row in result:
                hour = int(row.hour)
                hour_str = f"{hour:02d}:00"
                if hour_str not in hourly_data:
                    hourly_data[hour_str] = {"total": 0, "person": 0, "vehicle": 0, "other": 0}
                
                hourly_data[hour_str]["total"] += row.count
                
                if row.object_type == "person":
                    hourly_data[hour_str]["person"] += row.count
                elif row.object_type in ["car", "truck", "bus", "motorcycle"]:
                    hourly_data[hour_str]["vehicle"] += row.count
                else:
                    hourly_data[hour_str]["other"] += row.count
            
            # 轉換為列表格式
            trend_list = []
            for hour, counts in sorted(hourly_data.items()):
                trend_list.append({
                    "hour": hour,
                    "total": counts["total"],
                    "person": counts["person"],
                    "vehicle": counts["vehicle"],
                    "other": counts["other"]
                })
            
            return trend_list
            
        except Exception as e:
            api_logger.error(f"獲取小時趨勢失敗: {e}")
            # 返回空列表而不是空字典，確保數據結構正確
            return []
    
    async def _get_category_distribution(
        self,
        start_time: datetime,
        end_time: datetime,
        db: AsyncSession
    ) -> Dict[str, int]:
        """獲取類別分布統計"""
        try:
            query = select(
                DetectionResult.object_type,
                func.count(DetectionResult.id).label('count')
            ).where(
                and_(
                    DetectionResult.frame_timestamp >= start_time,
                    DetectionResult.frame_timestamp <= end_time
                )
            ).group_by(DetectionResult.object_type)
            
            result = await db.execute(query)
            
            distribution = {}
            for row in result:
                distribution[row.object_type] = row.count
            
            return distribution
            
        except Exception as e:
            api_logger.error(f"獲取類別分布失敗: {e}")
            return {}
    
    async def _get_time_period_analysis(
        self,
        start_time: datetime,
        end_time: datetime,
        db: AsyncSession
    ) -> Dict[str, int]:
        """獲取時段分析數據"""
        try:
            # 查詢不同時段的檢測數量
            periods = {
                "morning": (6, 12),    # 06:00-12:00
                "afternoon": (12, 18), # 12:00-18:00
                "evening": (18, 24),   # 18:00-24:00
                "night": (0, 6)        # 00:00-06:00
            }
            
            period_data = {}
            for period_name, (start_hour, end_hour) in periods.items():
                if start_hour < end_hour:
                    hour_condition = and_(
                        func.extract('hour', DetectionResult.frame_timestamp) >= start_hour,
                        func.extract('hour', DetectionResult.frame_timestamp) < end_hour
                    )
                else:  # 跨日情況（night period）
                    hour_condition = or_(
                        func.extract('hour', DetectionResult.frame_timestamp) >= start_hour,
                        func.extract('hour', DetectionResult.frame_timestamp) < end_hour
                    )
                
                query = select(func.count(DetectionResult.id)).where(
                    and_(
                        DetectionResult.frame_timestamp >= start_time,
                        DetectionResult.frame_timestamp <= end_time,
                        hour_condition
                    )
                )
                
                result = await db.execute(query)
                period_data[period_name] = result.scalar() or 0
            
            return period_data
            
        except Exception as e:
            api_logger.error(f"獲取時段分析失敗: {e}")
            return {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
    
    def _generate_mock_analytics(self, period: str) -> Dict[str, Any]:
        """生成模擬的分析數據"""
        import random
        
        # 根據時間段調整數據規模
        scale_factor = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 24)
        
        # 檢測數量統計
        detection_counts = {
            "total_detections": random.randint(100, 1000) * (scale_factor // 24 + 1),
            "person_count": random.randint(50, 500) * (scale_factor // 24 + 1),
            "vehicle_count": random.randint(20, 200) * (scale_factor // 24 + 1),
            "alert_count": random.randint(5, 50) * (scale_factor // 24 + 1)
        }
        
        # 小時趨勢數據
        hours = 24 if period in ["24h", "1h"] else min(scale_factor, 168)  # 最多顯示一週的小時數據
        hourly_trend = []
        for i in range(min(hours, 24)):
            hourly_trend.append({
                "time": f"{i:02d}:00",
                "person": random.randint(0, 100),
                "vehicle": random.randint(0, 50),
                "other": random.randint(0, 20)
            })
        
        # 類別分布
        category_distribution = {
            "person": random.randint(100, 500),
            "car": random.randint(50, 200),
            "bicycle": random.randint(20, 100),
            "motorcycle": random.randint(10, 50),
            "truck": random.randint(5, 30),
            "other": random.randint(10, 80)
        }
        
        # 時段分析
        time_period_analysis = {
            "morning": random.randint(50, 200),
            "afternoon": random.randint(100, 300),
            "evening": random.randint(80, 250),
            "night": random.randint(20, 100)
        }
        
        return {
            "detection_counts": detection_counts,
            "hourly_trend": hourly_trend,
            "category_distribution": category_distribution,
            "time_period_analysis": time_period_analysis
        }
    
    async def get_heatmap_data(self, db: AsyncSession = None) -> Dict[str, Any]:
        """獲取熱點圖數據"""
        try:
            if db:
                # 從數據庫獲取位置數據
                return await self._get_database_heatmap(db)
            else:
                # 生成模擬熱點圖數據
                return self._generate_mock_heatmap()
                
        except Exception as e:
            api_logger.error(f"獲取熱點圖數據失敗: {e}")
            return self._generate_mock_heatmap()
    
    async def _get_database_heatmap(self, db: AsyncSession) -> Dict[str, Any]:
        """從數據庫獲取熱點圖數據"""
        try:
            # 查詢檢測結果的位置分布
            yesterday = datetime.now() - timedelta(days=1)
            
            # 簡化的熱點數據查詢（實際應該根據檢測框的中心點計算）
            query = select(
                DetectionResult.x_min,
                DetectionResult.y_min,
                DetectionResult.x_max,
                DetectionResult.y_max,
                func.count(DetectionResult.id).label('count')
            ).where(
                DetectionResult.created_at >= yesterday
            ).group_by(
                DetectionResult.x_min,
                DetectionResult.y_min,
                DetectionResult.x_max,
                DetectionResult.y_max
            ).limit(100)
            
            result = await db.execute(query)
            
            heatmap_points = []
            for row in result:
                # 計算檢測框中心點
                center_x = (row.x_min + row.x_max) / 2
                center_y = (row.y_min + row.y_max) / 2
                
                heatmap_points.append({
                    "x": center_x,
                    "y": center_y,
                    "intensity": row.count
                })
            
            return {
                "points": heatmap_points,
                "max_intensity": max([p["intensity"] for p in heatmap_points]) if heatmap_points else 1
            }
            
        except Exception as e:
            api_logger.error(f"從數據庫獲取熱點圖數據失敗: {e}")
            return self._generate_mock_heatmap()
    
    def _generate_mock_heatmap(self) -> Dict[str, Any]:
        """生成模擬熱點圖數據"""
        import random
        
        # 生成隨機熱點
        points = []
        for _ in range(50):
            points.append({
                "x": random.uniform(0, 1),
                "y": random.uniform(0, 1),
                "intensity": random.randint(1, 100)
            })
        
        return {
            "points": points,
            "max_intensity": 100
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查緩存是否有效"""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key]["timestamp"]
        return (datetime.now() - cache_time).total_seconds() < self.cache_timeout
    
    def clear_cache(self):
        """清空緩存"""
        self.cache.clear()
        api_logger.info("分析數據緩存已清空")
