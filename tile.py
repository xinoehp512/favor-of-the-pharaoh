from enums import *


class Tile:
    def __init__(self, name: str, level: int, type: TileType) -> None:
        self.name = name
        self.level = level
        self.type = type

    def __str__(self) -> str:
        return self.name
    __repr__ = __str__


farmer = Tile("FARMER", 3, TileType.YELLOW)
guard = Tile("GUARD", 3, TileType.YELLOW)
indentured_worker = Tile("INDENTURED WORKER", 3, TileType.YELLOW)
serf = Tile("SERF", 3, TileType.YELLOW)
worker = Tile("WORKER", 3, TileType.YELLOW)
beggar = Tile("BEGGAR", 3, TileType.BLUE)
servant = Tile("SERVANT", 3, TileType.BLUE)
soothsayer = Tile("SOOTHSAYER", 3, TileType.BLUE)
ankh = Tile("ANKH", 3, TileType.RED)
omen = Tile("OMEN", 3, TileType.RED)
ancestral_guidance = Tile("ANCESTRAL GUIDANCE", 3, TileType.RED)
artisan = Tile("ARTISAN", 4, TileType.YELLOW)
builder = Tile("BUILDER", 4, TileType.YELLOW)
noble_adoption = Tile("NOBLE ADOPTION", 4, TileType.YELLOW)
palace_servants = Tile("PALACE SERVANTS", 4, TileType.YELLOW)
soldier = Tile("SOLDIER", 4, TileType.YELLOW)
grain_merchant = Tile("GRAIN MERCHANT", 4, TileType.BLUE)
entertainer = Tile("ENTERTAINER", 4, TileType.BLUE)
matchmaker = Tile("MATCHMAKER", 4, TileType.BLUE)
good_omen = Tile("GOOD OMEN", 4, TileType.RED)
palace_key = Tile("PALACE KEY", 4, TileType.RED)
spirit_of_the_dead = Tile("SPIRIT OF THE DEAD", 4, TileType.RED)
charioteer = Tile("CHARIOTEER", 5, TileType.YELLOW)
conspirator = Tile("CONSPIRATOR", 5, TileType.YELLOW)
overseer = Tile("OVERSEER", 5, TileType.YELLOW)
ship_captain = Tile("SHIP CAPTAIN", 5, TileType.YELLOW)
tomb_builder = Tile("TOMB BUILDER", 5, TileType.YELLOW)
head_servant = Tile("HEAD SERVANT", 5, TileType.BLUE)
master_artisan = Tile("MASTER ARTISAN", 5, TileType.BLUE)
priest = Tile("PRIEST", 5, TileType.BLUE)
bad_omen = Tile("BAD OMEN", 5, TileType.RED)
burial_mask = Tile("BURIAL MASK", 5, TileType.RED)
royal_decree = Tile("ROYAL DECREE", 5, TileType.RED)
embalmer = Tile("EMBALMER", 6, TileType.YELLOW)
estate_overseer = Tile("ESTATE OVERSEER", 6, TileType.YELLOW)
grain_trader = Tile("GRAIN TRADER", 6, TileType.YELLOW)
priest_of_the_dead = Tile("PRIEST OF THE DEAD", 6, TileType.YELLOW)
royal_attendents = Tile("ROYAL ATTENDENTS", 6, TileType.YELLOW)
astrologer = Tile("ASTROLOGER", 6, TileType.BLUE)
priestess = Tile("PRIESTESS", 6, TileType.BLUE)
surveyor = Tile("SURVEYOR", 6, TileType.BLUE)
pharaohs_gift = Tile("PHARAOH'S GIFT", 6, TileType.RED)
secret_passage = Tile("SECRET PASSAGE", 6, TileType.RED)
treasure = Tile("TREASURE", 6, TileType.RED)
general = Tile("GENERAL", 7, TileType.YELLOW)
grand_vizier = Tile("GRAND VIZIER", 7, TileType.YELLOW)
granary_master = Tile("GRANARY MASTER", 7, TileType.YELLOW)
heir = Tile("HEIR", 7, TileType.BLUE)
royal_astrologer = Tile("ROYAL ASTROLOGER", 7, TileType.BLUE)
royal_mother = Tile("ROYAL MOTHER", 7, TileType.BLUE)
queens_favor = Tile("QUEEN'S FAVOR", 7, TileType.RED)
royal_death = Tile("ROYAL DEATH", 7, TileType.RED)
royal_power = Tile("ROYAL POWER", 7, TileType.RED)

queen = Tile("QUEEN", 7, TileType.YELLOW)
herder = Tile("HERDER", 1, TileType.YELLOW)
