#!/bin/bash

input=$1

simhashc/stem $1 > $1.stem
simhashc/charikar $1.stem
rm $1.stem
