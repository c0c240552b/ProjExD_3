import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


# 演習問題1: スコア表示クラス
class Score:
    """
    スコアに関するクラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.score = 0
        self.color = (0, 0, 255) 
        self.text = self.font.render(f"Score: {self.score}", True, self.color)
        self.rct = self.text.get_rect(topleft=(10, 10))

    def score_up(self, add_score: int):
        """
        スコアを加算する
        """
        self.score += add_score

    def update(self, screen: pg.Surface):
        """
        スコアを更新し、画面に描画する
        """
        self.text = self.font.render(f"Score: {self.score}", True, self.color)
        screen.blit(self.text, self.rct)


# 演習問題3: 爆発エフェクトクラス 
class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, bomb_rct: pg.Rect, life: int = 50):
        """
        爆発エフェクトを初期化する
        引数1 bomb_rct: 爆発が発生する座標 (Rect)
        引数2 life: エフェクトの表示フレーム数
        """
        # 爆発画像がfig/explosion.gifに存在すると仮定し、ない場合は黄色い円で代用
        try:
            # 実際にはexplosion.gifの準備が必要です
            self.img = pg.image.load("fig/explosion.gif") 
            self.img = pg.transform.rotozoom(self.img, 0, 0.5)
        except pg.error:
            self.img = pg.Surface((50, 50))
            pg.draw.circle(self.img, (255, 255, 0), (25, 25), 25)
            self.img.set_colorkey((0, 0, 0))
        
        self.rct = self.img.get_rect(center=bomb_rct.center)
        self.life = life

    def update(self, screen: pg.Surface) -> bool:
        """
        爆発エフェクトの残り時間を減らし、描画する
        戻り値: True ならエフェクト継続、False なら消滅
        """
        self.life -= 1
        if self.life > 0:
            screen.blit(self.img, self.rct)
            return True
        return False


## 練習問題4: ゲームオーバー画面クラス 
class GameOver:
    """
    ゲームオーバー画面に関するクラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 150) # 大きめのフォント
        self.color = (255, 0, 0) # 赤
        self.text = self.font.render("Game Over", True, self.color)
        self.rct = self.text.get_rect(center=(WIDTH/2, HEIGHT/2))
        
    def draw(self, screen: pg.Surface):
        """
        画面中央にゲームオーバーメッセージを描画する
        """
        screen.blit(self.text, self.rct)



class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }
    # ハッピーエフェクト用の画像を追加 (例: fig/4.pngを使用)
    img_happy = pg.transform.rotozoom(pg.image.load("fig/4.png"), 0, 0.9) 

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.is_happy = False
        self.happy_timer = 0
        self.current_move = (+5, 0)

    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)
    
    def set_happy(self, duration: int = 50):
        self.is_happy = True
        self.happy_timer = duration

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
            
        if self.is_happy:
            self.happy_timer -= 1
            if self.happy_timer <= 0:
                self.is_happy = False
            self.img = __class__.img_happy
        elif not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.current_move = tuple(sum_mv)
            self.img = __class__.imgs[self.current_move]
        else:
            self.img = __class__.imgs[self.current_move] 

        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        self.img = pg.image.load(f"fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.centery = bird.rct.centery
        self.rct.left = bird.rct.right
        self.vx, self.vy = +10, 0

    def update(self, screen: pg.Surface) -> bool:
        self.rct.move_ip(self.vx, self.vy)
        if check_bound(self.rct) == (True, True):
            screen.blit(self.img, self.rct)
            return True
        return False


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx = random.choice([-5, -4, -3, 3, 4, 5])
        self.vy = random.choice([-5, -4, -3, 3, 4, 5])

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))

    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    
    beams: list[Beam] = []
    
    score = Score()

    explosions: list[Explosion] = []

    # 練習問題4: ゲームオーバーオブジェクトの生成
    game_over = GameOver() 

    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            
            # 演習問題2: スペースキー押下でBeamクラスのインスタンスを beams リストに追加
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])
        
        # こうかとんと爆弾の衝突判定
        for bomb in bombs:
            if bomb is not None and bird.rct.colliderect(bomb.rct):
                # ゲームオーバー処理
                bird.change_img(8, screen)
                
                # 練習問題4: Game Overメッセージの描画
                game_over.draw(screen) 
                
                score.update(screen) 
                pg.display.update()
                time.sleep(1) #1秒間停止して終了
                return

        # ビームと爆弾の衝突判定　
        for bomb_idx in range(len(bombs) -1, -1, -1):
            bomb = bombs[bomb_idx]
            if bomb is None:
                continue

            for beam_idx in range(len(beams) - 1, -1, -1):
                beam = beams[beam_idx]

                if beam.rct.colliderect(bomb.rct):
                    # 演習問題3: 爆発エフェクトの追加
                    explosions.append(Explosion(bomb.rct)) 
                    
                    # 演習問題1: スコア加算
                    score.score_up(100) 

                    # 爆弾とビームをリストから削除
                    del bombs[bomb_idx]
                    del beams[beam_idx]
                    
                    bird.set_happy()
                    
                    break 

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        beams = [beam for beam in beams if beam.update(screen)]
                
        for bomb in bombs:
            bomb.update(screen)
            
        explosions = [exp for exp in explosions if exp.update(screen)]

        score.update(screen)
            
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()