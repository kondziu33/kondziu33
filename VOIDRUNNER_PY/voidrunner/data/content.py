from dataclasses import dataclass
from random import Random

RARITIES = {
    'Common': (0.60, 1.00), 'Uncommon': (0.22, 1.25), 'Rare': (0.10, 1.55),
    'Epic': (0.055, 1.95), 'Legendary': (0.022, 2.45), 'Mythic': (0.003, 3.2)
}

WEAPONS = [
    ('Pistol', 20, 7.0, 12, 1.2, 40, .04, 1.8), ('SMG', 11, 13.0, 30, 1.8, 34, .06, 1.7),
    ('Assault Rifle', 17, 9.0, 30, 2.0, 55, .05, 1.9), ('Shotgun', 12, 1.2, 6, 2.4, 20, .08, 2.0),
    ('Burst Rifle', 18, 5.0, 24, 1.9, 65, .07, 1.9), ('Sniper', 85, .65, 5, 2.6, 110, .12, 2.2),
    ('Energy Rifle', 25, 6.0, 20, 2.1, 75, .10, 2.0), ('Plasma Cannon', 65, .9, 4, 2.8, 75, .10, 1.9),
    ('Rocket Launcher', 120, .45, 2, 3.0, 70, .0, 1.0), ('Void Gun', 35, 5.0, 18, 2.2, 100, .12, 2.1)
]

POSITIVE = [
    ('Vital Core','max_hp',20),('Swift Core','move_speed_pct',8),('Power Core','damage_pct',12),('Hunter Core','crit_pct',10),
    ('Titan Core','max_hp',25),('Void Core','elite_damage_pct',15),('Runner Core','jump_pct',15),('Regeneration Core','regen',2),
] + [(f'Positive Core {i:02d}', ['damage_pct','armor','stamina','attack_speed_pct','crit_damage_pct','range_pct'][i%6], 4+i%8) for i in range(1,51)]

NEGATIVE = [
    ('Cursed Core','max_hp',-20),('Heavy Core','move_speed_pct',-10),('Weak Core','damage_pct',-15),('Broken Sight','range_pct',-20),
    ('Unstable Core','recoil_pct',25),('Slow Trigger','attack_speed_pct',-20),('Fragile Core','armor',-15)
] + [(f'Cursed Core {i:02d}', ['damage_pct','armor','stamina','attack_speed_pct','crit_damage_pct','range_pct'][i%6], -(3+i%10)) for i in range(1,31)]

HYBRID = [(f'Hybrid Sigil {i:02d}', a, va, b, vb) for i,(a,va,b,vb) in enumerate([
    ('damage_pct',25,'max_hp',-10),('move_speed_pct',30,'armor',-15),('crit_damage_pct',50,'attack_speed_pct',-20),
    ('damage_pct',20,'move_speed_pct',-8),('regen',4,'max_hp',-15),('crit_pct',15,'armor',-10)
]*6,1)]

POTIONS = [(n,e) for n,e in [
    ('Health Potion','heal:30'),('Mega Health','heal:75'),('Speed Potion','temp:move_speed_pct:25:20'),
    ('Damage Potion','temp:damage_pct:40:20'),('Jump Potion','temp:jump_pct:20:20'),('Armor Potion','temp:armor:50:20'),
    ('Critical Potion','temp:crit_pct:25:20'),('Void Potion','temp:damage_pct:100:10:self_hp:-25'),
] + [(f'Cursed Potion {i:02d}', 'temp:curse') for i in range(1,13)]]

ENEMIES = [
    ('Void Drone','flying',80,10,6),('Shard Stalker','melee',100,14,5),('Rift Archer','ranged',90,16,4),('Grav Brute','tank',260,24,2.5),
    ('Phase Assassin','assassin',120,30,8),('Bomber Husk','explosive',70,45,5),('Void Medic','support',110,8,3.5),
    ('Ravager','melee',150,20,5),('Sky Reaver','flying',125,22,7),('Iron Warden','tank',340,32,3),('Plasma Caster','ranged',140,27,5),('Null Beast','melee',210,28,4)
]

LEVELS = [
    ('FLOATING RUINS','ruins'),('GREEN ISLANDS','forest'),('LAVA REALM','lava'),('FROZEN PEAKS','ice'),('ANCIENT TEMPLE','temple'),
    ('TOXIC FACTORY','factory'),('SKY CITY','city'),('VOID CAVERNS','cave'),('STORM ISLANDS','storm'),('VOID FORTRESS','fortress')
]

BOSSES = {3: ('MOLTEN COLOSSUS', 2600), 6: ('TOXIC OVERSEER', 3400), 8: ('CAVERN DEVOURER', 4200), 10: ('THE VOID WARDEN', 6200)}

ACHIEVEMENTS = [
    ('FIRST BLOOD','Kill first enemy'),('VOID RUNNER','Complete Level 1'),('SURVIVOR','Complete a level without dying'),
    ('TREASURE HUNTER','Find 10 secrets'),('LEGENDARY','Find Legendary item'),('ARMED','Unlock all weapons'),('BOSS SLAYER','Defeat first boss'),('VOID MASTER','Finish the game')
] + [(f'CHRONICLE {i:02d}', f'Discover lore fragment {i}') for i in range(1,23)]

@dataclass
class WeaponState:
    name: str
    level: int = 1
    ammo: int = 0
    reserve: int = 999

@dataclass
class ItemInstance:
    name: str
    rarity: str
    kind: str
    stats: tuple
    uid: int

class LootTable:
    def __init__(self, seed=1):
        self.rng = Random(seed)
    def roll(self, items, level, boss=False):
        r = self.rng.random()
        if boss: rarity = 'Legendary' if r > .22 else 'Epic'
        elif r > .997: rarity='Mythic'
        elif r > .975: rarity='Legendary'
        elif r > .91: rarity='Epic'
        elif r > .77: rarity='Rare'
        elif r > .50: rarity='Uncommon'
        else: rarity='Common'
        name, stat, val = self.rng.choice(items)
        mult = RARITIES[rarity][1]*(1+level*.015)
        return ItemInstance(name, rarity, 'stat', (stat, round(val*mult,1)), self.rng.randrange(1,10**9))
