import psutil

class SystemActions:
    @staticmethod
    def get_battery_status():
        battery = psutil.sensors_battery()
        if battery is None:
            return "I cannot detect a battery on this system."
        
        percent = battery.percent
        plugged = battery.power_plugged
        
        if plugged:
            return f"The battery is currently at {percent} percent and is charging."
        else:
            return f"The battery is at {percent} percent."

    @staticmethod
    def get_cpu_status():
        cpu_usage = psutil.cpu_percent(interval=1)
        return f"Current CPU usage is at {cpu_usage} percent."

    @staticmethod
    def get_memory_status():
        memory = psutil.virtual_memory()
        percent = memory.percent
        return f"System memory is currently at {percent} percent capacity."
