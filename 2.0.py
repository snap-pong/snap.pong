"""
Professional Ping Pong Game Implementation
A two-player Ping Pong game with adjustable AI difficulty, power-ups, and enhanced features.
"""

import pygame
import sys
import random
from enum import Enum
from typing import Tuple, Optional, List


# Configuration Constants
class GameConfig:
    """Game configuration and constants."""
    WINDOW_WIDTH: int = 800
    WINDOW_HEIGHT: int = 500
    TITLE: str = "snap pong "
    FPS: int = 60
    WIN_SCORE: int = 5
    
    # Colors
    WHITE: Tuple[int, int, int] = (255, 255, 255)
    RED: Tuple[int, int, int] = (180, 0, 0)
    DARK_RED: Tuple[int, int, int] = (120, 0, 0)
    YELLOW: Tuple[int, int, int] = (255, 255, 0)
    GOLD: Tuple[int, int, int] = (255, 215, 0)
    GREEN: Tuple[int, int, int] = (0, 255, 0)
    BLUE: Tuple[int, int, int] = (0, 100, 255)
    CYAN: Tuple[int, int, int] = (0, 255, 255)
    GRAY: Tuple[int, int, int] = (100, 100, 100)
    LIGHT_GRAY: Tuple[int, int, int] = (150, 150, 150)
    ORANGE: Tuple[int, int, int] = (255, 165, 0)
    PURPLE: Tuple[int, int, int] = (138, 43, 226)
    DARK_PURPLE: Tuple[int, int, int] = (75, 0, 130)
    ROYAL_BLUE: Tuple[int, int, int] = (65, 105, 225)
    DEEP_PURPLE: Tuple[int, int, int] = (48, 25, 52)
    
    # Paddle Configuration
    PADDLE_WIDTH: int = 10
    PADDLE_HEIGHT: int = 80
    PADDLE_SPEED: int = 10
    LEFT_PADDLE_X: int = 30
    RIGHT_PADDLE_X: int = WINDOW_WIDTH - 40
    
    # Ball Configuration
    BALL_SIZE: int = 15
    BALL_INITIAL_SPEED: int = 8
    MAX_BALL_SPEED: int = 15
    
    # AI Difficulty Levels
    AI_DIFFICULTY = {
        1: 3,   # Easy
        2: 4,   # Medium
        3: 6    # Hard
    }
    
    # Power-up Configuration
    POWERUP_SPAWN_CHANCE: float = 0.02
    POWERUP_SIZE: int = 15
    POWERUP_DURATION: int = 180  # frames
    POWERUP_SPEED: int = 2


class PowerUpType(Enum):
    """Power-up types available in the game."""
    SPEED_BOOST = "speed"
    SLOW_AI = "slow_ai"
    BIG_PADDLE = "big_paddle"
    FAST_BALL = "fast_ball"


class GameState(Enum):
    """Enumeration of game states."""
    START_SCREEN = "start"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class PowerUp:
    """Represents a power-up in the game."""
    
    def __init__(self, x: float, y: float, powerup_type: PowerUpType) -> None:
        """Initialize a power-up."""
        self.x = x
        self.y = y
        self.type = powerup_type
        self.rect = pygame.Rect(x, y, GameConfig.POWERUP_SIZE, GameConfig.POWERUP_SIZE)
        self.collected = False
    
    def update(self) -> None:
        """Update power-up position."""
        self.y += GameConfig.POWERUP_SPEED
        self.rect.y = self.y
        
        # Remove if out of bounds
        if self.y > GameConfig.WINDOW_HEIGHT:
            self.collected = True
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get the color based on power-up type."""
        colors = {
            PowerUpType.SPEED_BOOST: GameConfig.GREEN,
            PowerUpType.SLOW_AI: GameConfig.CYAN,
            PowerUpType.BIG_PADDLE: GameConfig.BLUE,
            PowerUpType.FAST_BALL: GameConfig.YELLOW,
        }
        return colors.get(self.type, GameConfig.WHITE)
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the power-up."""
        pygame.draw.ellipse(screen, self.get_color(), self.rect)
        pygame.draw.circle(screen, GameConfig.WHITE, self.rect.center, GameConfig.POWERUP_SIZE // 2, 2)


class PingPongGame:
    """Main Ping Pong game class."""
    
    def __init__(self) -> None:
        """Initialize the Ping Pong game."""
        pygame.init()
        
        self.screen = pygame.display.set_mode(
            (GameConfig.WINDOW_WIDTH, GameConfig.WINDOW_HEIGHT)
        )
        pygame.display.set_caption(GameConfig.TITLE)
        self.clock = pygame.time.Clock()
        
        # Setup fonts
        self.title_font = pygame.font.Font(None, 72)
        self.big_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 32)
        self.score_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 20)
        self.tiny_font = pygame.font.Font(None, 16)
        
        # Animation counter
        self.animation_counter = 0
        
        # Initialize ball speeds
        self.ball_speed_x = 0
        self.ball_speed_y = 0
        
        # Initialize game objects
        self.left_paddle = self._create_left_paddle()
        self.right_paddle = self._create_right_paddle()
        self.ball = self._create_ball()
        
        # Game state
        self.state = GameState.START_SCREEN
        self.left_score = 0
        self.right_score = 0
        self.ai_speed = GameConfig.AI_DIFFICULTY[2]
        self.current_difficulty = 2  # Default to medium
        self.is_two_player = False
        self.win_score = 5  # User-selectable win score
        
        # Power-ups
        self.powerups: List[PowerUp] = []
        self.active_powerups = {}  # {player: {type: frames_remaining}}
        
        # Statistics
        self.rally_count = 0
        self.longest_rally = 0
        self.left_rallies_won = 0
        self.right_rallies_won = 0
    
    @staticmethod
    def _create_left_paddle() -> pygame.Rect:
        """Create the left player paddle."""
        return pygame.Rect(
            GameConfig.LEFT_PADDLE_X,
            GameConfig.WINDOW_HEIGHT // 2 - GameConfig.PADDLE_HEIGHT // 2,
            GameConfig.PADDLE_WIDTH,
            GameConfig.PADDLE_HEIGHT
        )
    
    @staticmethod
    def _create_right_paddle() -> pygame.Rect:
        """Create the right AI paddle."""
        return pygame.Rect(
            GameConfig.RIGHT_PADDLE_X,
            GameConfig.WINDOW_HEIGHT // 2 - GameConfig.PADDLE_HEIGHT // 2,
            GameConfig.PADDLE_WIDTH,
            GameConfig.PADDLE_HEIGHT
        )
    
    def _create_ball(self) -> pygame.Rect:
        """Create and initialize the ball."""
        ball = pygame.Rect(
            GameConfig.WINDOW_WIDTH // 2,
            GameConfig.WINDOW_HEIGHT // 2,
            GameConfig.BALL_SIZE,
            GameConfig.BALL_SIZE
        )
        self.ball_speed_x = random.choice([-GameConfig.BALL_INITIAL_SPEED, GameConfig.BALL_INITIAL_SPEED])
        self.ball_speed_y = random.choice([-GameConfig.BALL_INITIAL_SPEED, GameConfig.BALL_INITIAL_SPEED])
        return ball
    
    def reset_ball(self) -> None:
        """Reset the ball to the center with random direction."""
        self.ball.center = (
            GameConfig.WINDOW_WIDTH // 2,
            GameConfig.WINDOW_HEIGHT // 2
        )
        self.ball_speed_x = random.choice([-GameConfig.BALL_INITIAL_SPEED, GameConfig.BALL_INITIAL_SPEED])
        self.ball_speed_y = random.choice([-GameConfig.BALL_INITIAL_SPEED, GameConfig.BALL_INITIAL_SPEED])
    
    def reset_game(self) -> None:
        """Reset game state for a new match."""
        self.left_score = 0
        self.right_score = 0
        self.rally_count = 0
        self.longest_rally = 0
        self.left_rallies_won = 0
        self.right_rallies_won = 0
        self.powerups.clear()
        self.active_powerups.clear()
        self.reset_ball()
        self.state = GameState.PLAYING
    
    def handle_events(self) -> bool:
        """
        Handle input events.
        
        Returns:
            bool: False if the game should quit, True otherwise.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
                # Handle space key (start/pause)
                if event.key == pygame.K_SPACE:
                    if self.state == GameState.START_SCREEN or self.state == GameState.GAME_OVER:
                        self.reset_game()
                    elif self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                
                # Game mode and difficulty selection (only on start screen)
                if self.state == GameState.START_SCREEN:
                    # Game mode selection: M key
                    if event.key == pygame.K_m:
                        if not self.is_two_player:
                            self.is_two_player = True
                            print("Mode: 2 Players")
                        else:
                            self.is_two_player = False
                            print("Mode: 1 Player (vs AI)")
                    
                    # AI Difficulty selection (only applies to 1-player mode)
                    elif event.key == pygame.K_1:
                        self.current_difficulty = 1
                        self.ai_speed = GameConfig.AI_DIFFICULTY[1]
                        print("Difficulty: EASY")
                    elif event.key == pygame.K_2:
                        self.current_difficulty = 2
                        self.ai_speed = GameConfig.AI_DIFFICULTY[2]
                        print("Difficulty: MEDIUM")
                    elif event.key == pygame.K_3:
                        self.current_difficulty = 3
                        self.ai_speed = GameConfig.AI_DIFFICULTY[3]
                        print("Difficulty: HARD")
                    
                    # Win score selection: + and - keys
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.win_score = min(self.win_score + 1, 20)
                        print(f"Win Score: {self.win_score}")
                    elif event.key == pygame.K_MINUS:
                        self.win_score = max(self.win_score - 1, 1)
                        print(f"Win Score: {self.win_score}")
        
        return True
    
    def move_player(self) -> None:
        """Move the left player paddle based on input."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] and self.left_paddle.top > 0:
            self.left_paddle.y -= GameConfig.PADDLE_SPEED
        if keys[pygame.K_s] and self.left_paddle.bottom < GameConfig.WINDOW_HEIGHT:
            self.left_paddle.y += GameConfig.PADDLE_SPEED
    
    def move_right_player(self) -> None:
        """Move the right player paddle (for two-player mode)."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and self.right_paddle.top > 0:
            self.right_paddle.y -= GameConfig.PADDLE_SPEED
        if keys[pygame.K_DOWN] and self.right_paddle.bottom < GameConfig.WINDOW_HEIGHT:
            self.right_paddle.y += GameConfig.PADDLE_SPEED
    
    def move_ai(self) -> None:
        """Move the right AI paddle to follow the ball."""
        paddle_center = self.right_paddle.y + self.right_paddle.height // 2
        ball_center = self.ball.y + self.ball.height // 2
        
        # Apply slow AI power-up if active
        current_speed = self.ai_speed
        if "right" in self.active_powerups and PowerUpType.SLOW_AI in self.active_powerups["right"]:
            current_speed = max(1, current_speed // 2)
        
        if paddle_center < ball_center and self.right_paddle.bottom < GameConfig.WINDOW_HEIGHT:
            self.right_paddle.y += current_speed
        elif paddle_center > ball_center and self.right_paddle.top > 0:
            self.right_paddle.y -= current_speed
    
    def spawn_powerup(self) -> None:
        """Randomly spawn a power-up near the ball."""
        if random.random() < GameConfig.POWERUP_SPAWN_CHANCE:
            powerup_type = random.choice(list(PowerUpType))
            self.powerups.append(
                PowerUp(self.ball.x, self.ball.y, powerup_type)
            )
    
    def activate_powerup(self, player: str, powerup: PowerUp) -> None:
        """Activate a power-up for a player."""
        if player not in self.active_powerups:
            self.active_powerups[player] = {}
        
        if powerup.type == PowerUpType.SPEED_BOOST:
            if player == "left":
                self.left_paddle.height = min(GameConfig.PADDLE_HEIGHT + 30, int(GameConfig.PADDLE_HEIGHT * 1.5))
            else:
                self.right_paddle.height = min(GameConfig.PADDLE_HEIGHT + 30, int(GameConfig.PADDLE_HEIGHT * 1.5))
        
        elif powerup.type == PowerUpType.BIG_PADDLE:
            if player == "left":
                self.left_paddle.height = int(GameConfig.PADDLE_HEIGHT * 1.3)
            else:
                self.right_paddle.height = int(GameConfig.PADDLE_HEIGHT * 1.3)
        
        elif powerup.type == PowerUpType.SLOW_AI and player == "left":
            pass  # Slows the AI
        
        elif powerup.type == PowerUpType.FAST_BALL:
            self.ball_speed_x = int(self.ball_speed_x * 1.3)
            self.ball_speed_y = int(self.ball_speed_y * 1.3)
        
        self.active_powerups[player][powerup.type] = GameConfig.POWERUP_DURATION
    
    def update_powerups(self) -> None:
        """Update active power-ups and remove expired ones."""
        for player in self.active_powerups:
            expired = []
            for powerup_type, frames in self.active_powerups[player].items():
                self.active_powerups[player][powerup_type] -= 1
                if self.active_powerups[player][powerup_type] <= 0:
                    expired.append(powerup_type)
            
            for powerup_type in expired:
                del self.active_powerups[player][powerup_type]
                
                # Revert paddle size
                if powerup_type in [PowerUpType.SPEED_BOOST, PowerUpType.BIG_PADDLE]:
                    if player == "left":
                        self.left_paddle.height = GameConfig.PADDLE_HEIGHT
                    else:
                        self.right_paddle.height = GameConfig.PADDLE_HEIGHT
        
        # Update power-up positions
        for powerup in self.powerups[:]:
            powerup.update()
            if powerup.collected:
                self.powerups.remove(powerup)
    
    def update_ball(self) -> None:
        """Update ball position and handle collisions."""
        self.ball.x += self.ball_speed_x
        self.ball.y += self.ball_speed_y
        
        # Clamp ball speed to maximum for stability
        speed_magnitude = (self.ball_speed_x ** 2 + self.ball_speed_y ** 2) ** 0.5
        if speed_magnitude > GameConfig.MAX_BALL_SPEED:
            scale = GameConfig.MAX_BALL_SPEED / speed_magnitude
            self.ball_speed_x *= scale
            self.ball_speed_y *= scale
        
        # Boundary collision (top/bottom) with proper clamping
        if self.ball.top <= 0:
            self.ball.top = 0
            self.ball_speed_y = abs(self.ball_speed_y)  # Ensure moving downward
        elif self.ball.bottom >= GameConfig.WINDOW_HEIGHT:
            self.ball.bottom = GameConfig.WINDOW_HEIGHT
            self.ball_speed_y = -abs(self.ball_speed_y)  # Ensure moving upward
        
        # Paddle collisions with improved detection
        left_collision = self.ball.colliderect(self.left_paddle) and self.ball_speed_x < 0
        if left_collision:
            # Ensure ball is pushed out of paddle
            self.ball.left = self.left_paddle.right
            self.ball_speed_x = abs(self.ball_speed_x)  # Ensure moving right
            # Add spin based on where ball hit paddle
            hit_pos = (self.ball.y - self.left_paddle.y) / self.left_paddle.height
            self.ball_speed_y += (hit_pos - 0.5) * 2
            self.rally_count += 1
        
        right_collision = self.ball.colliderect(self.right_paddle) and self.ball_speed_x > 0
        if right_collision:
            # Ensure ball is pushed out of paddle
            self.ball.right = self.right_paddle.left
            self.ball_speed_x = -abs(self.ball_speed_x)  # Ensure moving left
            # Add spin based on where ball hit paddle
            hit_pos = (self.ball.y - self.right_paddle.y) / self.right_paddle.height
            self.ball_speed_y += (hit_pos - 0.5) * 2
            self.rally_count += 1
        
        # Power-up collision detection
        for powerup in self.powerups:
            if self.ball.colliderect(powerup.rect):
                player = "left" if self.ball_speed_x < 0 else "right"
                self.activate_powerup(player, powerup)
                powerup.collected = True
        
        # Score updates
        if self.ball.left <= 0:
            self.right_score += 1
            self.longest_rally = max(self.longest_rally, self.rally_count)
            self.right_rallies_won += 1
            self.rally_count = 0
            self.reset_ball()
        
        if self.ball.right >= GameConfig.WINDOW_WIDTH:
            self.left_score += 1
            self.longest_rally = max(self.longest_rally, self.rally_count)
            self.left_rallies_won += 1
            self.rally_count = 0
            self.reset_ball()
        
        # Check win condition (use user-selected win score)
        if self.left_score == self.win_score or self.right_score == self.win_score:
            self.state = GameState.GAME_OVER
    
    def draw_start_screen(self) -> None:
        """Draw the start screen."""
        # Draw royal background
        self._draw_royal_background()
        
        # Draw semi-transparent panels for better text readability
        # Top title panel
        title_panel = pygame.Surface((GameConfig.WINDOW_WIDTH - 40, 80))
        title_panel.set_alpha(30)
        title_panel.fill(GameConfig.GOLD)
        self.screen.blit(title_panel, (20, 10))
        
        # Middle content panel
        content_panel = pygame.Surface((GameConfig.WINDOW_WIDTH - 80, 280))
        content_panel.set_alpha(20)
        content_panel.fill(GameConfig.GOLD)
        self.screen.blit(content_panel, (40, 105))
        
        # Title with glow effect
        title = self.title_font.render(GameConfig.TITLE.strip(), True, GameConfig.GOLD)
        
        # Draw multiple text layers for glow effect
        for offset in [3, 2, 1]:
            glow_text = self.title_font.render(GameConfig.TITLE.strip(), True, 
                                               (int(GameConfig.DARK_PURPLE[0] * 0.5), 
                                                int(GameConfig.DARK_PURPLE[1] * 0.5), 
                                                int(GameConfig.DARK_PURPLE[2] * 0.8)))
            self.screen.blit(glow_text, (GameConfig.WINDOW_WIDTH // 2 - title.get_width() // 2 + offset, 22))
        
        self.screen.blit(title, (GameConfig.WINDOW_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Current selections
        mode_text = "🎮 1 Player vs AI" if not self.is_two_player else "👥 2 Players"
        difficulty_names = {1: "⚡ EASY", 2: "⚡⚡ MEDIUM", 3: "⚡⚡⚡ HARD"}
        difficulty_text = difficulty_names.get(self.current_difficulty, "⚡⚡ MEDIUM")
        
        # Draw selection info
        selections = [
            (f"Mode: {mode_text}", GameConfig.CYAN, self.text_font, 120),
            (f"(Press M to toggle)", GameConfig.LIGHT_GRAY, self.small_font, 155),
            (f"Difficulty: {difficulty_text}", GameConfig.CYAN, self.text_font, 195),
            (f"(Press 1, 2, or 3)", GameConfig.LIGHT_GRAY, self.small_font, 230),
            (f"Win Score: {self.win_score} points", GameConfig.CYAN, self.text_font, 270),
            (f"(Press + or - to adjust)", GameConfig.LIGHT_GRAY, self.small_font, 305),
        ]
        
        for text, color, font, y in selections:
            txt = font.render(text, True, color)
            self.screen.blit(txt, (GameConfig.WINDOW_WIDTH // 2 - txt.get_width() // 2, y))
        
        # How to play section
        instructions = [
            ("⌨️ LEFT: W/S  •  RIGHT: ↑/↓", GameConfig.WHITE, self.small_font, 355),
            ("⭐ Power-ups appear during play ⭐", GameConfig.GOLD, self.small_font, 380),
            ("🏆 First to reach the goal wins!", GameConfig.WHITE, self.small_font, 405),
        ]
        
        for text, color, font, y in instructions:
            txt = font.render(text, True, color)
            self.screen.blit(txt, (GameConfig.WINDOW_WIDTH // 2 - txt.get_width() // 2, y))
        
        # Start button with animation
        button_width = 280
        button_height = 45
        button_x = GameConfig.WINDOW_WIDTH // 2 - button_width // 2
        button_y = 440
        
        # Pulsing button effect
        pulse = abs(((self.animation_counter) % 60) - 30) / 30.0
        button_brightness = int(200 + pulse * 55)
        
        # Draw button background with rounded appearance
        pygame.draw.rect(self.screen, (button_brightness, int(button_brightness * 0.8), 0), 
                        (button_x, button_y, button_width, button_height), border_radius=8)
        pygame.draw.rect(self.screen, GameConfig.GOLD, 
                        (button_x, button_y, button_width, button_height), 2, border_radius=8)
        
        start_txt = self.text_font.render("▶ PRESS SPACE TO START ◀", True, GameConfig.DEEP_PURPLE)
        self.screen.blit(start_txt, (GameConfig.WINDOW_WIDTH // 2 - start_txt.get_width() // 2, 448))
    
    def draw_game_over(self) -> None:
        """Draw the game over screen."""
        # Draw royal background
        self._draw_royal_background()
        
        # Draw semi-transparent panel
        panel = pygame.Surface((GameConfig.WINDOW_WIDTH, GameConfig.WINDOW_HEIGHT))
        panel.set_alpha(40)
        panel.fill(GameConfig.DEEP_PURPLE)
        self.screen.blit(panel, (0, 0))
        
        winner = "Player 1" if self.left_score > self.right_score else ("AI" if not self.is_two_player else "Player 2")
        
        # Winner announcement with glow effect
        for offset in [4, 2]:
            winner_glow = self.big_font.render(f"👑 {winner.upper()} WINS! 👑", True, 
                                              (int(GameConfig.DARK_PURPLE[0] * 0.7), 
                                               int(GameConfig.DARK_PURPLE[1] * 0.7), 
                                               int(GameConfig.DARK_PURPLE[2] * 0.9)))
            self.screen.blit(winner_glow, (GameConfig.WINDOW_WIDTH // 2 - 150 + offset, 60 + offset))
        
        winner_text = self.big_font.render(f"👑 {winner.upper()} WINS! 👑", True, GameConfig.GOLD)
        self.screen.blit(winner_text, (GameConfig.WINDOW_WIDTH // 2 - 150, 60))
        
        # Statistics panel with semi-transparency
        stats_panel = pygame.Surface((GameConfig.WINDOW_WIDTH - 100, 180))
        stats_panel.set_alpha(25)
        stats_panel.fill(GameConfig.GOLD)
        self.screen.blit(stats_panel, (50, 160))
        
        stats = [
            f"Final Score: {self.left_score} - {self.right_score}",
            f"Longest Rally: {self.longest_rally} hits",
            f"Player 1 Rallies: {self.left_rallies_won}  |  Player 2 Rallies: {self.right_rallies_won}",
        ]
        
        y = 180
        for stat in stats:
            txt = self.text_font.render(stat, True, GameConfig.WHITE)
            self.screen.blit(txt, (GameConfig.WINDOW_WIDTH // 2 - txt.get_width() // 2, y))
            y += 45
        
        # Restart button with animation
        button_width = 300
        button_height = 50
        button_x = GameConfig.WINDOW_WIDTH // 2 - button_width // 2
        button_y = 410
        
        # Pulsing button effect
        pulse = abs(((self.animation_counter) % 60) - 30) / 30.0
        button_brightness = int(200 + pulse * 55)
        
        pygame.draw.rect(self.screen, (button_brightness, int(button_brightness * 0.8), 0), 
                        (button_x, button_y, button_width, button_height), border_radius=10)
        pygame.draw.rect(self.screen, GameConfig.GOLD, 
                        (button_x, button_y, button_width, button_height), 2, border_radius=10)
        
        restart_txt = self.text_font.render("PRESS SPACE TO RESTART", True, GameConfig.DEEP_PURPLE)
        self.screen.blit(restart_txt, (GameConfig.WINDOW_WIDTH // 2 - restart_txt.get_width() // 2, 422))
    
    def draw_game(self) -> None:
        """Draw the active game state."""
        # Draw royal game background
        self._draw_royal_game_background()
        
        # Draw paddles with glow effect if powered up
        self._draw_paddle(self.left_paddle, "left")
        self._draw_paddle(self.right_paddle, "right")
        
        # Draw ball with glow
        pygame.draw.ellipse(self.screen, GameConfig.WHITE, self.ball)
        pygame.draw.circle(self.screen, GameConfig.GOLD, self.ball.center, GameConfig.BALL_SIZE // 2 + 2, 2)
        
        # Draw center line (dashed effect) in gold
        dash_height = 10
        gap_height = 5
        y = 0
        while y < GameConfig.WINDOW_HEIGHT:
            pygame.draw.line(
                self.screen,
                GameConfig.GOLD,
                (GameConfig.WINDOW_WIDTH // 2, y),
                (GameConfig.WINDOW_WIDTH // 2, y + dash_height),
                2
            )
            y += dash_height + gap_height
        
        # Draw top info bar with gradient panel
        info_panel = pygame.Surface((GameConfig.WINDOW_WIDTH, 55))
        info_panel.set_alpha(180)
        info_panel.fill(GameConfig.DARK_PURPLE)
        self.screen.blit(info_panel, (0, 0))
        
        # Draw scores
        left_score_text = self.score_font.render(str(self.left_score), True, GameConfig.GOLD)
        right_score_text = self.score_font.render(str(self.right_score), True, GameConfig.GOLD)
        
        self.screen.blit(left_score_text, (30, 5))
        self.screen.blit(right_score_text, (GameConfig.WINDOW_WIDTH - 60, 5))
        
        # Draw rally count in center with icon
        rally_text = self.text_font.render(f"🔥 Rally: {self.rally_count}", True, GameConfig.GOLD)
        self.screen.blit(rally_text, (GameConfig.WINDOW_WIDTH // 2 - rally_text.get_width() // 2, 10))
        
        # Draw power-ups
        for powerup in self.powerups:
            powerup.draw(self.screen)
        
        # Draw pause indicator with semi-transparent background
        if self.state == GameState.PAUSED:
            # Semi-transparent overlay
            overlay = pygame.Surface((GameConfig.WINDOW_WIDTH, GameConfig.WINDOW_HEIGHT))
            overlay.set_alpha(120)
            overlay.fill(GameConfig.DEEP_PURPLE)
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.title_font.render("⏸ PAUSED ⏸", True, GameConfig.GOLD)
            resume_text = self.text_font.render("Press SPACE to Resume", True, GameConfig.WHITE)
            
            self.screen.blit(pause_text, (GameConfig.WINDOW_WIDTH // 2 - pause_text.get_width() // 2, 180))
            self.screen.blit(resume_text, (GameConfig.WINDOW_WIDTH // 2 - resume_text.get_width() // 2, 280))
    
    def _draw_royal_background(self) -> None:
        """Draw an attractive royal gradient background."""
        for y in range(GameConfig.WINDOW_HEIGHT):
            # Create a royal purple to deep blue gradient
            ratio = y / GameConfig.WINDOW_HEIGHT
            r = int(75 + (65 - 75) * ratio)  # Deep purple to royal blue
            g = int(0 + (105 - 0) * ratio)
            b = int(130 + (225 - 130) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (GameConfig.WINDOW_WIDTH, y))
        
        # Add subtle animated stars/particles
        star_positions = [
            (50, 30), (150, 80), (300, 40), (500, 70), (700, 50),
            (100, 450), (350, 420), (600, 460), (750, 440),
            (200, 150), (650, 250), (400, 350),
        ]
        
        for idx, (x, y) in enumerate(star_positions):
            # Pulsing star effect
            pulse = abs(((self.animation_counter + idx * 5) % 60) - 30) / 30.0
            alpha_size = int(2 + pulse * 2)
            pygame.draw.circle(self.screen, GameConfig.GOLD, (x, y), alpha_size)
    
    def _draw_royal_game_background(self) -> None:
        """Draw royal background for gameplay."""
        for y in range(GameConfig.WINDOW_HEIGHT):
            ratio = y / GameConfig.WINDOW_HEIGHT
            r = int(75 + (30 - 75) * ratio)
            g = int(0 + (50 - 0) * ratio)
            b = int(130 + (150 - 130) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (GameConfig.WINDOW_WIDTH, y))
    
    def _draw_paddle(self, paddle: pygame.Rect, player: str) -> None:
        """Draw a paddle with optional glow effect."""
        # Main paddle
        pygame.draw.rect(self.screen, GameConfig.WHITE, paddle)
        pygame.draw.rect(self.screen, GameConfig.CYAN, paddle, 2)
        
        # Draw glow if powered up
        if player in self.active_powerups:
            if PowerUpType.SLOW_AI in self.active_powerups[player]:
                glow_color = GameConfig.CYAN
            else:
                glow_color = GameConfig.GREEN
            
            # Multiple layers for glow effect
            pygame.draw.rect(self.screen, glow_color, paddle, 4)
            pygame.draw.rect(self.screen, glow_color, (paddle.x - 2, paddle.y - 2, paddle.width + 4, paddle.height + 4), 1)
    
    def update_display(self) -> None:
        """Update the game display."""
        if self.state == GameState.START_SCREEN:
            self.draw_start_screen()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        else:
            self.draw_game()
        
        pygame.display.update()
    
    def run(self) -> None:
        """Main game loop."""
        running = True
        
        while running:
            running = self.handle_events()
            
            if self.state == GameState.PLAYING:
                self.move_player()
                if self.is_two_player:
                    self.move_right_player()
                else:
                    self.move_ai()
                self.update_ball()
                self.spawn_powerup()
                self.update_powerups()
            
            self.animation_counter += 1
            self.update_display()
            self.clock.tick(GameConfig.FPS)
        
        pygame.quit()
        sys.exit()


def main() -> None:
    """Entry point for the application."""
    game = PingPongGame()
    game.run()


if __name__ == "__main__":
    main()
