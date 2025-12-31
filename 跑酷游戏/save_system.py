# save_system.py
import json
import os
import time
from datetime import datetime


class SaveSystem:
    def __init__(self, save_file='game_saves.json'):
        self.save_file = save_file
        self.saves = self.load_saves()
        self.current_player_name = None
        self.current_save = None

        # 创建保存目录（如果不存在）
        if not os.path.exists('saves'):
            os.makedirs('saves')

    def load_saves(self):
        """加载所有存档"""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            except:
                print("无法读取存档文件，将创建新存档")
                return {"saves": [], "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        else:
            return {"saves": [], "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def save_all_saves(self):
        """保存所有存档到文件"""
        try:
            self.saves["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(self.saves, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存存档失败: {e}")
            return False

    def generate_save_name(self):
        """生成自动存档名称"""
        existing_saves = self.saves.get("saves", [])
        if not existing_saves:
            return "存档1"

        # 提取所有存档的序号
        save_numbers = []
        for save in existing_saves:
            name = save["player_name"]
            if name.startswith("存档"):
                try:
                    # 提取"存档"后面的数字
                    num = int(name[2:])
                    save_numbers.append(num)
                except ValueError:
                    continue

        # 找到最小的可用序号
        if not save_numbers:
            return "存档1"

        # 从1开始找到第一个可用的序号
        for i in range(1, max(save_numbers) + 2):
            if i not in save_numbers:
                return f"存档{i}"

        return f"存档{max(save_numbers) + 1}"

    def create_new_save(self):
        """创建新存档（自动生成名称）"""
        player_name = self.generate_save_name()

        # 创建新存档
        new_save = {
            "player_name": player_name,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_played": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "high_score": 0,
            "total_coins": 0,
            "games_played": 0,
            "total_score": 0,
            "character_stats": {
                "1": {"games_played": 0, "best_score": 0, "total_coins": 0},
                "2": {"games_played": 0, "best_score": 0, "total_coins": 0}
            },
            "achievements": {
                "first_game": False,
                "score_1000": False,
                "coins_100": False,
                "score_5000": False,
                "coins_1000": False
            }
        }

        self.saves.setdefault("saves", []).append(new_save)
        self.current_player_name = player_name
        self.current_save = new_save

        if self.save_all_saves():
            print(f"已创建新存档: {player_name}")
            return True
        else:
            return False

    def load_save(self, player_name):
        """加载指定玩家的存档"""
        for save in self.saves.get("saves", []):
            if save["player_name"].lower() == player_name.lower():
                self.current_player_name = player_name
                self.current_save = save
                return True
        return False

    def update_save(self, score=0, coins=0, character_id=1):
        """更新当前存档"""
        if not self.current_save:
            return False

        # 更新游戏次数
        self.current_save["games_played"] += 1
        self.current_save["total_score"] += int(score)

        # 更新角色统计
        char_id = str(character_id)
        if char_id in self.current_save["character_stats"]:
            char_stats = self.current_save["character_stats"][char_id]
            char_stats["games_played"] += 1
            if score > char_stats["best_score"]:
                char_stats["best_score"] = int(score)
            char_stats["total_coins"] += coins

        # 更新最高分
        if score > self.current_save["high_score"]:
            self.current_save["high_score"] = int(score)

        # 更新总金币
        self.current_save["total_coins"] += coins

        # 更新最后游戏时间
        self.current_save["last_played"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 检查成就
        self.check_achievements(score, coins)

        return self.save_all_saves()

    def check_achievements(self, score, coins):
        """检查并更新成就"""
        achievements = self.current_save["achievements"]

        # 第一次游戏
        achievements["first_game"] = True

        # 分数达到1000
        if score >= 1000:
            achievements["score_1000"] = True

        # 收集100个金币
        if coins >= 100:
            achievements["coins_100"] = True

        # 分数达到5000
        if score >= 5000:
            achievements["score_5000"] = True

        # 收集1000个金币
        if coins >= 1000:
            achievements["coins_1000"] = True

    def get_all_saves(self):
        """获取所有存档信息"""
        return self.saves.get("saves", [])

    def get_save_summary(self, player_name):
        """获取指定存档的摘要信息"""
        for save in self.saves.get("saves", []):
            if save["player_name"].lower() == player_name.lower():
                return {
                    "player_name": save["player_name"],
                    "high_score": save["high_score"],
                    "total_coins": save["total_coins"],
                    "games_played": save["games_played"],
                    "last_played": save["last_played"]
                }
        return None

    def get_current_save_info(self):
        """获取当前存档信息"""
        if not self.current_save:
            return None

        return {
            "player_name": self.current_save["player_name"],
            "high_score": self.current_save["high_score"],
            "total_coins": self.current_save["total_coins"],
            "games_played": self.current_save["games_played"],
            "total_score": self.current_save["total_score"]
        }

    def get_leaderboard(self, limit=10):
        """获取排行榜（按最高分排序）"""
        saves = self.saves.get("saves", [])
        # 按最高分排序
        sorted_saves = sorted(saves, key=lambda x: x["high_score"], reverse=True)
        return sorted_saves[:limit]

    def get_coins_leaderboard(self, limit=10):
        """获取金币排行榜（按总金币数排序）"""
        saves = self.saves.get("saves", [])
        # 按总金币数排序
        sorted_saves = sorted(saves, key=lambda x: x["total_coins"], reverse=True)
        return sorted_saves[:limit]

    def delete_save(self, player_name):
        """删除指定存档"""
        saves = self.saves.get("saves", [])
        for i, save in enumerate(saves):
            if save["player_name"].lower() == player_name.lower():
                # 如果要删除的是当前存档，清空当前存档
                if self.current_player_name and self.current_player_name.lower() == player_name.lower():
                    self.current_player_name = None
                    self.current_save = None
                saves.pop(i)
                return self.save_all_saves()
        return False

    def clear_all_saves(self):
        """清空所有存档"""
        self.saves = {"saves": [], "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        self.current_player_name = None
        self.current_save = None
        return self.save_all_saves()