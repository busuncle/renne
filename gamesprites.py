import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
import simulator
from animation import SpriteAnimator, SpriteEmotionAnimator
from controller import SpriteBrain
import etc.constant as cfg
import etc.setting as sfg



############## some tools for sprites ####################

def enemy_in_one_screen(hero, enemy):
    if abs(enemy.pos[0] - hero.pos[0]) > sfg.GameMap.ONE_SCREEN_DISTANCE_WIDTH or \
        abs(enemy.pos[1] - hero.pos[1]) > sfg.GameMap.ONE_SCREEN_DISTANCE_HEIGHT:
        # the distance between renne and enemy is beyond one screen size, ignore it for saving cpu
        return False
    return True



############## sprite module ###########################

class GameSprite(pygame.sprite.DirtySprite):
    """
    basic sprite class having basic attribute
    """

    def __init__(self, 
            name, 
            hp, # health point
            atk, # physical attack
            dfs, # defense
            pos, # position on the map, not screen
            direction # sprite direction it faces
        ):
        super(GameSprite, self).__init__()
        self.name = name
        self.hp = hp
        self.atk = atk
        self.dfs = dfs
        self.status = cfg.SpriteStatus.HEALTHY
        self.pos = Vector2(pos)
        self.direction = direction

        self.action = cfg.SpriteAction.STAND
        self.key_vec = Vector2() # a normal vector represents the direction

        self.attack_receiver = simulator.AttackReceiver(self)
        

    def is_collide_map_boundry(self):
        max_w, max_h = self.game_map.size
        w, h = self.area.center
        if w <= 0 or h <= 0 or w >= max_w or h >= max_h:
            return True
        return False


    def update(self):
        pass


    def draw_image(self, camera):
        # for drawing to the screen, 
        # y-axis should be a half of pos[1] and considering the distance from pos to image center
        image = self.animation.image
        if image is None:
            return 

        rect = image.get_rect()
        rect.center = (self.pos.x, self.pos.y / 2 - self.setting.D_COORD_TO_FOOT)

        shadow_image = self.animation.shadow_image
        shadow_rect = shadow_image.get_rect()
        shadow_rect.center = (rect.center[0], rect.center[1] + self.setting.D_COORD_TO_SHADOW)

        rect.top -= camera.rect.top
        rect.left -= camera.rect.left

        shadow_rect.top -= camera.rect.top
        shadow_rect.left -= camera.rect.left

        if self.attack_receiver.under_attack:
            # add mix color to the image for simulating a under-attack effect, like a blink body, pretty good
            self.attack_receiver.tick()
            image_mix = image.copy()
            image_mix.fill(pygame.Color("gray"), special_flags=BLEND_ADD)
            image = image_mix

        camera.screen.blit(shadow_image, shadow_rect)
        camera.screen.blit(image, rect)


    def draw(self, camera):
        pass



class Renne(GameSprite):
    def __init__(self, setting, pos, direction):
        super(Renne, self).__init__(setting.NAME, setting.HP, setting.ATK, setting.DFS, pos, direction)

        self.setting = setting
        self.stamina = self.setting.STAMINA
        self.level = 1
        self.exp = 0

        self.animation = SpriteAnimator(self)

        # represent the sprite area, used for deciding frame layer and collide, attack computing or so
        self.area = pygame.Rect(0, 0, self.setting.RADIUS * 2, self.setting.RADIUS * 2)
        self.area.center = self.pos('xy')


    def activate(self, allsprites, enemies, static_objects, game_map):
        self.allsprites = allsprites
        self.enemies = enemies
        self.static_objects = static_objects
        self.game_map = game_map
        self.attacker = simulator.AngleAttacker(self, angle=self.setting.ATTACK_ANGLE, 
            cal_frames=self.setting.ATTACK_CAL_FRAMES)


    def draw(self, camera):
        self.draw_image(camera)


    def move(self, speed, passed_seconds):
        # try x and y direction move, go back to the old position when collided with something unwalkable
        self.key_vec.normalize()
        for coord in ("x", "y"):
            key_vec_coord = getattr(self.key_vec, coord)
            if key_vec_coord != 0:
                old_coord = getattr(self.pos, coord)
                setattr(self.pos, coord, old_coord + key_vec_coord * speed * passed_seconds)
                self.area.center = self.pos("xy")
                if self.is_collide() or self.is_collide_map_boundry():
                    setattr(self.pos, coord, old_coord)
                    self.area.center = self.pos("xy")


    def is_collide(self):
        for v in self.static_objects:
            if v.is_block and self.area.colliderect(v.area):
                return True

        return False


    def stand(self, passed_seconds):
        # stamina recover when standing
        if self.hp > 0:
            self.stamina = min(self.setting.STAMINA, 
                self.stamina + self.setting.STAMINA_RECOVERY_RATE * passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.STAND, passed_seconds)


    def walk(self, passed_seconds):
        self.move(self.setting.WALK_SPEED, passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.WALK, passed_seconds)


    def run(self, passed_seconds):
        # cost some stamina when running
        self.stamina = max(0, self.stamina - self.setting.STAMINA_COST_RATE * passed_seconds)
        self.move(self.setting.RUN_SPEED, passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.RUN, passed_seconds)


    def attack(self, passed_seconds):
        is_finish = self.animation.run_sequence_frame(cfg.HeroAction.ATTACK, passed_seconds)
        if is_finish:
            self.attacker.finish_attack()
            self.action = cfg.HeroAction.STAND
        else:
            for em in self.enemies:
                self.attacker.do_attack(em, self.animation.get_current_frame_add(cfg.HeroAction.ATTACK))


    def win(self, passed_seconds):
        # painted egg!
        is_finish = self.animation._run_renne_win_frame(passed_seconds)
        if is_finish:
            self.action = cfg.HeroAction.STAND
        

    def event_handle(self, pressed_keys, external_event=None):
        if external_event is not None:
            if external_event == cfg.GameStatus.INIT:
                self.action = cfg.HeroAction.STAND
                return
            elif external_event == cfg.GameStatus.HERO_LOSE:
                if self.action != cfg.HeroAction.ATTACK:
                    self.action = cfg.HeroAction.STAND
                return 

        if self.action == cfg.HeroAction.ATTACK:
            # attacking, return directly
            return

        if self.action == cfg.HeroAction.WIN:
            # painted egg, return directly
            return

        # calculate direction
        self.key_vec.x = self.key_vec.y = 0.0
        if pressed_keys[sfg.UserKey.LEFT]:
            self.key_vec.x -= 1.0
        if pressed_keys[sfg.UserKey.RIGHT]:
            self.key_vec.x += 1.0
        if pressed_keys[sfg.UserKey.UP]:
            self.key_vec.y -= 1.0
        if pressed_keys[sfg.UserKey.DOWN]:
            self.key_vec.y += 1.0
        self.direction = cfg.Direction.VEC_TO_DIRECT.get(self.key_vec.as_tuple(), self.direction)

        if pressed_keys[sfg.UserKey.ATTACK]:
            self.action = cfg.HeroAction.ATTACK

        elif self.key_vec:
            if pressed_keys[sfg.UserKey.RUN] and self.stamina > 0:
                # press run and stamina enough
                self.action = cfg.HeroAction.RUN
            else:
                self.action = cfg.HeroAction.WALK

        elif pressed_keys[sfg.UserKey.WIN]:
            # egg, show win animation
            self.action = cfg.HeroAction.WIN

        else:
            self.action = cfg.HeroAction.STAND


    def update(self, passed_seconds):
        if self.action == cfg.HeroAction.ATTACK:
            self.attack(passed_seconds)

        elif self.action == cfg.HeroAction.RUN:
            self.run(passed_seconds)

        elif self.action == cfg.HeroAction.WALK:
            self.walk(passed_seconds)

        elif self.action == cfg.HeroAction.WIN:
            self.win(passed_seconds)

        elif self.action == cfg.HeroAction.STAND:
            self.stand(passed_seconds)



class Enemy(GameSprite):
    def __init__(self, setting, pos, direction):
        super(Enemy, self).__init__(setting.NAME, setting.HP, setting.ATK, setting.DFS, pos, direction)
        self.setting = setting
        self.emotion = cfg.SpriteEmotion.NORMAL
        self.emotion_animation = SpriteEmotionAnimator(self)

        self.animation = SpriteAnimator(self)

        self.area = pygame.Rect(0, 0, self.setting.RADIUS * 2, self.setting.RADIUS * 2)
        self.area.center = self.pos('xy')


    def activate(self, ai, allsprites, hero, static_objects, game_map):
        # activate the enemy by passing all the nessary external information and ai to it
        self.game_map = game_map
        self.allsprites = allsprites
        self.hero = hero
        self.static_objects = static_objects
        self.attacker = simulator.AngleAttacker(self, angle=self.setting.ATTACK_ANGLE, 
            cal_frames=self.setting.ATTACK_CAL_FRAMES)
        self.view_sensor = simulator.ViewSensor(self, angle=self.setting.VIEW_ANGLE)
        self.steerer = simulator.Steerer(self)
        self.brain = SpriteBrain(self, ai)


    def draw_emotion(self, camera):
        rect = self.emotion_animation.image.get_rect()
        rect.center = (self.pos.x, self.pos.y / 2 - self.setting.HEIGHT)
        rect.top -= camera.rect.top
        rect.left -= camera.rect.left
        camera.screen.blit(self.emotion_animation.image, rect)


    def draw(self, camera):
        self.draw_image(camera)

        if self.emotion_animation.image is not None:
            self.draw_emotion(camera)


    def move(self, speed, passed_seconds, to_check_block=False):
        self.key_vec.normalize()
        old_pos = self.pos.copy()
        self.pos += self.key_vec * speed * passed_seconds
        self.area.center = self.pos("xy")
        if self.is_collide_map_boundry() or (to_check_block and self.is_collide_static_objects()):
            self.pos = old_pos
            self.area.center = self.pos("xy")
            self.brain.interrupt = True


    def is_collide_static_objects(self):
        for v in self.static_objects:
            if v.is_block and self.area.colliderect(v.area):
                return True

        return False


    def stand(self, passed_seconds):
        self.animation.run_circle_frame(cfg.EnemyAction.STAND, passed_seconds)


    def walk(self, passed_seconds, to_check_block=False):
        self.move(self.setting.WALK_SPEED, passed_seconds, to_check_block)
        self.animation.run_circle_frame(cfg.EnemyAction.WALK, passed_seconds)


    def attack(self, passed_seconds):
        is_finish = self.animation.run_sequence_frame(cfg.EnemyAction.ATTACK, passed_seconds)
        if is_finish:
            self.attacker.finish_attack()
            self.brain.persistent = False
        else:
            self.attacker.do_attack(self.brain.target, 
                self.animation.get_current_frame_add(cfg.EnemyAction.ATTACK))


    def reset_action(self):
        if not self.brain.persistent:
            self.action = cfg.EnemyAction.STAND


    def set_emotion(self, emotion):
        self.emotion_animation.reset_frame(self.emotion)
        self.emotion = emotion


    def event_handle(self, pressed_keys=None, external_event=None):
        # perception and belief control level

        if external_event is not None:
            if external_event == cfg.GameStatus.INIT:
                self.action = cfg.EnemyAction.STAND
                return
            elif external_event == cfg.GameStatus.HERO_LOSE:
                self.reset_action()
                return 

        if self.status == cfg.SpriteStatus.DIE:
            return

        self.brain.think()
        for action in self.brain.actions:

            if action == cfg.EnemyAction.ATTACK:
                self.action = cfg.EnemyAction.ATTACK
            
            elif action == cfg.EnemyAction.STEER:
                self.steerer.steer()
                self.action = cfg.EnemyAction.STEER
                if self.steerer.is_end:
                    self.action = cfg.EnemyAction.STAND
                self.allsprites.notify_nearby_alliance_for_target(self, self.brain.target)

            elif action == cfg.EnemyAction.LOOKOUT:
                # tell its brain the current target found(or None if no target in view scope)
                self.brain.target = self.brain.target or self.view_sensor.do_view_sense(self.hero)

            elif action == cfg.EnemyAction.STAND:
                self.action = cfg.EnemyAction.STAND

            elif action == cfg.EnemyAction.WALK:
                self.action = cfg.EnemyAction.WALK
                self.key_vec.x, self.key_vec.y = cfg.Direction.DIRECT_TO_VEC[self.direction] 
    

    def update(self, passed_seconds):
        # physics level

        if not self.attack_receiver.under_attack and self.status == cfg.SpriteStatus.DIE:
            return

        if self.action == cfg.EnemyAction.ATTACK:
            self.attack(passed_seconds)

        elif self.action == cfg.EnemyAction.STEER:
            self.walk(passed_seconds)

        elif self.action == cfg.EnemyAction.STAND:
            self.stand(passed_seconds)

        elif self.action == cfg.EnemyAction.WALK:
            self.walk(passed_seconds, True)

        if self.emotion != cfg.SpriteEmotion.NORMAL:
            is_finish = self.emotion_animation.run_sequence_frame(self.emotion, passed_seconds)
            if is_finish:
                self.emotion = cfg.SpriteEmotion.NORMAL


######## sprite group subclass ########
class GameSpritesGroup(pygame.sprite.LayeredDirty):
    def __init__(self):
        super(GameSpritesGroup, self).__init__()


    def update(self, passed_seconds):
        for v in self.sprites():
            v.update(passed_seconds)


    def notify_nearby_alliance_for_target(self, sprite, target):
        for nearby_sprite in filter(lambda sp: sp is not target and \
            sprite.pos.get_distance_to(sp.pos) <= sprite.setting.NEARBY_ALLIANCE_RANGE, self.sprites()):
            if nearby_sprite.pos.get_distance_to(target.pos) < nearby_sprite.setting.VIEW_RANGE \
                and nearby_sprite.brain.target is None:
                # found by alliance, and within chase range, chase it
                nearby_sprite.brain.target = target


    def draw(self, camera):
        sprites = sorted(self.sprites(), key=lambda sp: sp.pos.y)
        for v in sprites:
            v.draw(camera)


