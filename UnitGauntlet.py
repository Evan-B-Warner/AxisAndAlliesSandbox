import itertools
import json
import numpy as np
import pandas as pd
import time
from tqdm import tqdm

from BattleSimulator import BattleSimulator


def simulate_army_battles(armies):
    """Simulates a head-to-head battle between each pair of armies in `armies`,

    where each army gets the chance to be the attacker and defender once.

    Then returns the attacking, defending, and combined win rate for each army 
    
    formatted in a DataFrame.
    """
    print("Simulating battles...")
    num_battles = len(armies)*(len(armies)-1)
    pbar = tqdm(total=num_battles)
    att_win_rates, def_win_rates = [0][:]*len(armies), [0][:]*len(armies)
    for i in range(len(armies)):
        for ii in range(i+1, len(armies)):
            # simulate with first army as attacker
            attack_sim = BattleSimulator(armies[i], armies[ii])
            att_win_rate, def_win_rate = attack_sim.simulate_battle(precision=5, verbose=0)
            att_win_rates[i] += att_win_rate
            def_win_rates[ii] += def_win_rate
            pbar.update(1)

            # simulate with second army as attacker
            def_sim = BattleSimulator(armies[ii], armies[i])
            att_win_rate, def_win_rate = def_sim.simulate_battle(precision=5, verbose=0)
            att_win_rates[ii] += att_win_rate
            def_win_rates[i] += def_win_rate
            pbar.update(1)
    
    # normalize all rates
    avg_win_rates = []
    for i in range(len(att_win_rates)):
        att_win_rates[i] = round(att_win_rates[i]/len(att_win_rates)*100, 2)
        def_win_rates[i] = round(def_win_rates[i]/len(def_win_rates)*100, 2)
        avg_win_rates.append(round((att_win_rates[i]+def_win_rates[i])/2, 2))
    
    # format and return results
    results = pd.DataFrame()
    results["Units"] = armies
    results["Attacking Win Rate %"] = att_win_rates
    results["Defending Win Rate %"] = def_win_rates
    results["Combined Average Win Rate %"] = avg_win_rates
    results.sort_values(by="Combined Average Win Rate %", inplace=True, ascending=False)
    return results


def unit_gauntlet(ipc_value=20):
    """Determines the best single unit army worth `ipc_value` ipcs.

    """
    # form the armies
    with open("units.json") as f:
        unit_data = json.load(f)
    armies = []
    for unit in unit_data:
        num_units = int(ipc_value/unit_data[unit]["cost"])
        if num_units:
            armies.append({unit: num_units})
    
    # simulate the head to head of each army
    return simulate_army_battles(armies)


def best_army_by_ipc(ipc_value=20):
    """Determines all possible combinations of units costing at most `ipc_value`,

    and matches them all head-to-head to determine which is the best.
    """
    # load the unit data
    with open("units.json") as f:
        unit_data = json.load(f)
    
    # determine the units we can sample from without replacement
    # we add floor(ipc_value/unit cost) of each unit, since
    # having more of this unit in a sample would go over the allowed cost
    unit_sample = []
    largest_army = 0
    for unit in unit_data:
        num_units = int(ipc_value/unit_data[unit]["cost"])
        largest_army = max(num_units, largest_army)
        for i in range(num_units):
            unit_sample.append([unit, unit_data[unit]["cost"]])

    # form all possible armies
    print("Generating all possible armies...")
    armies = []
    cheapest_unit = 3 # infantry is the cheapest - cost of 3
    for army_size in tqdm(range(1, largest_army+1)):
        for combination in itertools.combinations_with_replacement(unit_sample, army_size):
            # the combination cost must satisfy: ipc_value - cheapest_unit < cost <= ipc_value
            # otherwise this combination would be strictly better by adding an infantry, 
            # and is not worth considering
            combination_cost = sum([unit[1] for unit in combination])
            if combination_cost > ipc_value - cheapest_unit and combination_cost <= ipc_value:
                # if we have a valid combination, reformat it into the expected army format
                army = {}
                for unit in combination:
                    name, cost = unit
                    if name not in army:
                        army[name] = 0
                    army[name] += 1
                if army not in armies:
                    armies.append(army)
    
    # simulate the head to head of each army
    return simulate_army_battles(armies)


if __name__ == "__main__":
    print(unit_gauntlet(ipc_value=20))
    print(best_army_by_ipc(ipc_value=20))