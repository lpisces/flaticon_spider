#! /bin/sh

mkdir -p ./data/icons
cd ./data/icons
while read url; do axel -n 16 $url; done < ../download.txt
