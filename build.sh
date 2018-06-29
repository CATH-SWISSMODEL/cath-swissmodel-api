#!/bin/bash

cd perl5

cpanm --quiet --installdeps --notest .

prove -l -v t