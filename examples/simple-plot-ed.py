'''
Usage:
  python3 simple-plot-ed.py
'''
import matplotlib.pyplot as plt
from swplotlib.energy_diagram import (
    EnergyDiagram,
    EnergyLevel,
    plot_ed
)


color = 'tab:blue'
ed = EnergyDiagram()

# Add levels
edu = ed.add_level(EnergyLevel(0, color=color))
ts1 = ed.add_level(EnergyLevel(21.1, color=color))
int1 = ed.add_level(EnergyLevel(12.5, color=color, va='top'))
ts2 = ed.add_level(EnergyLevel(23.3, color=color))
pro = ed.add_level(EnergyLevel(-9.5, color=color))
# Add alternative level to int1
ed.column_counter = 2 # Reset column index to int1's position
int1_alt = ed.add_level(EnergyLevel(10.1, color=color))

# Direct linking
ed.link_levels(edu, ts1, int1, ts2, pro, color=color)
# Linking with TS that is 3.6 higher than higher level in between
ed.link_levels(edu, int1_alt, TS_energy_rel=3.6, color=color)
# Linking with TS of 17.6 in between
ed.link_levels(int1_alt, pro, TS_energy=17.6, color=color)

# Show difference
ed.add_difference(int1, ts2, column=4+1/6)

# Manipulating the matplotlib instance
ax = plot_ed(ed, '', hide_interval=False)
ax.set_ylim(-15, 25)
fig = plt.gcf()
fig.tight_layout()
plt.show()

