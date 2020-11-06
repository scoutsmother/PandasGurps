import numpy as np
from direct.showbase.DirectObject import DirectObject

from events import Event

from managers.status_effect_manager import StatusEffectManager
from managers.action_resolvers.generic import GenericActionResolver
from managers.entity_manager import EntityComponentManager

from data_models.entities.being import Being
from data_models.entities.stats import StatType, StatSet, SecondaryStats, PrimaryStats, get_derived
from data_models.entities.modifiers import ModifiedStatSet
from data_models.entities.status_effects.energy import *


class CharacterCreator(DirectObject):
    def __init__(self, action_resolver: GenericActionResolver,
                 entity_component_manager: EntityComponentManager,
                 status_effect_manager: StatusEffectManager,
                 being_factory,
                 ):
        super(CharacterCreator, self).__init__()
        # TODO: configuration for different aspects of the character creator.
        #   e.g.
        #   - rules on what skills, advantages, items, etc are allowed.
        #   - contextual rules on what selections can be made together (exclusivity, etc)
        #   - costs for different stats, skills, adv/dis, etc.
        self.action_resolver = action_resolver
        self.entity_component_manager = entity_component_manager
        self.status_effect_manager = status_effect_manager
        self.being_factory = being_factory

        Event.register("generate_random_character", self, self.generate_random_character)

    def generate_random_character(self):
        stats = self.generate_stats_via_normals(0.5)
        self.generate_character(base_stats=stats)

    def generate_character(self, base_stats: StatSet, inventory=None, skills=None):
        """
        Given all the parts of a character, create a full data model for the character (including all required statuses,
        etc.
        """
        # Create the base model from all the pieces.
        modified_stats = ModifiedStatSet(base_stats)
        actor_model = self.being_factory(base_stats=base_stats, modified_stats=modified_stats)

        behavior = HumanPlayerBehavior(actor_model.entity_id)
        actor_fsm = ActorFsmContainer.fsm(data_model=actor_model,
                                          behavior=behavior,
                                          action_resolver=self.action_resolver)
        actor = ActorComponentContainer.component(data_model=actor_model, fsm=actor_fsm)

        self.entity_component_manager[actor.id] = actor

        # Add all required status effects.
        # TODO: modifications of each required status_effect would be done here, since the advantages and disadvantages
        #  are known.
        required_status_effects = [Fed(), Hydrated(), Starving(), Dehydrated()] # TODO: the rest here.
        for status_effect in required_status_effects:
            self.status_effect_manager.add_status_effect_to_entity(entity_id, status_effect)

        return character

    # TODO: create the genetics stat / adv / dis generator here.

    def generate_stats_via_normals(self, rho, defaults=None):
        defaults = {StatType.ST: 10,
                    StatType.IQ: 10,
                    StatType.DX: 10,
                    StatType.HT: 10,
                    StatType.WILL: 10,
                    StatType.PER: 10,
                    StatType.FP: 10,
                    StatType.HP: 10,
                    StatType.SPD: 100,
                    # TODO: switch back to 5 SPD
                    StatType.BM: 5} if not defaults else defaults
        keys, values = zip(*defaults.items())
        stats = np.round(np.random.normal(np.zeros(shape=(len(defaults))), scale=rho)).astype(int)
        generated_stats = dict(zip(keys, stats))

        combined_stats = dict()
        for pstype in PrimaryStats:
            stype = StatType(pstype.value)

            # Set the value of the default + generated change
            combined_stats[stype] = defaults[stype] + generated_stats[stype]

            # Set the secondary stat value
            for secondary in get_derived(pstype):
                sec_type = StatType(secondary)
                combined_stats[sec_type] = combined_stats[stype] + generated_stats[sec_type]

        for sstype in SecondaryStats:
            stype = StatType(sstype.value)

            # Set the value of the default + generated change
            combined_stats[stype] = defaults[stype] + generated_stats[stype]

            # Set the tertiary stat value
            for tertiary in get_derived(sstype):
                ter_type = StatType(tertiary)
                combined_stats[ter_type] = combined_stats[stype] + generated_stats[ter_type]

        stat_set = StatSet()
        for stype, value in combined_stats.items():
            stat_set[stype] = value

        stat_set[StatType.CURR_HP] = stat_set[StatType.HP]
        stat_set[StatType.CURR_FP] = stat_set[StatType.FP]
        stat_set[StatType.CURR_BM] = stat_set[StatType.BM]

        return stat_set

    def calculate_total(self, character: Being):
        # TODO: assume standard costs for stats (only thing that costs points at the moment)
        # Total primary stat costs.
        primary_stats = {
            StatType.ST: 10,
            StatType.DX: 20,
            StatType.IQ: 20,
            StatType.HT: 10
        }

        point_total = 0

        for stat in primary_stats.keys():
            # assume 10 is default.
            stat_difference = character.stats[stat] - 10
            stat_cost = stat_difference * primary_stats[stat]
            point_total += stat_cost

        return point_total