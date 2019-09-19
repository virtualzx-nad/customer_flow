# living_pipeline
A live-updating pipeline that can be adapted online by utilizing data queues and a dynamic list of transformations.

## Functionalities

* A pipeline that dynamically process a list of transformations as data stream in.
* Up-to-date features are accessible real time for on-line predictions etc.
* No need to query the main data store, in order to alleviate burden on the main databases.
* The list of transformations (aggregations, flags, filters etc) can be changed and the pipeline
should properly recompute the features as needed.  Some reasonable delay is allowed when feature list is changed.

## Business case

Placeholder

## Datasets

Currently, the following datasets are used.  For details,
see [data set specifications](dataset.md)
* Yelp Reviews and Check-ins
* Foursquare check-in data
* UMN Foursquare check-in data
* Gowalla
* Google local reviews
* Tweet screams

## Architecture

Placeholder

## Example

Placeholder

## Cluster setup

See descriptions in the `cluster_setup` directory.
