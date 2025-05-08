import math
import random
from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.player import Bot, Computer
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2, Pointlike

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

    def speedMiningPositions(self, workerRadius : float) -> dict:
        positionsMapping = {}
        for base in self.expansion_locations_dict:
            for resource in self.expansion_locations_dict[base]:
                miningRadius = 1.325
                target = resource.position.towards(base.position, miningRadius)

                positionsMapping.update({resource.position:target})
        
        return positionsMapping

    def closestMineral(self,miner : Unit) -> Unit:
        closestBaseDist = 1000
        for base in self.expansion_locations_dict:
            if miner.distance_to(base.position) < closestBaseDist:
                closestBaseDist = miner.distance_to(base.position)
                closestBase = base
        
        closestMineralDist = 1000
        for resource in self.expansion_locations_dict[closestBase]:
            if miner.distance_to(resource.position) < closestMineralDist:
                closestMineralDist = miner.distance_to(resource.position)
                closestMineral = resource
        
        return closestMineral

    def getResourceFromWorkerOrder(self,targetTag) -> Unit:
        for base in self.expansion_locations_dict:
            for resource in self.expansion_locations_dict[base]:
                if targetTag == resource.tag:
                    return resource

    def speedMineWorker(self, worker :Unit):
            target = None
            townhall = self.townhalls.closest_to(worker.position)
            
            if worker.is_carrying_minerals:
                target = townhall.position.towards(worker.position,(townhall.radius + worker.radius))

            elif worker.is_gathering:
                resource = self.getResourceFromWorkerOrder(worker.order_target)
                if resource.position in speedMiningPositionMap:
                    target = speedMiningPositionMap[resource.position]
                else:
                    for unit in self.units(UnitTypeId.ASSIMILATOR):
                        if unit.tag == worker.order_target:
                            target = unit.position.towards(townhall.position,unit.radius + worker.radius)
                
            if target != None:
                if worker.distance_to(target) < 2:
                    if worker.distance_to(target) > 0.5:
                        worker.move(target)
                        if worker.is_carrying_minerals:
                            worker.smart(townhall, True)
                        else:
                            worker.gather(resource, True)

    def produceProbes(self,targetCount: int = 200) -> None:
        if self.can_afford(UnitTypeId.PROBE) and self.supply_workers < targetCount:
            self.train(UnitTypeId.PROBE)

    def buildWithProbe(self, structure, placementPosition, queue = False, worker = None, move = False, idle = False) -> Unit | None:

        if worker == None:
            worker = self.getWorker(placementPosition)

        if worker:
            if self.can_afford(structure):
                worker.build(structure, placementPosition, queue)
            elif move:
                worker.move(placementPosition)

        if idle == False:
            if worker.is_idle:
                closestMineral = self.mineral_field.closest_to(worker.position)
                worker.gather(closestMineral)
        
        return worker

    async def avoidSupplyCap(self, supplyRemainingLimit: int) -> None:
        if (self.supply_left < supplyRemainingLimit):
            map_center = self.game_info.map_center
            placement_aproximation = self.start_location.towards(map_center, distance=5)
            placement = await self.find_placement(UnitTypeId.PYLON, near=placement_aproximation, placement_step=1)
            self.buildWithProbe(UnitTypeId.PYLON,placement)

    def getWorker(self, placementPosition, performingAction = False) -> Unit | None:
        if performingAction == False:
            availableWorker = self.workers.filter(lambda worker: (worker.is_collecting or worker.is_idle) and worker.tag not in self.unit_tags_received_action)
        elif performingAction:
            availableWorker = self.workers.filter(lambda worker: (worker.is_collecting or worker.is_idle))
        
        if availableWorker:
            workerToBuild = availableWorker.closest_to(placementPosition)
            return workerToBuild

    async def getNearestExpoFromPoint(self,startPoint) -> Point2:
        closest = None
        distance = math.inf
        for expansion in self.expansion_locations_list:

            pathedDistance = await self.client.query_pathing(startPoint, expansion)
            if pathedDistance is None:
                continue

            if pathedDistance < distance:
                distance = pathedDistance
                closest = expansion

        return closest

    async def getEnemyNatural(self) -> Point2 :
        enemyNatural = await self.getNearestExpoFromPoint(self.enemy_start_locations[0])
        return enemyNatural
     
    async def getEnemyThird(self) -> Point2 :
        enemyThird = await self.getNearestExpoFromPoint(self.enemyNatural)
        return enemyThird

    async def buildOrderProxy4gate(self) -> None:
        ## (0) Produce a worker 
        ## (1) First produced worker  places a proxy pylon (Produce probes until supply cap)
        ## Pylon should avoid the routes and direct lines from enemy main to my natural and my main to avoid overlord scouting
        ## (2) When pylon completes, place 4 gateways (As minerals become available) around the pylon to cover it's entire surface area
        ## (3)  {   Resume probe production to saturation (17)
        ##          Produce zealots for remainder of game
        ##          Avoid supply capping (1 full zealot spawn = 1 entire pylon)
        ##          When zealots = 4 push into their base and kill 'em

        if self.buildOrderStep == 0:
            self.produceProbes(13)
            if self.supply_workers == 13:
                self.buildOrderStep += 1

        elif self.buildOrderStep == 1:
            self.produceProbes(15)

            pylonProgress = self.structure_type_build_progress(UnitTypeId.PYLON)
            if pylonProgress == 0:
                initialPylonPos = await self.find_placement(UnitTypeId.PYLON, near=self.enemyThird, placement_step=1)
                if initialPylonPos == self.enemyThird:
                    globalWorker[0] = self.buildWithProbe(UnitTypeId.PYLON, initialPylonPos, worker = globalWorker[0], move = True, idle = True)
                else: 
                    globalWorker[0] = self.buildWithProbe(UnitTypeId.PYLON, initialPylonPos, worker = globalWorker[0], idle = True)
            elif pylonProgress == 1:
                self.buildOrderStep += 1

        elif self.buildOrderStep == 2:
            pylonPos = self.structures(UnitTypeId.PYLON).center
            self.worker = self.getWorker(pylonPos, performingAction=True)

            deltaPos = [(-3,0),(0,2),(2,-1),(-1,-3)]
            gatewayCount = len(self.structures(UnitTypeId.GATEWAY))

            if gatewayCount < 4:
                gatewayPos = pylonPos.offset(Point2(Pointlike(deltaPos[gatewayCount])))
                globalWorker[0] = self.buildWithProbe(UnitTypeId.GATEWAY, gatewayPos, queue = True, worker = globalWorker[0], move = True, idle = True)
                

            elif gatewayCount == 4:
                self.buildOrderStep += 1
        
        elif self.buildOrderStep ==3:
            if len(self.workers.filter(lambda worker: (worker.is_collecting))) < 16:
                self.produceProbes(17)

            self.train(UnitTypeId.ZEALOT)

            await self.avoidSupplyCap(8)

            zealotList = self.units(UnitTypeId.ZEALOT)
            if len(zealotList) > 3:
                for zealot in zealotList:
                    zealot.attack(self.enemy_start_locations[0])
        

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        global globalWorker
        global speedMiningPositionMap
        globalWorker = [None]
        minerList = self.workers
        speedMiningPositionMap = self.speedMiningPositions(minerList[0].radius)

        for miner in minerList:
            miner.gather(self.closestMineral(miner))

        buildList = [self.buildOrderProxy4gate]
        self.buildOrder = random.choice(buildList)
        self.buildOrderStep = 0
        print("Game started")
        print("Build order selected: " + self.buildOrder.__name__)
        self.client.chat_send("Build order selected: " + self.buildOrder.__name__, True)

        self.enemyNatural = await self.getEnemyNatural()
        self.enemyThird = await self.getEnemyThird()

    async def on_step(self, iteration: int) -> None:
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """

        await self.buildOrder()

        minerList = self.workers

        for miner in minerList:
             if miner not in globalWorker:
                self.speedMineWorker(miner)

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
