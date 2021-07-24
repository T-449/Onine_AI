#!/bin/bash
# USAGE: ./runner.sh LANG SOURCE_FILE
# return codes: 0:okay, 1:Compilation_Error, 2:Runtime_Error

echo "Running" $1 $2 >/dev/stderr

if [ $1 = "g++11" ]; then
    g++ -std=c++11 -O2 -x c++ "$2" -o "$3.out"
    if [ $? -ne 0 ]; then exit 1; fi

    "./$3.out"
    if [ $? -ne 0 ]; then exit 2; fi

elif [ $1 = "g++14" ]; then
    g++ -std=c++14 -O2 -x c++ "$2" -o "$3.out"
    if [ $? -ne 0 ]; then exit 1; fi

    "./$3.out"
    if [ $? -ne 0 ]; then exit 2; fi

elif [ $1 = "g++17" ]; then
    g++ -std=c++17 -O2 -x c++ "$2" -o "$3.out"
    if [ $? -ne 0 ]; then exit 1; fi

    "./$3.out"
    if [ $? -ne 0 ]; then exit 2; fi

elif [ $1 = "g++20" ]; then
    g++ -std=c++20 -O2 -x c++ "$2" -o "$3.out"
    if [ $? -ne 0 ]; then exit 1; fi

    "./$3.out"
    if [ $? -ne 0 ]; then exit 2; fi

elif [ $1 = "python2" ]; then
    python2 "./$2"
    if [ $? -ne 0 ]; then exit 2; fi

elif [ $1 = "python3" ]; then
    python3 "./$2"
    if [ $? -ne 0 ]; then exit 2; fi
fi