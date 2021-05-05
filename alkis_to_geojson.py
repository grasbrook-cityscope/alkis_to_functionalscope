import os
import geopandas as gpd
import matplotlib.pyplot as plt

cwd = os.getcwd()
shp_folder = cwd + '/SHP/'


def get_land_use_for_alkis_code(row):
    try:
        return alkis_translations[row.GFK]
    except KeyError:
        if (row.GFK <= 1024):
            return "residential"
        if (row.GFK < 2100):
            return "commercial"
        if (row.GFK <= 2200):
            return "industrial"
        if (row.GFK >= 3000):
            return "public use"

    return "unknown"


def get_city_scope_id(row):
    return "B-" + str(row.name)


def get_row_index(row):
    return row.name


def make_geojsons_for_city_scope():

    # read shape file with existing buildings (ALKIS)
    buildings_existing = gpd.read_file(shp_folder + "buildings_existing_focus_area_01-03.shp")
    buildings_existing.loc[:, 'is_existing'] = True
    buildings_existing = buildings_existing.to_crs("EPSG:4326")

    # keep only relevant rows : Keep "BEZEICH" == AX_Gebäude, Delete AX_Bauteil or GFK == 0
    # AX_Bauteil are irrelevant small building parts, often without allocated use (GFK)
    buildings_existing = buildings_existing[buildings_existing.BEZEICH == 'AX_Gebaeude']
    buildings_existing = buildings_existing[buildings_existing.GFK != 0]

    # keep only relevant columns
    buildings_existing = buildings_existing.filter(['id', 'AOG', 'GFK', 'geometry', 'GRF', 'is_existing'])

    # read shapefile with new buildings
    buildings_new = gpd.read_file(shp_folder + "buildings_4.shp")
    buildings_new.loc[:, 'is_existing'] = False

    # merge existing and new buildings to old buildings
    all_buildings = buildings_existing.append(buildings_new)
    all_buildings.reset_index(inplace=True, drop=True)  # replace indexes


    # add properties needed for cityScope
    # new column with building height, calculated from number of upperfloor stories
    all_buildings.loc[:, 'upper_floor_count'] = all_buildings["AOG"] - 1  # groundfloor is counted in AOG
    all_buildings.loc[:, 'building_height'] = all_buildings['upper_floor_count'] * 3 + 4  # assume 4m for groundlvl
    all_buildings.loc[:, 'area_planning_type'] = "building"
    all_buildings.loc[:, 'floor_area'] = all_buildings["GRF"]
    all_buildings["floor_area"].astype("float")
    all_buildings['id'] = all_buildings.apply(get_row_index, axis=1)
    all_buildings.loc[:, 'city_scope_id'] = all_buildings.apply(get_city_scope_id, axis=1)
    all_buildings.loc[:, 'land_use_detailed_type'] = all_buildings.apply(get_land_use_for_alkis_code, axis=1)

    # drop columns with alkis naming
    all_buildings = all_buildings.drop(columns=['GFK', 'GRF', 'AUG', 'AOG'])

    # plot buildings
    all_buildings.plot(column='land_use_detailed_type')
    plt.show()

    # include only buildings with upper floors in upperfloors.json
    upperfloor = all_buildings[all_buildings.upper_floor_count >= 1]
    upperfloor.to_file(cwd + "/upperfloor.json", driver='GeoJSON')

    groundfloor = all_buildings.drop(columns=['building_height'])  # building height col not needed for groundfloor.json
    groundfloor.to_file(cwd + "/groundfloor.json", driver='GeoJSON')



alkis_translations = {
    1000: "residential",
    1010: "residential",
    1011: "apartments",
    1012: "large apartments",
    1020: "dormitory",
    1022: "senior living",
    1024: "student dormitory",
    1100: "residential mixed use (general)",
    1120: "residential with retail and services",
    1130: "residential with commercial and industrial uses",
    1220: "medical practice",
    1230: "supermarket",
    1313: "allotment garden house",
    2000: "commercial",
    2010: "commercial and services",
    2020: "office",
    2050: "shop",
    2051: "department store",
    2052: "shopping center",
    2054: "retail",
    2055: "kiosk",
    2056: "drug store",
    2071: "hotel",
    2080: "restaurant",
    2081: "restaurant",
    2082: "hut",
    2083: "cafeteria",
    2084: "cafe",
    2085: "bakery",
    2086: "fast food",
    2087: "bar",
    2090: "leisure",
    2092: "movie theater",
    2095: "gambling hall",
    2100: "light industrial",
    2110: "manufacturing",
    2112: "production",
    2120: "workshop",
    2130: "gas station",
    2140: "warehouse",
    2143: "warehouse",
    2150: "logistics",
    2310: "commercial and services",
    2320: "commercial and industrial with residential",
    2420: "rail transport",
    2443: "lock",
    2460: "parking",
    2461: "parking garage",
    2463: "garage",
    2464: "vehicle depot",
    2500: "utilities",
    2510: "water utilities",
    2520: "electric utilities",
    2540: "telecommunications",
    2570: "gas utilities",
    2611: "water treatment",
    2612: "toilet",
    2620: "waste processing",
    2621: "waste storage",
    2622: "waste incineration",
    3000: "public",
    3010: "public administrative servcies",
    3013: "post office",
    3014: "customs",
    3021: "school",
    3023: "university",
    3025: "high school",
    3026: "elementary school",
    3030: "creative space",
    3033: "event space",
    3034: "museum",
    3037: "library",
    3040: "religious use",
    3041: "church",
    3046: "mosque",
    3053: "health center",
    3060: "social use",
    3061: "youth center",
    3062: "community center",
    3065: "daycare",
    3070: "public safety",
    3072: "fire station",
    3074: "bunker",
    3094: "u-bahn station",
    3210: "sports facility",
    3212: "sports facility"
}


if __name__ == "__main__":
    make_geojsons_for_city_scope()
