#!/usr/bin/env bash

python manage.py dumpdata --format yaml core.BaseWorkflow core.ObligationGroup core.Envelope
