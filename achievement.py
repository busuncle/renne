import time
import etc.setting as sfg
import etc.constant as cfg



class Achievement(object):
    def __init__(self, hero, enemy_list):
        self.hero = hero
        self.enemy_list = enemy_list
        self.n_hit_list = []
        self.n_kill_list = []
        self.has_killed = set()


    def update(self):
        n_hit = 0
        for em in filter(lambda x: id(x) not in self.has_killed, self.enemy_list):
            if em.status["hp"] == cfg.SpriteStatus.DIE:
                self.record_n_kill(id(em))
            elif em.status["under_attack"]:
                n_hit += 1

        if n_hit > 1:
            self.n_hit_list.append(n_hit)


    def record_n_hit(self, n):
        self.n_hit_list.append(n)


    def record_n_kill(self, enemy_id):
        self.has_killed.add(enemy_id)
        kill_time = time.time()
        # kill_time should be a timestamp
        self.n_kill_list.append(kill_time)


    def cal_n_kill(self):
        n = 0
        last_time = time.time()
        for kill_time in reversed(self.n_kill_list):
            if last_time - kill_time <= sfg.Achievement.N_KILL_TIMEDELTA:
                n += 1
                last_time = kill_time
            else:
                break

        return n


    def draw(self, camera):
        pass
