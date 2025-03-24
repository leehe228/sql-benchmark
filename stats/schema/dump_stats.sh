#!/bin/bash

mysqldump -h relational.fel.cvut.cz -P 3306 -u guest -p'ctu-relational' --skip-lock-tables --skip-ssl stats > ./stats.sql
