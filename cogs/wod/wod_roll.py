from .true_random import D10Pool


class WoDDice:
    def __init__(self, result: int, additional: bool):
        self.result: int = result
        self.additional: bool = additional


class WoDRoll:
    def __init__(self, count: int, difficulty: int, mod: int = 0):
        self.count: int = count
        self.difficulty: int = difficulty
        self.mod: int = mod
        self.additional_dice: int = 0
        self.results: list[list[WoDDice]] = []

    @property
    def pool(self) -> int:
        return self.count + self.mod + self.additional_dice

    @property
    def blind(self) -> bool:
        return self.pool < 1

    @property
    def success_count(self) -> int:
        difficulty = 10 if self.blind else self.difficulty
        return sum(sum(1 if d.result >= difficulty else 0 for d in row) for row in self.results)

    async def execute(self, pool: D10Pool):
        self.results.clear()
        for _ in range(max(1, self.pool)):
            await self.add_dice(pool, additional=False)

    async def add_dice(self, pool: D10Pool, *, additional: bool = True):
        if additional:
            if self.blind:
                if self.pool == 0:
                    self.results.clear()
                else:
                    self.additional_dice += 1
                    return
            self.additional_dice += 1

        i = 0
        while True:
            dice = WoDDice(await pool.next(), additional)
            if i == len(self.results):
                self.results.append([])
            self.results[i].append(dice)
            if dice.result != 10:
                break
            i += 1
