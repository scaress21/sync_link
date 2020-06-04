# Sync Link

There are often lots of discrepancies when researching music rights online. In my experience, one of the best ways to combat this is to check as many sources as possible. However,  this can be very time consuming (and frustrating). For this project, I wanted to create a better way to search. 

“Sync Link” aims to link multiple sources together to create a dashboard of master/publishing info and more! It utilizes APIs from Spotify, Genius, Deezer, and MusicBrainz in conjunction with web scraping additional sites to return two master sources, two publishing sources, lyrics, artwork, and embedded audio in one click. It also uses a Random Forests model to classify and predict the “clearability” of a song based on a dozen key features. 

##### Overview: [1A. What-Song (Scrape)]() | [1B. Building the Dataset]() | [1C. Deezer (Master)]() | [1D. LyricsFreak (Publishing)]() | [1E. Spotify Pt. 1]() | [1F. Spotify Pt 2.]() | [2. Cleaning]() | [3. EDA]()  | [4. Modeling]()  | [5. Application]()

### Problem Statement
Researching song ownership can be very time consuming but is a neccessary step to find out if a song is licensable. How can we speed up the process of finding and analyzing song ownership?


### Data Overview 
Gathering data was the most time intensive part of this project. This is because I used multiple sources to build it from the ground up:
1. Scrape data from What-Song.com.
    - This the basis for teh categories. If a song is in here, it's in the "synced" category. If it's not, it's "not synced".
2. Gather songs, both "synced" and "unsynced" 
    - Since "synced" songs should only make up about half of the dataset, I wanted to incorporate a larger set of songs. I used a karaoke catalog for a wide variety of songs in both categories.
3. Gather master info from Deezer
    - Master info gathered included bpm, album, artist, 
4. Gather publishing info from LyricsFreak
5. Gather audio features from Spotify


### Exploratory Data Analysis
There were lots of interesting categorial and numerical feature to explore. Analysing the relationship between the classes and Spotify audio features, genres, and number of writers and publishers yielded the most interesting results.

### Modeling
I tried a variety of classification models including Logistic Regression, Naive Bayes, AdaBoost, Extra Trees, and Random Forests. After modeling with different combinations of features, Random Forests performed the best overall with 70% test accuracy in the final model. This means it accurately classified songs as "synced" or "not synced" 70% of the time.

### Application - Sync Link
My main goal of this project was to turn it into a usable product. I believe lots of music professionals could benefit from service that gathers multiple resources into one easily accessed place. This application essentially goes through all the steps of my project for an individual song and returns the information and prediction. The screenshot below shows how each source is used. 

### Next Steps
I would love to continue exploring this topic and improving my model/application. I think the biggest hurdle is by getting a larger and more accurate dataset to train the model on. There are lots of syncs that are not documented online so right now the model is limited to learning uses that have caught enough attention to be recorded by the public. 

Also, there's a lot of nuance in determining whether or not a song is clearable, only some of this information is openly available and included here. I would love to do more reserach to see what other avenues are available to capture more levels of detail. 

Thanks for taking the time to read about my project!
