import os
import temp_ds18b20


def get_temperature_summary():
  temperature_report = 'Temperature summary\n'
  temperature_report += 'Processor temperature : ' + str(get_cpu_temperature()) + ' C\n'
  temperature_report += 'Room temperature : ' + str(temp_ds18b20.read_temp()) + ' C\n'
  return temperature_report

def get_cpu_temperature():
  temp = os.popen("cat /sys/class/thermal/thermal_zone0/temp").readline()
  return float(temp) / 1000  # Convert from millidegree Celsius to degree 