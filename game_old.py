import sys
from time import sleep

import pygame

from space_invaders.settings import Settings
from space_invaders.game_stats import GameStats
from space_invaders.scoreboard import Scoreboard
from space_invaders.button import Button
from space_invaders.ship import Ship
from space_invaders.bullet import Bullet
from space_invaders.alien import Alien

class Game:

    def __init__(self):
        pygame.init()
        self.settings = Settings()

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Space Invaders!!")

        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship1 = Ship(self, "player1")
        self.ship2 = Ship(self, "player2")
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()
        
        self.play_button = Button(self, "Play")

    def run_game(self):
        while True:
            self._check_events()
            if self.stats.game_active:
                self.ship1.update()
                self.ship2.update()
                self._update_bullets()
                #print(len(self.bullets))
                self._update_aliens()
            self._update_screen()

    def _check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)

    def _check_play_button(self, mouse_pos):
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            self.settings.initialize_dynamic_settings()
            pygame.mouse.set_visible(False)
            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            self.aliens.empty()
            self.bullets.empty()

            self._create_fleet()
            self.ship1.center_ship()

    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship1.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship1.moving_left = True
        elif event.key == pygame.K_d:
            self.ship2.moving_right = True
        elif event.key == pygame.K_a:
            self.ship2.moving_left = True
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
        elif event.key == pygame.K_q:
            sys.exit()

    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship1.moving_right = False
        if event.key == pygame.K_LEFT:
            self.ship1.moving_left = False
        if event.key == pygame.K_d:
            self.ship2.moving_right = False
        if event.key == pygame.K_a:
            self.ship2.moving_left = False


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

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            self.stats.level += 1
            self.sb.prep_level()

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
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)
        self.sb.show_score()
        if not self.stats.game_active:
            self.play_button.draw_button()

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
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)


if __name__ == '__main__':
    ai = Game()
    ai.run_game()