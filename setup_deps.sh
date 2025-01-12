#! /usr/bin/env bash

pip install https://github.com/robotics-4-all/commlib-py/archive/devel.zip -U
pip install https://github.com/robotics-4-all/goalee/archive/devel.zip -U

pip install -r requirements.txt

rm -rf goal-dsl 2&1>/dev/null
git clone https://github.com/robotics-4-all/goal-dsl.git && \
    cd goal-dsl && git checkout devel && pip install . && rm -rf goal-dsl
