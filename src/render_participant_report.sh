#!/bin/bash

default_pid="testjen"
global_output_dir="../output/"
output_dir="output"
output_file="$output_dir/"*".html"

pid="$1"

echo "Processing data and report for ""$pid"

# overwrite YAML file defaults with participant-specific info
python update_yaml_files.py "$pid"

# render report for participant and move it to correct output directory
quarto render final_report_template.qmd --execute-params params.yml --output-dir $output_dir
mv $output_file $global_output_dir

# clean up and reset YAML files to defaults
python update_yaml_files.py $default_pid