import pygame
from base.util import MusicController
from base import constant as cfg
from etc import setting as sfg



class BackgroundBox(object):
    box = MusicController(sfg.BACKGROUND_MUSICS[0], pygame.mixer.music.load)
    box.add_from_list(sfg.BACKGROUND_MUSICS[1])
    def __init__(self):
        self.current_playing = None


    def play(self, key, loops=-1):
        if self.current_playing is not None:
            # stop current playing before play another one
            self.stop()

        load_success = self.box.load(key)
        if load_success:
            self.current_playing = key
            pygame.mixer.music.set_volume(sfg.Music.BACKGROUND_VOLUME)
            pygame.mixer.music.play(loops)


    def stop(self):
        self.current_playing = None
        pygame.mixer.music.stop()


    def pause(self):
        pygame.mixer.music.pause()


    def unpause(self):
        pygame.mixer.music.unpause()



class SoundBox(object):
    box = MusicController(sfg.SOUND_EFFECT[0])
    box.add_from_list(sfg.SOUND_EFFECT[1])
    def __init__(self):
        pass 

    def play(self, key):
        snd = self.box.get(key)
        snd.set_volume(sfg.Music.SOUND_VOLUME)
        snd.play()

