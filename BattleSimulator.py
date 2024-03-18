import json
import time
import itertools


class Unit(object):

    def __init__(self, attack, defense, cost, health, bonuses):
        self.attack = attack
        self.defense = defense
        self.cost = cost
        self.health = health
        self.bonuses = bonuses
        self.precision = 5
        self.defender_wins = 0
        self.attacker_wins = 0
        self.unresolved_battles = 0
        self.battles_simulated = 0


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
            converted_unit = Unit(
                unit_stats["attack"],
                unit_stats["defense"],
                unit_stats["cost"],
                unit_stats["health"],
                unit_stats["bonuses"]
            )
            converted_units.extend([converted_unit][:]*units[unit])
        return converted_units
    

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
        # determine the raw probability of each unit hitting
        hit_probs_by_unit = []
        for unit in units:
            if is_attacker:
                hit_probs_by_unit.append(unit.attack/6)
            else:
                hit_probs_by_unit.append(unit.defense/6)
        
        # find the probability for each number of hits
        probability_of_hits = {}
        for num_hits in range(len(units)+1):
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
                unit_health -= 1
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
            #print('att', len(orig_attacking_units), len(orig_defending_units), hit_probabilities)
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
            #print('def', len(orig_attacking_units), len(orig_defending_units), num_casualties, hit_probabilities)
            return sum(
                [hit_probabilities[num_hits]*self.compute_victory_probabilities(
                    self.remove_worst_units(orig_attacking_units, num_hits, side='attack'), defending_units, num_rounds+1,
                    attacker_first=(not attacker_first), num_casualties=0
                ) for num_hits in hit_probabilities]
            )
    

    def compute_victory_probabilities_2(self, attacking_units, defending_units):
        num_rounds = 1
        scenarios = [[attacking_units, defending_units]]
        seen = {}
        while True:
            new_scenarios = []
            for scen_attacking_units, scen_defending_units in scenarios:
                # determine the probability of each number of hits by the attackers and defenders
                att_hit_probabilities = self.compute_hit_probabilities(scen_attacking_units, is_attacker=True)
                def_hit_probabilities = self.compute_hit_probabilities(scen_defending_units, is_attacker=False)

                # determine all new scenarios that can result from the hit probabilities
                for att_num_hits in att_hit_probabilities:
                    for def_num_hits in def_hit_probabilities:
                        new_defending_units = self.remove_worst_units(scen_defending_units, att_num_hits, side='defense')[:]
                        new_attacking_units = self.remove_worst_units(scen_attacking_units, def_num_hits, side='attack')[:]
                        if not len(new_attacking_units):
                            # defenders win draws
                            self.defender_wins += 1
                            self.battles_simulated += 1
                        elif not len(new_defending_units):
                            self.attacker_wins += 1
                            self.battles_simulated += 1
                        elif num_rounds <= self.precision:
                            new_scenarios.append([new_attacking_units, new_defending_units])
                        else:
                            self.unresolved_battles += 1
                            self.battles_simulated += 1
                
            # increment the number of rounds, and check for remaining scenarios
            num_rounds += 1
            if new_scenarios == []:
                return
            else:
                scenarios = new_scenarios[:]

    
    def simulate_battle(self, num_rounds_precision=5, verbose=True):
        """Wrapper for the computation of victory probabilities for a battle

        """
        # Update/reset attributes for new simulation
        self.precision = num_rounds_precision
        self.battles_simulated = 0
        self.unresolved_battles = 0
        self.defender_wins = 0
        self.attacker_wins = 0

        # simulate the battle
        start_time = time.perf_counter()
        self.compute_victory_probabilities_2(self.attacking_units, self.defending_units)
        run_time = round(time.perf_counter()-start_time, 4)

        # print results if verbose
        if verbose:
            print(f"Att wins {self.attacker_wins}, {round(self.attacker_wins/self.battles_simulated*100, 2)}%")
            print(f"Def wins {self.defender_wins}, {round(self.defender_wins/self.battles_simulated*100, 2)}%")
            print(f"Unresolved: {self.unresolved_battles}, {round(self.unresolved_battles/self.battles_simulated*100, 2)}%")
            print(f"Simulated {self.battles_simulated} scenarios in {run_time}s")
