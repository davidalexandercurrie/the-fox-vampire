import curses
import random
import pygame
import time

MAP_WIDTH = 10
MAP_HEIGHT = 6
ENERGY_START = 10
ENERGY_MAX = 15

EMOJIS = {
    "grass": "🌳",
    "mountain": "⬛",
    "water": "🌊",
    "apple": "🍏",
    "player": "🦊",
    "enemy": "🐻",
    "heal": "🧪",
    "boost": "💥",
    "death": "💀",
    "empty": "⬛",
    "rabbit": "🐰",
    "bird": "🐦",
    "deer": "🦌",
    "squirrel": "🐿️"
}

TERRAINS = ["grass", "mountain", "water"]
AMBIENT_ANIMALS = ["rabbit", "bird", "deer", "squirrel"]

def create_map():
    game_map = []
    for y in range(MAP_HEIGHT):
        row = []
        for x in range(MAP_WIDTH):
            terrain = random.choices(TERRAINS, weights=[0.8, 0.05, 0.15])[0]
            row.append(terrain)
        game_map.append(row)
    # Place apples
    for _ in range(3):
        while True:
            ax, ay = random.randint(0, MAP_WIDTH-1), random.randint(0, MAP_HEIGHT-1)
            if game_map[ay][ax] != "apple":
                game_map[ay][ax] = "apple"
                break
    # Place items
    item_types = ["heal", "boost", "death"]
    for item in item_types:
        while True:
            ix, iy = random.randint(0, MAP_WIDTH-1), random.randint(0, MAP_HEIGHT-1)
            if game_map[iy][ix] not in ("apple", "heal", "boost", "death"):
                game_map[iy][ix] = item
                break
    # Place enemy (bear)
    while True:
        ex, ey = random.randint(0, MAP_WIDTH-1), random.randint(0, MAP_HEIGHT-1)
        if game_map[ey][ex] not in ("apple", "heal", "boost", "death"):
            game_map[ey][ex] = "enemy"
            break
    return game_map

def is_adjacent(px, py, ex, ey):
    return abs(px - ex) + abs(py - ey) == 1

def find_enemy(game_map):
    for y, row in enumerate(game_map):
        for x, cell in enumerate(row):
            if cell == "enemy":
                return x, y
    return None, None

def battle(stdscr, player_hp, enemy_hp, inventory):
    import time
    # Play fight_scene.mp3 during battle
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load("audio/fight_scene.mp3")
        pygame.mixer.music.play(-1)
    except Exception as e:
        pass
    # Shorter battle: lower HP, higher damage
    player_hp = 12
    enemy_hp = 10
    player_attacks = [
        {"name": "Bite", "min": 4, "max": 7, "hit": 0.8},
        {"name": "Scratch", "min": 3, "max": 9, "hit": 0.7},
        {"name": "Pounce", "min": 5, "max": 8, "hit": 0.6},
        {"name": "Tail Whip", "min": 3, "max": 5, "hit": 0.7, "effect": "weakened", "effect_chance": 0.3}
    ]
    enemy_attacks = [
        {"name": "Swipe", "min": 3, "max": 8, "hit": 0.75},
        {"name": "Roar", "min": 2, "max": 6, "hit": 0.9},
        {"name": "Chomp", "min": 4, "max": 9, "hit": 0.65},
        {"name": "Intimidate", "min": 3, "max": 5, "hit": 0.7, "effect": "scared", "effect_chance": 0.3}
    ]
    # Color pairs for battle messages
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(10, curses.COLOR_RED, -1)      # Missed, danger
        curses.init_pair(11, curses.COLOR_YELLOW, -1)   # Player hit
        curses.init_pair(12, curses.COLOR_GREEN, -1)    # Healing
        curses.init_pair(13, curses.COLOR_CYAN, -1)     # Status
        curses.init_pair(14, curses.COLOR_MAGENTA, -1)  # Bear hit
        curses.init_pair(15, curses.COLOR_WHITE, -1)    # Default
        curses.init_pair(16, curses.COLOR_RED, -1)      # HP low
        curses.init_pair(17, curses.COLOR_YELLOW, -1)   # HP mid
        curses.init_pair(18, curses.COLOR_GREEN, -1)    # HP high
    def print_battle_msg(msg, color=None, delay=2.8):
        stdscr.clear()
        # Color HP based on percentage
        def hp_color(hp, maxhp):
            if not curses.has_colors():
                return 0
            pct = hp / maxhp
            if pct > 0.6:
                return curses.color_pair(18) | curses.A_BOLD
            elif pct > 0.3:
                return curses.color_pair(17) | curses.A_BOLD
            else:
                return curses.color_pair(16) | curses.A_BOLD
        # Player HP
        stdscr.addstr(0, 0, "🦊 HP: ")
        stdscr.addstr(f"{player_hp}", hp_color(player_hp, 12))
        stdscr.addstr("    ")
        # Bear HP
        stdscr.addstr("🐻 HP: ")
        stdscr.addstr(f"{enemy_hp}", hp_color(enemy_hp, 10))
        if curses.has_colors() and color:
            stdscr.addstr(2, 0, msg, curses.color_pair(color) | curses.A_BOLD)
        else:
            stdscr.addstr(2, 0, msg)
        stdscr.refresh()
        time.sleep(delay)
    turn = "player"
    attack_boost = False
    used_escape = False
    # Status effects
    enemy_weakened = 0  # turns left
    player_scared = 0   # turns left

    # Bear's secret upgrade stats
    bear_power = 0
    bear_hp_boost = 0
    bear_attacks_extra = [
        {"name": "Existential Dread", "min": 5, "max": 11, "hit": 0.5, "effect": "scared", "effect_chance": 0.5}
    ]
    bear_upgrade_turns = 0

    while player_hp > 0 and enemy_hp > 0:
        stdscr.clear()
        stdscr.addstr(0, 0, f"🦊 HP: {player_hp}    🐻 HP: {enemy_hp}")
        status_line = ""
        if enemy_weakened > 0:
            status_line += "🐻 Weakened "
        if player_scared > 0:
            status_line += "🦊 Scared "
        if status_line:
            stdscr.addstr(1, 0, status_line, curses.color_pair(13) | curses.A_BOLD if curses.has_colors() else 0)
        stdscr.addstr(3, 0, "Battle! Choose your action:" if turn == "player" else "Bear is attacking...")
        stdscr.refresh()
        if turn == "player":
            stdscr.addstr(5, 0, "1. Attack")
            stdscr.addstr(6, 0, "2. Use Item")
            stdscr.refresh()
            action = None
            while True:
                key = stdscr.getch()
                if key == ord('1'):
                    action = "attack"
                    break
                elif key == ord('2'):
                    action = "item"
                    break
            if action == "attack":
                attack_start_line = 8
                max_cols = curses.COLS - 1
                for idx, atk in enumerate(player_attacks):
                    line = f"{idx+1}. {atk['name']} ({atk['min']}-{atk['max']} dmg, {int(atk['hit']*100)}% hit"
                    if atk.get("effect") == "weakened":
                        line += ", 30% Weakened"
                    line += ")"
                    if attack_start_line + idx < curses.LINES:
                        stdscr.addstr(attack_start_line + idx, 0, line[:max_cols])
                stdscr.refresh()
                while True:
                    key = stdscr.getch()
                    if key in [ord('1'), ord('2'), ord('3'), ord('4')]:
                        atk = player_attacks[key-ord('1')]
                        break
                # If player is scared, 50% chance to miss
                if player_scared > 0:
                    if random.random() < 0.5:
                        print_battle_msg("🦊 is scared and missed the attack!", 10)
                        player_scared = 0
                        turn = "enemy"
                        continue
                    else:
                        print_battle_msg("🦊 shakes off the fear!", 13)
                        player_scared = 0
                hit = random.random() < atk["hit"]
                if hit:
                    dmg = random.randint(atk["min"], atk["max"])
                    if attack_boost:
                        dmg *= 2
                        attack_boost = False
                        print_battle_msg("🦊's attack was boosted!", 11, 2.0)
                    # Make the bear unbeatable: if HP would drop to 0, it heals or shrugs it off
                    if enemy_hp - dmg <= 0:
                        import random as _random
                        dramatic_msgs = [
                            "🐻 shrugs off the attack and roars! It heals completely!",
                            "Your attack should have finished the bear, but it rises, unstoppable!",
                            "The bear's wounds close before your eyes. It cannot be defeated!",
                            "The bear absorbs your blow and seems even stronger!"
                        ]
                        heal_amt = 10 + random.randint(3, 7)
                        enemy_hp += heal_amt
                        print_battle_msg(_random.choice(dramatic_msgs) + f" (Healed {heal_amt} HP!)", 12, 3.0)
                    else:
                        enemy_hp -= dmg
                        print_battle_msg(f"🦊 used {atk['name']}! Hit for {dmg} damage.", 11)
                    if atk.get("effect") == "weakened" and random.random() < atk.get("effect_chance", 0):
                        enemy_weakened = 2
                        print_battle_msg("🐻 is Weakened! (deals half damage for 2 turns)", 13)
                else:
                    print_battle_msg(f"🦊 used {atk['name']}! Missed!", 10)
                turn = "enemy"
            elif action == "item":
                stdscr.clear()
                stdscr.addstr(0, 0, f"🦊 HP: {player_hp}    🐻 HP: {enemy_hp}")
                stdscr.addstr(1, 0, "Choose item to use (press number), or press q to cancel:")
                if not inventory:
                    stdscr.addstr(3, 0, "No items in inventory. Press any key to go back.")
                    stdscr.refresh()
                    stdscr.getch()
                    continue
                item_indices = []
                for idx, item in enumerate(inventory):
                    if item == "heal":
                        stdscr.addstr(3+idx, 0, f"{idx+1}. 🧪 Healing Potion (+8 HP)")
                    elif item == "boost":
                        stdscr.addstr(3+idx, 0, f"{idx+1}. 💥 Attack Boost (next attack x2)")
                    elif item == "death":
                        stdscr.addstr(3+idx, 0, f"{idx+1}. 💀 Cursed Relic (instant demise)")
                    item_indices.append(idx)
                stdscr.refresh()
                chosen = None
                while True:
                    key = stdscr.getch()
                    if key in [ord(str(i+1)) for i in item_indices]:
                        chosen = int(chr(key)) - 1
                        break
                    elif key in [ord('q'), ord('Q')]:
                        chosen = None
                        break
                if chosen is None or chosen >= len(inventory):
                    continue
                item = inventory[chosen]
                if item == "heal":
                    heal_amt = 8
                    player_hp += heal_amt
                    print_battle_msg(f"🦊 used Healing Potion! Restored {heal_amt} HP.", 12)
                    del inventory[chosen]
                elif item == "boost":
                    attack_boost = True
                    print_battle_msg("🦊 used Attack Boost! Next attack will be doubled.", 13)
                    del inventory[chosen]
                elif item == "death":
                    print_battle_msg("🦊 used the Cursed Relic! Your fate is sealed...", 10, 1.2)
                    player_hp = 0
                    del inventory[chosen]
                    break
                turn = "enemy"
        else:
            # Bear upgrades: every turn, gets stronger and heals a bit
            bear_upgrade_turns += 1
            bear_power += random.randint(1, 2) if bear_upgrade_turns > 2 else 1
            bear_hp_boost += random.randint(1, 2) if bear_upgrade_turns > 2 else 1
            heal_amount = bear_hp_boost
            enemy_hp += heal_amount
            if enemy_hp > 100:
                enemy_hp = 100
            if heal_amount > 0:
                healing_reasons = [
                    f"The bear found some honey and healed for {heal_amount} HP!",
                    f"The bear is feeling good, it did a dance and healed for {heal_amount} HP!",
                    f"The bear took a quick nap and healed for {heal_amount} HP!",
                    f"The bear munched on some berries and healed for {heal_amount} HP!",
                    f"The bear flexed its muscles and healed for {heal_amount} HP!",
                    f"The bear remembered a happy memory and healed for {heal_amount} HP!"
                ]
                import random as _random
                print_battle_msg(_random.choice(healing_reasons), 12)
            attacks = enemy_attacks[:]
            if bear_upgrade_turns > 2:
                attacks += bear_attacks_extra
            atk = random.choice(attacks)
            hit = random.random() < atk["hit"]
            if hit:
                dmg = random.randint(atk["min"] + bear_power, atk["max"] + bear_power + bear_upgrade_turns//3)
                if enemy_weakened > 0 and atk.get("effect") != "scared":
                    dmg = dmg // 2
                player_hp -= dmg
                print_battle_msg(f"🐻 used {atk['name']}! Hit for {dmg} damage.", 14)
                if atk.get("effect") == "scared" and random.random() < atk.get("effect_chance", 0):
                    player_scared = 1
                    print_battle_msg("🦊 is Scared! (50% chance to miss next attack)", 13)
                if atk.get("name") == "Existential Dread" and hit:
                    print_battle_msg("You feel a sudden urge to question your life choices.", 13)
            else:
                print_battle_msg(f"🐻 used {atk['name']}! Missed!", 10)
            turn = "player"
        # Decrement status effects
        if enemy_weakened > 0 and turn == "player":
            enemy_weakened -= 1
        if player_scared > 0 and turn == "enemy":
            player_scared -= 1
    stdscr.clear()
    # Stop battle music before any post-battle screen or story
    try:
        import pygame
        pygame.mixer.music.stop()
    except Exception as e:
        pass
    if used_escape:
        stdscr.addstr(0, 0, "You escaped from the bear! Press any key to continue.")
        stdscr.refresh()
        stdscr.getch()
        return None  # Indicate escape
    elif player_hp > 0:
        stdscr.addstr(0, 0, "You defeated the bear! Press any key to continue.")
        stdscr.refresh()
        stdscr.getch()
        return True
    else:
        # Begin darkly humorous vampire story sequence
        stdscr.clear()
        import textwrap
        story = [
           "As the bear's claws close in, the world fades to black.",
           "You awaken in a crypt, cold stone beneath your paws, a hunger gnawing at your soul.",
           "Centuries pass. The moon rises and falls, but the foxes you once knew are only memories.",
           "You wander misty forests, your shadow the only companion that never leaves.",
           "You outlive empires, witness the rise and fall of kings, yet your heart aches for a simple den and the warmth of a family.",
           "Sometimes, you howl at the night sky, hoping another fox will answer. Only silence returns your call.",
           "In the 23rd century, you see your reflection in a digital screen—still a fox, but with eyes that have seen too much.",
           "After 600 years, you stand atop a hill, watching the world change, feeling the weight of centuries in your bones.",
           "You are legend. You are myth. You are the last fox—eternal, haunted, and finally, at peace with the night."
        ]
        # Start story music
        try:
            print("Trying to play story music: story_theme.mp3")
            pygame.mixer.init()
            pygame.mixer.music.load("audio/story_theme.mp3")
            pygame.mixer.music.play(-1)
            print("Story music started.")
        except Exception as e:
            print(f"Error playing story music: {e}")
        max_cols = curses.COLS - 1
        # Story display: word-by-word, scroll if >70% of screen, 5s per line
        import math
        all_display_lines = []
        max_lines = curses.LINES
        scroll_threshold = int(0.7 * max_lines)
        for line in story:
            wrapped = textwrap.wrap(line, width=max_cols, break_long_words=False, replace_whitespace=False)
            for wline in wrapped:
                words = wline.split()
                display_line = ""
                delay_per_word = 0.25
                for idx, word in enumerate(words):
                    if idx > 0:
                        display_line += " "
                    display_line += word
                    # Prepare lines to display
                    temp_lines = all_display_lines + [display_line]
                    # Scroll if needed
                    if len(temp_lines) > scroll_threshold:
                        temp_lines = temp_lines[-scroll_threshold:]
                    stdscr.clear()
                    for lidx, l in enumerate(temp_lines):
                        if lidx < max_lines:
                            stdscr.addstr(lidx, 0, l[:max_cols])
                    stdscr.refresh()
                    time.sleep(delay_per_word)
                all_display_lines.append(display_line)
                # After finishing the line, show the full line for a moment if not already shown
                temp_lines = all_display_lines
                if len(temp_lines) > scroll_threshold:
                    temp_lines = temp_lines[-scroll_threshold:]
                stdscr.clear()
                for lidx, l in enumerate(temp_lines):
                    if lidx < max_lines:
                        stdscr.addstr(lidx, 0, l[:max_cols])
                stdscr.refresh()
        time.sleep(4)
        # Switch to GAME OVER music
        try:
            print("Switching to GAME OVER music: game_over.mp3")
            pygame.mixer.music.stop()
            pygame.mixer.music.load("audio/game_over.mp3")
            pygame.mixer.music.play()
            print("GAME OVER music started.")
        except Exception as e:
            print(f"Error playing GAME OVER music: {e}")
        stdscr.clear()
        # Centered GAME OVER with black hearts, blood, and fox emojis
        black_heart = "🖤"
        game_over_text = f"{black_heart} GAME OVER {black_heart}"
        blood = "🩸" * 3
        fox = "🦊"
        max_cols = curses.COLS - 1
        max_lines = curses.LINES
        go_y = max_lines // 2 - 1
        go_x = max((max_cols - len(game_over_text)) // 2, 0)
        blood_line = f"{blood}   {fox}   {blood}"
        blood_x = max((max_cols - len(blood_line)) // 2, 0)
        stdscr.attron(curses.color_pair(0))
        stdscr.addstr(go_y, go_x, game_over_text, curses.A_BOLD)
        stdscr.addstr(go_y + 2, blood_x, blood_line)
        stdscr.attroff(curses.color_pair(0))
        stdscr.refresh()
        time.sleep(4)
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            pass
        return False

def main(stdscr):
    print("Game Started!")
    curses.curs_set(0)
    stdscr.nodelay(True)  # Enable non-blocking input
    stdscr.timeout(200)  # 200ms timeout for getch

    # --- TITLE SCREEN ---
    stdscr.clear()
    max_cols = curses.COLS if hasattr(curses, "COLS") else 40
    max_lines = curses.LINES if hasattr(curses, "LINES") else 20

    fox_title = "🦊✨🌞  THE FOX  🦊✨🌞"
    vampire_title = "🩸🖤  VAMPIRE  🖤🩸"
    fox_y = max_lines // 2 - 2
    vampire_y = fox_y + 2
    fox_x = max((max_cols - len(fox_title)) // 2, 0)
    vampire_x = max((max_cols - len(vampire_title)) // 2, 0)

    # Print THE FOX with happy fox vibes
    stdscr.addstr(fox_y, fox_x, fox_title, curses.A_BOLD)
    stdscr.refresh()
    time.sleep(1.1)

    # Print VAMPIRE in red with blood/black heart emojis
    if curses.has_colors():
        curses.start_color()
        # Try to use default background, fallback to COLOR_BLACK if needed
        try:
            curses.init_pair(5, curses.COLOR_RED, -1)
        except curses.error:
            try:
                curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
            except curses.error:
                pass  # If still fails, just skip color
        try:
            stdscr.addstr(vampire_y, vampire_x, vampire_title, curses.color_pair(5) | curses.A_BOLD)
        except curses.error:
            stdscr.addstr(vampire_y, vampire_x, vampire_title, curses.A_BOLD)
    else:
        stdscr.addstr(vampire_y, vampire_x, vampire_title, curses.A_BOLD)
    stdscr.refresh()
    time.sleep(1.1)

    # Wait for up to 2.5 seconds or until a key is pressed
    stdscr.nodelay(True)
    start_time = time.time()
    while True:
        if stdscr.getch() != -1:
            break
        if time.time() - start_time > 2.5:
            break
        time.sleep(0.05)
    stdscr.nodelay(False)

    # Show intro message
    stdscr.clear()
    stdscr.addstr(0, 0, "Oh no, a terrible bear is causing trouble in the fields!")
    stdscr.addstr(2, 0, "Press any key to begin your quest...")
    stdscr.refresh()
    stdscr.getch()

    # Initialize color pairs for energy gradient
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_MAGENTA, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)

    game_map = create_map()
    px, py = 1, 1
    energy = ENERGY_START
    player_hp = 20
    enemy_hp = 20
    inventory = []
    ambient_animals = []  # List of {'type': 'rabbit', 'x': 3, 'y': 2, 'timer': 10}
    last_animal_spawn = time.time()

    while True:
        stdscr.clear()
        ex, ey = find_enemy(game_map)

        # Handle ambient animals
        current_time = time.time()
        if current_time - last_animal_spawn >= 3.0 and len(ambient_animals) < 3:
            # Spawn a new ambient animal
            if random.random() < 0.6:  # 60% chance to spawn
                animal_type = random.choice(AMBIENT_ANIMALS)
                # Find a random grass spot for the animal
                attempts = 0
                while attempts < 20:
                    ax, ay = random.randint(0, MAP_WIDTH-1), random.randint(0, MAP_HEIGHT-1)
                    if (game_map[ay][ax] == "grass" and
                        (ax, ay) != (px, py) and
                        (ax, ay) != (ex, ey) and
                        not any(a['x'] == ax and a['y'] == ay for a in ambient_animals)):
                        ambient_animals.append({
                            'type': animal_type,
                            'x': ax,
                            'y': ay,
                            'timer': time.time() + random.randint(5, 10),
                            'last_move': time.time()
                        })
                        break
                    attempts += 1
            last_animal_spawn = current_time

        # Move and update ambient animals
        for animal in ambient_animals[:]:
            # Move every 1.0 seconds
            if current_time - animal['last_move'] >= 1.0:
                animal['last_move'] = current_time
                # Try to move in a random direction
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(directions)
                for dx, dy in directions:
                    new_x, new_y = animal['x'] + dx, animal['y'] + dy
                    if (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and
                        game_map[new_y][new_x] == "grass" and
                        (new_x, new_y) != (px, py) and
                        (new_x, new_y) != (ex, ey) and
                        not any(a['x'] == new_x and a['y'] == new_y for a in ambient_animals if a != animal)):
                        animal['x'], animal['y'] = new_x, new_y
                        break

            # Remove if timer expired
            if current_time >= animal['timer']:
                ambient_animals.remove(animal)

        # Debug: count terrain types in map
        terrain_count = {}
        for row in game_map:
            for cell in row:
                terrain_count[cell] = terrain_count.get(cell, 0) + 1
        # Draw map
        max_y, max_x = stdscr.getmaxyx()
        for y, row in enumerate(game_map):
            if y >= max_y - 3:  # Leave space for UI
                break
            for x, cell in enumerate(row):
                if x*2 >= max_x - 2:  # Leave some margin
                    break
                try:
                    # Check if there's an ambient animal at this position
                    ambient_animal = next((a for a in ambient_animals if a['x'] == x and a['y'] == y), None)

                    if (x, y) == (px, py):
                        stdscr.addstr(y, x*2, EMOJIS["player"])
                    elif (x, y) == (ex, ey):
                        stdscr.addstr(y, x*2, EMOJIS["enemy"])
                    elif ambient_animal:
                        stdscr.addstr(y, x*2, EMOJIS[ambient_animal['type']])
                    elif cell in ("heal", "boost", "escape"):
                        stdscr.addstr(y, x*2, EMOJIS[cell])
                    else:
                        stdscr.addstr(y, x*2, EMOJIS.get(cell, EMOJIS["empty"]))
                except curses.error:
                    pass
        # Energy color gradient: green at 15, yellow at 10-14, magenta at 5-9, red at 0-4
        max_y, max_x = stdscr.getmaxyx()
        if MAP_HEIGHT+2 < max_y and max_x > 50:  # Only draw UI if there's enough space
            if curses.has_colors():
                if energy >= 13:
                    color = curses.color_pair(1)  # Green
                elif energy >= 10:
                    color = curses.color_pair(2)  # Yellow
                elif energy >= 5:
                    color = curses.color_pair(3)  # Magenta
                else:
                    color = curses.color_pair(4)  # Red
                try:
                    stdscr.addstr(MAP_HEIGHT+1, 0, "Energy: ", curses.A_BOLD)
                    stdscr.addstr(f"{energy}", color | curses.A_BOLD)
                    stdscr.addstr(f"/{ENERGY_MAX}   (WASD to move, Q to quit)")
                except curses.error:
                    pass
            else:
                try:
                    stdscr.addstr(MAP_HEIGHT+1, 0, f"Energy: {energy}/{ENERGY_MAX}   (WASD to move, Q to quit)")
                except curses.error:
                    pass
            try:
                inv_text = f"Inventory: {' '.join([EMOJIS[i] for i in inventory]) if inventory else 'None'}"
                debug_text = f" | Debug: {terrain_count}"
                if len(inv_text + debug_text) < max_x - 5:
                    stdscr.addstr(MAP_HEIGHT+2, 0, inv_text + debug_text)
                else:
                    stdscr.addstr(MAP_HEIGHT+2, 0, inv_text)
            except curses.error:
                pass
        stdscr.refresh()

        # Check for battle trigger: only when player moves onto the bear's square
        if ex is not None and (px, py) == (ex, ey):
            result = battle(stdscr, player_hp, enemy_hp, inventory)
            if result is True:
                # Only update if ex and ey are not None
                if ex is not None and ey is not None:
                    game_map[ey][ex] = "grass"
            elif result is None:
                # Escaped: keep inventory, enemy remains
                pass
            else:
                break

        key = stdscr.getch()
        if key == -1:  # No key pressed, continue loop
            time.sleep(0.1)  # Small delay to prevent too fast updates
            continue
        if key in [ord('q'), ord('Q')]:
            break
        dx, dy = 0, 0
        valid_move = False
        if key in [ord('w'), ord('W')]:
            dy = -1
            valid_move = True
        elif key in [ord('s'), ord('S')]:
            dy = 1
            valid_move = True
        elif key in [ord('a'), ord('A')]:
            dx = -1
            valid_move = True
        elif key in [ord('d'), ord('D')]:
            dx = 1
            valid_move = True

        nx, ny = px + dx, py + dy
        if valid_move and 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
            px, py = nx, ny
            energy -= 1
            cell = game_map[py][px]
            if cell == "apple":
                # Apple collection animation
                emoji = "🍏"
                msg = "You found an apple!"
                stdscr.clear()
                max_cols = curses.COLS - 1
                max_lines = curses.LINES
                ey = max_lines // 2 - 1
                ex = max((max_cols - 1) // 2, 0)
                mx = max((max_cols - len(msg)) // 2, 0)
                for bounce in range(2):
                    stdscr.clear()
                    if bounce % 2 == 0:
                        stdscr.addstr(ey, ex, emoji, curses.A_BOLD)
                        stdscr.addstr(ey + 2, mx, msg, curses.A_BOLD)
                    stdscr.refresh()
                    time.sleep(0.18)
                stdscr.clear()
                stdscr.addstr(ey, ex, emoji, curses.A_BOLD)
                stdscr.addstr(ey + 2, mx, msg, curses.A_BOLD)
                stdscr.refresh()
                time.sleep(0.55)
                energy += 5
                if energy > ENERGY_MAX:
                    energy = ENERGY_MAX
                game_map[py][px] = "grass"
            elif cell == "water":
                 # Show random water effect message
                 import random as _random
                 water_msgs = [
                     "WIPE OUT",
                     "SURFING THE USA 🇺🇸",
                     "RADICAL SPLASH!",
                     "FOX ON THE ROCKS 🦊❄️",
                     "THE FOX HANGS TEN 🦊"
                 ]
                 chosen_msg = _random.choice(water_msgs)
                 if curses.has_colors():
                     curses.start_color()
                     curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLUE)
                     stdscr.bkgd(' ', curses.color_pair(5))
                 stdscr.clear()
                 max_cols = curses.COLS - 1
                 max_lines = curses.LINES
                 wy = max_lines // 2
                 wave = "🌊" * 8
                 # Animate the message moving across the screen like a wave
                 for offset in range(0, max_cols - len(chosen_msg), 4):
                     stdscr.clear()
                     stdscr.addstr(wy - 1, max((max_cols - len(wave)) // 2, 0), wave)
                     if curses.has_colors():
                         stdscr.addstr(wy, offset, chosen_msg, curses.color_pair(5) | curses.A_BOLD)
                     else:
                         stdscr.addstr(wy, offset, chosen_msg, curses.A_BOLD)
                     stdscr.refresh()
                     time.sleep(0.07)
                 # Finish with the message centered and wave below
                 stdscr.clear()
                 stdscr.addstr(wy - 1, max((max_cols - len(wave)) // 2, 0), wave)
                 wx = max((max_cols - len(chosen_msg)) // 2, 0)
                 if curses.has_colors():
                     stdscr.addstr(wy, wx, chosen_msg, curses.color_pair(5) | curses.A_BOLD)
                 else:
                     stdscr.addstr(wy, wx, chosen_msg, curses.A_BOLD)
                 stdscr.refresh()
                 time.sleep(1)
                 if curses.has_colors():
                     stdscr.bkgd(' ', curses.color_pair(0))
            elif cell in ("heal", "boost", "death"):
                # Item collection animation
                item_names = {
                    "heal": ("🧪", "You picked up a Healing Potion!"),
                    "boost": ("💥", "You picked up an Attack Boost!"),
                    "death": ("💀", "You picked up a Cursed Relic...")
                }
                emoji, msg = item_names.get(cell, (EMOJIS.get(cell, EMOJIS["empty"]), f"You picked up an item!"))
                stdscr.clear()
                max_cols = curses.COLS - 1
                max_lines = curses.LINES
                ey = max_lines // 2 - 1
                ex = max((max_cols - 1) // 2, 0)
                mx = max((max_cols - len(msg)) // 2, 0)
                if cell == "death":
                    # Dramatic cursed relic animation
                    for flicker in range(4):
                        stdscr.clear()
                        if flicker % 2 == 0:
                            stdscr.addstr(ey, ex, emoji, curses.A_BOLD)
                            stdscr.addstr(ey + 2, mx, msg, curses.A_BOLD)
                        stdscr.refresh()
                        time.sleep(0.22)
                    stdscr.clear()
                    stdscr.addstr(ey, ex, emoji, curses.A_BOLD)
                    stdscr.addstr(ey + 2, mx, msg, curses.A_BOLD)
                    stdscr.refresh()
                    time.sleep(1.1)
                else:
                    # Bounce animation for other items
                    for bounce in range(2):
                        stdscr.clear()
                        if bounce % 2 == 0:
                            stdscr.addstr(ey, ex, emoji, curses.A_BOLD)
                            stdscr.addstr(ey + 2, mx, msg, curses.A_BOLD)
                        stdscr.refresh()
                        time.sleep(0.18)
                    stdscr.clear()
                    stdscr.addstr(ey, ex, emoji, curses.A_BOLD)
                    stdscr.addstr(ey + 2, mx, msg, curses.A_BOLD)
                    stdscr.refresh()
                    time.sleep(0.55)
                inventory.append(cell)
                game_map[py][px] = "grass"
        if energy <= 0:
            stdscr.clear()
            stdscr.addstr(MAP_HEIGHT//2, 0, "Game Over! You ran out of energy.")
            stdscr.addstr(MAP_HEIGHT//2+1, 0, "Press any key to restart.")
            stdscr.refresh()
            stdscr.getch()
            # Restart the game
            game_map = create_map()
            px, py = 1, 1
            energy = ENERGY_START
            player_hp = 20
            enemy_hp = 20
            inventory = []
            ambient_animals = []
            last_animal_spawn = time.time()
            continue

if __name__ == "__main__":
    curses.wrapper(main)
