#!/usr/bin/env sh

file_list='us_d us_cmd mon_test script/*'

rsync -av $file_list /usr/local/bin/

