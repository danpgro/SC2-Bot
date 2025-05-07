import sc2
import math
import random
from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.player import Bot, Computer
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit

class CompetitiveBot(BotAI):
    NAME: str = "Hahaproxy4gate"
    """This bot's name"""

    RACE: Race = Race.Protoss
    """This bot's Starcraft 2 race.

    Options are:
        Race.Terran
        Race.Zerg
        Race.Protoss
        Race.Random
    """

    def produceProbes(self,targetCount) -> None:
        if self.can_afford(UnitTypeId.PROBE) and self.supply_workers < targetCount:
            self.train(UnitTypeId.PROBE)

    async def buildPylon(self) -> None:
        availableWorker = self.workers.filter(lambda worker: (worker.is_collecting or worker.is_idle) and worker.tag not in self.unit_tags_received_action)
        if availableWorker:
            map_center = self.game_info.map_center
            placementAnchor = self.start_location.towards(map_center, distance=7)
            placementPosition = await self.find_placement(UnitTypeId.PYLON, near=placementAnchor, placement_step=1)
            if placementPosition:
                workerToBuild = availableWorker.closest_to(placementPosition)
                workerToBuild.build(UnitTypeId.PYLON, placementPosition)

                print(placementPosition)

    async def buildOrderProxy4gate(self) -> None:
        print("Proxy4gated")

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        buildList = [self.buildOrderProxy4gate]
        buildOrder = random.choice(buildList)
        print("Game started")
        print("Build order selected: " + buildOrder.__name__)

    async def on_step(self, iteration: int) -> None:
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """

        if self.can_afford(UnitTypeId.PYLON) and self.already_pending(UnitTypeId.GATEWAY) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.GATEWAY and structure.is_ready).amount == 0:
            await self.buildPylon()
            
        self.produceProbes(16)

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
