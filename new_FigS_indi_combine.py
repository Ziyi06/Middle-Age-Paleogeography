"""
make 5*2 plots for 1.8-1.3 Ga (or 1.3-0.8 Ga), 
each panel showing different time slices and contains three rock types
"""
from paths import *
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from config_paleomap import make_plate_reconstruction_and_plot
from config_paleomap import plumes_loc, plot_dataframe, get_clean_data

matplotlib.rcParams['font.family'] = 'Arial'

df_anor, df_aty, df_pt = get_clean_data('all_data_compiled.xlsx')

size = 50 ## this is marker size
fontsize = 12

style_map = {'a-type':   {'marker': 'D', 'label': 'A-type', 'color': 'violet', 'zorder': 9},
             'anor':   {'marker': 's', 'label': 'Anorthosites', 'color': 'cornflowerblue', 'zorder': 10},
             't/p':   {'marker': 'o', 'label': 'Metamorphic P/T', 'color': 'bwr', 'zorder': 15}}

## Choose which half to plot: 'old' = 1800-1300 Ma, 'young' = 1300-800 Ma
period = 'young'
age_start = 1800 if period == 'old' else 1300

## Five rows, two columns, 50-Myr intervals:
## axes[0,0] = age_start to age_start-50 Ma, axes[0,1] = next 50 Myr, ..., axes[4,1] = last 50 Myr
## background map is drawn at the middle of each interval; each sample is reconstructed
## to its own age (or its plate's oldest rotation, see get_clean_data)
model_name = "Cao2024"
# model_name = "Muller2025"

projection = ccrs.Mollweide(central_longitude=140) if model_name == "Cao2024" else ccrs.Mollweide(central_longitude=160)
interval = 50  # Myr
age_tops = np.arange(age_start, age_start - 500, -interval)  # 10 panels

## all three rock types in every panel: (dataframe, style key)
rock_types = [(df_anor, 'anor'), (df_aty, 'a-type'), (df_pt, 't/p')]

## export the number of samples of each rock type in each time window to Excel
export_counts = False

if export_counts:
    def n_in_window(d, age_range, extra=None):
        """Samples in the window, same selection as the panels (recon_time, with a location)."""
        sel = ((d['recon_time'] > age_range[0]) & (d['recon_time'] <= age_range[1])
               & d['latitude'].notnull() & d['longitude'].notnull())
        if extra is not None:
            sel &= extra
        return int(sel.sum())

    rows = []
    for age_max in age_tops:
        age_range = (age_max - interval, age_max)
        rows.append({'window (Ma)': f'{age_max}-{age_max - interval}',
                     'map time (Ma)': age_max - interval / 2,
                     'Anorthosites': n_in_window(df_anor, age_range),
                     'A-type granites': n_in_window(df_aty, age_range),
                     'HT-UHT rocks': n_in_window(df_pt, age_range),
                     'of which UHT (HUHT)': n_in_window(df_pt, age_range, df_pt['cato'] == 'HUHT')})
    counts = pd.DataFrame(rows)
    counts['Total'] = counts[['Anorthosites', 'A-type granites', 'HT-UHT rocks']].sum(axis=1)
    counts_file = data_path + f'counts_indi_combine_{age_start}_{age_start - 500}.xlsx'
    counts.to_excel(counts_file, index=False)
    print(counts.to_string(index=False))
    print('saved', counts_file)

## each plume location in plumes_loc stands for a 50-Myr window centred on its time
## (as in distance_to_plume), so it is drawn in every 50-Myr panel inside that window
plume_window = 100  # Myr

fig, axes = plt.subplots(5, 2, figsize=(9, 13.5), subplot_kw={'projection': projection})
plt.subplots_adjust(left=0.03, right=0.97, bottom=0.12, top=0.93, hspace=0.15, wspace=0.05)

for k, (ax, age_max) in enumerate(zip(axes.flat, age_tops)):
    age_range = (age_max - interval, age_max)
    map_time = age_max - interval / 2

    model_i, _ = make_plate_reconstruction_and_plot(model_name=model_name, projection=projection,
                                                    time=map_time, ax=ax)
    for df, plot_type in rock_types:
        plot_dataframe(df, age_range, ax, style_map, size=size,
                       type=plot_type, model_name=model_name,
                       time=map_time, proj=projection,
                       model=model_i, own_age=1,  # each data point is reconstructed to its own age
                       plot_label=1)
    ax.set_global()

    # number of analyses plotted in this window (same selection as plot_dataframe)
    n = sum(((d['recon_time'] > age_range[0]) & (d['recon_time'] <= age_range[1])
             & d['latitude'].notnull() & d['longitude'].notnull()).sum()
            for d, _ in rock_types)
    ax.set_title(f'{age_max}-{age_max - interval} Ma', fontsize=10)

    # panel letter A, B, C, ... at the top left
    ax.text(0.0, 1.02, chr(ord('A') + k), transform=ax.transAxes,
            ha='left', va='bottom', fontsize=12, fontweight='bold')

## legend for all three rock types, symbol sizes and plumes
def marker_handle(marker, label, mfc, mec='k', ms=8):
    return plt.Line2D([0], [0], marker=marker, ls='None', mfc=mfc, mec=mec, ms=ms, label=label)

fig.suptitle(f'Each sample reconstructed to its own age, based on {model_name}',
             fontsize=14, fontweight='bold', y=0.99, va='top')

# plt.savefig(fig_path + f'Individual_50Myr_{age_start}_{age_start - 500}_muller.png', dpi=300, bbox_inches='tight')

plt.show()
