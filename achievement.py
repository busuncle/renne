import time
import etc.setting as sfg
import etc.constant as cfg



class Achievement(object):
    def __init__(self, hero, enemy_list):
        self.hero = hero
        self.enemy_list = enemy_list
        self.n_hit_list = []
        self.kill_time_list = []
        self.current_kill_time_index = 0
        self.has_killed = set()


    def update(self):
        for record in self.hero.attacker.hit_record:
            if record["n_hit"] > 1:
                print "%s hit!" % record["n_hit"]
                self.n_hit_list.append(record["n_hit"])

        for em in filter(lambda x: id(x) not in self.has_killed, self.enemy_list):
            if em.status["hp"] == cfg.SpriteStatus.DIE:
                self.record_n_kill(id(em))


    def record_n_hit(self, n):
        self.n_hit_list.append(n)


    def record_n_kill(self, enemy_id):
        self.has_killed.add(enemy_id)
        kill_time = time.time()
        # kill_time should be a timestamp
        self.kill_time_list.append(kill_time)


    def cal_n_kill(self):
        n = 0
        last_time = time.time()
        for kill_time in reversed(self.kill_time_list):
            if last_time - kill_time <= sfg.Achievement.N_KILL_TIMEDELTA:
                n += 1
                last_time = kill_time
            else:
                break

        return n


    def draw(self, camera):
        pass
