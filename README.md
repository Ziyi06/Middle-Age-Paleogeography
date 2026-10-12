# Middle-Age-Paleogeography

This folder contains three scripts that reconstruct the samples in all_data_compiled.xlsx to their
positions at the time they formed, using the Cao et al. (2024) 1.8 Ga plate model, and then
(1) export the reconstructed positions and related quantities to Excel, and (2) plot them on
paleogeographic maps.
  new_export_paleo.py       -> Excel table of reconstructed positions, plate IDs and distances
  new_Fig6_8_paleo_map.py   -> present-day map and single-time paleomaps (Figures 6-8)
  new_FigS_indi_combine.py  -> 5 x 2 maps in 50-Myr steps, all three rock types together

All three use shared functions in config_paleomap.py and folder paths in paths.py, so these two
files must be in the same folder as the scripts.


1. SETUP
--------

Python 3.11 with these packages (versions used for the figures in brackets):
  gplately (2.0.0), pygplates (1.0.0), plate-model-manager (1.3.2), cartopy (0.25.0),
  matplotlib (3.11.1), pandas (3.0.5), numpy (2.4.6), scikit-learn (1.9.1), openpyxl (3.1.5)

Steps:
  1. Put all_data_compiled.xlsx in a folder called Data/ next to the scripts.
  2. Create a folder called Figures/ next to the scripts (for saved figures).
  3. Edit paths.py so that proj_path points to the folder holding the scripts
     (data_path = proj_path + 'Data/', fig_path = proj_path + 'Figures/').
  4. Run a script from that folder, e.g.  python new_export_paleo.py

The plate model is downloaded automatically by plate-model-manager the first time a script runs
(internet needed once) into a folder called plate-model-repo/ next to the scripts.
Plate model: "Cao2024" (Cao et al., 2024, 1.8 Ga - present). Some figure scripts can also be
switched to "Muller2025" with the model_name setting.


2. INPUT DATA: all_data_compiled.xlsx
------------------------------------

Three sheets, one per rock type. Columns used by the scripts:

  Sheet         Rows  Columns used
  anorthosite     81  name, age_ma, latitude, longitude, area
  atype          116  name, age_ma, latitude, longitude, area
  HT-UHT          58  name, age_ma, latitude, longitude, t_p, cato

  name       sample number, used as the label on maps and plots
  age_ma     formation age (Ma)
  latitude,  present-day location (decimal degrees); samples without a location are skipped
  longitude
  area       outcrop area (km2) of anorthosites / A-type granites; sets the symbol size
             (< 1000, 1000-5000, > 5000 km2); blank = plotted as an open symbol
  t_p        thermal gradient T/P (deg C/GPa) = T (deg C) / P (GPa); colours HT-UHT symbols
  cato       HT-UHT category: HUHT = ultrahigh-temperature (plotted as a star),
             HAG = high-T/P amphibolite-granulite facies (plotted as a circle)

Other columns (references, units, countries, etc.) are carried through unchanged.


3. HOW SAMPLES ARE RECONSTRUCTED
--------------------------------

Plate ID: each sample is assigned to the plate whose static polygon contains its present-day
location (gplately.Points).

Position at time of formation: each sample is rotated with its plate's rotations from the present
to its own age (age_ma, rounded to 1 Myr).

Oldest rotation of each plate (plate_max_rotation_ma): the oldest time in any rotation sequence
in which that plate is the moving plate, read from the model's rotation files.
Some samples are older than their plate's oldest rotation. When the map scripts read the data
with get_clean_data (config_paleomap.py):
  - older than the plate's oldest rotation by more than 100 Myr -> sample removed from the maps
  - older by up to 100 Myr -> plotted at its position at the plate's oldest rotation, and placed
    in the map panel for that time
  - otherwise -> plotted at its own age (recon_time = age_ma)
(The capping only matters when samples are plotted at their own age, as in
new_FigS_indi_combine.py; new_Fig6_8_paleo_map.py normally reconstructs all samples to one
map time.)
The removed and capped samples are listed (by name) in the console when a map script runs.
new_export_paleo.py does not remove anything; it reports the check in rotation_exceeds_age.


4. new_export_paleo.py
----------------------

Purpose: one table per rock type with reconstructed positions and distances.

Output: Data/all_data_compi_recons.xlsx, sheets "Anorthosites", "A-type granites",
"HT-UHT rocks". All input columns are kept and these are added:

  plate_id               plate the sample sits on (blank if no location)
  plate_max_rotation_ma  oldest rotation time of that plate (Ma)
  rotation_exceeds_age   True if the plate's rotations reach back to age_ma;
                         False if the sample is older than its plate's oldest rotation
                         (also False when there is no location)
  reconstructed_lon,     position at age_ma (decimal degrees)
  reconstructed_lat
  dist_subduction_km     distance to the nearest subduction zone at age_ma (km)
  distance_to_plume      distance to the nearest plume centre in the same 100-Myr window (km)
  which_plume            name of that plume (P1-P7)

dist_subduction_km: the model's subduction zones at the sample's age (rounded to 1 Myr) are
sampled as points about 6 km apart (gplately tessellate_subduction_zones), and the great-circle
distance (Earth radius 6371 km) from the reconstructed sample to the nearest of these points is
taken. It is the shortest distance in any direction, regardless of trench polarity.

distance_to_plume / which_plume: great-circle distance from the reconstructed sample to the
plume centres listed in plumes_loc (config_paleomap.py). A plume at time t is used for samples
with t - 50 < age_ma <= t + 50 Myr; the nearest one is reported. Plume positions are fixed
paleo-coordinates for that time (not moved with the plates). Samples with no plume in their
window (roughly younger than 1200 Ma or older than 1800 Ma) are left blank.

  Plume  Time (Ma)  Longitude  Latitude
  P1     1750, 1650    -82        -2
  P2     1650          186        32
  P3     1550         -110        38
  P4     1450          -94        -8
  P5_1   1350         -130        -1
  P5_2   1350         -100       -20
  P6     1350          -95        20
  P7     1250         -156        16

If the output file already exists, the three sheets are replaced and any other sheets are kept.


5. new_Fig6_8_paleo_map.py
-------------------------

Purpose: main-text maps (Figures 6-8): a present-day overview of all samples, and paleomaps
of the samples of one age range reconstructed to a single time.

Choose the map with  set = set1 ... set5  near the bottom of the script:

  Set   Map time   Samples shown      Projection
  set1  0 Ma       800-1800 Ma        Mollweide, centred on 140 E (present-day overview)
  set2  1000 Ma    900-1100 Ma        Orthographic, centred on 140 E, 0 N
  set3  1350 Ma    1300-1400 Ma       Orthographic, centred on 125 W, 15 N
  set4  1500 Ma    1400-1600 Ma       Orthographic, centred on 125 W, 15 N
  set5  1650 Ma    1600-1700 Ma       Orthographic, centred on 125 W, 15 N

A sample is included when (lower age) < age_ma <= (upper age).

Options of plot_paleo_map (in the call at the bottom of the script):
  if3plot     1 -> three panels (A anorthosites, B A-type granites, C HT-UHT rocks) with one
                   combined legend; use with set1. All samples are read directly from
                   all_data_compiled.xlsx (no plate-rotation check).
              0 -> 2 x 2 panels for a paleomap: top-left = plate reconstruction only (continents,
                   coastlines, plate boundaries and subduction zones at the map time), then
                   anorthosites, A-type granites and HT-UHT rocks, each with its own legend.
                   Samples are read with get_clean_data, so samples more than 100 Myr older
                   than their plate's oldest rotation are left out (section 3).
  own_age     0 -> every sample is reconstructed to the map time (used for Figures 6-8)
              1 -> every sample is reconstructed to its own age instead
  plot_label  1 -> sample numbers next to the symbols
  iflegend    1 -> legends and T/P colorbar
  ifsavefig   1 -> save to Figures/new_Fig6_paleo_map_<map time>.png (300 dpi)
  ifshow      1 -> show the figure on screen

The number of samples of each rock type in the chosen age range is printed in the console.
Symbols are the same as in new_FigS_indi_combine.py (section 6).
The plume stars of Figures 6-8 are not drawn by this script; their positions are listed in
section 4 (plumes_loc in config_paleomap.py).


6. new_FigS_indi_combine.py
---------------------------

Purpose: paleogeographic maps through time, with ALL THREE rock types in every panel.

Layout: 5 rows x 2 columns, 50-Myr windows (panel A = first window, ... J = last). Mollweide
projection centred on 140 E. Each panel's background (continents, coastlines, plate boundaries,
subduction zones) is drawn at the middle of its window, and each sample is plotted at its
position at its own age (section 3). Choose the half with:
  period = 'old'    -> 1800-1300 Ma
  period = 'young'  -> 1300-800 Ma
Other settings:
  model_name     "Cao2024" (default) or "Muller2025"
  export_counts  True -> also write the number of samples of each rock type in each window to
                 Data/counts_indi_combine_<start>_<end>.xlsx (columns: window, map time,
                 Anorthosites, A-type granites, HT-UHT rocks, of which UHT (HUHT), Total).
                 Samples are counted exactly as on the maps (by the time they are plotted at,
                 with a location).

Symbols: anorthosites = blue squares, A-type granites = violet diamonds (both sized by area; open
symbol = no area data); HT-UHT = circles (HAG) and stars (HUHT), coloured by T/P (0-2500 deg C/GPa,
blue-white-red). Sample numbers are shown next to the symbols.

Output: the figure is shown on screen; the plt.savefig line at the end is commented out -
uncomment it to save to Figures/.


7. REFERENCES
-------------

Plate model: Cao, X., Collins, A.S., Pisarevsky, S., Flament, N., Li, S., Hasterok, D. and
Müller, R.D. (2024), Earth's tectonic and plate boundary evolution over 1.8 billion years,
Geoscience Frontiers, 15, 101922 ("Cao2024" in plate-model-manager / GPlately).
Software: GPlately and pyGPlates (EarthByte group); plate-model-manager.
