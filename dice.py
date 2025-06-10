import random
from enums import *


class PipUpException(Exception):
    ...


class Die:
    def __init__(self, dice_type: DiceType, face_pairs: list[tuple[DiceFace, DiceFace]], starting_face: DiceFace = DiceFace.NULL) -> None:
        self.dice_type = dice_type
        self.face_pairs = face_pairs
        self.starting_value = starting_face
        self.face = starting_face

    def clone(self):
        return Die(self.dice_type, self.face_pairs, starting_face=self.starting_value)

    @property
    def faces(self):
        return [face for pair in self.face_pairs for face in pair]

    @property
    def can_pipup(self):
        if self.face == DiceFace.NULL:
            return False
        return self.has_value(one_higher(to_value(self.face)))

    def get_flipped(self, face: DiceFace):
        if not self.has_face(face):
            raise Exception(f"Face {face} not on dice {self.dice_type}.")
        for face_pair in self.face_pairs:
            if face in face_pair:
                return face_pair[1-face_pair.index(face)]

    def has_face(self, face: DiceFace) -> bool:
        return face in self.faces

    def has_value(self, value: DiceValue) -> bool:
        return value is not DiceValue.NULL and value in [to_value(face) for face in self.faces]

    def roll(self):
        self.face = random.choice(self.faces)
        return self.face

    def pipup(self):
        if not self.can_pipup:
            raise PipUpException(f"Can't Pipup {self.face} on {self.dice_type}")
        new_value = one_higher(to_value(self.face))
        for face in self.faces:
            if to_value(face) == new_value:
                self.set_face(face)
                return

    def set_face(self, face: DiceFace):
        if face not in self.faces:
            raise Exception(f"Face {face} not on dice {self.dice_type}.")
        self.face = face
        return self

    def __str__(self) -> str:
        return f"{self.dice_type.name} {self.face.name}"
    __repr__ = __str__


standard = Die(DiceType.STANDARD, [(DiceFace.ONE, DiceFace.SIX), (DiceFace.TWO, DiceFace.FIVE), (DiceFace.THREE, DiceFace.FOUR)])
immediate = Die(DiceType.IMMEDIATE, [(DiceFace.ONE, DiceFace.SIX), (DiceFace.TWO, DiceFace.FIVE), (DiceFace.THREE, DiceFace.FOUR)])
serf = Die(DiceType.SERF, [(DiceFace.ONE, DiceFace.TWO), (DiceFace.TWO, DiceFace.ONE), (DiceFace.THREE, DiceFace.FOUR)])
noble = Die(DiceType.NOBLE, [(DiceFace.THREE, DiceFace.FOUR), (DiceFace.FIVE, DiceFace.SIX), (DiceFace.SIX, DiceFace.FIVE)])
artisan = Die(DiceType.ARTISAN, [(DiceFace.STAR_ONE, DiceFace.SIX), (DiceFace.TWO, DiceFace.FIVE), (DiceFace.THREE, DiceFace.FOUR)])
intrigue = Die(DiceType.INTRIGUE, [(DiceFace.ONE, DiceFace.TWO_STAR), (DiceFace.TWO, DiceFace.FIVE), (DiceFace.THREE, DiceFace.FOUR)])
voyage = Die(DiceType.VOYAGE, [(DiceFace.STAR, DiceFace.ADD_TWO), (DiceFace.REROLL, DiceFace.BLANK), (DiceFace.REROLL, DiceFace.BLANK)])
decree = Die(DiceType.DECREE, [(DiceFace.STAR_DECREE, DiceFace.SIX), (DiceFace.TWO, DiceFace.FIVE), (DiceFace.THREE, DiceFace.FOUR)])
all_dice = [standard, immediate, serf, noble, artisan, intrigue, voyage, decree]
dice_dict = {DiceType.STANDARD: standard,
             DiceType.IMMEDIATE: immediate,
             DiceType.SERF: serf,
             DiceType.NOBLE: noble,
             DiceType.ARTISAN: artisan,
             DiceType.INTRIGUE: intrigue,
             DiceType.VOYAGE: voyage,
             DiceType.DECREE: decree}


def get_die(type: DiceType):
    return dice_dict[type].clone()
