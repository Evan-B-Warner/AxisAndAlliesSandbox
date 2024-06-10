# Axis and Allies Sandbox
As a huge fan of Axis and Allies, I have often thought about questions like:
What is the win probability of this battle?
Which unit is the most IPC efficient in combat?

Although there are some online tools to determine win probability, in my experience, they produce win probabilities
based on some number of randomly simulated battles. This means that the win probabilities will fluctuate when simulating
the same battle multiple times.

I decided to take the accuracy of battle simulation one step further, by creating this sandbox tool. The included battle
simulator considers the probability of each and every winning or losing scenario in a battle, and uses this to determine
a "true" winning probability.

This sandbox also includes some methods that help answer interesting questions about combat theory in A&A. UnitGauntlet 
contains `unit_gauntlet(ipc_value)`, which determines the best single-unit army worth at most `ipc_value` IPCs. There is
also `best_army_by_ipc(ipc_value)`, which determines the best army in general worth at most `ipc_value` IPCs.

<br>

## Limitations
The reason why I say this sandbox computes a "true" probability, is because the actual true probability of a battle is
impossible to compute. This is because it is theoretically possible for the attacker and defender to perpetually achieve
0 hits in each round of combat, meaning that a battle could last forever. As a result, the BattleSimulator has a modifiable
`round precision` attribute. When simulating a battle, any scenario that takes more than `round precision` 
rounds will be treated as half of a win for the attacker and defender. Naturally as you increase `round precision`, the probabilities
become more accurate, but it also takes much longer to simulate the battle. A `round precision` of 5 strikes a good balance,
where battles with 50+ units can be simulated reasonably quickly, with a high degree of accuracy (usually less than 0.1% error).

<br>

## Quick Start
1. Install the necessary dependencies
```
pip install requirements.txt
```

2. Try out the BattleSimulator:
```
from BattleSimulator import BattleSimulator

# define the units in the battle
attacking_units = {
    "Infantry": 3
}
defending_untis = {
    "Infantry": 1
}

# simulate the battle
sim = BattleSimulator(attacking_units, defending_units)
sim.simulate_battle(precision=5, verbose=1)
```

3. Discover the best units using UnitGauntlet:
```
from UnitGauntlet import unit_gauntlet, best_army_by_ipc

# find the best single unit army
print(unit_guantlet(ipc_value=20))

# find the best general army
print(best_army_by_ipc(ipc_value=20))
```
