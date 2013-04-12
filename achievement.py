import time
import etc.setting as sfg
import etc.constant as cfg



class Achievement(object):
    def __init__(self):
        self.n_hit_list = []
        self.n_kill_list = []


    def record_n_hit(self, n):
        self.n_hit_list.append(n)


    def record_n_kill(self, kill_time):
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
