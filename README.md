#UNIT TEST

### Crawler Behaviour

To ensure that the crawler behaves as expected a set of html pages have been created with specific words in them. The crawler will traverse the pages and come up with **three (3)** resulting data structures, namely:

1. Lexicon
2. Document Index
3. Inverted Index

The words in each of the pages are shown in the table below

|   Page | Words (Frequency of occurrence) |
| -----: | ------------------------------- |
| Page 1 | boy(1), cat(1), dog(1)          |
| Page 2 | boy(2), cat(1)                  |
| Page 3 | cat(1), dog(2)                  |
| Page 4 | ant(1), cat(1), egg(1)          |
| Page 5 | fat(1)                          |



In view of the above table, the expected result form the crawler should be as follows:

###### Lexicon
| word |  id  |
| :--: | :--: |
| boy  |  6   |
| dog  |  5   |
| egg  |  4   |
| cat  |  3   |
| ant  |  2   |
| fat  |  1   |

###### Document Index
| url                              |  id  |
| :------------------------------- | :--: |
| http://localhost:8080/test       |  1   |
| http://localhost:8080/page1.html |  2   |
| http://localhost:8080/page2.html |  3   |
| http://localhost:8080/page3.html |  4   |
| http://localhost:8080/page4.html |  5   |
| http://localhost:8080/page5.html |  6   |

###### Inverted Index
| word id | associated document ids |
| :-----: | :---------------------- |
|    1    | set([6])                |
|    2    | set([5])                |
|    3    | set([5, 4, 3, 2])       |
|    4    | set([5])                |
|    5    | set([4, 2])             |
|    6    | set([3, 2])             |

### Implementation
The code for unit test is saved in the file `test_crawler.py`. The unit test implementation makes use of the unittest class in python.

A class, `TestCrawlerMethods` was created to handle the various test cases for the newly created functions in the `Crawler` class in `crawler.py`.

 1. First the server is run to serve local test html pages as specified in `test_urls.txt`.
 2. Then the crawler is called when the unit test crawler class is called. 
 3. This crawls through the test html pages and generates the requisite data structures
 4. The data structures in question should be as shown in the tables above.
 5. The unit test runs all the test cases and compares them to the expected output.
 6. The results are printed out with errors if any.