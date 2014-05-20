#!/bin/bash

WKSP=/home/nlg-05/xingshi/workspace
#WKSP=/Users/xingshi/Workspace
ROOT=/misc/pyPBMT #
#ROOT=/misc/pyPBMT

EXP=$WKSP$ROOT/exp/mosis-mert

INI=$EXP/moses.ini
DECODER=$WKSP/tools/mosesdecoder/bin/moses
TUNE=$WKSP/tools/mosesdecoder/scripts/training/mert-moses.pl

INPUT=$WKSP$ROOT/data/dev.clean.de
REF=$WKSP$ROOT/data/dev.clean.en



cd $EXP

$TUNE $INPUT $REF $DECODER $INI --decoder-flags '-inputtype 0 -threads 11'

