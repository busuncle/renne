import pygame
from base.util import MusicController
import etc.setting as sfg
import etc.constant as cfg



class BackgroundBox(object):
    box = MusicController(sfg.BACKGROUND_MUSICS[0], pygame.mixer.music.load)
    box.add_from_list(sfg.BACKGROUND_MUSICS[1])
    def __init__(self, volume):
        pygame.mixer.music.set_volume(volume)


    def play(self, key):
        self.box.get(key)
        pygame.mixer.music.play(-1)


    def stop(self):
        pygame.mixer.music.stop()


    def pause(self):
        pygame.mixer.music.pause()



class SoundBox(object):
    box = MusicController(sfg.SOUND_EFFECT[0])
    box.add_from_list(sfg.SOUND_EFFECT[1])
    def __init__(self):
        pass


