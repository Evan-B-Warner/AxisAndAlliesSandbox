import json
import time
import itertools


class Unit(object):

    def __init__(self, name, attack, defense, cost, health):
        self.name = name
        self.attack = attack
        self.defense = defense
        self.cost = cost
        self.health = health
    
    def copy(self):
        """Creates and returns a shallow copy of the unit

        """
        new_copy = Unit(
            self.name,
            self.attack,
            self.defense,
            self.cost,
            self.health
        )
        return new_copy


class BattleSimulator(object):

    def __init__(self, attacking_units=None, defending_units=None):
        # resolve arguments
        if attacking_units is None:
            attacking_units = {}
        if defending_units is None:
            defending_units = {}

        # initalize variables
        self.attacking_units = self.convert_to_unit_type(attacking_units)
        self.defending_units = self.convert_to_unit_type(defending_units)
        self.precision = 5
        self.defender_wins = 0
        self.attacker_wins = 0
        self.unresolved_battles = 0
        self.battles_simulated = 0
    

    def convert_to_unit_type(self, units):
        """Converts a dictionary of unit counts into a list of Unit objects

        """
        # load unit data from json
        converted_units = []
        with open("units.json") as f:
            unit_info = json.load(f)

        # convert each unit
        for unit in units:
            unit_stats = unit_info[unit]
            for i in range(units[unit]):
                converted_units.append(
                    Unit(
                        unit,
                        unit_stats["attack"],
                        unit_stats["defense"],
                        unit_stats["cost"],
                        unit_stats["health"]
                    ))
        return converted_units
    

    def add_bonuses(self, units):
        """Determines and adds all applicable bonuses to the attacking units

        """
        # check for artillery + infantry
        num_artillery = sum([1 if u.name == 'Artillery' else 0 for u in units])
        
        # check for tac bomber + fighter or tank
        num_fighters_and_tanks = sum([1 if u.name in ["Fighter", "Tank"] else 0 for u in units])

        # apply bonuses
        for u in units:
            if num_artillery and "Infantry" in u.name:
                u.attack += 1
                num_artillery -= 1
            if num_fighters_and_tanks and u.name == "Tactical Bomber":
                u.attack += 1
                num_fighters_and_tanks -= 1
    

    def probability_of_x_hits(self, hit_probs_by_unit, num_hits):
        """Compute the probability of exactly `num_hits` hits, given an array of
        
        hit probabilities
        """
        # generate all combinations of `num_hits` units
        n = len(hit_probs_by_unit)
        total_prob = 0
        hitting_unit_combinations = list(itertools.combinations(range(n), num_hits))
        for hitting_units in hitting_unit_combinations:
            # compute the probability for each combination
            # start with probability that each hitting unit hits
            prob = 1
            for i in range(n):
                if i in hitting_units:
                    prob *= hit_probs_by_unit[i]
                else:
                    prob *= 1-hit_probs_by_unit[i]
            total_prob += prob
        return total_prob

    
    def compute_hit_probabilities(self, units, is_attacker):
        """Computes the probability of the units achieving all possible

        numbers of hits
        """
        # add bonuses to units if applicable
        new_units = []
        for unit in units:
            new_units.append(unit.copy())
        self.add_bonuses(new_units)

        # determine the raw probability of each unit hitting
        hit_probs_by_unit = []
        for unit in new_units:
            if is_attacker:
                hit_probs_by_unit.append(unit.attack/6)
            else:
                hit_probs_by_unit.append(unit.defense/6)
        
        # find the probability for each number of hits
        probability_of_hits = {}
        for num_hits in range(len(new_units)+1):
            probability_of_hits[num_hits] = self.probability_of_x_hits(hit_probs_by_unit, num_hits)
        return probability_of_hits
    

    def find_worst_unit(self, units, side):
        """Returns the index of the weakest unit in units by combat

        """
        lowest, lowest_index = -1, 0
        for i, unit in enumerate(units):
            if side == 'attack':
                combat_value = unit.attack
            else:
                combat_value = unit.defense
            if lowest == -1 or combat_value < lowest:
                lowest = combat_value
                lowest_ind = i
        return lowest_ind
    

    def remove_worst_units(self, units, num_hits, side):
        """Given the side (attack or defense) and the a list of units,

        removes the `num_hits` least valuable units by combat strength
        """
        # first remove one health from any units with more than one health
        units_copy = units[:]
        for unit in units_copy:
            if not num_hits:
                return units_copy
            if unit.health > 1:
                unit.health -= 1
                num_hits -= 1
        
        # otherwise let the worst unit take the hit
        while num_hits and len(units_copy):
            units_copy.pop(self.find_worst_unit(units_copy, side))
            num_hits -= 1
        
        return units_copy
    

    def compute_victory_probabilities(self, attacking_units, defending_units, num_rounds, attacker_first, num_casualties):
        """Performs the computation to determine the probability of the attacking side winning the fight

        """
        # precision limit
        if num_rounds > self.precision:
            self.unresolved_battles += 1
            self.battles_simulated += 1
            return 0.5
        
        # check for guaranteed attacker or defender wins
        orig_attacking_units, orig_defending_units = attacking_units[:], defending_units[:]
        if not(len(orig_attacking_units)):
            # defenders win all "draws"
            self.battles_simulated += 1
            return 0
        elif not(len(orig_defending_units)):
            self.battles_simulated += 1
            return 1
        
        # check if it is the attackers turn
        if attacker_first:
            # determine the probability of each number of hits by the attackers
            hit_probabilities = self.compute_hit_probabilities(orig_attacking_units, attacker_first)
            # take a sum of the win probabilities of each scenario resulting from the number of attacker hits
            return sum(
                [hit_probabilities[num_hits]*self.compute_victory_probabilities(
                    orig_attacking_units, orig_defending_units, num_rounds+1,
                    attacker_first=(not attacker_first), num_casualties=num_hits
                ) for num_hits in hit_probabilities]
            )
        else:
            # determine the probability of each number of hits by the defenders
            hit_probabilities = self.compute_hit_probabilities(orig_defending_units, attacker_first)
            
            # remove defender casualties
            defending_units = self.remove_worst_units(orig_defending_units, num_casualties, side='defense')[:]
            # take a sum of the win probabilities of each scenario resulting from the number of defender hits
            return sum(
                [hit_probabilities[num_hits]*self.compute_victory_probabilities(
                    self.remove_worst_units(orig_attacking_units, num_hits, side='attack'), defending_units, num_rounds+1,
                    attacker_first=(not attacker_first), num_casualties=0
                ) for num_hits in hit_probabilities]
            )

    
    def simulate_battle(self, precision=5, verbose=True):
        """Wrapper for the computation of victory probabilities for a battle

        """
        # Update/reset attributes for new simulation
        self.precision = precision
        self.battles_simulated = 0
        self.unresolved_battles = 0
        self.defender_wins = 0
        self.attacker_wins = 0

        # simulate the battle
        start_time = time.perf_counter()
        attacking_win_rate = self.compute_victory_probabilities(self.attacking_units, self.defending_units, num_rounds=1, attacker_first=True, num_casualties=0)
        defending_win_rate = 1 - attacking_win_rate
        run_time = round(time.perf_counter()-start_time, 4)

        # print results if verbose
        if verbose:
            print(f"Att wins {round(attacking_win_rate*100, 2)}% of battles")
            print(f"Def wins {round(defending_win_rate*100, 2)}% of battles")
        
        return attacking_win_rate, defending_win_rate


if __name__ == "__main__":
    attack = {
        "Infantry": 3,
        "Artillery": 1
    }
    defense = {
        "Infantry": 2,
        "Artillery": 1
    }
    sim = BattleSimulator(attack, defense)
    sim.simulate_battle(precision=10)