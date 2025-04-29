import pandas as pd 
import numpy as np
import plotnine as p9 
import matplotlib
import matplotlib.pyplot as plt  
import warnings
import yaml

from sqlalchemy import create_engine
from great_tables import *

def load_credentials(group):
	with open("../credentials.yaml") as file:
		credentials = yaml.safe_load(file)[group]
	return credentials

def connect_to_database(credentials):
	user = credentials["user"]
	password = credentials["password"]
	host = credentials["host"]
	name = credentials["database"]

	engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{name}")
	connection = engine.connect()
	return connection

def generate_custom_cmap(pal=["redyellowgreen", "indigo"], cmap_type=["discrete", "continuous"], n_colors=None):
	if pal == "redyellowgreen":
		LOW = "#FF5252"
		MEDIUM = "#FFC108"
		HIGH = "#4CAF50"
	elif pal == "indigo":
		LOW = "#FFFFFF"
		MEDIUM = "#5C6BC0"
		HIGH = "#283593" 
	else:
		raise ValueError("`pal` must be one of: redyellowgreen, indigo")

	color_list = [LOW, MEDIUM, HIGH]
	
	if cmap_type == "discrete":
		return plt.cm.colors.LinearSegmentedColormap.from_list("cmap_discrete", color_list, N=n_colors)
	elif cmap_type == "continuous":
		return plt.cm.colors.LinearSegmentedColormap.from_list("cmap_continuous", color_list)
	else:
		raise ValueError("cmap_type must be one of: discrete, continuous")

def get_cmap_hexcodes(cmap, n_colors):
	return [matplotlib.colors.to_hex(cmap(i)) for i in range(n_colors)]

def chunk_list(input_list, n):
	size = len(input_list) // n
	remainder = len(input_list) % n
	result = []
	start = 0
	
	for _ in range(n):
		end = start + size + (1 if remainder > 0 else 0)
		result.append(input_list[start:end])
		start = end
		remainder -= 1

	return result

def abbreviate_day_of_week(data, col):
	abbrev = data[col].case_when(
		caselist=[
			(data[col] == "Monday", "Mon"),
			(data[col] == "Tuesday", "Tues"),
			(data[col] == "Wednesday", "Weds"),
			(data[col] == "Thursday", "Thurs"),
			(data[col] == "Friday", "Fri"),
			(data[col] == "Saturday", "Sat"),
			(data[col] == "Sunday", "Sun")
		]
	)
	return abbrev

def get_longest_streak(data, phase):
	if phase == 2:
		df = data.query("has_morning == 1 & has_evening == 1")
	else:
		df = data
    
	longest_streak = (
		df
		.filter(["Date"], axis=1)
		.drop_duplicates()
		.reset_index(drop=True)
		.assign(streak_breaks = lambda x: x["Date"].diff() != pd.Timedelta("1d"))
		.assign(streak_groups = lambda x: x["streak_breaks"].cumsum())
		.groupby("streak_groups")
		.agg({"Date":"count"})
		.max()
		.iloc[0]
	)
	return longest_streak

def get_value_box_data(data, phase, extra_data=None):
	if phase == 1:
		if extra_data is None:
			raise ValueError("Must supply 'extra' data for phase 1 value boxes")
			
		value_descriptions = [
			"Surveys completed", 
			"Longest survey completion streak", 
			"Average goodness rating", 
			"Total activities logged", 
			"Unique activities logged", 
			"Average activity rating",
			"Days with valid Fitbit data",
			"Average step count",
			"Average hours of sleep"
		]	
		
		value_box_stats = pd.DataFrame({
			"n_surveys": [data.shape[0]],
			"longest_streak_days": [get_longest_streak(data, 1)],
			"avg_goodness": [round(data["Goodness rating"].mean(), 1)],
			"n_activities": [extra_data["n_activities"][0]],
			"n_distinct_activities": [extra_data["n_distinct_activities"][0]],
			"avg_activity_score": [extra_data["avg_activity_score"][0]],
			"days_with_fitbit": [int(data["has_fitbit"].sum())],
			"average_steps": [data[data["has_fitbit"] == 1]["Steps"].mean().round(0).astype(int) if not np.isnan(data[data["has_fitbit"] == 1]["Steps"].mean()) else np.nan],
			"average_sleep": [data[data["has_fitbit"] == 1]["Sleep"].mean().round(0).astype(int) if not np.isnan(data[data["has_fitbit"] == 1]["Sleep"].mean()) else np.nan]
		})
		
		value_box_stats = value_box_stats.fillna({"n_surveys": 0, "n_activities": 0, "n_distinct_activities": 0, "days_with_fitbit": 0, "avg_activity_score": np.NaN})

	elif phase == 2:
		value_descriptions = [
			"Morning surveys completed", 
			"Evening surveys completed", 
			"Longest survey completion streak", 
			"Average goodness rating", 
			"Total activities planned", 
			"Total activities completed",
			"Days with valid Fitbit data",
			"Average step count",
			"Average hours of sleep"
		]
		
		value_box_stats = pd.DataFrame({
			"n_morning_surveys": [data.query("has_morning == 1").shape[0]],
			"n_evening_surveys": [data.query("has_evening == 1").shape[0]],
			"longest_streak_days": [get_longest_streak(data, 2)],
			"avg_goodness": [round(data["Goodness rating"].mean(), 1)],
			"n_planned_activities": [int(data["n_planned_activities"].sum())],
			"n_completed_activities": [int(data["n_completed_activities"].sum())],
			"days_with_fitbit": [data["has_fitbit"].sum()],
			"average_steps": [data[data["has_fitbit"] == 1]["Steps"].mean().round(0).astype(int) if not np.isnan(data[data["has_fitbit"] == 1]["Steps"].mean()) else np.nan],
			"average_sleep": [data[data["has_fitbit"] == 1]["Sleep"].mean().round(0).astype(int) if not np.isnan(data[data["has_fitbit"] == 1]["Sleep"].mean()) else np.nan]
		})

		value_box_stats = value_box_stats.fillna({"n_surveys": 0, "n_activities": 0, "n_distinct_activities": 0, "days_with_fitbit": 0})

	else:
		raise ValueError("Phase must be 1 or 2")

	return (
		value_box_stats
		.melt()
		.assign(value=lambda x: x["value"].map("{:,.1f}".format).str.replace(".0", "").str.replace("nan", "N/A"))
		.assign(description=value_descriptions)
		.assign(variable = lambda x: pd.Categorical(x["variable"], categories=x["variable"].tolist()))
		.assign(
			description_x = 0.05,
			description_y = 0.15,
			value_x = 0.05,
			value_y = 0.45,
			xmin = 0,
			xmax = 1,
			ymin = 0,
			ymax = 1
		)
	)

def create_value_box_plot(data, font="Ayuthaya"):
	INDIGO = "#3F51B5"
	WIDTH = 12
	HEIGHT = 2.8
	NROW = 3
	NCOL = 3

	MPL_FONTS = ["Avenir", "Ayuthaya", "Muna"]
	if not font in MPL_FONTS:
		print("Using default font")
		font = "Ayuthaya"

	plot = (
		p9.ggplot(data = data)
		+ p9.geom_rect(
			mapping=p9.aes(xmin="xmin", xmax="xmax",ymin="ymin", ymax="ymax"),
			fill=INDIGO
		)
		+ p9.geom_text(
			mapping=p9.aes(x="description_x", y="description_y", label="description"),
			color="white",
			ha="left",
			size=12,
			family=font,
			fontweight="bold",
			alpha=0.7
		)
		+ p9.geom_text(
			mapping=p9.aes(x="value_x", y="value_y", label="value"),
			color="white",
			ha="left",
			size=20,
			family=font,
			fontweight="bold"
		)
		+ p9.facet_wrap("~variable", nrow=NROW, ncol=NCOL)
		+ p9.scale_x_continuous(expand=[0, 0])
		+ p9.labs(x="", y="", title="")
		+ p9.theme_void()
		+ p9.theme(
			figure_size=(WIDTH, HEIGHT),
			legend_position="none",
			plot_margin=0,
			panel_spacing_x=0.01,
			panel_spacing_y=0,
			panel_grid_major=p9.element_blank(),
			panel_grid_minor=p9.element_blank(),
			panel_background=p9.element_rect(fill="white"),
			plot_background=p9.element_rect(fill="white"),
			axis_text=p9.element_blank(),
			axis_title=p9.element_blank(),
			axis_ticks=p9.element_blank(),
			plot_title=p9.element_text(family=font, face="bold", size=14, ha="left"),
			strip_text=p9.element_blank()
		)
	)

	return plot

def create_data_table(data, cols_labels, cols_widths, goodness_hexcodes, fitbit_hexcodes, font="Inconsolata", font_size=12, dashed=False, scrollable=False):
	GOOGLE_FONT_OPTIONS = ["Inconsolata", "Source Code Pro", "Space Mono", "Fira Mono"]
	if not font in GOOGLE_FONT_OPTIONS:
		print("Using default font")
		font="Inconsolata"

	dt = (
		GT(data)
		.cols_label(cols_labels)
		.opt_table_font(font=google_font(font))
		.data_color(
			columns=["Goodness rating"],
			palette=goodness_hexcodes,
			domain=[0, 10],
			na_color="white"
		)
		.data_color(
			columns=["Sleep"],
			palette=fitbit_hexcodes,
			na_color="white"
		)
		.data_color(
			columns=["Steps"],
			palette=fitbit_hexcodes,
			na_color="white"
		)
		.fmt_number(
			columns=["Steps", "Sleep"],
			decimals=0
		)
		.tab_style(
			style=style.text(weight="bold"),
			locations=loc.body(columns=["Date", "Goodness rating"])
		)
		.tab_options(
			table_width="100%",
			table_layout="auto",
			column_labels_font_weight=700,
			table_font_size=f"{font_size}px",
			column_labels_font_size=f"{font_size+2}px",
			column_labels_border_bottom_color="#D3D3D3"
		)
		.cols_width(cases = cols_widths)
	) 

	if dashed:
		dt = dt.tab_style(
			style=style.borders(sides="top", color="black", style="dashed", weight="1px"),
			locations=loc.body(rows=data.index.tolist())
		)
	if scrollable:
		dt = dt.tab_options(
			container_overflow_y="True",
			container_height="700px"
		)

	return dt

def generate_queries(pid):
	phase1_query = f'''
	with
	pid_goodness as (
		select 
			pId, 
			dayname(date) as day, 
			date, 
			goodnessScore, 
			concat(ucase(substring(trim(lower(note)), 1, 1)), substring(trim(note), 2)) as note_formatted
		from survey_responses
		where 
			pId = "{pid}" and sId = "DAILY" and
			date >= (select startDate from user_study_phases where pId = "{pid}" and phaseId = "PHASE_1") and
			date <= (select date_sub(endDate, interval 1 day) from user_study_phases where pId = "{pid}" and phaseId = "PHASE_1")
	),
	activity_names as (
		select activityId, concat(ucase(substring(trim(lower(name)), 1, 1)), substring(trim(name), 2)) as activityName
		from user_activities
		union all
		select activityId, concat(ucase(substring(trim(lower(name)), 1, 1)), substring(trim(name), 2)) as activityName		
		from activities
	),
	pid_activities as (
		select pId, date, activityName
		from survey_response_details
		left join survey_responses on survey_responses.surveyId = survey_response_details.surveyId
		left join activity_names on activity_names.activityId = survey_response_details.activityId
	),
	pid_activities_list as (
		select pId, date, group_concat(activityName order by activityName separator ",  ") as completedActivities
		from pid_activities
		group by pId, date
	),
	fitbit_days as (
		select pId, date, 1 as has_fitbit 
		from fitbit_data
		where 
			pId = "{pid}" and
			date >= (select startDate from user_study_phases where pId = "{pid}" and phaseId = "PHASE_1") and
			date <= (select date_sub(endDate, interval 1 day) from user_study_phases where pId = "{pid}" and phaseId = "PHASE_1") and
			fitbitDataType = "heartrate" and value > 0 
	),
	fitbit_steps as (
		select pId, date, value as steps
		from fitbit_data
		where fitbitDataType = "steps"
	),
	fitbit_sleep as (
		select pId, date, value as sleep
		from fitbit_data
		where fitbitDataType = "sleep"
	),
	fitbit_data as (
		select fitbit_days.pId, fitbit_days.date, steps, sleep, has_fitbit
		from fitbit_days
		left join fitbit_steps on fitbit_days.pId = fitbit_steps.pId and fitbit_days.date = fitbit_steps.date
		left join fitbit_sleep on fitbit_days.pId = fitbit_sleep.pId and fitbit_days.date = fitbit_sleep.date
	)
	select
		day as "Day of week",
		pid_goodness.date as "Date",
		goodnessScore as "Goodness rating",
		completedActivities as "Completed activities",
		note_formatted as "Note",
		steps as "Steps",
		sleep as "Sleep",
		has_fitbit
	from pid_goodness
	left join pid_activities_list on pid_goodness.pId = pid_activities_list.pId and pid_goodness.date = pid_activities_list.date
	left join fitbit_data on pid_goodness.pId = fitbit_data.pId and pid_goodness.date = fitbit_data.date;
	'''

	phase1_extra_query = f'''
	with
	pid_goodness as (
		select pId, dayname(date) as day, date, goodnessScore, concat(ucase(substring(trim(lower(note)), 1, 1)), substring(trim(note), 2)) as note_formatted
		from survey_responses
		where
			pId = "{pid}" and sId = "DAILY" and
			date >= (select startDate from user_study_phases where pId = "{pid}" and phaseId = "PHASE_1") and
			date <= (select date_sub(endDate, interval 1 day) from user_study_phases where pId = "{pid}" and phaseId = "PHASE_1")
	),
	pid_activities as (
		select pId, date, activityId, score
		from survey_response_details
		left join survey_responses on survey_responses.surveyId = survey_response_details.surveyId
	)
	select
		count(activityId) as n_activities,
		count(distinct activityId) as n_distinct_activities,
		round(avg(case when score = -1 then null else score end), 1) as avg_activity_score
	from pid_goodness 
	left join pid_activities on pid_goodness.pId = pid_activities.pId and pid_goodness.date = pid_activities.date;
	'''

	phase2_query = f''' 
	with
	pid_responses as (
		select distinct pid, dayname(date) as day, date
		from survey_responses
		where 
			pId = "{pid}" and sId in ("MORNING", "EVENING") and
			date >= (select startDate from user_study_phases where pId = "{pid}" and phaseId = "PHASE_2") and
			date <= (select date_sub(endDate, interval 1 day) from user_study_phases where pId = "{pid}" and phaseId = "PHASE_2")
	),
	pid_goodness as (
		select pId, date, goodnessScore, concat(ucase(substring(trim(lower(note)), 1, 1)), substring(trim(note), 2)) as evening_note_formatted, 1 as has_evening
		from survey_responses
		where 
			pId = "{pid}" and sId = "EVENING" and
			date >= (select startDate from user_study_phases where pId = "{pid}" and phaseId = "PHASE_2") and
			date <= (select date_sub(endDate, interval 1 day) from user_study_phases where pId = "{pid}" and phaseId = "PHASE_2")
	),
	pid_plan as (
		select pId, date, concat(ucase(substring(trim(lower(note)), 1, 1)), substring(trim(note), 2)) as morning_note_formatted, 1 as has_morning
		from survey_responses
		where 
			pId = "{pid}" and sId = "MORNING" and
			date >= (select startDate from user_study_phases where pId = "{pid}" and phaseId = "PHASE_2") and
			date <= (select date_sub(endDate, interval 1 day) from user_study_phases where pId = "{pid}" and phaseId = "PHASE_2")
	),
	activity_names as (
		select activityId, concat(ucase(substring(trim(lower(name)), 1, 1)), substring(trim(name), 2)) as activityName
		from user_activities
		union all
		select activityId, concat(ucase(substring(trim(lower(name)), 1, 1)), substring(trim(name), 2)) as activityName		
		from activities
	),
	pid_planned_activities as (
		select distinct pId, date, activityName
		from survey_response_details
		left join survey_responses on survey_responses.surveyId = survey_response_details.surveyId
		left join activity_names on activity_names.activityId = survey_response_details.activityId
		where survey_response_details.surveyId like "%_MORNING_%"
	),
	pid_planned_activities_list as (
		select pId, date, group_concat(activityName order by activityName separator ", ") as plannedActivities, count(activityName) as n_planned_activities
		from pid_planned_activities
		group by pId, date
	),
	pid_completed_activities as (
		select distinct pId, date, activityName
		from survey_response_details
		left join survey_responses on survey_responses.surveyId = survey_response_details.surveyId
		left join activity_names on activity_names.activityId = survey_response_details.activityId
		where survey_response_details.surveyId like "%_EVENING_%"
	),
	pid_completed_activities_list as (
		select pId, date, group_concat(activityName order by activityName separator ", ") as completedActivities, count(activityName) as n_completed_activities
		from pid_completed_activities
		group by pId, date
	),
	fitbit_days as (
		select pId, date, 1 as has_fitbit
		from fitbit_data
		where
			pId = "{pid}" and
			date >= (select startDate from user_study_phases where pId = "{pid}" and phaseId = "PHASE_2") and
			date <= (select date_sub(endDate, interval 1 day) from user_study_phases where pId = "{pid}" and phaseId = "PHASE_2") and
			fitbitDataType = "heartrate" and value > 0 
	),
	fitbit_steps as (
		select pId, date, value as steps
		from fitbit_data
		where fitbitDataType = "steps"
	),
	fitbit_sleep as (
		select pId, date, value as sleep
		from fitbit_data
		where fitbitDataType = "sleep"
	),
	fitbit_data as (
		select fitbit_days.pId, fitbit_days.date, steps, sleep, has_fitbit
		from fitbit_days
		left join fitbit_steps on fitbit_days.pId = fitbit_steps.pId and fitbit_days.date = fitbit_steps.date
		left join fitbit_sleep on fitbit_days.pId = fitbit_sleep.pId and fitbit_days.date = fitbit_sleep.date
	)
	select
		day as "Day of week",
		pid_responses.date as "Date",
		case when goodnessScore = -1 then null else goodnessScore end as "Goodness rating",
		plannedActivities as "Planned activities",
		completedActivities as "Completed activities",
		morning_note_formatted as "Morning plan",
		evening_note_formatted as "Evening note",
		steps as "Steps",
		sleep as "Sleep",
		has_morning,
		has_evening,
		n_planned_activities,
		n_completed_activities,
		has_fitbit
	from pid_responses
	left join pid_goodness on pid_responses.pId = pid_goodness.pId and pid_responses.date = pid_goodness.date
	left join pid_plan on pid_responses.pId = pid_plan.pId and pid_responses.date = pid_plan.date
	left join pid_planned_activities_list on pid_responses.pId = pid_planned_activities_list.pId and pid_responses.date = pid_planned_activities_list.date
	left join pid_completed_activities_list on pid_responses.pId = pid_completed_activities_list.pId and pid_responses.date = pid_completed_activities_list.date
	left join fitbit_data on pid_responses.pId = fitbit_data.pId and pid_responses.date = fitbit_data.date
	order by date;
	'''

	phase2_extra_query = f''' 
	with
	activity_names as (
		select activityId, concat(ucase(substring(trim(lower(name)), 1, 1)), substring(trim(name), 2)) as activityName
		from user_activities
		union all
		select activityId, concat(ucase(substring(trim(lower(name)), 1, 1)), substring(trim(name), 2)) as activityName
		from activities
	)
	select group_concat(distinct activityName order by activityName separator ', ') as activity_list
	from user_activity_preferences
	left join activity_names on user_activity_preferences.activityId = activity_names.activityId
	where participantPhaseId = "{pid}_PHASE_2";
	'''

	qs = {
		"phase1": phase1_query,
		"phase1_extra": phase1_extra_query,
		"phase2": phase2_query,
		"phase2_extra": phase2_extra_query
	}
	return qs