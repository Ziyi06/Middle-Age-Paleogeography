"""
Export reconstructed position of each point into an excel file 
"""
from paths import *
import pandas as pd
import os
import numpy as np
import gplately
import pygplates
from plate_model_manager import PlateModelManager
from config_paleomap import obtain_paleo_coordinates, distance_to_subduction_at_own_age, obtain_model, \
    distance_to_plume, plate_max_rotation_time

name_ano = 'anorthosite'
name_atype = 'atype'
name_ht = 'HT-UHT'

df_anor = pd.read_excel(data_path + 'all_data_compiled.xlsx', sheet_name=name_ano)
df_aty = pd.read_excel(data_path + 'all_data_compiled.xlsx', sheet_name=name_atype) 
df_pt = pd.read_excel(data_path + 'all_data_compiled.xlsx', sheet_name=name_ht)

model = obtain_model(model_name="Cao2024")

def obtain_plate_id(df, model, lon_col='longitude', lat_col='latitude'):
    """Plate ID of each sample, from the static polygon its present-day location
    falls in (the same plate gplately uses to reconstruct it). NaN if no location."""
    lons = df[lon_col].to_numpy(dtype=float)
    lats = df[lat_col].to_numpy(dtype=float)
    plate_id = np.full(len(df), np.nan)
    valid = ~(np.isnan(lons) | np.isnan(lats))
    if valid.any():
        plate_id[valid] = gplately.Points(model, lons[valid], lats[valid]).plate_id
    return pd.array(plate_id, dtype='Int64')  # whole numbers, blank when missing


plate_max_time = plate_max_rotation_time(model_name="Cao2024")

for df in [df_anor, df_aty, df_pt]:
    df['plate_id'] = obtain_plate_id(df, model)
    df['plate_max_rotation_ma'] = df['plate_id'].map(plate_max_time)  # oldest rotation of that plate
    df['rotation_exceeds_age'] = df['plate_max_rotation_ma'] >= df['age_ma']  # False: sample older than its plate's rotations
    df['reconstructed_lon'], df['reconstructed_lat'] = obtain_paleo_coordinates(df, model, df['age_ma'])
    df['dist_subduction_km'] = distance_to_subduction_at_own_age(df, model)

# --- Export ---
out_file = data_path + 'all_data_compi_recons.xlsx'
mode = 'a' if os.path.exists(out_file) else 'w'
writer_kwargs = {'if_sheet_exists': 'replace'} if mode == 'a' else {}

with pd.ExcelWriter(out_file, mode=mode, engine='openpyxl', **writer_kwargs) as writer:
    df_anor.to_excel(writer, index=False, sheet_name='Anorthosites')
    df_aty.to_excel(writer, index=False, sheet_name='A-type granites')
    df_pt.to_excel(writer, index=False, sheet_name='HT-UHT rocks')
