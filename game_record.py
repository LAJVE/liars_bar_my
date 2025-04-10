from dataclasses import dataclass, field
from typing import List, Dict, Optional
import datetime
import json
import os

def generate_game_id():
    """生成包含时间信息的游戏ID"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return timestamp

@dataclass
class PlayerInitialState:
    """记录玩家初始状态，包括手枪状态和手牌"""
    player_name: str
    bullet_position: int
    current_gun_position: int
    initial_hand: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "player_name": self.player_name,
            "bullet_position": self.bullet_position,
            "current_gun_position": self.current_gun_position,
            "initial_hand": self.initial_hand
        }

@dataclass
class PlayAction:
    """记录一次出牌行为"""
    player_name: str
    played_cards: List[str]
    remaining_cards: List[str]
    next_player: str
    was_challenged: bool = False
    challenge_result: Optional[bool] = None
    
    def to_dict(self) -> Dict:
        return {
            "player_name": self.player_name,
            "played_cards": self.played_cards,
            "remaining_cards": self.remaining_cards,
            "next_player": self.next_player,
            "was_challenged": self.was_challenged,
            "challenge_result": self.challenge_result,
        }
    
    def update_challenge(self, was_challenged: bool, result: bool) -> None:
        """更新质疑信息"""
        self.was_challenged = was_challenged
        self.challenge_result = result

@dataclass
class ShootingResult:
    """记录一次开枪结果"""
    shooter_name: str
    bullet_hit: bool
    
    def to_dict(self) -> Dict:
        return {
            "shooter_name": self.shooter_name,
            "bullet_hit": self.bullet_hit,
        }

@dataclass
class RoundRecord:
    """记录一轮游戏"""
    round_id: int
    target_card: str
    starting_player: str
    player_initial_states: List[PlayerInitialState]
    round_players: List[str] = field(default_factory=list)
    play_history: List[PlayAction] = field(default_factory=list)
    round_result: Optional[ShootingResult] = None
    
    def to_dict(self) -> Dict:
        return {
            "round_id": self.round_id,
            "target_card": self.target_card,
            "round_players": self.round_players,
            "starting_player": self.starting_player,
            "player_initial_states": [ps.to_dict() for ps in self.player_initial_states],
            "play_history": [play.to_dict() for play in self.play_history],
            "round_result": self.round_result.to_dict() if self.round_result else None
        }
    
    def add_play_action(self, action: PlayAction) -> None:
        """添加出牌记录"""
        self.play_history.append(action)
    
    def get_last_action(self) -> Optional[PlayAction]:
        """获取最后一次出牌记录"""
        return self.play_history[-1] if self.play_history else None
    
    def set_shooting_result(self, result: ShootingResult) -> None:
        """设置射击结果"""
        self.round_result = result





@dataclass
class GameRecord:
    """完整游戏记录"""
    def __init__(self):
        self.game_id: str = generate_game_id()
        self.player_names: List[str] = []
        self.rounds: List[RoundRecord] = []
        self.winner: Optional[str] = None
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.save_directory: str = os.path.join(self.current_dir,"game_records")
        
        # 确保保存目录存在
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)
    
    def to_dict(self) -> Dict:
        return {
            "game_id": self.game_id,
            "player_names": self.player_names,
            "rounds": [round.to_dict() for round in self.rounds],
            "winner": self.winner,
        }
    
    def start_game(self, player_names: List[str]) -> None:
        """初始化游戏，记录玩家信息"""
        self.player_names = player_names
    
    def start_round(self, round_id: int, target_card: str, round_players: List[str], starting_player: str, player_initial_states: List[PlayerInitialState]) -> None:
        """开始新的一轮游戏"""
        round_record = RoundRecord(
            round_id=round_id,
            target_card=target_card,
            round_players=round_players,
            starting_player=starting_player,
            player_initial_states=player_initial_states,
        )
        self.rounds.append(round_record)
    
    def record_play(self, player_name: str, played_cards: List[str], remaining_cards: List[str],  next_player: str) -> None:
        """记录玩家的出牌行为"""
        current_round = self.get_current_round()
        if current_round:
            play_action = PlayAction(
                player_name=player_name,
                played_cards=played_cards,
                remaining_cards=remaining_cards,
                next_player=next_player,
            )
            current_round.add_play_action(play_action)
    
    def record_challenge(self, was_challenged: bool, result: bool = None) -> None:
        """记录质疑信息"""
        current_round = self.get_current_round()
        if current_round:
            last_action = current_round.get_last_action()
            if last_action:
                last_action.update_challenge(was_challenged, result)
    
    def record_shooting(self, shooter_name: str, bullet_hit: bool) -> None:
        """记录射击结果"""
        current_round = self.get_current_round()
        if current_round:
            shooting_result = ShootingResult(shooter_name=shooter_name, bullet_hit=bullet_hit)
            current_round.set_shooting_result(shooting_result)
            self.auto_save()  # 射击后自动保存
    
    def finish_game(self, winner_name: str) -> None:
        """记录胜利者并保存最终结果"""
        self.winner = winner_name
        self.auto_save()  # 游戏结束时保存
    
    def get_current_round(self) -> Optional[RoundRecord]:
        """获取当前轮次"""
        return self.rounds[-1] if self.rounds else None
    
   
    def auto_save(self) -> None:
        """自动保存当前游戏记录到文件"""
        file_path = os.path.join(self.save_directory, f"{self.game_id}.json")
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, indent=4, ensure_ascii=False)
        print(f"游戏记录已自动保存至 {file_path}")
