"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
#added state: S_GAMING, from S_CHATTING and to S_CHATTING

import sys

from chat_utils import *
import json
import os
import time
from game import Game
import pygame
from space_invaders.settings import Settings
from space_invaders.game_stats import GameStats
from space_invaders.scoreboard import Scoreboard
from space_invaders.button import Button
from space_invaders.ship import Ship
from space_invaders.bullet import Bullet
from space_invaders.alien import Alien

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    # print(poem)
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.peer = peer_msg["from"]
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += 'You are connected with ' + self.peer
                    self.out_msg += '. Chat away!\n\n'
                    self.out_msg += '------------------------------------\n'
                    self.state = S_CHATTING

#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:     # my stuff going out
                mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
                if my_msg == "game":
                    self.state = S_GAMING
                    mysend(self.s, json.dumps({"action": "game"}))
            if len(peer_msg) > 0:    # peer's stuff, coming in
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.out_msg += "(" + peer_msg["from"] + " joined)\n"
                elif peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                elif peer_msg["action"] == "game":
                    self.state = S_GAMING
                else:
                    self.out_msg += peer_msg["from"] + peer_msg["message"]


            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# NEW STATE: GAMING
#==============================================================================
        elif self.state == S_GAMING:
            time.sleep(2)
            print("client starting")
            self.game_client()
            #game = Game()
            #game.run_game()
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
    
    def game_client(self):

        self.settings = Settings()

        self.s_game_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s_game_in.connect((CHAT_IP, GAME_PORT))

        pygame.init()
        clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Space Invaders!!")

        #self.stats = GameStats(self)
        #self.sb = Scoreboard(self)

        self.ship1 = Ship(self, "player1")
        self.ship2 = Ship(self, "player2")
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        #self._create_fleet()

        while True:
            command = self._check_events()
            data = json.dumps(command).encode()
            try:
                self.s_game_in.send(bytes(data, encoding='utf-8'))
            except:
                self.state == S_GAMING
                pygame.quit()
                sys.exit()
                break
            feedback = self.s_game_in.recv(1024).decode('utf-8')
            feedback = json.loads(feedback)
            #feedback: [ship1pos, ship2pos]
            self.ship1.rect.x = feedback[0]
            self.ship2.rect.x = feedback[1]
            #if self.stats.game_active:
            #self._update_bullets()
                #print(len(self.bullets))
            #self._update_aliens()
            self._update_screen()


    # {right: 1, right_stop: 2, left: 3, left_stop: 4, fire:5}
    def _check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mysend(self.s, json.dumps({"action": "disconnect"}))
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                return self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                return self._check_keyup_events(event)

    def _check_play_button(self, mouse_pos):
        if not self.stats.game_active:
            self.settings.initialize_dynamic_settings()
            pygame.mouse.set_visible(False)
            #self.stats.reset_stats()
            #self.stats.game_active = True
            #self.sb.prep_score()
            #self.sb.prep_level()
            #self.sb.prep_ships()

            self.aliens.empty()
            self.bullets.empty()

            self._create_fleet()
            self.ship1.center_ship()

    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            return 1
        elif event.key == pygame.K_LEFT:
            return 3
        elif event.key == pygame.K_SPACE:
            return 5
        elif event.key == pygame.K_q:
            mysend(self.s, json.dumps({"action": "disconnect"}))
            pygame.quit()
            sys.exit()

    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            return 2
        if event.key == pygame.K_LEFT:
            return 4


    def _fire_bullet(self):
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        self.bullets.update()

        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True
        )

        #if collisions:
            #for aliens in collisions.values():
                #self.stats.score += self.settings.alien_points * len(aliens)
            #self.sb.prep_score()
            #self.sb.check_high_score()

        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            #self.stats.level += 1
            #self.sb.prep_level()

    def _create_fleet(self):
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        ship_height = self.ship1.rect.height
        available_space_y = (self.settings.screen_height - 
                            (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)

        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _update_aliens(self):
        self._check_fleet_edges()
        self.aliens.update()
        if pygame.sprite.spritecollideany(self.ship1, self.aliens) or (pygame.sprite.spritecollideany(self.ship2, self.aliens)):
            self._ship_hit()
        self._check_aliens_bottom()

    def _check_fleet_edges(self):
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break
    
    def _change_fleet_direction(self):
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_screen(self):
        self.screen.fill(self.settings.bg_color)
        self.ship1.blitme()
        self.ship2.blitme()
        #for bullet in self.bullets.sprites():
            #bullet.draw_bullet()
        #self.aliens.draw(self.screen)
        #self.sb.show_score()

        pygame.display.flip()

    def _check_aliens_bottom(self):
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._ship_hit()
                break

    def _ship_hit(self):
        if (self.stats.ships_1_left > 0) and (self.stats.ships_2_left > 0):
            if pygame.sprite.spritecollideany(self.ship1, self.aliens):
                self.stats.ships_1_left -= 1
            if pygame.sprite.spritecollideany(self.ship2, self.aliens):
                self.stats.ships_2_left -= 1
            self.sb.prep_ships()
            self.aliens.empty()
            self.bullets.empty()
            self._create_fleet()
            self.ship1.center_ship()
            self.ship2.center_ship()
            time.sleep(0.5)
        else:
            self.stats.game_active = False

        


