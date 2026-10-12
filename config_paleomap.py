
from paths import *
import gplately
import pygplates
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from plate_model_manager import PlateModelManager
from sklearn.neighbors import BallTree
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

R_EARTH = 6371.0  # km

def make_plate_reconstruction_and_plot(model_name="Muller2019", projection=ccrs.Orthographic(-110, 15), time=50, ax=None):
    # --- 1. Set up the plate reconstruction model and plot topologies ---  
    pm_manager = PlateModelManager()
    plate_model = pm_manager.get_model(model_name, data_dir="plate-model-repo")
    rotation_model = plate_model.get_rotation_model()
    topology_features = plate_model.get_topologies()
    static_polygons = plate_model.get_static_polygons()

    model = gplately.PlateReconstruction(rotation_model, topology_features, static_polygons)

    subduction_data = model.tessellate_subduction_zones(time)
    ridge_data = model.tessellate_mid_ocean_ridges(time)

    # Obtain geometry shapefiles with gdownload
    coastlines = plate_model.get_coastlines()
    continents = plate_model.get_continental_polygons()
    COBs = plate_model.get_COBs()
   
    # Call the PlotTopologies object
    gplot = gplately.PlotTopologies(model, coastlines=coastlines, continents=continents, COBs=COBs, time=time)

    # Set up a GeoAxis plot
    # fig = plt.figure(figsize=(10, 8), dpi=100)
    # ax = fig.add_subplot(111, projection=ccrs.Mollweide(190)) # before 1100
    # ax = fig.add_subplot(111, projection=ccrs.Orthographic(-110, -5)) # before 1100
    
    if ax is None:
        fig = plt.figure(figsize=(10, 8), dpi=100)
        ax = fig.add_subplot(1, 1, 1, projection=projection)

    ax.gridlines(color='0.7',linestyle='--', 
                      xlocs=np.arange(-180,180,30), ylocs=np.arange(-90,90,30),
                      x_inline=False, y_inline=False)

    # plt.title('Plate reconstruction at %i Ma' % (time))

    # Plot shapefile features, subduction zones and MOR boundaries at 50 Ma
    gplot.time = time # Ma
    gplot.plot_continent_ocean_boundaries(ax, color='b', alpha=0.05)
    gplot.plot_continents(ax, facecolor='palegoldenrod', alpha=0.2)
    gplot.plot_coastlines(ax, color='DarkKhaki')
    gplot.plot_ridges(ax, color='red', alpha=0.5)
    gplot.plot_transforms(ax, color='red', alpha=0.5)
    gplot.plot_trenches(ax, color='k')
    gplot.plot_subduction_teeth(ax, color='k')
    ax.set_global()

    return model, ax

# --- 3. Create pygplates point features ---
def create_point_feature(lon, lat):
    point = pygplates.PointOnSphere(lat, lon)  # note: (lat, lon) order!
    feature = pygplates.Feature()
    feature.set_geometry(point)
    return feature

def obtain_paleo_coordinates(df, model, reconstruction_time,
                             lon_col='longitude', lat_col='latitude'):
    """
    Reconstruct points to paleo-positions.

    reconstruction_time can be:
      - a scalar (all points reconstructed to the same time), or
      - an array-like of the same length as df (each point reconstructed
        to its own time, e.g. its formation age).
    Returns (rlons, rlats) as numpy arrays aligned with df's rows.
    """
    lons = df[lon_col].to_numpy(dtype=float)
    lats = df[lat_col].to_numpy(dtype=float)

    # Scalar time: one call is enough
    if np.isscalar(reconstruction_time):
        gpts = gplately.Points(model, lons, lats)
        rlons, rlats = gpts.reconstruct(float(reconstruction_time), return_array=True)
        return np.asarray(rlons), np.asarray(rlats)

    # Per-point times: reconstruct each group of identical ages together
    times = np.asarray(reconstruction_time, dtype=float)
    if len(times) != len(df):
        raise ValueError("reconstruction_time must be a scalar or match the number of rows in df")

    rlons = np.full(len(df), np.nan)
    rlats = np.full(len(df), np.nan)

    valid = ~(np.isnan(times) | np.isnan(lons) | np.isnan(lats))
    for t in np.unique(times[valid]):
        idx = np.where(valid & (times == t))[0]
        gpts = gplately.Points(model, lons[idx], lats[idx])
        rl, rb = gpts.reconstruct(float(t), return_array=True)
        rlons[idx] = rl
        rlats[idx] = rb

    return rlons, rlats


def reconstruct_at_own_age(df, model):
    """Reconstruct each point to its own age_ma (rounded to 1 Myr).
    Returns (rlons, rlats) as numpy arrays aligned with df's rows."""
    ages = np.round(df['age_ma'].to_numpy(dtype=float))
    rlons = np.full(len(df), np.nan)
    rlats = np.full(len(df), np.nan)
    for t in np.unique(ages[~np.isnan(ages)]):
        idx = np.where(ages == t)[0]
        rl, rb = obtain_paleo_coordinates(df.iloc[idx], model, t)
        rlons[idx] = rl
        rlats[idx] = rb
    return rlons, rlats

def nearest_distance_km(plon, plat, flon, flat):
    """
    Compute the nearest distance (in km) from each point to a set of reference points.

    Parameters:
    plon, plat : array-like
        Longitudes and latitudes of the points to query. [sample coordinates]
    flon, flat : array-like
        Longitudes and latitudes of the reference points. [subduction zone coordinates]

    Returns:
    distances : numpy array
        Array of distances (in km) from each point to the nearest reference point.
    """
    tree = BallTree(np.radians(np.c_[flat, flon]), metric='haversine')
    d, _ = tree.query(np.radians(np.c_[plat, plon]), k=1)
    return d[:, 0] * R_EARTH


def distance_to_subduction_at_own_age(df, model, age_round=1.0):
    """Distance (km) from each reconstructed point to the nearest
    subduction zone at that point's own (rounded) age."""
    d_sz = np.full(len(df), np.nan)
    ages = np.round(df['age_ma'].to_numpy(dtype=float) / age_round) * age_round
    rlon = df['reconstructed_lon'].to_numpy(dtype=float)
    rlat = df['reconstructed_lat'].to_numpy(dtype=float)
    valid = ~(np.isnan(ages) | np.isnan(rlon) | np.isnan(rlat))

    for t in np.unique(ages[valid]):
        idx = np.where(valid & (ages == t))[0]
        sz = model.tessellate_subduction_zones(t, ignore_warnings=True)  # cols 0,1 = lon, lat
        if sz is not None and len(sz):
            d_sz[idx] = nearest_distance_km(rlon[idx], rlat[idx], sz[:, 0], sz[:, 1])
    return d_sz

def obtain_model(model_name = "Cao2024"):
    pm_manager = PlateModelManager()
    plate_model = pm_manager.get_model(model_name, data_dir="plate-model-repo")
    rotation_model = plate_model.get_rotation_model()
    topology_features = plate_model.get_topologies()
    static_polygons = plate_model.get_static_polygons()

    model = gplately.PlateReconstruction(rotation_model, topology_features, static_polygons)
    return model

def plate_max_rotation_time(model_name="Cao2024"):
    """Oldest time (Ma) with a rotation for each plate ID in the model's rotation files,
    i.e. the largest time in any rotation sequence where that plate is the moving plate.
    Returns a dict {plate_id: max_time}."""
    rot_files = PlateModelManager().get_model(model_name, data_dir="plate-model-repo").get_rotation_model()
    max_time = {}
    for rot_file in rot_files:
        for feature in pygplates.FeatureCollection(rot_file):
            pole = feature.get_total_reconstruction_pole()
            if pole is None:
                continue
            _, moving_plate, sampling = pole
            times = [t.get_time() for t in sampling.get_enabled_time_samples()]
            if times:
                max_time[moving_plate] = max(max_time.get(moving_plate, 0.0), max(times))
    return max_time


def place_labels(ax, lons, lats, labels, fontsize=7, color='red', marker_pt=5):
    """Label points on a map with little overlap. For each label, try positions
    around its point (close ones first, then further out with a leader line) and
    keep the one that overlaps least with labels already placed and with the points."""
    lons, lats = np.asarray(lons, dtype=float), np.asarray(lats, dtype=float)
    labels = [str(l) for l in labels]
    ok = np.isfinite(lons) & np.isfinite(lats)
    xy = ax.projection.transform_points(ccrs.PlateCarree(), lons[ok], lats[ok])[:, :2]
    labels = [l for l, k in zip(labels, ok) if k]
    vis = np.isfinite(xy).all(axis=1)
    xy, labels = xy[vis], [l for l, k in zip(labels, vis) if k]
    if not len(xy):
        return

    px = ax.figure.dpi / 72  # pixels per point
    pts = ax.transData.transform(xy)  # display coordinates (pixels)
    outline = ax.patch  # map outline (ellipse for Mollweide)
    h = fontsize * px
    r = marker_pt * px  # half size of a marker
    point_boxes = [(x - r, y - r, x + r, y + r) for x, y in pts]

    def overlap(a, b):
        w = min(a[2], b[2]) - max(a[0], b[0])
        hh = min(a[3], b[3]) - max(a[1], b[1])
        return w * hh if w > 0 and hh > 0 else 0.0

    # candidate offsets (points) and matching alignment
    dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]
    candidates = [(dx * d, dy * d, d) for d in (9, 15, 22) for dx, dy in dirs]

    placed = []
    # label crowded points first, so they get the best spots
    crowd = [np.sum(np.hypot(*(pts - p).T) < 30 * px) for p in pts]
    for i in np.argsort(crowd)[::-1]:
        x, y = pts[i]
        w = 0.62 * fontsize * len(labels[i]) * px
        best = None
        for dx, dy, d in candidates:
            ox, oy = x + dx * px, y + dy * px
            x0 = ox if dx > 0 else ox - w if dx < 0 else ox - w / 2
            y0 = oy if dy > 0 else oy - h if dy < 0 else oy - h / 2
            box = (x0, y0, x0 + w, y0 + h)
            cost = sum(overlap(box, b) for b in placed)
            cost += sum(overlap(box, b) for j, b in enumerate(point_boxes) if j != i)
            corners = [(box[0], box[1]), (box[0], box[3]), (box[2], box[1]), (box[2], box[3])]
            if not all(outline.contains_point(c) for c in corners):
                cost += w * h  # outside the map outline
            cost += 0.01 * d  # prefer close positions
            if best is None or cost < best[0]:
                best = (cost, dx, dy, d, box)
        _, dx, dy, d, box = best
        placed.append(box)
        ax.annotate(labels[i], xy=xy[i], xycoords='data', xytext=(dx, dy), textcoords='offset points',
                    ha='left' if dx > 0 else 'right' if dx < 0 else 'center',
                    va='bottom' if dy > 0 else 'top' if dy < 0 else 'center',
                    fontsize=fontsize, color=color, zorder=30,
                    # arrow from the centre of the symbol (xy) to the label
                    arrowprops=dict(arrowstyle='<-', color=color, lw=0.5,
                                    mutation_scale=6, shrinkA=1, shrinkB=0, patchA=None,
                                    # end at the label corner nearest the symbol
                                    relpos=(0 if dx > 0 else 1 if dx < 0 else 0.5,
                                            0 if dy > 0 else 1 if dy < 0 else 0.5)))


def plot_dataframe(df, age_range, ax, style_map, size=50,
                   type='t/p', model_name='Cao2023',
                   time=0, proj=ccrs.Mollweide(central_longitude=190), 
                   model=None, own_age=False, plot_label=False):
    """
    this function will plot df for a given age range on a given axis with a given projection and time.
    size: the marker size for the plotted points.

    time: the geological time (in Ma) at which to plot the background map.
    type: the type of data being plotted (e.g., 'anor', 'a-type', 't/p').

    proj: the cartopy projection to use for plotting.
    model: if given, the background map is assumed to be already drawn on ax and is not redrawn.
    
    own_age: if True, each point is reconstructed to its own age_ma instead of time.
    plot_label: if True, labels will be plotted for each point.

    """
    
    age_min, age_max = age_range  # Ma
    
    # panel chosen by recon_time when available (a sample capped at its plate's oldest
    # rotation goes on the map of that time), otherwise by age_ma
    t_col = 'recon_time' if (own_age and 'recon_time' in df) else 'age_ma'
    df_i = df[(df[t_col] > age_min) & (df[t_col] <= age_max) 
              & (df['latitude'].notnull()) & (df['longitude'].notnull())]
    ## print the number of samples in the given age range
    print(f"Number of '{type}' samples in age range {age_min}-{age_max} Ma: {len(df_i)}")

    if model is None:
        model_i, _ = make_plate_reconstruction_and_plot(model_name=model_name, projection=proj, 
                                                        time=time, ax=ax)
    else:
        model_i = model
    if not df_i.empty:
        # remove those with NAN latitude or longitude
        df_i = df_i[df_i['latitude'].notnull() & df_i['longitude'].notnull()]
        if own_age and 'recon_time' in df_i:
            # own age, or the plate's oldest rotation time if the sample is older (see recon_time above)
            rlons_pt_i, rlats_pt_i = obtain_paleo_coordinates(df_i, model_i, np.round(df_i['recon_time'].to_numpy(float)))
        elif own_age:
            rlons_pt_i, rlats_pt_i = reconstruct_at_own_age(df_i, model_i)
        else:
            rlons_pt_i, rlats_pt_i = obtain_paleo_coordinates(df_i, model_i, time)
        rlons_pt_i, rlats_pt_i = np.asarray(rlons_pt_i), np.asarray(rlats_pt_i)

        if type == 't/p': ## t/p data will be colored by their t/p ratios
            huht_ind = df_i['cato'] == 'HUHT'
            ## for HUHT data, using star, while the rest using circle
            ax.scatter(rlons_pt_i[huht_ind], rlats_pt_i[huht_ind], marker='*', 
                       c=df_i.loc[huht_ind, 't_p'], cmap=plt.get_cmap(style_map['t/p']['color']), 
                       s=150, edgecolor='k', vmin=0, vmax=2500, alpha=0.8,
                       transform=ccrs.PlateCarree(), label='HUHT', zorder=20)

            sc_i = ax.scatter(rlons_pt_i[~huht_ind], rlats_pt_i[~huht_ind], marker=style_map['t/p']['marker'],
                                c=df_i.loc[~huht_ind, 't_p'], cmap=plt.get_cmap(style_map['t/p']['color']), 
                                s=size, edgecolor='k', vmin=0, vmax=2500, alpha=0.8,
                                transform=ccrs.PlateCarree(), label=style_map['t/p']['label'], 
                                zorder=style_map['t/p']['zorder'])
            
            with_age = df_i['age_ma'].notna() 
            if plot_label:
                place_labels(ax, rlons_pt_i[with_age], rlats_pt_i[with_age], df_i.loc[with_age, 'name'])
            
            return sc_i  # return the scatter plot object for colorbar or legend
            
        elif type == 'a-type' or type == 'anor': ## distinguished based on with area data or not
            
            has_area = df_i['area'].notna() ## has area data
            no_area = df_i['area'].isna() ## no area data

            # Sizes for points with area data
            sizes = np.select([df_i.loc[has_area, 'area'] <= 1000, df_i.loc[has_area, 'area'] <= 5000], 
                              [30, 70], default=120) # size 120 for area > 5000, 70 for area between 1000 and 5000, 30 for area < 1000

            # Plot points WITHOUT area data as diamonds
            ax.scatter(rlons_pt_i[no_area], rlats_pt_i[no_area],
                      marker=style_map[type]['marker'], c='w', s=50, alpha=0.8,
                      ec=style_map[type]['color'], transform=ccrs.PlateCarree(), zorder=style_map[type]['zorder'])
            
            # Plot points WITH area data
            ax.scatter(rlons_pt_i[has_area], rlats_pt_i[has_area],
                    marker=style_map[type]['marker'], c=style_map[type]['color'],
                    s=sizes, ec='k', alpha=0.8, transform=ccrs.PlateCarree(),
                    label=style_map[type]['label'], zorder=style_map[type]['zorder'])

            # number labels placed around each point to limit overlap
            with_age = df_i['age_ma'].notna() 
            if plot_label:
                place_labels(ax, rlons_pt_i[with_age], rlats_pt_i[with_age], df_i.loc[with_age, 'name'])
 
        else: ## ploted using the same color and marker for each type
            ax.scatter(rlons_pt_i, rlats_pt_i, marker=style_map[type]['marker'],
                                c=style_map[type]['color'], s=size, edgecolor='k', alpha=0.8,
                                transform=ccrs.PlateCarree(), label=style_map[type]['label'], 
                                zorder=style_map[type]['zorder'])
            
            with_age = df_i['age_ma'].notna() 
            if plot_label:
                place_labels(ax, rlons_pt_i[with_age], rlats_pt_i[with_age], df_i.loc[with_age, 'name'])

def get_clean_data(file_name):
    """
    Get clean data from the Excel file, limiting reconstruction times based on plate rotations.
    Returns three dataframes: df_anor, df_aty, df_pt.
    """
    name_ano = 'anorthosite'
    name_atype = 'atype'
    name_ht = 'HT-UHT'

    df_anor = pd.read_excel(data_path + file_name, sheet_name=name_ano)
    df_aty = pd.read_excel(data_path + file_name, sheet_name=name_atype) ## contains all the data points
    df_pt = pd.read_excel(data_path + file_name, sheet_name=name_ht)

    ## Limit reconstruction times by how far back each sample's plate has rotations.
    ## If a sample is older than its plate's oldest rotation (plate_max_rotation_ma):
    ##   - by more than max_age_gap Myr: the sample is removed from the plots
    ##   - by up to max_age_gap Myr: it is plotted at its position at plate_max_rotation_ma
    ## Otherwise it is plotted at its position at its own age (recon_time = age_ma).
    max_age_gap = 100  # Myr
    rotation_model_name = "Cao2024"
    plate_max_time = plate_max_rotation_time(model_name=rotation_model_name)
    recon_model = obtain_model(model_name=rotation_model_name)

    for d, d_name in [(df_anor, name_ano), (df_aty, name_atype), (df_pt, name_ht)]:
        has_loc = d['latitude'].notnull() & d['longitude'].notnull()
        d['plate_id'] = np.nan
        d.loc[has_loc, 'plate_id'] = gplately.Points(recon_model, d.loc[has_loc, 'longitude'].to_numpy(float),
                                                    d.loc[has_loc, 'latitude'].to_numpy(float)).plate_id
        d['plate_max_rotation_ma'] = d['plate_id'].map(plate_max_time)
        d['recon_time'] = np.fmin(d['age_ma'], d['plate_max_rotation_ma'])  # own age, capped by the plate's rotations
        too_old = (d['age_ma'] - d['plate_max_rotation_ma']) > max_age_gap
        capped = (d['age_ma'] > d['plate_max_rotation_ma']) & ~too_old
        print(f"{d_name}: removed {too_old.sum()} samples > {max_age_gap} Myr older than their plate's rotations "
            f"(names {d.loc[too_old, 'name'].tolist()}); {capped.sum()} plotted at plate_max_rotation_ma "
            f"(names {d.loc[capped, 'name'].tolist()})")
        d.drop(index=d.index[too_old], inplace=True)  # in place, so df_plot is df_anor etc. still holds

    return df_anor, df_aty, df_pt
