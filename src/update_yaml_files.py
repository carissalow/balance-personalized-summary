import yaml

def open_file(file_name):
    with open(file_name) as infile:
        settings = yaml.safe_load(infile)
    return settings

def update_settings(settings, pid):
    title = f"BALANCE final study report for {pid}"
    output_file = f"balance_final_report_{pid}.html"

    settings["title"] = title
    settings["output-file"] = output_file
    return settings

def get_quoted_values(settings):
    TOP_LEVEL_KEYS = ["title", "author", "output-file", "output-dir", "from"]
    HTML_LEVEL_KEYS = ["linkcolor", "toc-color"]

    top_level_values = [value for key, value in settings.items() if key in TOP_LEVEL_KEYS] 
    html_level_values = [value for key, value in settings["format"]["html"].items() if key in HTML_LEVEL_KEYS]
    
    quoted_values = top_level_values + html_level_values
    return quoted_values

def write_file(file_name, settings, quoted_values):
    class QuotedDumper(yaml.Dumper):
        def represent_data(self, data):
            if data in quoted_values:
                return self.represent_scalar("tag:yaml.org,2002:str", data, style='"')
            return super().represent_data(data)

    with open(file_name, "w") as outfile:
        yaml.dump(settings, outfile, default_flow_style=False, sort_keys=False, Dumper=QuotedDumper)

def update_header(pid):
    FILE_NAME = "_quarto.yml"

    settings = open_file(FILE_NAME)
    settings = update_settings(settings, pid)
    quoted_values = get_quoted_values(settings)

    write_file(FILE_NAME, settings, quoted_values)

def update_params(pid):
    FILE_NAME = "params.yml"

    params = open_file(FILE_NAME)
    params["pid"] = pid

    write_file(FILE_NAME, params, [pid])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("pid")
    args = parser.parse_args()

    try:
        update_header(args.pid)
        update_params(args.pid)
    except Exception as err:
        print(err)