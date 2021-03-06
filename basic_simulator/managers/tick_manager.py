from managers.status_effect_manager import StatusEffectManager
import time


class TickManager:
    def __init__(self, status_effect_manager: StatusEffectManager, tick_value, tick_rate):
        if tick_rate <= 0:
            raise Exception("tick_rate cannot be zero of less.")

        self.tick_value = tick_value
        self.tick_rate = tick_rate
        self.status_effect_manager = status_effect_manager
        self.start_time = time.perf_counter()
        self.last_time = time.perf_counter()

        self.update_time = time.time()
        self.time_history = []

    def tick(self):
        """
        Handle all the events that the tick manager knows about.
        Order matters, certain tick events are prioritized over others.
        :return:
        """

        # Bootstrap all new status effects.
        self.status_effect_manager.bootstrap_status_effects(self.tick_value, self.tick_rate)

        # Update the tick count.
        self.tick_value += self.tick_rate

        current_time = time.perf_counter()
        time_elapsed = current_time - self.last_time
        total_time = current_time - self.start_time
        self.last_time = current_time

        c_time = time.time()
        tick_rate = 1 / time_elapsed if time_elapsed != 0 else 0
        self.time_history.append(tick_rate)
        if self.update_time + 5 < c_time:
            self.update_time = c_time
            av = sum(self.time_history) / len(self.time_history)
            print("%f" % av)
            self.time_history.clear()

        # Tick all status effects
        self.status_effect_manager.tick_status_effects(self.tick_value, self.tick_rate)

        # TODO: after all statuses ticked, trigger effects to resolve new statuses.
        # TODO: call to generic status trigger manager

        # Clear out all triggered statuses.
        self.status_effect_manager.triggered_statuses.clear()

