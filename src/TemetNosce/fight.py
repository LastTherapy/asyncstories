import asyncio

from enum import Enum, auto
from random import choice


class Action(Enum):
    HIGHKICK = auto()
    LOWKICK = auto()
    HIGHBLOCK = auto()
    LOWBLOCK = auto()


class Agent:

    def __aiter__(self, health=5):
        self.health = health
        self.actions = list(Action)
        return self

    async def __anext__(self):
        return choice(self.actions)


async def fight():
    agent = Agent()
    async for agent_action in agent.__aiter__(health=5):  # Используем агент в асинхронном цикле
        neo_action = choice(list(Action))

        if neo_action == Action.HIGHKICK and agent_action != Action.HIGHBLOCK:
            agent.health -= 1
        if neo_action == Action.LOWKICK and agent_action != Action.LOWBLOCK:
            agent.health -= 1

        print(f"Agent: {agent_action}, Neo: {neo_action}, Agent health: {agent.health}")

        if agent.health <= 0:
            print("Neo wins")
            break


async def battle(agent: Agent, agent_id: int):
    async for agent_action in agent.__aiter__(health=5):  # Используем асинхронный цикл
        neo_action = choice(list(Action))

        # pause for dispersion
        await asyncio.sleep(0.1)

        if agent_action == Action.LOWBLOCK and neo_action == Action.HIGHKICK:
            agent.health -= 1
        if agent_action == Action.HIGHBLOCK and neo_action == Action.LOWKICK:
            agent.health -= 1

        print(f"Agent {agent_id}: {agent_action}, Neo: {neo_action}, Agent {agent_id} health: {agent.health}")

        if agent.health <= 0:
            print(f"Neo wins")
            break


async def fightmany(n):
    agents = [Agent() for _ in range(n)]
    tasks = [battle(agent, agent_id) for agent_id, agent in enumerate(agents, 1)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(fightmany(3))
