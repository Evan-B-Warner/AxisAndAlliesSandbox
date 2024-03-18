import json
import numpy as np
import pandas as pd
import time
from tqdm import tqdm

from BattleSimulator import BattleSimulator


def unit_gauntlet(ipc_value=20):
    """Determines the best single unit army worth `ipc_value` ipcs

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
    
    # display results
    results = pd.DataFrame()
    results["Unit Name"] = [list(army)[0] for army in armies]
    results["# of Units"] = [army[list(army)[0]] for army in armies]
    results["Attacking Win Rate %"] = att_win_rates
    results["Defending Win Rate %"] = def_win_rates
    results["Combined Average Win Rate %"] = avg_win_rates
    results.sort_values(by="Combined Average Win Rate %", inplace=True, ascending=False)
    return results


if __name__ == "__main__":
    print(unit_gauntlet(ipc_value=20))