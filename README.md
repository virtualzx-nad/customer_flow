# live_features
A live-updating pipeline that computes a dynamic list of features to be used in ML models.   

## Functionalities

* A pipeline that, parallel to the data storage process, dynamically compute a list of features as data stream in.
* Up-to-date features are accessible real time for on-line predictions etc.
* Does not involve query to the main data store to alleviate burden on the main databases.
* The list of features can be changed and the pipeline should properly recompute the features as needed.  Some reasonable delay is allowed when feature list is changed.

## Datasets

### Yelp Reviews and Check-ins

Yelp user check-ins, business reviews and photo data.  (8.7G)

  * Data address https://www.yelp.com/dataset/download
  * Schemas https://www.yelp.com/dataset/documentation/main

### Foursquare check-in data

Foursquare global user check-in data (33M check-ins) Apr 2012 to Sep 2013. (2.4G)

  * Data address  https://drive.google.com/file/d/0BwrgZ-IdrTotZ0U0ZER2ejI3VVk/view?usp=sharing
  * Readme file https://drive.google.com/file/d/0BwrgZ-IdrTotamw5endPNTZCanc/view?usp=sharing
  * Citation:  Dingqi Yang, Daqing Zhang, Bingqing Qu. Participatory Cultural Mapping Based on Collective Behavior Data in Location Based Social Networks. ACM Trans. on Intelligent Systems and Technology (TIST), 2015. 

### UMN Foursquare check-in data

UMN/Sarwat Foursquare Dataset.  27M check-ins, venues, users and user friendship data.  (G)

  * Data address https://archive.org/download/201309_foursquare_dataset_umn/fsq.zip
  * Citation: Mohamed Sarwat, Justin J. Levandoski, Ahmed Eldawy, and Mohamed F. Mokbel. LARS*: A Scalable and Efficient Location-Aware Recommender System. in IEEE Transactions on Knowledge and Data Engineering TKDE

### Gowalla

Gowalla check-in data and user profile and friendship info Feb 2009 to Oct 2010.  (1.73G)

  * Data address https://drive.google.com/file/d/0BzpKyxX1dqTYRTFVYTd1UG81ZXc/view
  * Description  https://snap.stanford.edu/data/loc-gowalla.html
  * Citation: Yong Liu, Wei Wei, Aixin Sun, Chunyan Miao, “Exploiting Geographical Neighborhood Characteristics for Location Recommendation”, In Proceedings of the 23rd ACM International Conference on Information and Knowledge Management (CIKM’14), pp. 739-748. ACM, 2014. 

### Google local reviews

3M businesses, 4.6M users and 11.5M local business reviews from Google Maps. (2GB)

  * Description http://cseweb.ucsd.edu/~jmcauley/datasets.html#google_local
  * Citation: Translation-based factorization machines for sequential recommendation
Rajiv Pasricha, Julian McAuley
RecSys, 2018

### Tweet screams

Large amount of tweets

https://archive.org/search.php?query=collection%3Atwitterstream&sort=-publicdate&page=2



## Architecture

