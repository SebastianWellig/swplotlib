import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.text import Annotation
from matplotlib import colors

def flattened_transparency(color, alpha=0.4, bc=(1,1,1)):
    out = np.array(colors.to_rgb(color))
    out *= alpha
    out += (1 - alpha) * np.array(bc)
    return out

class EnergyDiagram:
    def __init__(self):
        self.objects = []
        self.column_counter = 0
            
    def add_level(self, level):
        if level.column == 'auto':
            level.column = self.column_counter
            self.column_counter += 1
        self.objects.append(level)
        return level
        
    def add_link(self, link):
        self.objects.append(link)
        return link
        
    def link_levels(self, *levels, **kwargs):
        for level_pair in zip(levels[1:], levels[:-1]):
            self.add_link(EnergyLevelLink(*level_pair, **kwargs))
    
    def add_difference(self, *levels, **kwargs):
        self.objects.append(EnergyLevelDifference(*levels, **kwargs))
            
    def plot(self, ax, hide_interval=False):
        for obj in self.objects:
            obj.draw(ax, hide_interval=hide_interval)

class EnergyLevel:
    def __init__(self, energy, energy_interval=(), column='auto', color='auto', linewidth=4, va = 'bottom'):
        self.energy = energy
        if not energy_interval:
            energy_interval = (energy, energy)
        self.energy_interval = energy_interval
        self.column = column
        self.color = color
        self.linewidth = linewidth
        self.va = va
    
    @classmethod
    def from_matter(cls, matter, scf_model, thermo_model, **kwargs):
        energy = matter.get_gibbs_energy(scf_model, thermo_model)
        energies = [matter.get_gibbs_energy(*model) for model in matter.get_models()]
        energy_interval = (min(energies), max(energies))
        return cls(energy, energy_interval=energy_interval, **kwargs)
        
    def draw(self, ax, hide_interval=False):
        # Draw horizontal line
        start = 3*self.column
        end = start + 2
        ax.hlines(self.energy, start, end, color=self.color, lw=self.linewidth, zorder=3)
        # Draw interval rectangle
        energy_range = self.energy_interval[1] - self.energy_interval[0]
        if not hide_interval and energy_range > 0:
            rectangle = patches.Rectangle((start, self.energy_interval[0]), 2, energy_range, color=self.color, alpha=0.4, linewidth=0)
            #rectangle = Rectangle((start, self.energy_interval[0]), 2, energy_range, color=flattened_transparency(self.color, alpha=0.4), linewidth=0)
            ax.add_patch(rectangle)
        # Add label
        if not hide_interval and energy_range > 0:
            if self.va == 'bottom':
                y = self.energy_interval[0]
                ytext = -15
            else:
                y = self.energy_interval[1]
                ytext = 15
            text = f'{self.energy:.1f}\n[{self.energy_interval[0]:.1f}, {self.energy_interval[1]:.1f}]'
        else:
            y = self.energy
            if self.va == 'bottom':
                ytext = -15
            else:
                ytext = 15
            text = f'{self.energy:.1f}'
        ax.annotate(text, (start + 1, y), ha='center', va='center', xytext=(0, ytext), textcoords='offset points', color=self.color)
        ''''
        ax.text(
            start + 1,
            y,
            f'{self.energy:.1f}{text}',
            horizontalalignment='center',
            verticalalignment='center',
            color=self.color
        )'''

class EnergyLevelLink:
    def __init__(self, level_1, level_2, TS_energy=None, TS_energy_rel=None, color='auto', linewidth=1):
        self.levels = (level_1, level_2)
        self.color = color
        self.linewidth = linewidth
        if TS_energy_rel is not None:
            self.TS_energy = max(level_1.energy, level_2.energy) + TS_energy_rel
        else:
            self.TS_energy = TS_energy
    def draw(self, ax, hide_interval=False):
        level_1, level_2 = self.levels
        if level_1.column > level_2.column:
            xx = [3*level_2.column + 2, 3*level_1.column]
            yy = [level_2.energy, level_1.energy]
        else:
            xx = [3*level_1.column + 2, 3*level_2.column]
            yy = [level_1.energy, level_2.energy]
        if self.TS_energy is None:
            dx = (xx[1] - xx[0]) / 2
            patch = patches.PathPatch(patches.Path([
               (xx[0], yy[0]),
               (xx[0] + dx, yy[0]),
               (xx[1] - dx, yy[1]),
               (xx[1], yy[1])
            ], [
                patches.Path.MOVETO,
                patches.Path.CURVE4,
                patches.Path.CURVE4,
                patches.Path.CURVE4
            ]), ec=self.color, fc='none', lw=self.linewidth, zorder=2)
            ax.add_patch(patch)
        else:
            x_TS = (xx[1] + xx[0]) / 2
            dx = (xx[1] - xx[0]) / 4
            patch = patches.PathPatch(patches.Path([
               (xx[0], yy[0]),
               (xx[0] + dx, yy[0]),
               (x_TS - dx, self.TS_energy),
               (x_TS, self.TS_energy),
               (x_TS + dx, self.TS_energy),
               (xx[1] - dx, yy[1]),
               (xx[1], yy[1])
            ], [
                patches.Path.MOVETO,
                patches.Path.CURVE4,
                patches.Path.CURVE4,
                patches.Path.CURVE4,
                patches.Path.CURVE4,
                patches.Path.CURVE4,
                patches.Path.CURVE4
            ]), ec=self.color, fc='none', lw=self.linewidth, zorder=2)
            ax.add_patch(patch)
            
        # Connect level intervals with trapezoid
        if not hide_interval and (level_1.energy_interval or level_2.energy_interval):
            if level_1.column > level_2.column:
                offset_1, offset_2 = 0, 2
            else:
                offset_1, offset_2 = 2, 0
            vertices = [
                (3*level_1.column + offset_1, level_1.energy_interval[1]),
                (3*level_2.column + offset_2, level_2.energy_interval[1]),
                (3*level_2.column + offset_2, level_2.energy_interval[0]),
                (3*level_1.column + offset_1, level_1.energy_interval[0])
            ]
            if self.TS_energy is None:
                patch = patches.PathPatch(patches.Path([
                    vertices[0],
                    (vertices[0][0] - dx, vertices[0][1]),
                    (vertices[1][0] + dx, vertices[1][1]),
                    vertices[1],
                    vertices[2],
                    (vertices[2][0] + dx, vertices[2][1]),
                    (vertices[3][0] - dx, vertices[3][1]),
                    vertices[3],
                    vertices[0]
                ], [
                    patches.Path.MOVETO,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.LINETO,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CLOSEPOLY
                ]), fc=self.color, alpha=0.4, lw=0)
                #]), fc=flattened_transparency(self.color, alpha=0.4), lw=0)
                ax.add_patch(patch)
            else:
                vertices_TS = [
                    (x_TS, self.TS_energy + abs(level_1.energy_interval[1] - level_1.energy + level_2.energy_interval[1] - level_2.energy) / 2),
                    (x_TS, self.TS_energy - abs(level_1.energy - level_1.energy_interval[0] + level_2.energy - level_2.energy_interval[0]) / 2)
                ]
                patch = patches.PathPatch(patches.Path([
                    vertices[0],
                    (vertices[0][0] - dx, vertices[0][1]),
                    (vertices_TS[0][0] + dx, vertices_TS[0][1]),
                    vertices_TS[0],
                    (vertices_TS[0][0] - dx, vertices_TS[0][1]),
                    (vertices[1][0] + dx, vertices[1][1]),
                    vertices[1],
                    vertices[2],
                    (vertices[2][0] + dx, vertices[2][1]),
                    (vertices_TS[1][0] - dx, vertices_TS[1][1]),
                    vertices_TS[1],
                    (vertices_TS[1][0] + dx, vertices_TS[1][1]),
                    (vertices[3][0] - dx, vertices[3][1]),
                    vertices[3],
                    vertices[0]
                ], [
                    patches.Path.MOVETO,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.LINETO,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CURVE4,
                    patches.Path.CLOSEPOLY
                ]), fc=self.color, alpha=0.4, lw=0)
                #]), fc=flattened_transparency(self.color, alpha=0.4), lw=0)
                ax.add_patch(patch)

class EnergyLevelDifference:
    def __init__(self, *levels, column='auto', xytext=(0, 0), fctext='white', ha='center'):
        self.levels = levels
        if column == 'auto':
            column = levels[0].column + 1/3
        self.column = column
        self.xytext = xytext
        self.fctext = fctext
        self.ha = ha
    def draw(self, ax, **kwargs):
        level_1, level_2 = self.levels
        diff = level_1.energy - level_2.energy
        middle = level_1.energy - 0.5*diff
        if self.column != self.levels[0].column:
            if self.column > self.levels[0].column:
                xy = (3*self.levels[0].column+2, self.levels[0].energy)
            else:
                xy = (3*self.levels[0].column, self.levels[0].energy)
            ax.annotate("", xy=xy, xytext=(3*self.column, self.levels[0].energy), arrowprops=dict(arrowstyle='-', linestyle=':', ec='grey'))
        if self.column != self.levels[1].column:
            if self.column > self.levels[1].column:
                xy = (3*self.levels[1].column+2, self.levels[1].energy)
            else:
                xy = (3*self.levels[1].column, self.levels[1].energy)
            ax.annotate("", xy=xy, xytext=(3*self.column, self.levels[1].energy), arrowprops=dict(arrowstyle='-', linestyle=':', ec='grey'))
        print((3*self.column, level_1.energy), (3*self.column, level_2.energy))
        ax.annotate("", xy=(3*self.column, level_1.energy), xytext=(3*self.column, level_2.energy), arrowprops=dict(arrowstyle='|-|', ec='grey'))
        if self.ha[0] == 'c':
            dx_text = 0
        elif self.ha[0] == 'l':
            dx_text = 13
        else:
            dx_text = -13
        ax.annotate(f'{abs(diff):.1f}', xy=(3*self.column, middle), xytext=self.xytext, textcoords="offset points", color='grey',
                bbox=dict(boxstyle='square,pad=0.3', fc=self.fctext, ec='none'),
                ha=self.ha, va='center'
        )

def plot_ed(ed, title='', hide_interval=False):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.get_xaxis().set_visible(False)
    for loc in ['top', 'right', 'bottom']:
        ax.spines[loc].set_visible(False)
    ax.set_ylabel(r'$\Delta$G° [kcal/mol]')
    if title:
        ax.set_title(title)
    ed.plot(ax, hide_interval=hide_interval)
    return ax

def fix_annoations(ax):
    positions = []
    for child in reversed(ax.get_children()):
        if isinstance(child, Annotation):
            cur_pos = np.array(child.get_position())
            for pos in positions:
                if np.linalg.norm(cur_pos-pos) < 2:
                    child.set_visible(False)
            positions.append(cur_pos)
