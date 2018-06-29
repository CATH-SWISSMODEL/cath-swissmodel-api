#!/bin/bash

cd perl5

cpanm --quiet --installdeps .

prove -l -v t/

