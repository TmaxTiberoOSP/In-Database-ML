LOAD DATA LOCAL INFILE './cifar10_paths_train.csv'
INTO TABLE t_training_data
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(image_path, label);

LOAD DATA LOCAL INFILE './cifar10_paths_test.csv'
INTO TABLE t_test_data
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(image_path, label);