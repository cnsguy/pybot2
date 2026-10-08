from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from core.module import Module
from core.irc_line import IrcSenderUser
from core.config import Config
from random import randint, choice, random

if TYPE_CHECKING:
    from core.irc_bot import IrcBot

START_MAX_HP = 100
START_ATTACK = 15
START_DEFENSE = 5
START_GOLD = 50
START_POTIONS = 3
CRIT_CHANCE = 8
CRIT_MULTIPLIER = 2
LEVEL_XP_BASE = 50
LEVEL_XP_STEP = 30
LEVEL_HP_GAIN = 25
LEVEL_ATTACK_GAIN = 3
LEVEL_DEFENSE_GAIN = 2
LEVEL_MAGIC_GAIN = 3
LEVEL_MANA_GAIN = 20
LEVEL_POTION_GAIN = 1
DEATH_GOLD_DIVISOR = 4
DEATH_HP_DIVISOR = 2
MANA_REGEN_WIN_DIVISOR = 4
ICE_SHIELD_DEFENSE = 8
HEAL_SPELL_HEAL = 30
HEAL_SPELL_SCALING = 2.0


class MonsterType:
    name: str
    hp: int
    attack: int
    xp: int
    gold: int

    def __init__(self, name: str, hp: int, attack: int, xp: int, gold: int) -> None:
        self.name = name
        self.hp = hp
        self.attack = attack
        self.xp = xp
        self.gold = gold


MONSTERS: list[MonsterType] = [
    MonsterType("Slime", 30, 8, 10, 5),
    MonsterType("Goblin", 45, 10, 14, 7),
    MonsterType("Wolf", 60, 13, 18, 9),
    MonsterType("Skeleton", 75, 15, 22, 12),
    MonsterType("Orc", 100, 18, 30, 16),
    MonsterType("Dragon", 150, 22, 60, 50),
]


class SpellDef:
    id: str
    name: str
    mana_cost: int
    base_damage: int
    magic_scaling: float
    description: str
    heal: int
    heal_scaling: float
    defense_boost: int
    drain_ratio: float
    enemy_debuff: float

    def __init__(
        self,
        id: str,
        name: str,
        mana_cost: int,
        base_damage: int,
        magic_scaling: float,
        description: str,
        *,
        heal: int = 0,
        heal_scaling: float = 0.0,
        defense_boost: int = 0,
        drain_ratio: float = 0.0,
        enemy_debuff: float = 1.0,
    ) -> None:
        self.id = id
        self.name = name
        self.mana_cost = mana_cost
        self.base_damage = base_damage
        self.magic_scaling = magic_scaling
        self.description = description
        self.heal = heal
        self.heal_scaling = heal_scaling
        self.defense_boost = defense_boost
        self.drain_ratio = drain_ratio
        self.enemy_debuff = enemy_debuff


SPELLS: dict[str, SpellDef] = {
    "fireball": SpellDef(
        "fireball", "Fireball", 8, 25, 2.0, "Hurls a ball of fire at the enemy"
    ),
    "heal": SpellDef(
        "heal",
        "Heal",
        10,
        0,
        0.0,
        "Restores HP",
        heal=HEAL_SPELL_HEAL,
        heal_scaling=HEAL_SPELL_SCALING,
    ),
    "ice_shield": SpellDef(
        "ice_shield",
        "Ice Shield",
        12,
        0,
        0.0,
        "Boosts your defense for this fight",
        defense_boost=ICE_SHIELD_DEFENSE,
    ),
    "lightning": SpellDef(
        "lightning", "Lightning", 18, 45, 3.0, "Strikes the enemy with lightning"
    ),
    "drain": SpellDef(
        "drain",
        "Life Drain",
        14,
        25,
        1.5,
        "Drains the enemy, healing you",
        drain_ratio=0.5,
    ),
    "frost_nova": SpellDef(
        "frost_nova",
        "Frost Nova",
        20,
        30,
        2.0,
        "Freezes the enemy, halving their attack",
        enemy_debuff=0.5,
    ),
}

SPELL_MILESTONES: dict[int, str] = {
    2: "fireball",
    3: "heal",
    4: "ice_shield",
}

SHOP_CATEGORIES: list[tuple[str, str]] = [
    ("weapon", "Weapons"),
    ("armor", "Armor"),
    ("accessory", "Accessories"),
    ("potion", "Potions"),
    ("scroll", "Scrolls"),
    ("consumable", "Consumables"),
]


class ItemDef:
    name: str
    category: str
    rarity: str
    price: int
    sell_value: int
    description: str
    attack: int
    defense: int
    magic: int
    heal: int
    mana_restore: int
    spell_id: Optional[str] = None
    permanent_attack: int
    permanent_defense: int
    permanent_magic: int

    def __init__(
        self,
        name: str,
        category: str,
        rarity: str,
        price: int,
        sell_value: int,
        description: str,
        *,
        attack: int = 0,
        defense: int = 0,
        magic: int = 0,
        heal: int = 0,
        mana_restore: int = 0,
        spell_id: Optional[str] = None,
        permanent_attack: int = 0,
        permanent_defense: int = 0,
        permanent_magic: int = 0,
    ) -> None:
        self.name = name
        self.category = category
        self.rarity = rarity
        self.price = price
        self.sell_value = sell_value
        self.description = description
        self.attack = attack
        self.defense = defense
        self.magic = magic
        self.heal = heal
        self.mana_restore = mana_restore
        self.spell_id = spell_id
        self.permanent_attack = permanent_attack
        self.permanent_defense = permanent_defense
        self.permanent_magic = permanent_magic


ITEM_CATALOG: list[ItemDef] = [
    ItemDef("Rusty Sword", "weapon", "common", 80, 20, "+3 attack", attack=3),
    ItemDef("Iron Sword", "weapon", "common", 200, 50, "+7 attack", attack=7),
    ItemDef(
        "Steel Greatsword", "weapon", "uncommon", 500, 125, "+14 attack", attack=14
    ),
    ItemDef("Flame Blade", "weapon", "rare", 1200, 300, "+24 attack", attack=24),
    ItemDef("Dragon Slayer", "weapon", "legendary", 3000, 750, "+40 attack", attack=40),
    ItemDef("Leather Vest", "armor", "common", 60, 15, "+2 defense", defense=2),
    ItemDef("Chain Mail", "armor", "common", 180, 45, "+6 defense", defense=6),
    ItemDef("Plate Armor", "armor", "uncommon", 450, 112, "+12 defense", defense=12),
    ItemDef("Mithril Coat", "armor", "rare", 1000, 250, "+20 defense", defense=20),
    ItemDef("Dragon Scale", "armor", "legendary", 2500, 625, "+35 defense", defense=35),
    ItemDef(
        "Ring of Strength", "accessory", "uncommon", 400, 100, "+5 attack", attack=5
    ),
    ItemDef(
        "Ring of Protection", "accessory", "uncommon", 400, 100, "+5 defense", defense=5
    ),
    ItemDef("Amulet of Magic", "accessory", "uncommon", 600, 150, "+8 magic", magic=8),
    ItemDef(
        "Scroll of Fireball",
        "scroll",
        "uncommon",
        200,
        50,
        "Teaches the fireball spell",
        spell_id="fireball",
    ),
    ItemDef(
        "Scroll of Healing",
        "scroll",
        "uncommon",
        200,
        50,
        "Teaches the heal spell",
        spell_id="heal",
    ),
    ItemDef(
        "Scroll of Ice Shield",
        "scroll",
        "uncommon",
        250,
        62,
        "Teaches the ice shield spell",
        spell_id="ice_shield",
    ),
    ItemDef(
        "Scroll of Lightning",
        "scroll",
        "rare",
        500,
        125,
        "Teaches the lightning spell",
        spell_id="lightning",
    ),
    ItemDef(
        "Scroll of Life Drain",
        "scroll",
        "rare",
        500,
        125,
        "Teaches the life drain spell",
        spell_id="drain",
    ),
    ItemDef(
        "Scroll of Frost Nova",
        "scroll",
        "rare",
        600,
        150,
        "Teaches the frost nova spell",
        spell_id="frost_nova",
    ),
    ItemDef("Potion", "potion", "common", 40, 10, "Restores 50 HP", heal=50),
    ItemDef(
        "Mana Potion", "potion", "common", 50, 12, "Restores 30 mana", mana_restore=30
    ),
    ItemDef(
        "Greater Potion", "potion", "uncommon", 120, 30, "Restores 120 HP", heal=120
    ),
    ItemDef(
        "Elixir of Power",
        "consumable",
        "rare",
        800,
        200,
        "Permanently increases attack by 2",
        permanent_attack=2,
    ),
    ItemDef(
        "Elixir of Fortitude",
        "consumable",
        "rare",
        800,
        200,
        "Permanently increases defense by 2",
        permanent_defense=2,
    ),
    ItemDef(
        "Elixir of Wisdom",
        "consumable",
        "rare",
        1000,
        250,
        "Permanently increases magic by 3",
        permanent_magic=3,
    ),
]

LOOT_TABLES: dict[str, list[tuple[str, float]]] = {
    "Slime": [("Mana Potion", 0.15), ("Potion", 0.10)],
    "Goblin": [("Iron Sword", 0.05), ("Mana Potion", 0.12), ("Potion", 0.10)],
    "Wolf": [("Leather Vest", 0.10), ("Ring of Strength", 0.03)],
    "Skeleton": [
        ("Scroll of Lightning", 0.06),
        ("Chain Mail", 0.08),
        ("Mana Potion", 0.15),
    ],
    "Orc": [
        ("Steel Greatsword", 0.05),
        ("Plate Armor", 0.05),
        ("Greater Potion", 0.10),
    ],
    "Dragon": [
        ("Flame Blade", 0.12),
        ("Dragon Scale", 0.08),
        ("Scroll of Frost Nova", 0.10),
    ],
}


class Enemy(Config):
    name: str
    level: int
    max_hp: int
    hp: int
    attack: int
    xp: int
    gold: int


class Player(Config):
    level: int = 1
    max_hp: int = START_MAX_HP
    hp: int = START_MAX_HP
    attack: int = START_ATTACK
    defense: int = START_DEFENSE
    magic: int = 0
    max_mana: int = 0
    mana: int = 0
    xp: int = 0
    gold: int = START_GOLD
    inventory: dict[str, int] = {}
    equipped_weapon: Optional[str] = None
    equipped_armor: Optional[str] = None
    equipped_accessory: Optional[str] = None
    known_spells: list[str] = []
    shield_active: bool = False
    enemy_attack_debuff: float = 1.0
    enemy: Optional[Enemy] = None


class ModuleConfig(Config):
    players: dict[str, Player] = {}


def xp_to_next(level: int) -> int:
    return LEVEL_XP_BASE + (level - 1) * LEVEL_XP_STEP


def spawn_enemy(level: int) -> Enemy:
    monster = choice(MONSTERS)
    max_hp = monster.hp * level

    return Enemy(
        name=monster.name,
        level=level,
        max_hp=max_hp,
        hp=max_hp,
        attack=monster.attack + level * 3,
        xp=monster.xp * level,
        gold=monster.gold * level,
    )


def new_player() -> Player:
    return Player(inventory={"Potion": START_POTIONS})


def find_item(name: str) -> Optional[ItemDef]:
    lower = name.lower()

    for item in ITEM_CATALOG:
        if item.name.lower() == lower:
            return item

    return None


def find_spell(spell_id: str) -> Optional[SpellDef]:
    return SPELLS.get(spell_id.lower(), None)


def add_item(player: Player, item_name: str, amount: int = 1) -> None:
    player.inventory[item_name] = player.inventory.get(item_name, 0) + amount


def remove_item(player: Player, item_name: str, amount: int = 1) -> bool:
    current = player.inventory.get(item_name, 0)

    if current < amount:
        return False

    if current == amount:
        del player.inventory[item_name]
    else:
        player.inventory[item_name] = current - amount

    return True


def drop_loot(enemy: Enemy, player: Player) -> Optional[str]:
    loot_table = LOOT_TABLES.get(enemy.name, [])

    for item_name, chance in loot_table:
        if random() < chance:
            add_item(player, item_name)
            return item_name

    return None


class ModuleMain(Module):
    config: ModuleConfig

    def __init__(self, name: str, bot: IrcBot) -> None:
        super().__init__(name, bot)
        self.config = self.read_config(ModuleConfig)

        self.register_irc_command_handler(
            "rpg_start", self.handle_rpg_start, None, "Start a new RPG game"
        )
        self.register_irc_command_handler(
            "rpg_status", self.handle_rpg_status, None, "Show your RPG status"
        )
        self.register_irc_command_handler(
            "rpg_explore",
            self.handle_rpg_explore,
            None,
            "Search for a monster to fight",
        )
        self.register_irc_command_handler(
            "rpg_attack", self.handle_rpg_attack, None, "Attack the current monster"
        )
        self.register_irc_command_handler(
            "rpg_cast",
            self.handle_rpg_cast,
            "<spell>",
            "Cast a spell",
            min_args=1,
        )
        self.register_irc_command_handler(
            "rpg_heal",
            self.handle_rpg_heal,
            None,
            "Drink a potion to restore HP",
        )
        self.register_irc_command_handler(
            "rpg_spells", self.handle_rpg_spells, None, "List your known spells"
        )
        self.register_irc_command_handler(
            "rpg_inventory",
            self.handle_rpg_inventory,
            None,
            "Show your inventory",
        )
        self.register_irc_command_handler(
            "rpg_equip",
            self.handle_rpg_equip,
            "<item>",
            "Equip a weapon, armor or accessory",
            min_args=1,
        )
        self.register_irc_command_handler(
            "rpg_unequip",
            self.handle_rpg_unequip,
            "<weapon|armor|accessory>",
            "Unequip an item slot",
            min_args=1,
        )
        self.register_irc_command_handler(
            "rpg_shop", self.handle_rpg_shop, None, "Show the shop"
        )
        self.register_irc_command_handler(
            "rpg_buy",
            self.handle_rpg_buy,
            "<item>",
            "Buy an item from the shop",
            min_args=1,
        )
        self.register_irc_command_handler(
            "rpg_sell",
            self.handle_rpg_sell,
            "<item>",
            "Sell an item from your inventory",
            min_args=1,
        )
        self.register_irc_command_handler(
            "rpg_use",
            self.handle_rpg_use,
            "<item>",
            "Use a scroll, potion or elixir",
            min_args=1,
        )

    def get_player(self, nick: str, channel: str) -> Optional[Player]:
        player = self.config.players.get(nick, None)

        if player is None:
            self.bot.send_message(
                channel, "You haven't started a game yet. Use rpg_start."
            )

        return player

    def effective_attack(self, player: Player) -> int:
        bonus = 0
        item = find_item(player.equipped_weapon) if player.equipped_weapon else None
        if item is not None:
            bonus += item.attack
        item = (
            find_item(player.equipped_accessory) if player.equipped_accessory else None
        )
        if item is not None:
            bonus += item.attack
        return player.attack + bonus

    def effective_defense(self, player: Player) -> int:
        bonus = 0
        item = find_item(player.equipped_armor) if player.equipped_armor else None
        if item is not None:
            bonus += item.defense
        item = (
            find_item(player.equipped_accessory) if player.equipped_accessory else None
        )
        if item is not None:
            bonus += item.defense
        if player.shield_active:
            bonus += ICE_SHIELD_DEFENSE
        return player.defense + bonus

    def effective_magic(self, player: Player) -> int:
        magic = player.magic
        item = (
            find_item(player.equipped_accessory) if player.equipped_accessory else None
        )
        if item is not None:
            magic += item.magic
        return magic

    def restore_mana(self, player: Player, amount: int) -> int:
        restored = min(player.max_mana - player.mana, amount)
        player.mana += restored
        return restored

    def complete_fight(self, player: Player) -> None:
        player.enemy = None
        player.shield_active = False
        player.enemy_attack_debuff = 1.0

    def format_status_lines(self, player: Player) -> list[str]:
        weapon = player.equipped_weapon
        armor = player.equipped_armor
        accessory = player.equipped_accessory

        weapon_item = find_item(weapon) if weapon is not None else None
        armor_item = find_item(armor) if armor is not None else None

        weapon_str = (
            f"{weapon} (+{weapon_item.attack} atk)"
            if weapon_item is not None
            else "None"
        )
        armor_str = (
            f"{armor} (+{armor_item.defense} def)" if armor_item is not None else "None"
        )

        lines = [
            " | ".join(
                [
                    f"Lv {player.level}",
                    f"HP {player.hp}/{player.max_hp}",
                    f"Mana {player.mana}/{player.max_mana}",
                    f"XP {player.xp}/{xp_to_next(player.level)}",
                    f"Gold {player.gold}",
                    f"Atk {self.effective_attack(player)}",
                    f"Def {self.effective_defense(player)}",
                    f"Mag {self.effective_magic(player)}",
                ]
            ),
            f"Equipped: Weapon: {weapon_str} | Armor: {armor_str} | Accessory: {accessory or 'None'}",
        ]

        enemy = player.enemy

        if enemy is not None:
            lines.append(
                f"Fighting {enemy.name} (Lv {enemy.level}) "
                f"{enemy.hp}/{enemy.max_hp} HP"
            )

        return lines

    def advance_level(self, player: Player) -> list[str]:
        messages = []

        while player.xp >= xp_to_next(player.level):
            player.xp -= xp_to_next(player.level)
            player.level += 1
            player.max_hp += LEVEL_HP_GAIN
            player.hp = player.max_hp
            player.attack += LEVEL_ATTACK_GAIN
            player.defense += LEVEL_DEFENSE_GAIN
            player.max_mana += LEVEL_MANA_GAIN
            player.mana = player.max_mana
            player.magic += LEVEL_MAGIC_GAIN
            add_item(player, "Potion", LEVEL_POTION_GAIN)

            gain_line = (
                f"You reached level {player.level}! HP, attack and defense "
                f"increased, you got a Potion, and your mana is full."
            )

            if player.level >= 2:
                gain_line += f" Magic increased to {player.magic}."

            spell_id = SPELL_MILESTONES.get(player.level, None)

            if spell_id is not None and spell_id not in player.known_spells:
                player.known_spells.append(spell_id)
                spell = SPELLS[spell_id]
                gain_line += f" You learned {spell.name}!"

            messages.append(gain_line)

        return messages

    async def handle_rpg_start(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = new_player()
        self.config.players[sender.nick] = player
        self.write_config(self.config)

        for line in self.format_status_lines(player):
            self.bot.send_message(
                channel,
                f"A new adventure begins for {sender.nick}! {line}",
            )

        self.bot.send_message(
            channel,
            "Commands: rpg_attack, rpg_cast <spell>, rpg_explore, rpg_heal, "
            "rpg_spells, rpg_inventory, rpg_equip, rpg_shop, rpg_buy. "
            "Good luck!",
        )

    async def handle_rpg_status(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        for line in self.format_status_lines(player):
            self.bot.send_message(channel, line)

    async def handle_rpg_explore(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        if player.enemy is not None:
            self.bot.send_message(
                channel, f"You are already fighting the {player.enemy.name}."
            )
            return

        mana_restored = self.restore_mana(player, player.max_mana)

        if mana_restored > 0:
            self.bot.send_message(
                channel, f"Your arcane energy returns, restoring {mana_restored} mana."
            )

        player.enemy = spawn_enemy(player.level)
        self.write_config(self.config)
        self.bot.send_message(
            channel,
            f"A {player.enemy.name} (Lv {player.enemy.level}) appears "
            f"with {player.enemy.hp} HP! Use rpg_attack or rpg_cast to fight it.",
        )

    async def handle_rpg_attack(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        enemy = player.enemy

        if enemy is None:
            self.bot.send_message(
                channel,
                "There is nothing to attack. Use rpg_explore to find a monster.",
            )
            return

        messages = []
        attacker = self.effective_attack(player)
        damage = randint(attacker // 2, attacker * 2)

        if randint(1, CRIT_CHANCE) == 1:
            damage *= CRIT_MULTIPLIER
            messages.append(
                f"CRITICAL HIT! You smash the {enemy.name} for {damage} damage!"
            )
        else:
            messages.append(f"You hit the {enemy.name} for {damage} damage.")

        self.resolve_attack(player, enemy, damage, messages)

        if enemy.hp > 0:
            self.enemy_counterattack(player, enemy, messages)

        self.write_config(self.config)

        for message in messages:
            self.bot.send_message(channel, message)

    async def handle_rpg_cast(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        spell_id = args[0].lower()
        spell = find_spell(spell_id)

        if spell is None:
            self.bot.send_message(
                channel,
                f"No such spell '{spell_id}'. Use rpg_spells to see what you know.",
            )
            return

        if spell_id not in player.known_spells:
            self.bot.send_message(channel, f"You don't know the {spell.name} spell.")
            return

        if player.mana < spell.mana_cost:
            self.bot.send_message(
                channel,
                f"Not enough mana. You need {spell.mana_cost} mana and have {player.mana}.",
            )
            return

        enemy = player.enemy

        if enemy is None and spell.id != "heal":
            self.bot.send_message(
                channel, "There is nothing to fight. Use rpg_explore to find a monster."
            )
            return

        player.mana -= spell.mana_cost
        messages = []
        magic = self.effective_magic(player)

        if spell.base_damage > 0:
            assert enemy is not None

            damage = spell.base_damage + round(magic * spell.magic_scaling)
            messages.append(
                f"You cast {spell.name} on the {enemy.name} for {damage} damage!"
            )

            self.resolve_attack(player, enemy, damage, messages)

            if spell.drain_ratio > 0 and player.hp < player.max_hp:
                drained = round(damage * spell.drain_ratio)
                healed = min(drained, player.max_hp - player.hp)
                player.hp += healed
                messages.append(f"You drain the {enemy.name}, restoring {healed} HP.")

            if enemy.hp > 0 and spell.enemy_debuff < 1.0:
                player.enemy_attack_debuff = spell.enemy_debuff
                messages.append(f"The {enemy.name} is frozen and enfeebled!")

        elif spell.heal > 0:
            healed = min(
                spell.heal + round(magic * spell.heal_scaling),
                player.max_hp - player.hp,
            )
            player.hp += healed
            messages.append(f"You cast {spell.name} and restore {healed} HP.")

        elif spell.defense_boost > 0:
            if player.shield_active:
                messages.append("You are already protected by the Ice Shield.")
            else:
                player.shield_active = True
                messages.append(
                    f"An arcane shield forms around you, boosting your defense by "
                    f"{spell.defense_boost} for this fight."
                )

        if enemy is not None and enemy.hp > 0 and player.hp > 0:
            self.enemy_counterattack(player, enemy, messages)

        self.write_config(self.config)

        for message in messages:
            self.bot.send_message(channel, message)

    def resolve_attack(
        self,
        player: Player,
        enemy: Enemy,
        damage: int,
        messages: list[str],
    ) -> None:
        enemy.hp -= damage

        if enemy.hp <= 0:
            player.xp += enemy.xp
            player.gold += enemy.gold
            messages.append(
                f"You defeated the {enemy.name}! You gain {enemy.xp} XP "
                f"and {enemy.gold} gold."
            )

            dropped = drop_loot(enemy, player)

            if dropped is not None:
                messages.append(f"The {enemy.name} dropped a {dropped}!")

            mana_restored = self.restore_mana(
                player, player.max_mana // MANA_REGEN_WIN_DIVISOR
            )

            if mana_restored > 0:
                messages.append(
                    f"You catch your breath, restoring {mana_restored} mana."
                )

            self.complete_fight(player)
            messages.extend(self.advance_level(player))

    def enemy_counterattack(
        self, player: Player, enemy: Enemy, messages: list[str]
    ) -> None:
        debuffed_attack = round(enemy.attack * player.enemy_attack_debuff)
        enemy_damage = max(
            1,
            randint(debuffed_attack // 2, debuffed_attack)
            - self.effective_defense(player) // 2,
        )
        player.hp = max(0, player.hp - enemy_damage)
        messages.append(f"The {enemy.name} hits you for {enemy_damage} damage.")

        if player.hp == 0:
            lost_gold = player.gold // DEATH_GOLD_DIVISOR
            player.gold -= lost_gold
            player.hp = player.max_hp // DEATH_HP_DIVISOR
            player.mana = player.max_mana
            self.complete_fight(player)

            messages.append(
                f"You were defeated and dropped {lost_gold} gold, limping back "
                f"to camp with {player.hp} HP. Your mana regenerates fully."
            )

    async def handle_rpg_heal(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        if player.hp >= player.max_hp:
            self.bot.send_message(channel, "You are already at full health.")
            return

        if not remove_item(player, "Potion"):
            self.bot.send_message(
                channel, "You don't have any Potions. Use rpg_buy or rpg_shop."
            )
            return

        healed = min(50, player.max_hp - player.hp)
        player.hp += healed
        self.write_config(self.config)
        self.bot.send_message(channel, f"You drink a Potion and restore {healed} HP.")

    async def handle_rpg_spells(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        if len(player.known_spells) == 0:
            self.bot.send_message(
                channel,
                "You know no spells yet. Level up or use a scroll to learn one.",
            )
            return

        spells = []

        for spell_id in player.known_spells:
            spell = SPELLS[spell_id]
            spells.append(f"{spell.name} [{spell.mana_cost} MP]")

        self.bot.send_message(channel, "Spells: " + " | ".join(spells))

    async def handle_rpg_inventory(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        if len(player.inventory) == 0:
            self.bot.send_message(channel, "Your bag is empty.")
        else:
            contents = []

            for item_name, count in player.inventory.items():
                contents.append(f"{item_name} x{count}")

            self.bot.send_message(channel, "Bag: " + " | ".join(contents))

        self.bot.send_message(
            channel,
            f"Equipped: Weapon={player.equipped_weapon or 'None'} | "
            f"Armor={player.equipped_armor or 'None'} | "
            f"Accessory={player.equipped_accessory or 'None'}",
        )

    async def handle_rpg_equip(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        item_name = " ".join(args)
        item = find_item(item_name)

        if item is None:
            self.bot.send_message(channel, f"No such item '{item_name}'.")
            return

        if item.category not in ("weapon", "armor", "accessory"):
            self.bot.send_message(channel, f"The {item.name} can't be equipped.")
            return

        if not remove_item(player, item.name):
            self.bot.send_message(
                channel, f"You don't have a {item.name}. Use rpg_buy to get one."
            )
            return

        slot: Optional[str] = None

        if item.category == "weapon":
            slot = player.equipped_weapon
            player.equipped_weapon = item.name
        elif item.category == "armor":
            slot = player.equipped_armor
            player.equipped_armor = item.name
        else:
            slot = player.equipped_accessory
            player.equipped_accessory = item.name

        if slot is not None:
            add_item(player, slot)
            self.bot.send_message(
                channel, f"You equip the {item.name}, returning {slot} to your bag."
            )
        else:
            self.bot.send_message(channel, f"You equip the {item.name}.")

        self.write_config(self.config)

    async def handle_rpg_unequip(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        slot = args[0].lower()

        if slot not in ("weapon", "armor", "accessory"):
            self.bot.send_message(
                channel, "Specify weapon, armor or accessory to unequip."
            )
            return

        if slot == "weapon":
            item_name = player.equipped_weapon
            player.equipped_weapon = None
        elif slot == "armor":
            item_name = player.equipped_armor
            player.equipped_armor = None
        else:
            item_name = player.equipped_accessory
            player.equipped_accessory = None

        if item_name is None:
            self.bot.send_message(channel, "Nothing is equipped in that slot.")
            return

        add_item(player, item_name)
        self.write_config(self.config)
        self.bot.send_message(channel, f"You unequip the {item_name}.")

    async def handle_rpg_shop(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        for category, label in SHOP_CATEGORIES:
            items = [item for item in ITEM_CATALOG if item.category == category]

            if len(items) == 0:
                continue

            listing = " | ".join(f"{item.name} {item.price}g" for item in items)

            self.bot.send_message(channel, f"{label}: {listing}")

    async def handle_rpg_buy(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        item_name = " ".join(args)
        item = find_item(item_name)

        if item is None:
            self.bot.send_message(channel, f"No such item '{item_name}'.")
            return

        if item.price <= 0:
            self.bot.send_message(channel, f"The {item.name} is not for sale.")
            return

        if player.gold < item.price:
            self.bot.send_message(
                channel,
                f"You need {item.price} gold for a {item.name}, "
                f"and have {player.gold} gold.",
            )
            return

        player.gold -= item.price
        add_item(player, item.name)
        self.write_config(self.config)

        hint = ""

        if item.category == "weapon":
            hint = f" Equip it with rpg_equip {item.name}."
        elif item.category == "scroll":
            hint = f" Use it with rpg_use {item.name}."

        self.bot.send_message(
            channel, f"You buy a {item.name} for {item.price} gold.{hint}"
        )

    async def handle_rpg_sell(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        item_name = " ".join(args)
        item = find_item(item_name)

        if item is None:
            self.bot.send_message(channel, f"No such item '{item_name}'.")
            return

        if not remove_item(player, item.name):
            self.bot.send_message(channel, f"You don't have a {item.name} to sell.")
            return

        player.gold += item.sell_value
        self.write_config(self.config)
        self.bot.send_message(
            channel, f"You sell a {item.name} for {item.sell_value} gold."
        )

    async def handle_rpg_use(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        player = self.get_player(sender.nick, channel)

        if player is None:
            return

        item_name = " ".join(args)
        item = find_item(item_name)

        if item is None:
            self.bot.send_message(channel, f"No such item '{item_name}'.")
            return

        if item.category not in ("scroll", "potion", "consumable"):
            self.bot.send_message(channel, f"You can't use the {item.name} like that.")
            return

        if not remove_item(player, item.name):
            self.bot.send_message(channel, f"You don't have a {item.name} to use.")
            return

        result = ""

        if item.category == "scroll" and item.spell_id is not None:
            spell_id = item.spell_id

            if spell_id in player.known_spells:
                add_item(player, item.name)
                result = f"You already know the {item.name} spell."
            else:
                player.known_spells.append(spell_id)
                spell = SPELLS[spell_id]
                result = f"You read the {item.name} and learn the {spell.name} spell!"

        elif item.category == "potion":
            can_heal = item.heal > 0 and player.hp < player.max_hp
            can_mana = (
                item.mana_restore > 0
                and player.max_mana > 0
                and player.mana < player.max_mana
            )

            if not can_heal and not can_mana:
                add_item(player, item.name)
                result = "The potion would have no effect right now, so you save it."
            else:
                messages = []

                if can_heal:
                    healed = min(item.heal, player.max_hp - player.hp)
                    player.hp += healed
                    messages.append(f"You restore {healed} HP.")

                if can_mana:
                    restored = self.restore_mana(player, item.mana_restore)
                    messages.append(f"You restore {restored} mana.")

                result = " ".join(messages)

        elif item.category == "consumable":
            if item.permanent_attack > 0:
                player.attack += item.permanent_attack
                result = (
                    f"Your attack permanently increases by {item.permanent_attack}!"
                )
            elif item.permanent_defense > 0:
                player.defense += item.permanent_defense
                result = (
                    f"Your defense permanently increases by {item.permanent_defense}!"
                )
            elif item.permanent_magic > 0:
                player.magic += item.permanent_magic
                result = f"Your magic permanently increases by {item.permanent_magic}!"
            else:
                add_item(player, item.name)
                result = f"The {item.name} has no effect."

        self.write_config(self.config)
        self.bot.send_message(channel, result)
