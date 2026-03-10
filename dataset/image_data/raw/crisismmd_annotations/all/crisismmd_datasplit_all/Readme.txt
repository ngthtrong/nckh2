CrisisMMD version 2.0 data splits

Description of the dataset
==========================
The CrisisMMD multimodal Twitter dataset consists of several thousands of manually annotated tweets and images collected during seven major natural disasters including earthquakes, hurricanes, wildfires, and floods that happened in the year 2017 across different parts of the World.
The provided datasets include three types of annotations (for details please refer to our paper [1] and [2]):

Change log v2.0: In this version of this dataset, we mapped "Not relevant or can't judge" to "Not humanitarian" for the humanitarian task. Also the "Not informative" label from informative task also mapped to "Not humanitarian" for the humanitarian task.
We also removed duplicate entries that appeared while combined the tweets from different events. Both informative and humanitarian tasks are now aligned and can be useful for multitask classification learning.
-

** Task 1: Informative vs Not informative
   * Informative
   * Not informative

** Task 2: Humanitarian categories
   * Affected individuals
   * Infrastructure and utility damage
   * Injured or dead people
   * Missing or found people
   * Rescue, volunteering or donation effort
   * Vehicle damage
   * Other relevant information
   * Not humanitarian

** Task 3: Damage severity assessment
   * Severe damage
   * Mild damage
   * Little or no damage

Data format and files
===========================
The directory contains the files for different tasks:

- "task*.tsv" - training, development and test set split for the mentioned tasks.

Format of the TSV files under the "annotations" directory
---------------------------------------------------------
Each TSV file in this directory contains the following columns, separated by a tab:

* event_name: corresponds to the name of the event.
* tweet_id: corresponds to the actual tweet id from Twitter.
* image_id: corresponds to a combination of a "tweet_id" and an index concatenated with an underscore. The integer indices represent different images associated with a given tweet.
* tweet_text: corresponds to the original text of a given tweet as downloaded from Twitter.
* image: corresponds to the relative path of an image inside the "data_image" folder for a given tweet.
* label: for informativeness and humanitarian tasks randomly selected labels from text and image labels; for damage task we only have a label for the image.
* label_text: corresponds to the task-specific label (i.e., informative for informativeness, infrastructure_and_utility_damage for humanitarian) assigned to a given tweet text; for the damage task, we do not provide this column.
* label_image: corresponds to the task-specific label (i.e., informative, infrastructure_and_utility_damage for humanitarian) assigned to a given tweet image; for the damage task, we do not provide this column.
* label_text_image: corresponds to the positive and negative label, which represents whether text and image labels are the same (e.g., positive) or not (e.g., negative).




Author name and affiliation
===========================
* Firoj Alam (Qatar Computing Research Institute, Hamad Bin Khalifa University)
ORCID: 0000-0001-7172-1997

* Ferda Ofli (Qatar Computing Research Institute, Hamad Bin Khalifa University)
ORCID: 0000-0003-3918-3230

* Muhammad Imran (Qatar Computing Research Institute, Hamad Bin Khalifa University)
ORCID: 0000-0001-7882-5502

For issues and inquiries, please contact:
Ferda Ofli (fofli@hbku.edu.qa)
Muhammad Imran (mimran@hbku.edu.qa)


Citation
========
If you use this data in your research, please consider citing the following papers:

[1] Ferda Ofli, Firoj Alam and Muhammad Imran. Analysis of Social Media Data using Multimodal Deep Learning for Disaster Response. 17th International Conference on Information Systems for Crisis Response and Management (ISCRAM), 2020, Blacksburg, Virginia, USA.
[2] Firoj Alam, Ferda Ofli and Muhammad Imran. CrisisMMD: Multimodal Twitter Datasets from Natural Disasters. International AAAI Conference on Web and Social Media (ICWSM), 2018, Stanford, California, USA.


@inproceedings{multimodalbaseline2020,
Author = {Ferda Ofli and Firoj Alam and Muhammad Imran},
Booktitle = {17th International Conference on Information Systems for Crisis Response and Management},
Keywords = {Multimodal deep learning, Multimedia content, Natural disasters, Crisis Computing, Social media},
Month = {May},
Organization = {ISCRAM},
Publisher = {ISCRAM},
Title = {Analysis of Social Media Data using Multimodal Deep Learning for Disaster Response},
Year = {2020}
}

@inproceedings{CrisisMMD2018,
	Address = {Stanford, California, USA},
	Author = {Firoj Alam and Ferda Ofli and Muhammad Imran},
	Booktitle = {AAAI Conference on Web and Social Media (ICWSM)},
	Keywords = {Multimodal, Twitter datasets, Textual and multimedia content, Natural disasters},
	Month = {June},
	Organization = {AAAI},
	Publisher = {AAAI},
	Title = {CrisisMMD: Multimodal Twitter Datasets from Natural Disasters},
	Year = {2018}
}

Terms of Use
============
Please follow the terms of use mentioned here:
https://dataverse.mpi-sws.org/dataset.xhtml?persistentId=doi%3A10.5072%2FFK2%2F0YU5RD
