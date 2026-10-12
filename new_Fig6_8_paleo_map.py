
from paths import *
import numpy as np
import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from config_paleomap import make_plate_reconstruction_and_plot
from config_paleomap import get_clean_data, plot_dataframe
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

matplotlib.rcParams['font.family'] = 'Arial'

style_map = {'a-type':   {'marker': 'D', 'label': 'A-type', 'color': 'violet', 'zorder': 9},
             'anor':   {'marker': 's', 'label': 'Anorthosites', 'color': 'cornflowerblue', 'zorder': 10},
             't/p':   {'marker': 'o', 'label': 'Metamorphic P/T', 'color': 'bwr', 'zorder': 15}}

size = 50 ## this is marker size
fontsize = 12

def plot_paleo_map(time=0, age_range=(800, 1800), model_name='Muller2019',
                   projection=ccrs.Mollweide(central_longitude=190),
                   if3plot=0, iflegend=0, ifsavefig=0, ifshow=1,
                   own_age=False, plot_label=False):
    """
    This function will plot the paleo map for a given time, age range, and projection.
    It will plot the anorthosite data, A-type data, and P/T data on the same map.
    if3plot: whether to plot 3 subplots (present-day maps) with legend on the right bottom of the whole figure,
                          or 4 subplots (1300, 1600) with legend on each subplot.
    iflegend: whether to add legend and colorbar for the whole figure
    ifsavefig: whether to save the figure
    ifshow: whether to show the figure
    """

    if if3plot:
        fig_range = (1, 4) # only 3 panels for time = 0
        m = 0
        fig = plt.figure(figsize=(14, 7))
        plt.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95,
                        hspace=0.06, wspace=0.02) #hspace for vertical space, wspace for horizontal space

        ## 3plot to show all present-day maps that include all data without filtering by age
        name_ano = 'anorthosite'
        name_atype = 'atype'
        name_ht = 'HT-UHT'

        df_anor = pd.read_excel(data_path + 'all_data_compiled.xlsx', sheet_name=name_ano)
        df_aty = pd.read_excel(data_path + 'all_data_compiled.xlsx', sheet_name=name_atype) ## contains all the data points
        df_pt = pd.read_excel(data_path + 'all_data_compiled.xlsx', sheet_name=name_ht)

    
    else: 
        fig_range = (1, 5)  
        m = 1
        fig = plt.figure(figsize=(8.5, 8))   
        plt.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95,
                        hspace=0.06, wspace=0.06) #hspace for vertical space, wspace for horizontal space
        df_anor, df_aty, df_pt = get_clean_data('all_data_compiled.xlsx')
    
    axes_flat = [] # it needs to have projection for later plotting 
    for i in range(fig_range[0], fig_range[1]):        # panels 1..3 or 4   
        ax = fig.add_subplot(2, 2, i, projection=projection)
        ax.set_global()          # show the whole globe
        axes_flat.append(ax)

    # Latitude labels only, left side only
    gl = axes_flat[0].gridlines(draw_labels={"left": True,      # latitude labels on left
                                "right": False, "top": False, "bottom": False}, 
                                xlocs=[], ylocs=[-60, -30, 0, 30, 60],
                                x_inline=False, y_inline=False, linewidth=0)
    gl.right_labels = gl.top_labels = gl.bottom_labels = False
    gl.left_labels = True
    gl.ylabel_style = {"size": 8}
    gl.yformatter = LatitudeFormatter()

    lon0 = projection.proj4_params.get("lon_0", 0)
    lon0 = (lon0 + 180) % 360 - 180 
    axes_flat[0].text(0.5, -0.02, f"{abs(lon0):.0f}°{'W' if lon0 < 0 else 'E'}",
            transform=axes_flat[0].transAxes, ha='center', va='top', fontsize=8)

    ## plot in red stars the following four points at 1.59, 1.64, 1.78 and 1.5
    
    # special_points = [(40, -115), (19, -165), (8, -77), (-22, -94)] # 1.6 Ga, lat, lon
    # special_points = [(-82, -2), (186,  32)]  # P1-2 1.65 Ga
    # special_points = [(-118, 34), (-98, -8)]  # P3-P4, lon, lat at 1.5 Ga

    # special_points1 = [(-90, 23), (-145, 18)]  # P6-P7, lon, lat at 1.3 Ga
    # special_points2 = [(-125,  -1), (-100, -10)]  # P5 1.3 Ga

    # special_points1 = [(-93, 23), (-143, 18)]  # P6-P7, lon, lat at 1.35 Ga
    # special_points2 = [(-125,  -1), (-100, -17)]  # P5 1.35 Ga

    # for lon, lat in special_points1:
    #     axes_flat[0].plot(lon, lat, marker='*', color='pink', mec='darkred', 
    #                       markersize=25, transform=ccrs.Geodetic(), zorder=30)
    # for lon, lat in special_points2:
    #     axes_flat[0].scatter(lon, lat, marker='*', s=625, facecolor='pink', edgecolor='darkred',
    #             linestyle='--', transform=ccrs.PlateCarree(), zorder=25)

    ## Step 2: plot the data on each subplot
       
    ## first plot the anorthosite data on the first subplot
    plot_dataframe(df_anor, age_range, axes_flat[0+m], style_map, size=size,
                   type='anor',model_name=model_name, time=time, proj=projection, 
                   own_age=own_age, plot_label=plot_label)  

    ## A-type data on the second subplot
    plot_dataframe(df_aty, age_range, axes_flat[1+m], style_map, size=size,
                   type='a-type', model_name=model_name, time=time, proj=projection, 
                   own_age=own_age, plot_label=plot_label)  

    # ## plot P/T data on the last subplot
    sc_pt = plot_dataframe(df_pt, age_range, axes_flat[2+m], style_map, size=size,
                           type='t/p', model_name=model_name, time=time, 
                           proj=projection, own_age=own_age, plot_label=plot_label)  

    if if3plot == False:
        make_plate_reconstruction_and_plot(model_name=model_name, projection=projection, 
                                            time=time, ax=axes_flat[0])

    if iflegend:  ## Step 3: add legends and colorbar for the whole figure
        if if3plot:  ## combine all legend and plot on the bottom right
            handles = []
        
            ## creat legend for anorthosite data with different sizes based on area
            size_classes = [(30, '< 1000'), (70, '1000-5000'), (120, '> 5000')]
            for s, area_lab in size_classes:
                handles.append(plt.Line2D([0], [0],
                                        marker=style_map['anor']['marker'],
                                        color=style_map['anor']['color'],
                                        ls='None',
                                        mfc=style_map['anor']['color'],
                                        mec='k',
                                        ms=np.sqrt(s),
                                        label=f"{style_map['anor']['label']} (area {area_lab} km²)"))

            handles.append(plt.Line2D([0], [0], marker=style_map['anor']['marker'], color='w',
                                        ls='None',
                                        mfc='w',
                                        mec=style_map['anor']['color'],
                                        ms=np.sqrt(50),
                                        label=f"{style_map['anor']['label']} (without area data)"))

            ## creat legend for A-type data with different sizes based on area
            size_classes = [(30, '< 1000'), (70, '1000-5000'), (120, '> 5000')]
            for s, area_lab in size_classes:
                handles.append(plt.Line2D([0], [0],
                                        marker=style_map['a-type']['marker'],
                                        color=style_map['a-type']['color'],
                                        ls='None',
                                        mfc=style_map['a-type']['color'],
                                        mec='k',
                                        ms=np.sqrt(s),
                                        label=f"{style_map['a-type']['label']} (area {area_lab} km²)"))
            handles.append(plt.Line2D([0], [0], marker=style_map['a-type']['marker'], color='w',
                                        ls='None',
                                        mfc='w',
                                        mec=style_map['a-type']['color'],
                                        ms=np.sqrt(50),
                                        label=f"{style_map['a-type']['label']} (without area data)"))

            handles.append(plt.Line2D([0], [0], marker=style_map['t/p']['marker'], color='w',
                            label='High-T/P amphibolite-granulite\nfacies metamorphic rocks',
                            ls='None', mfc='w', mec='k', ms=8))
            handles.append(plt.Line2D([0], [0], marker='*', color='w',label='UHT rocks',
                            ls='None', mfc='w', mec='k', ms=12))
         
                
            leg = fig.legend(handles=handles, loc='lower right', fontsize=12, framealpha=1, frameon=True,
                    bbox_to_anchor=(0.84, 0.11),   # figure coordinates, 0-1
                    columnspacing=0.3, handlelength=0.6, labelspacing=0.5)
        
            ## create legend for the colorbar for P/T data
            cbaxins = inset_axes(axes_flat[2+m], width="20%",height="10%", loc='lower left',
                                        bbox_to_anchor=(0.66, 0.08, 0.5, 0.3),   # [x0, y0, width, height]
                                        bbox_transform=fig.transFigure, borderpad=0)
        
            # add coloarbar legend for the whole plot
            cbar = fig.colorbar(sc_pt, cax=cbaxins,orientation='horizontal', ticks=[0, 1250, 2500])
            cbar.set_label('T/P (°C/GPa)', size=10,  labelpad=5, rotation=0)
            cbar.ax.tick_params(labelsize=8, direction='out')

            for ax, label in zip([axes_flat[0], axes_flat[1], axes_flat[2]], ['A', 'B', 'C']):
                ax.text(0.08, 0.94, label, transform=ax.transAxes,
                            fontsize=14, fontweight='bold', va='top', ha='right',
                            bbox=dict(facecolor="#f6f6f6", edgecolor='k',
                            boxstyle='square,pad=0.2'))
            
        else:
            #legend for axes_flat[1]:
            ## creat legend for anorthosite data with different sizes based on area
            size_classes = [(30, '< 1000'), (70, '1000-5000'), (120, '> 5000')]

            handles2 = []
            for s, area_lab in size_classes:
                handles2.append(plt.Line2D([0], [0],
                                        marker=style_map['anor']['marker'],
                                        color=style_map['anor']['color'],
                                        ls='None',
                                        mfc=style_map['anor']['color'],
                                        mec='k',
                                        ms=np.sqrt(s),
                                        label=f"{style_map['anor']['label']} ({area_lab} km²)"))
            handles2.append(plt.Line2D([0], [0], marker=style_map['anor']['marker'], color='w',
                                                    ls='None',
                                                    mfc='w',
                                                    mec=style_map['anor']['color'],
                                                    ms=np.sqrt(50),
                                                    label=f"{style_map['anor']['label']} (without area data)"))
            
            axes_flat[1].legend(handles=handles2, loc='lower right', fontsize=fontsize-4, framealpha=.9, frameon=True,
                            columnspacing=0.3, handlelength=0.6, labelspacing=0.5)
            
            #Legend for axes_flat[2]: ## for A-type data with different sizes based on area
            handles3 = []
            for s, area_lab in size_classes:
                handles3.append(plt.Line2D([0], [0],
                                        marker=style_map['a-type']['marker'],
                                        color=style_map['a-type']['color'],
                                        ls='None',
                                        mfc=style_map['a-type']['color'],
                                        mec='k',
                                        ms=np.sqrt(s),
                                        label=f"{style_map['a-type']['label']} ({area_lab} km²)"))
            handles3.append(plt.Line2D([0], [0], marker=style_map['a-type']['marker'], color='w',
                                        ls='None',
                                        mfc='w',
                                        mec=style_map['a-type']['color'],
                                        ms=np.sqrt(50),
                                        label=f"{style_map['a-type']['label']} (without area data)"))
            axes_flat[2].legend(handles=handles3, loc='lower right', fontsize=fontsize-4, framealpha=.9, frameon=True,
                            columnspacing=0.3, handlelength=0.6, labelspacing=0.8)


            # legend for axes_flat[3]:
            ## create legend for the colorbar for P/T data
            cbaxins = inset_axes(axes_flat[3], width="20%",height="10%", loc='lower right',
                                        bbox_to_anchor=(0.1, 0.15, 0.8, 0.5),   # [x0, y0, width, height]
                                        bbox_transform=axes_flat[3].transAxes, borderpad=0)
        
            # add coloarbar legend for the whole plot
            cbar = fig.colorbar(sc_pt, cax=cbaxins,orientation='horizontal', ticks=[0, 1250, 2500])
            cbar.set_label('T/P (°C/GPa)', size=fontsize-4,  labelpad=5, rotation=0)
            cbar.ax.tick_params(labelsize=fontsize-4, direction='out')

            # white background + black border for the colorbar axes
            for spine in cbaxins.spines.values():
                spine.set_visible(True)
                spine.set_edgecolor('k')
                spine.set_linewidth(1)

            cbar.ax.xaxis.label.set_backgroundcolor('white')
            for t in cbar.ax.get_xticklabels():
                t.set_backgroundcolor('white')
            cbar.solids.set_zorder(0)
            for spine in cbaxins.spines.values():
                spine.set_zorder(3)

    ## addd a plt title for the whole figure
    fig.suptitle('Reconstruction at %.2f Ga' % (0.001 * time)
                 +' for rocks of %.1f-%.1f Ga' % (0.001*age_range[1], 0.001*age_range[0])
                 +' based on '+ model_name, 
                 fontsize=14, fontweight='bold', y=0.99)
    # remove the fix 2:1 ratio
    for ax in axes_flat:
        ax.set_aspect('auto')

    if ifsavefig:
        plt.savefig(fig_path + 'new_Fig6_paleo_map_'+f'{time}'+'.png', dpi=300, bbox_inches='tight')
    if ifshow:
        plt.show()

model_name="Cao2024"   
loc_list = [ccrs.Mollweide(central_longitude=140), ccrs.Orthographic(140, 0), 
            ccrs.Orthographic(-125, 15), ccrs.Orthographic(-125, 15),
            ccrs.Orthographic(-125, 15)]

# model_name="Muller2025"  
# loc_list = [ccrs.Mollweide(central_longitude=140), ccrs.Orthographic(0, -15), 
#             ccrs.Orthographic(-80, 15), ccrs.Orthographic(-75, 15)]

set1 = [0, [800, 1800], loc_list[0]]  # the present-day map with all samples between 800-1800 Ma
set2 = [1000, [900, 1100], loc_list[1]]  # the paleo map at 1000 Ma with all samples between 900-1100 Ma
set3 = [1350, [1300, 1400], loc_list[2]]  # the paleo map at 1350 Ma with all samples between 1300-1400 Ma
set4 = [1500, [1400, 1600], loc_list[3]]  # the paleo map at 1500 Ma with all samples between
set5 = [1650, [1600, 1700], loc_list[4]]  # the paleo map at 1650 Ma with all samples between 1600-1700 Ma

set = set5

## choice one: ccrs.Mollweide(central_longitude=190) and if3plot=1, to see broad distribution of all samples
## choice two: use more rounded projection and if3plot=0, to see more details of the distribution of samples at each time slice

plot_paleo_map(time=set[0], age_range=set[1], model_name=model_name, projection=set[2],
               if3plot=0, iflegend=1, ifsavefig=1, ifshow=1, 
               own_age=0, plot_label=0) 