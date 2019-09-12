# live_features
A live-updating pipeline that computes a dynamic list of features to be used in ML models.   

## Functionalities

* A pipeline that, parallel to the data storage process, dynamically compute a list of features as data stream in.
* Up-to-date features are accessible real time for on-line predictions etc.
* Does not involve query to the main data store to alleviate burden on the main databases.
* The list of features can be changed and the pipeline should properly recompute the features as needed.  Some reasonable delay is allowed when feature list is changed.

## Architecture

