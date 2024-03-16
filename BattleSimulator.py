import json
import itertools


class Unit(object):

    def __init__(self, attack, defense, cost, health, bonuses):
        self.attack = attack
        self.defense = defense
        self.cost = cost
        self.health = health
        self.bonuses = bonuses


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
        for unit in units:
            if not num_hits:
                return units
            if unit.health > 1:
                unit_health -= 1
                num_hits -= 1
        
        # otherwise let the worst unit take the hit
        while num_hits:
            units.pop(self.find_worst_unit(units, side))
        
        return units


    def compute_victory_probabilities(self, attacking_units, defending_units, attacker_first=True, num_casualties=0):
        """Determines the probability of the attacking side winning the fight

        """
        # check for guaranteed attacker of defender wins
        if not(len(attacking_units)):
            return 0
        elif not(len(defending_units)):
            return 1
        
        # check if it is the attackers turn
        if attacker_first:
            # determine the probability of each number of hits by the attackers
            hit_probabilities = self.compute_hit_probabilities(attacking_units, attacker_first)
            # take a sum of the win probabilities of each scenario resulting from the number of attacker hits
            return sum(
                [prob*self.compute_victory_probabilities(
                    attacking_units, defending_units, 
                    attacker_first=(not attacker_first), num_casualties=num_hits
                ) for num_hits, prob in hit_probabilities]
            )
        else:
            # determine the probability of each number of hits by the defenders
            hit_probabilities = self.compute_hit_probabilities(defending_units, attacker_first)
            # remove defender casualties
            new_defending_units = self.remove_worst_units(defending_units, num_casualties, side='defense')[:]
            # take a sum of the win probabilities of each scenario resulting from the number of defender hits
            return sum(
                [prob*self.compute_victory_probabilities(
                    self.remove_worst_units(attacking_units, num_hits, side='attack'), new_defending_units, 
                    attacker_first=(not attacker_first), num_casualties=0
                ) for prob, num_hits in hit_probabilities]
            )

            

if __name__ == "__main__":
    sim = BattleSimulator(attacking_units={"Infantry": 3}, defending_units={"Infantry": 1})
    sim.compute_victory_probabilities(sim.attacking_units, sim.defending_units)
