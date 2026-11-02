from collections import OrderedDict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def create_energy_getter(energy_getter_name, model):
    def get_energy(s):
        try:
            return getattr(s, energy_getter_name)(*model)
        except AttributeError:
            return np.nan
        except TypeError:
            pass

        if energy_getter_name in ['get_entropy']:
            try:
                return getattr(s, energy_getter_name)(model[1])
            except AttributeError:
                return np.nan
        elif energy_getter_name in ['get_energy']:
            try:
                return getattr(s, energy_getter_name)(model[0])
            except AttributeError:
                return np.nan
        else:
            raise NotImplementedError(energy_getter_name)

    return get_energy

def create_all_energies_getter(energy_getter_name):
    def get_all_energies(s):
        try:
            return [getattr(s, energy_getter_name)(*m) for m in s.get_models()]
        except AttributeError:
            return np.nan
        except TypeError:
            pass

        if energy_getter_name in ['get_entropy']:
            try:
                return [getattr(s, energy_getter_name)(m[1]) for m in s.get_models()]
            except AttributeError:
                return []
        elif energy_getter_name in ['get_energy']:
            try:
                return [getattr(s, energy_getter_name)(m[0]) for m in s.get_models()]
            except AttributeError:
                return []
        else:
            raise NotImplementedError(energy_getter_name)

    return get_all_energies


def get_energy_df(df, energy_getter, model=None):
    return df.applymap(energy_getter)

def get_energy_yerr(df, sel_energy_getter, all_energies_getter):
    def get_interval(s):
        try:
            E_sel = sel_energy_getter(s)
            energies = all_energies_getter(s)
            return [E_sel - min(energies),  max(energies) - E_sel]
        except (ValueError, TypeError):
            return [np.nan, np.nan]
    out = df.applymap(get_interval)    
    return np.moveaxis([[x for x in y] for y in out.values], 0, -1)

def plot_eb(df, sel_energy_getter, all_energies_getter, **kwargs):
    ax = get_energy_df(df, sel_energy_getter).plot.bar(yerr=get_energy_yerr(df, sel_energy_getter, all_energies_getter), **kwargs)
    for ebc, bc in zip(ax.containers[::2], ax.containers[1::2]):
        E_max = ebc.lines[1][0].get_data()[1][0]
        E_min = ebc.lines[1][1].get_data()[1][0]
        errbar_segments = ebc.lines[2][0].get_segments()
        bar_patches = bc.patches
        for patch, segment in zip(bar_patches, errbar_segments):
            x = patch.get_x() + patch.get_width()/2
            E_int = patch.get_height()
            if round(E_int, 2) == 0.:
                ax.annotate('\\textbf{N/A}', (x, 0), ha='center', va='center', xytext=(0, 10), textcoords='offset points', fontsize=8)
                continue
            E_min = segment[0,1]
            E_max = segment[1,1]
            y = E_max if E_int >= 0 else E_min
            if E_int >= 0:
                ytext = 20
            else:
                ytext = -25
            ax.annotate(f'\\begin{{gather*}}\\mathbf{{{E_int:.1f}}}\\\\\\begin{{bmatrix}}{E_max:.1f}\\\\{E_min:.1f}\\end{{bmatrix}}\\end{{gather*}}', (x, y), ha='center', va='center', xytext=(2, ytext), textcoords='offset points', fontsize=8)
    return ax

def get_energy_yerr_v2(df):
    def get_interval(data):
        try:
            E_sel, E_min, E_max = data
            return [E_sel - E_min,  E_max - E_sel]
        except ValueError:
            return [np.nan, np.nan]
    out = df.applymap(get_interval)    
    return np.moveaxis([[x for x in y] for y in out.values], 0, -1)

def plot_eb_v2(df, sel_energy_getter, all_energies_getter, **kwargs):
    ax = df.applymap(lambda d: d[0]).plot.bar(yerr=get_energy_yerr_v2(df), **kwargs)
    for ebc, bc in zip(ax.containers[::2], ax.containers[1::2]):
        E_max = ebc.lines[1][0].get_data()[1][0]
        E_min = ebc.lines[1][1].get_data()[1][0]
        errbar_segments = ebc.lines[2][0].get_segments()
        bar_patches = bc.patches
        for patch, segment in zip(bar_patches, errbar_segments):
            x = patch.get_x() + patch.get_width()/2
            E_int = patch.get_height()
            if round(E_int, 2) == 0.:
                ax.annotate('\\textbf{N/A}', (x, 0), ha='center', va='center', xytext=(0, 10), textcoords='offset points', fontsize=8)
                continue
            E_min = segment[0,1]
            E_max = segment[1,1]
            y = E_max if E_int >= 0 else E_min
            if E_int >= 0:
                ytext = 20
            else:
                ytext = -25
            ax.annotate(f'\\begin{{gather*}}\\mathbf{{{E_int:.1f}}}\\\\\\begin{{bmatrix}}{E_max:.1f}\\\\{E_min:.1f}\\end{{bmatrix}}\\end{{gather*}}', (x, y), ha='center', va='center', xytext=(2, ytext), textcoords='offset points', fontsize=8)
    return ax

def custom_bar_plotter(labels, group_generator, model=None, energy_getter_name='get_gibbs_energy', base_plotter=plot_eb, df_modifier=None, **kwargs):
    data = OrderedDict()
    sel_energy_getter = create_energy_getter(energy_getter_name, model)
    all_energies_getter = create_all_energies_getter(energy_getter_name)
    for label in labels:
        data.update(group_generator(*label, sel_energy_getter=sel_energy_getter))
    df = pd.DataFrame(data)
    #df = df.sort_index()
    if df_modifier is not None:
        df = df_modifier(df)
    ax = base_plotter(df, sel_energy_getter, all_energies_getter, width=0.9, capsize=5, **kwargs)
    ax.set_xticklabels(df.index, rotation=0)
    ax.set_ylabel(r'$\mathrm{\Delta^\ddag G^\circ}$ [kcal/mol]')
    ax.legend(framealpha=1)
    plt.tight_layout()
    return ax