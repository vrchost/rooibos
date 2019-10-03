#!/bin/bash

TRAVIS_BRANCH=`git branch --show-current`
TRAVIS_BUILD_NUMBER=0

VERSION=$(git describe --always)
NAME=rooibos-$TRAVIS_BRANCH-$VERSION-build$TRAVIS_BUILD_NUMBER
mkdir -p travis-build
echo VERSION=\"$VERSION\" > rooibos/version.py
git checkout -B $TRAVIS_BRANCH-local-build
git add rooibos/version.py
git commit -m "Update version number"
git archive --prefix rooibos-$VERSION/ -o travis-build/$NAME.tar.gz HEAD
rm -rf travis-build-temp
mkdir -p travis-build-temp
cd travis-build-temp
tar xzf ../travis-build/$NAME.tar.gz
zip -r ../travis-build/$NAME.zip *
cd ..
rm -rf travis-build-temp
git checkout $TRAVIS_BRANCH
git branch -D $TRAVIS_BRANCH-local-build
