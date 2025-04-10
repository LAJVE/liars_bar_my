import random
from typing import List, Optional, Dict
import os
from game_record import GameRecord, PlayerInitialState


class Player:
    def __init__(self, name: str):
        """初始化玩家 
        Args:
            name: 玩家名称
        """
        self.name = name
        self.hand = []
        self.alive = True
        self.bullet_position = random.randint(0, 5)
        self.current_bullet_position = 0

    def process_penalty(self) -> bool:
        """处理惩罚"""
        print(f"玩家 {self.name} 执行射击惩罚：")
        if self.bullet_position == self.current_bullet_position:
            print(f"{self.name} 中枪死亡！")
            self.alive = False
        else:
            print(f"{self.name} 幸免于难！")
        self.current_bullet_position = (self.current_bullet_position + 1) % 6
        return self.alive
    
class Game:
    def __init__(self, players: List[str]) -> None:
        """初始化游戏
        
        Args:
            player_configs: 包含玩家配置的列表，每个配置是一个字典，包含 name 和 model 字段
        """
        # 使用配置创建玩家对象
        self.players = [Player(name) for name in players]        
        self.deck: List[str] = []
        self.target_card: Optional[str] = None
        self.current_player_idx: int = random.randint(0, len(self.players) - 1)
        self.last_shooter_name: Optional[str] = None
        self.game_over: bool = False

        # 游戏规则
        self.rules = '''
        你正在参加一场名为“骗子酒馆”的生死游戏。 
        规则：
        游戏可以由2-4名玩家参加，游戏使用20张扑克牌，包括6张Q、6张K、6张A和2张Joker（Joker可以等同为任何牌使用，即万能牌）。
        游戏按轮次进行，每轮每人发5张牌，并从Q、K、A中随机选择一张作为“目标牌”。
        玩家按顺序轮流出牌，每个玩家每次可出1-3张牌，宣称它们是“目标牌”(可以出假牌欺骗)，下家可以选择是否质疑，如果不质疑则下家继续出牌。
        每个玩家各自有一把6个仓位的左轮手枪，游戏开始时一发实弹会随机装填在6个仓位中一个，每开一枪，仓位会移动一格。
        在质疑环节，如果质疑成功（上家出的牌中存在非目标牌），上家输；如果质疑失败（上家出的牌全部都是目标牌），质疑者输。输者需要对自己开一枪。
        一旦有人质疑，本轮游戏结束，还存活的玩家将进入下一轮。新一轮开始时会清空玩家原有手牌，每个玩家重新发5张牌，并选定新的目标牌。
        特殊情况：一轮游戏中，当轮到某个玩家出牌时，其他玩家手牌均已打空，则该玩家剩余手牌视为自动打出并受到系统质疑。
        当仅剩一个玩家存活时游戏结束。'''

        # 创建游戏记录
        self.game_record: GameRecord = GameRecord()
        self.game_record.start_game([p.name for p in self.players])
        self.round_count = 0


    def clear_screen(self):
        """清空当前的屏幕输出, 确保不同玩家的手牌等私人信息只有自己能看到"""
        if os.name == 'nt': # Windows 系统
            os.system('cls')
        else: # Mac 和 Linux 系统
            os.system('clear')

    def print_current_status(self):
        print()
        print("当前对局信息: ")
        print(f"目标牌是 {self.target_card}.")
        for player in self.players:
            if player.alive:
                print(f"{player.name} 仍存活, 当前手牌数量为 {len(player.hand)}, 当前已开枪次数为 {player.current_bullet_position}.")
        print()


    def _create_deck(self) -> List[str]:
        """创建并洗牌牌组"""
        deck = ['Q'] * 6 + ['K'] * 6 + ['A'] * 6 + ['Joker'] * 2
        random.shuffle(deck)
        return deck

    def deal_cards(self) -> None:
        """发牌并清空旧手牌"""
        self.deck = self._create_deck()
        for player in self.players:
            if player.alive:
                player.hand.clear()
        # 每位玩家发 5 张牌
        for _ in range(5):
            for player in self.players:
                if player.alive and self.deck:
                    player.hand.append(self.deck.pop())

    def choose_target_card(self) -> None:
        """随机选择目标牌"""
        self.target_card = random.choice(['Q', 'K', 'A'])
        print(f"目标牌是: {self.target_card}")

    def start_round_record(self) -> None:
        """开始新的回合，并在 `GameRecord` 里记录信息"""
        self.round_count += 1
        starting_player = self.players[self.current_player_idx].name
        player_initial_states = [
            PlayerInitialState(
                player_name=player.name,
                bullet_position=player.bullet_position,
                current_gun_position=player.current_bullet_position,
                initial_hand=player.hand.copy()
            ) 
            for player in self.players if player.alive
        ]

        # 获取当前存活的玩家
        round_players = [player.name for player in self.players if player.alive]

        self.game_record.start_round(
            round_id=self.round_count,
            target_card=self.target_card,
            round_players=round_players,
            starting_player=starting_player,
            player_initial_states=player_initial_states,
        )

    def is_valid_play(self, cards: List[str]) -> bool:
        """
        判断出牌是否符合目标牌规则：
        每张牌必须为目标牌或 Joker
        """
        return all(card == self.target_card or card == 'Joker' for card in cards)

    def find_next_player_with_cards(self, start_idx: int) -> int:
        """返回下一个存活且有手牌的玩家索引"""
        idx = start_idx
        for _ in range(len(self.players)):
            idx = (idx + 1) % len(self.players)
            if self.players[idx].alive and self.players[idx].hand:
                return idx
        return start_idx  # 理论上不会发生

    def perform_penalty(self, player: Player) -> None:
        """
        执行射击惩罚，并根据结果更新游戏状态和记录

        Args:
            player: 需要执行惩罚的玩家
        """        
        # 执行射击并获取存活状态
        still_alive = player.process_penalty()
        self.last_shooter_name = player.name        
        # 检查胜利条件

        # 记录射击结果
        self.game_record.record_shooting(
            shooter_name=player.name,
            bullet_hit=not still_alive  # 如果玩家死亡，说明子弹命中
        )

        if not self.check_victory():
            self.reset_round(record_shooter=True)

    def reset_round(self, record_shooter: bool) -> None:
        """重置当前小局"""
        print("小局游戏重置，开始新的一局！")
        input("请输入任意键重置当前小局.")
        self.clear_screen()

        # 重新发牌
        self.deal_cards()
        self.choose_target_card()

        if record_shooter and self.last_shooter_name:
            shooter_idx = next((i for i, p in enumerate(self.players)
                                if p.name == self.last_shooter_name), None)
            if shooter_idx is not None and self.players[shooter_idx].alive:
                self.current_player_idx = shooter_idx
            else:
                print(f"{self.last_shooter_name} 已死亡，顺延至下一个存活且有手牌的玩家")
                self.current_player_idx = self.find_next_player_with_cards(shooter_idx or 0)
        else:
            self.last_shooter_name = None
            alive_players = [p for p in self.players if p.alive]
            self.current_player_idx = self.players.index(random.choice(alive_players))

        self.start_round_record()
        print(f"从 {self.players[self.current_player_idx].name} 开始新的一轮！")

    def check_victory(self) -> bool:
        """
        检查胜利条件（仅剩一名存活玩家时），并记录胜利者
        
        Returns:
            bool: 游戏是否结束
        """
        alive_players = [p for p in self.players if p.alive]
        if len(alive_players) == 1:
            winner = alive_players[0]
            print(f"\n{winner.name} 获胜！")
            # 记录胜利者并保存游戏记录
            self.game_record.finish_game(winner.name)
            self.game_over = True
            return True
        return False
    
    def check_other_players_no_cards(self, current_player: Player) -> bool:
        """
        检查是否所有其他存活玩家都没有手牌
        """
        others = [p for p in self.players if p != current_player and p.alive]
        return all(not p.hand for p in others)

    def handle_play_cards(self, current_player: Player, next_player: Player) -> List[str]:
        """
        处理玩家出牌环节
        
        Args:
            current_player: 当前玩家
            next_player: 下一个玩家
            
        Returns:
            List[str]: 返回打出的牌组
        """
        check_player = ''
        while check_player != current_player.name:
            check_player = input(f"请 {current_player.name} 输入自己的姓名以确认身份, 请确保其它玩家无法看到屏幕.")

        # 清空屏幕
        self.clear_screen()

        self.print_current_status()

        # 让当前玩家选择出牌
        valid_play = False
        while not valid_play:
            play_result = input(f"{current_player.name} 的当前手牌为 {current_player.hand}, 目标牌是 {self.target_card}. 请输入你的的出牌(Q, K, A, Joker), 各个牌之间用一个空格分开:").split()
            if len(play_result) not in [1,2,3]:
                print("你的出牌数量不正确. 你应该出1-3张手牌.请重新输入你的出牌.")
            else:
                hands = current_player.hand.copy()
                try:
                    for card in play_result:
                        hands.remove(card)
                    current_player.hand = hands
                    valid_play = True
                except:
                    print("你出了当前没有的手牌. 请重新输入你的出牌.")

        input('请输入随机字符以开始下一个环节. 输入之后当前屏幕内容会清空, 之后请将屏幕出示给所有玩家.')
        self.clear_screen()

        # 记录出牌行为
        self.game_record.record_play(
            player_name=current_player.name,
            played_cards=play_result.copy(),
            remaining_cards=current_player.hand.copy(),
            next_player=next_player.name,
        )

        return play_result
    
    def handle_challenge(self, current_player: Player, next_player: Player, played_cards: List[str]) -> Player:
        """
        处理玩家质疑环节
        
        Args:
            current_player: 当前玩家（被质疑者）
            next_player: 下一个玩家（质疑者）
            played_cards: 被质疑者打出的牌
            
        Returns:
            Player: 返回需要执行惩罚的玩家
        """
        check_player = ''
        while check_player != next_player.name:
            check_player = input(f"请 {next_player.name} 输入自己的姓名以确认身份, 请确保其它玩家无法看到屏幕.")
        # 清空屏幕
        self.clear_screen()

        self.print_current_status()

        # 让下一位玩家决定是否质疑
        print(f"{current_player.name} 声称自己出了 {len(played_cards)} 张目标牌 {self.target_card}.")
        print(f"{next_player.name} 的当前手牌为 {next_player.hand}")
        challenge_result = input(f"请 {next_player.name} 选择是否质疑. 输入 y 表示质疑, 输入其它表示不质疑.") == 'y'

        # 如果选择质疑
        if challenge_result:
            # 验证出牌是否合法
            is_valid = self.is_valid_play(played_cards)

            # 记录质疑结果
            self.game_record.record_challenge(
                was_challenged=True,
                result=not is_valid,  # 质疑成功意味着出牌不合法
            )

            # 根据验证结果返回需要受罚的玩家
            return next_player if is_valid else current_player
        else:
            # 记录未质疑的情况
            self.game_record.record_challenge(
                was_challenged=False,
                result=None,
            )            
            return None

    def handle_system_challenge(self, current_player: Player) -> None:
        """
        处理系统自动质疑的情况
        当其他所有存活玩家都没有手牌时，系统自动对当前玩家进行质疑
        
        Args:
            current_player: 当前玩家（最后一个有手牌的玩家）
        """
        print(f"系统自动质疑 {current_player.name} 的手牌！")
        
        # 记录玩家自动出牌
        all_cards = current_player.hand.copy()  # 复制当前手牌以供记录
        current_player.hand.clear()  # 清空手牌

        # 记录出牌行为
        self.game_record.record_play(
            player_name=current_player.name,
            played_cards=all_cards,
            remaining_cards=[],  # 剩余手牌为空列表
            next_player="无",
        )

        # 验证出牌是否合法
        is_valid = self.is_valid_play(all_cards)

        # 记录系统质疑
        self.game_record.record_challenge(
            was_challenged=True,
            result=not is_valid,  # 质疑成功意味着出牌不合法
        )

        if is_valid:
            print(f"系统质疑失败！{current_player.name} 的手牌符合规则。随机选取当前存活玩家开始下一轮。")
            # 记录一个特殊的射击结果（无人射击）
            self.game_record.record_shooting(
                shooter_name="无",
                bullet_hit=False
            )
            self.reset_round(record_shooter=False)
        else:
            print(f"系统质疑成功！{current_player.name} 的手牌违规，将执行射击惩罚。")
            self.perform_penalty(current_player)



    def play_round(self) -> None:
        """执行一轮游戏逻辑"""
        current_player = self.players[self.current_player_idx]

         # 当其他所有存活玩家都没有手牌时，系统自动对当前玩家进行质疑
        if self.check_other_players_no_cards(current_player):
            self.handle_system_challenge(current_player)
            return

        print(f"\n轮到 {current_player.name} 出牌, 目标牌是 {self.target_card}. 目前 {current_player.name}  的手牌数量为 {len(current_player.hand)}. ")

        self.print_current_status()

        # 找到下一位有手牌的玩家
        next_idx = self.find_next_player_with_cards(self.current_player_idx)
        next_player = self.players[next_idx]

        # 处理出牌环节
        played_cards = self.handle_play_cards(current_player, next_player)

        # 处理质疑环节
        if next_player != current_player:
            player_to_penalize = self.handle_challenge(current_player, next_player, played_cards)
            if player_to_penalize:
                self.perform_penalty(player_to_penalize)
                return
            else:
                print(f"{next_player.name} 选择不质疑，游戏继续。")                        
                # 切换至下一玩家
                self.current_player_idx = next_idx

    def start_game(self) -> None:
        """启动游戏主循环"""
        self.deal_cards()
        self.choose_target_card()
        self.start_round_record()
        while not self.game_over:
            self.play_round()

if __name__ == '__main__':
    players = ['log', 'tubus']

    print("游戏开始！玩家如下：")
    for name in players:
        print(f"玩家：{name}")
    print("-" * 50)

    # 创建游戏实例并开始游戏
    game = Game(players)
    game.start_game()
