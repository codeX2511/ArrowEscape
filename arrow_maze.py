
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.clock import Clock
from collections import deque
import random

ROWS = 9
COLS = 9

BG = (0.035, 0.06, 0.13, 1)
CYAN = (0.1, 0.85, 1, 1)
GOLD = (1, 0.75, 0.1, 1)
PURPLE = (0.65, 0.4, 1, 1)


class MazeWidget(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = None
        self.bind(size=self.draw, pos=self.draw)

    def draw(self, *args):

        self.canvas.clear()

        if not self.game:
            return

        g = self.game

        cell = min(
            self.width / COLS,
            self.height / ROWS
        )

        ox = self.x + (self.width - cell * COLS) / 2
        oy = self.y + (self.height - cell * ROWS) / 2

        def center(r, c):
            return (
                ox + (c + 0.5) * cell,
                oy + (ROWS - r - 0.5) * cell
            )

        with self.canvas:

            Color(*BG)
            Rectangle(pos=self.pos, size=self.size)

            for r in range(ROWS):
                for c in range(COLS):

                    x = ox + c * cell
                    y = oy + (ROWS-r-1) * cell

                    Color(0.07, 0.12, 0.23, 1)

                    Rectangle(
                        pos=(x+2, y+2),
                        size=(cell-4, cell-4)
                    )

                    walls = g.maze[r][c]

                    Color(0.25, 0.38, 0.55, 1)

                    if walls[0]:
                        Line(points=[x,y+cell,x+cell,y+cell], width=2)

                    if walls[1]:
                        Line(points=[x+cell,y+cell,x+cell,y], width=2)

                    if walls[2]:
                        Line(points=[x,y,x+cell,y], width=2)

                    if walls[3]:
                        Line(points=[x,y,x,y+cell], width=2)

            # Start
            sx, sy = center(0, 0)

            Color(0.1, 0.9, 0.5, 1)
            Ellipse(pos=(sx-7, sy-7), size=(14,14))

            # Exit
            ex, ey = center(ROWS-1, COLS-1)

            Color(*GOLD)
            Ellipse(pos=(ex-12, ey-12), size=(24,24))

            # Diamonds
            for r, c in g.gems - g.collected:

                x, y = center(r, c)

                Color(*PURPLE)

                Line(
                    points=[
                        x,y+9,
                        x+7,y,
                        x,y-9,
                        x-7,y,
                        x,y+9
                    ],
                    width=2.5
                )

            # Arrows
            for (r,c), (dr,dc) in g.arrows.items():

                x,y = center(r,c)

                Color(*CYAN)

                Rectangle(
                    pos=(x-cell*.3,y-cell*.3),
                    size=(cell*.6,cell*.6)
                )

                Color(0.02,0.1,0.18,1)

                if dr == -1:
                    Line(points=[x,y+8,x,y-8,x-5,y-3,x,y-8,x+5,y-3],width=2)

                elif dr == 1:
                    Line(points=[x,y-8,x,y+8,x-5,y+3,x,y+8,x+5,y+3],width=2)

                elif dc == 1:
                    Line(points=[x-8,y,x+8,y,x+3,y+5,x+8,y,x+3,y-5],width=2)

                else:
                    Line(points=[x+8,y,x-8,y,x-3,y+5,x-8,y,x-3,y-5],width=2)

            # Player
            r,c = g.player
            px,py = center(r,c)

            Color(*PURPLE)
            Ellipse(pos=(px-11,py-11),size=(22,22))

            Color(1,1,1,1)
            Ellipse(pos=(px-3,py-3),size=(6,6))


class ArrowEscape(App):

    def build(self):

        self.score = 0
        self.level = 1
        self.moves = 0
        self.seconds = 0

        self.generate_maze()

        main = BoxLayout(
            orientation="vertical",
            padding=10,
            spacing=8
        )

        with main.canvas.before:
            Color(*BG)
            self.background = Rectangle(
                pos=main.pos,
                size=main.size
            )

        main.bind(
            pos=lambda obj,val: setattr(self.background,"pos",val),
            size=lambda obj,val: setattr(self.background,"size",val)
        )

        title = Label(
            text="[b]🏹 ARROW ESCAPE[/b]",
            markup=True,
            font_size="25sp",
            color=CYAN,
            size_hint_y=None,
            height=48
        )

        main.add_widget(title)

        self.stats = Label(
            text="",
            font_size="14sp",
            color=GOLD,
            size_hint_y=None,
            height=35
        )

        main.add_widget(self.stats)

        self.maze_view = MazeWidget()
        self.maze_view.game = self

        main.add_widget(self.maze_view)

        self.message = Label(
            text="💎 Collect diamonds and reach EXIT!",
            font_size="13sp",
            size_hint_y=None,
            height=35
        )

        main.add_widget(self.message)

        controls = GridLayout(
            cols=3,
            rows=2,
            spacing=7,
            size_hint=(1,None),
            height=112
        )

        controls.add_widget(Label(text=""))

        self.add_control(controls,"⬆️",(-1,0))

        controls.add_widget(Label(text=""))

        self.add_control(controls,"⬅️",(0,-1))
        self.add_control(controls,"⬇️",(1,0))
        self.add_control(controls,"➡️",(0,1))

        main.add_widget(controls)

        restart = Button(
            text="🔄 NEW GAME",
            size_hint_y=None,
            height=48,
            background_normal="",
            background_color=GOLD,
            color=(0.05,0.08,0.15,1)
        )

        restart.bind(on_release=lambda x:self.restart())

        main.add_widget(restart)

        Clock.schedule_interval(self.timer,1)

        self.update_stats()

        return main

    # FIXED BUTTON FUNCTION
    def add_control(self,layout,text,direction):

        btn = Button(
            text=text,
            font_size="26sp",
            background_normal="",
            background_color=(0.1,0.25,0.45,1)
        )

        def button_pressed(instance):

            print("BUTTON CLICKED:",direction)

            self.move_player(*direction)

        btn.bind(on_release=button_pressed)

        layout.add_widget(btn)

    # MAZE GENERATION
    def generate_maze(self):

        self.maze = [
            [[1,1,1,1] for c in range(COLS)]
            for r in range(ROWS)
        ]

        visited = {(0,0)}
        stack = [(0,0)]

        directions = [
            (-1,0,0,2),
            (0,1,1,3),
            (1,0,2,0),
            (0,-1,3,1)
        ]

        while stack:

            r,c = stack[-1]
            choices = []

            for dr,dc,wall,opposite in directions:

                nr,nc = r+dr,c+dc

                if (0 <= nr < ROWS and
                    0 <= nc < COLS and
                    (nr,nc) not in visited):

                    choices.append((nr,nc,wall,opposite))

            if choices:

                nr,nc,wall,opposite = random.choice(choices)

                self.maze[r][c][wall] = 0
                self.maze[nr][nc][opposite] = 0

                visited.add((nr,nc))
                stack.append((nr,nc))

            else:
                stack.pop()

        # Find path
        queue = deque([((0,0),[(0,0)])])
        seen = {(0,0)}
        self.path = []

        while queue:

            (r,c),route = queue.popleft()

            if (r,c) == (ROWS-1,COLS-1):
                self.path = route
                break

            for dr,dc,wall,opposite in directions:

                nr,nc = r+dr,c+dc

                if (0 <= nr < ROWS and
                    0 <= nc < COLS and
                    self.maze[r][c][wall] == 0 and
                    (nr,nc) not in seen):

                    seen.add((nr,nc))
                    queue.append(((nr,nc),route+[(nr,nc)]))

        self.arrows = {}

        for i in range(4,len(self.path)-1,10):

            r,c = self.path[i]
            nr,nc = self.path[i+1]

            self.arrows[(r,c)] = (nr-r,nc-c)

        self.gems = set()

        for i in range(5,len(self.path)-1,8):

            if self.path[i] not in self.arrows:
                self.gems.add(self.path[i])

            if len(self.gems) == 3:
                break

        self.collected = set()
        self.player = (0,0)
        self.moves = 0
        self.game_active = True

        if hasattr(self,"maze_view"):
            self.maze_view.draw()

    # PLAYER MOVEMENT
    def move_player(self,dr,dc):

        if not self.game_active:
            return

        r,c = self.player
        nr,nc = r+dr,c+dc

        if not (0 <= nr < ROWS and 0 <= nc < COLS):
            return

        wall = {
            (-1,0):0,
            (0,1):1,
            (1,0):2,
            (0,-1):3
        }[(dr,dc)]

        if self.maze[r][c][wall]:
            self.message.text = "🧱 Wall! Try another direction."
            return

        self.player = (nr,nc)
        self.moves += 1

        # Collect diamonds
        if self.player in self.gems:

            if self.player not in self.collected:

                self.collected.add(self.player)
                self.score += 20

                self.message.text = "💎 Diamond collected!"

        # Exit
        if self.player == (ROWS-1,COLS-1):

            if self.collected == self.gems:

                self.score += 50
                self.game_active = False

                self.message.text = "🎉 LEVEL COMPLETED!"

                self.level += 1

                Clock.schedule_once(
                    lambda dt:self.next_level(),1.5
                )

            else:
                self.message.text = "🔒 Collect all Diamonds!"

        self.update_stats()
        self.maze_view.draw()

    def timer(self,dt):

        if self.game_active:
            self.seconds += 1

        self.update_stats()

    def update_stats(self):

        self.stats.text = (
            f"⭐ {self.score}   "
            f"🏆 Level {self.level}   "
            f"💎 {len(self.collected)}/{len(self.gems)}   "
            f"⏱️ {self.seconds}s"
        )

    def next_level(self):

        self.generate_maze()

        self.message.text = "🚀 New Level! Find the diamonds!"

    def restart(self):

        self.score = 0
        self.level = 1
        self.seconds = 0

        self.generate_maze()

        self.message.text = "🎮 New Game Started!"

        self.update_stats()


if __name__ == "__main__":
    ArrowEscape().run()
