# STAC Catalog for AHN

This repository contains material to build a SpatioTemporal Asset Catalog (STAC) for AHN datasets.

> [!WARNING]
> This material is under active development and could drastically change at any time.

## Static collections

The [`data`](./data) folder contains static STAC collections structured as [stac-geoparquet](https://stac-geoparquet.org/). You can visualize the collections at the following links: [AHN2][stac-map-ahn2], [AHN3][stac-map-ahn3], [AHN4][stac-map-ahn4], [AHN5][stac-map-ahn5], [AHN6][stac-map-ahn6]

[stac-map-ahn2]: https://developmentseed.org/stac-map/?href=https://raw.githubusercontent.com/cloud-nes/ahn-stac/main/data/AHN2.parquet
[stac-map-ahn3]: https://developmentseed.org/stac-map/?href=https://raw.githubusercontent.com/cloud-nes/ahn-stac/main/data/AHN3.parquet
[stac-map-ahn4]: https://developmentseed.org/stac-map/?href=https://raw.githubusercontent.com/cloud-nes/ahn-stac/main/data/AHN4.parquet
[stac-map-ahn5]: https://developmentseed.org/stac-map/?href=https://raw.githubusercontent.com/cloud-nes/ahn-stac/main/data/AHN5.parquet
[stac-map-ahn6]: https://developmentseed.org/stac-map/?href=https://raw.githubusercontent.com/cloud-nes/ahn-stac/main/data/AHN6.parquet

### Search the collections

The STAC collection files can be searched using [`rustac`](https://stac-utils.github.io/rustac), which can be installed with:

```shell
python -m pip install rustac
```

Using `rustac` you can run queries like the following (change the name of the parquet file in the URL to search the corresponding AHN[2-6] collection):

```shell
# find all items intersecting the given bbox
rustac search --bbox 5.085297,52.050390,5.197220,52.117516 https://raw.githubusercontent.com/cloud-nes/ahn-stac/main/data/AHN2.parquet > results.json
```

Check `rustac search --help` to see other options. The `results.json` file contains the resulting items (you can visualize the file e.g. on [stac-map](https://developmentseed.org/stac-map/)). 

### Download assets

You can download the assets linked to a set of items using [`stac-asset`](https://github.com/stac-utils/stac-asset), which can be installed with:

```shell
python -m pip install stac-asset[cli]
```

To download assets from a selection of items identified as above:

```shell
# only donwload point cloud assets ("PC" key) from the selected items
stac-asset download -i PC --max-concurrent-downloads 1 results.json
```

Note that `stac-asset` also read items from standard input, so that `rustac` and `stac-asset` commands can be chained:

```shell
rustac search --bbox 5.085297,52.050390,5.197220,52.117516 https://raw.githubusercontent.com/cloud-nes/ahn-stac/main/data/AHN2.parquet | \
  stac-asset download -i PC --max-concurrent-downloads 1
```


