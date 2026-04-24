# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "geopandas",
#     "pyyaml",
#     "rustac",
#     "shapely",
# ]
# ///
import asyncio
import json
import pathlib

import geopandas as gpd
import rustac
import shapely
import yaml


CONFIG_PATH = pathlib.Path(__file__).parent / "generate-ahn-geoparquet.yaml"

CRS = "EPSG:28992"
STAC_VERSION = "1.1.0"
STAC_EXTENSIONS = ["https://stac-extensions.github.io/projection/v1.0.0/schema.json"]


async def main() -> None:

    config = load_config(CONFIG_PATH)
    resource_dir = (CONFIG_PATH.parent / config["resources"]["dir"]).resolve()
    output_dir = (CONFIG_PATH.parent / config["output_dir"]).resolve()
    output_dir.mkdir(exist_ok=True)

    assets_info = config["assets"]

    collections = []
    for collection_id, collection_info in config["collections"].items():
        resource_files = config["resources"]["files"][collection_id]
        start_datetime = collection_info["start_datetime"]
        end_datetime = collection_info["end_datetime"]
        assets = load_asset_urls(resource_dir, resource_files)
        items = generate_item_table(assets, assets_info)
        item_dicts = [
            create_item_dict(
                item_id, x.bbox, x.bbox_proj, x.geometry, x.assets, start_datetime, end_datetime,
                collection_id
            ) for item_id, x in items.iterrows()
        ]
        await rustac.write(str(output_dir / f"{collection_id}.parquet"), item_dicts)
        collection_bbox = items.total_bounds.tolist()
        collection_description = collection_info["description"]
        collections.append(create_collection_dict(
            collection_id, collection_bbox, start_datetime, end_datetime, collection_description,
        ))
    write_collections(output_dir / "collections.json", collections)


def load_asset_urls(
        resource_dir: pathlib.Path, resource_files: dict[str, str]
) -> dict[str, gpd.GeoDataFrame]:
    """Load and clean all asset URL tables."""
    assets_all = {}
    for asset_key, file_name in resource_files.items():
        file_path = resource_dir / file_name
        assets = gpd.read_file(f"zip://{file_path}" if file_path.suffix == ".zip" else file_path)

        # correct CRS (it is actually Amersfoort RD New)
        assets = assets.set_crs(CRS, allow_override=True)

        # keep only asset URL columns, rename them according to data type
        assets = assets[["file", "geometry"]]
        assets = assets.rename(columns={"file": asset_key})

        assets_all[asset_key] = assets
    return assets_all


def generate_item_table(
        assets: dict[str, gpd.GeoDataFrame], assets_info: dict[str, str]
) -> gpd.GeoDataFrame:
    """Merge all asset tables under unique items, and structure them according to the STAC spec."""
    # match all asset tables with a spatial join on the asset geometries
    items = None
    for a in assets.values():
        items = a if items is None else gpd.sjoin(items, a, how="left", predicate="within")
        items = items.drop(columns="index_right") if "index_right" in items else items

    # structure assets according to STAC spec
    def create_asset_dict(urls):
        """Generate STAC-compliant Asset dictionary."""
        assets = {}
        for key, href in urls.dropna().items():
            assets[key] = {
                "href": href,
                "title": assets_info[key]["title"],
                "type": assets_info[key]["type"],
                "roles": ["data"],
            }
        return assets
    items["assets"] = items[[key for key in assets_info.keys()]].apply(create_asset_dict, axis=1)
    items = items[["assets", "geometry"]]

    # define item identifiers
    bounds = items.bounds
    items["id"] = bounds.apply(lambda x: f"{x.minx:.0f}_{x.miny:.0f}", axis=1)
    items = items.set_index("id")

    # also store bounding boxes in projected coordinates
    items["bbox_proj"] = bounds.values.tolist()

    # transform item geometries to lat/lon, and calculate new bounding boxes
    items = items.to_crs("EPSG:4326")
    items["bbox"] = items.bounds.values.tolist()
    return items


def create_item_dict(
        id: str, bbox: list[float], bbox_proj: list[float], geometry: shapely.Geometry,
        assets: dict, start_datetime: str, end_datetime: str, collection_id: str,
):
    """Generate STAC-compliant Item dictionary."""
    return {
        "type": "Feature",
        "stac_version": STAC_VERSION,
        "stac_extensions": STAC_EXTENSIONS,
        "id": id,
        "bbox": bbox,
        "geometry": geometry.__geo_interface__,
        "assets": assets,
        "links": [],
        "collection": collection_id,
        "properties": {
            "datetime": None,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "proj:bbox": bbox_proj,
            "proj:epsg": CRS,
        }
    }

def create_collection_dict(
        id: str, bbox: list[float], start_datetime: str, end_datetime: str, description: str
):
    """Generate STAC-compliant Collection dictionary."""
    return {
        "type": "Collection",
        "stac_version": STAC_VERSION,
        "id": id,
        "description": description,
        "license": "other",
        "extent": {
            "spatial": {
                "bbox": [bbox]
            },
            "temporal": {
                "interval": [
                    [
                        start_datetime,
                        end_datetime
                    ]
                ]
            }
        },
        "links": [],
        "assets": {
            "data": {
                "href": f"./{id}.parquet",
                "type": "application/vnd.apache.parquet"
            }
        }
    }


def write_collections(filepath: str | pathlib.Path, collections: list[dict]) -> None:
    """Write list of collections to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(collections, f, indent=2)


def load_config(config_path: str | pathlib.Path) -> dict:
    """Load YAML configuration file."""
    with open(config_path) as f:
        return yaml.safe_load(f.read())


if __name__ == "__main__":
    asyncio.run(main())
