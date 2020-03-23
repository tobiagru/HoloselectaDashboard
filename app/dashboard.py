#!/usr/bin/env python3
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import os
import math
from scipy.stats import mannwhitneyu, ttest_ind
from nutris import nutris

BASEPATH = "/data"

app = dash.Dash(__name__)
app.config['suppress_callback_exceptions']=True


def combine_all_data():
  print("getting new data")
  survey_df = pd.DataFrame()
  #tracking_files = {}
  machineLayouts = pd.DataFrame()
  timings = pd.DataFrame()

  for filename in os.listdir(BASEPATH):
    if ".csv" in filename:
      if "machineLayout" in filename:
        user_id = filename.split("_")[0]
        task = filename.split("_")[1]
        #the machinelayout is the same for all tasks no need to store it multiple times
        #extract the machine layout
        machinelayout_df_tmp = pd.read_csv(os.path.join(BASEPATH, filename), sep=';')
        machinelayout_df_tmp["user_id"] = user_id
        machinelayout_df_tmp["task"] = task
        machineLayouts = machineLayouts.append(machinelayout_df_tmp, ignore_index=True)
      if "_trackings_" in filename:
        user_id = filename.split("_")[0]
        task = filename.split("_")[1]
        timings_df_tmp = pd.read_csv(os.path.join(BASEPATH, filename), sep=',')
        timings = timings.append({"user_id":user_id, "task":task, "time":timings_df_tmp.iloc[-1]["timestamp"] / 1000}, ignore_index=True)

  for filename in os.listdir(BASEPATH):
    if ".csv" in filename and not "BAK" in filename:
      if "_evaluation_" in filename:
        survey_df_tmp = pd.read_csv(os.path.join(BASEPATH, filename), index_col="user_id", sep=';')
        survey_df = survey_df_tmp.combine_first(survey_df)
      elif "_basic_" in filename:
        survey_df_tmp = pd.read_csv(os.path.join(BASEPATH, filename), index_col="user_id", sep=';')
        survey_df = survey_df_tmp.combine_first(survey_df)
      elif "_guess_" in filename:
        survey_df_tmp = pd.read_csv(os.path.join(BASEPATH, filename), index_col="user_id", sep=';')
        survey_df = survey_df_tmp.combine_first(survey_df)
      elif "_task_" in filename:
        #extract the nutriscore & label from machine layout if available
        survey_df_tmp = pd.read_csv(os.path.join(BASEPATH, filename), index_col="user_id", sep=';')
        user_id = str(survey_df_tmp.index[0])
        #assuming there is only one row in the survey_task.csv, which is fine if data from typeform
        for taskNr in range(1,5):
          try:
            product = machineLayouts[ (machineLayouts["user_id"] == user_id) & \
                                      (machineLayouts["BoxNr"] == int(survey_df_tmp["t_{}".format(taskNr)].iloc[0]))
                                      ].iloc[0]
            survey_df_tmp["nutri_label_{}".format(taskNr)] = product["ProductNutriLabel"]
            survey_df_tmp["nutri_score_{}".format(taskNr)] = product["ProductNutriScore"]
            survey_df_tmp["energy_{}".format(taskNr)] = nutris[product["ProductId"]]["energy"]
            survey_df_tmp["sugar_{}".format(taskNr)] = nutris[product["ProductId"]]["sugar"]
            survey_df_tmp["sat_fat_{}".format(taskNr)] = nutris[product["ProductId"]]["sat_fat"]
            survey_df_tmp["natrium_{}".format(taskNr)] = nutris[product["ProductId"]]["natrium"]
            survey_df_tmp["protein_{}".format(taskNr)] = nutris[product["ProductId"]]["protein"]
            survey_df_tmp["fiber_{}".format(taskNr)]= nutris[product["ProductId"]]["fiber"]
            survey_df_tmp["health_percentage_{}".format(taskNr)] = nutris[product["ProductId"]]["health_percentage"]
            survey_df_tmp["time_{}".format(taskNr)] = timings.loc[(timings["user_id"]==user_id) & (timings["task"]==str(taskNr)),"time"].iloc[0]
          except:
            survey_df_tmp["nutri_label_{}".format(taskNr)] = None
            survey_df_tmp["nutri_score_{}".format(taskNr)] = None
            survey_df_tmp["energy_{}".format(taskNr)] = None
            survey_df_tmp["sugar_{}".format(taskNr)] = None
            survey_df_tmp["sat_fat_{}".format(taskNr)] = None
            survey_df_tmp["natrium_{}".format(taskNr)] = None
            survey_df_tmp["protein_{}".format(taskNr)] = None
            survey_df_tmp["fiber_{}".format(taskNr)]= None
            survey_df_tmp["health_percentage_{}".format(taskNr)] = None
            survey_df_tmp["time_{}".format(taskNr)] = None                                                   
        survey_df = survey_df_tmp.combine_first(survey_df)

  age_classes = {
    0: "0.) < 19yrs",
    1: "1.) 20 - 29 yrs",
    2: "2.) 30 - 49 yrs",
    3: "2.) 30 - 49 yrs",
    4: "3.) 50 - 65 yrs",
    5: "4.) > 65 yrs",
    6: "4.) > 65 yrs"}

  survey_df["age_class"] = survey_df["age"].apply(lambda x: safe_dict(x, age_classes))

  ages = {
    0: 18,
    1: 25,
    2: 35,
    2: 45,
    3: 57,
    4: 72,
    5: 85
  }
  survey_df["age"] = survey_df["age"].apply(lambda x: safe_dict(x, ages))

  weights = {
    "39-": 35,
    "40-49": 45,
    "50-59": 55,
    "60-69": 65,
    "70-79": 75,
    "80-89": 85,
    "90-99": 95,
    "100-109": 105,
    "110-119": 115,
    "120-129": 125,
    "130-139": 135,
    "140-149": 145,
    "150+": 155
  }
  survey_df["weight"] = survey_df["weight"].apply(lambda x: safe_dict(x, weights, False))

  heights = {
    "139-": 1.35,
    "140-149": 1.45,
    "150-159": 1.55,
    "160-169": 1.65,
    "170-179": 1.75,
    "180-189": 1.85,
    "190-199": 1.95,
    "200-209": 2.05,
    "210+": 2.15
  }

  survey_df["height"] = survey_df["height"].apply(lambda x: safe_dict(x, heights, False))

  genders = {
    "male": "0.) Male",
    "female": "1.)Female"
  }

  survey_df["gender"] = survey_df["gender"].apply(lambda x: safe_dict(x, genders, False))

  survey_df["bmi"] = survey_df["weight"] / (survey_df["height"] * survey_df["height"])

  survey_df["bmi_class"] = survey_df["bmi"].apply(bmi_class)

  diets = {
    "No I don't follow a certain diet": "None",
    "Nein, ich folge keiner bestimmten Diät": "None",
    "I avoid certain foods because of an allergy or food intolerance": "Allergy / Intolerance",
    "Ich vermeide bestimmte Lebensmittel wegen Allergie oder Unverträglichkeit": "Allergy / Intolerance",
    "I eat vegetarian": "Vegiatrian / Vegan",
    "Ich esse vegetarisch (ovo-lacto-vegetarisch, lacto-vegetarisch)": "Vegiatrian / Vegan",
    "I eat vegan": "Vegiatrian / Vegan",
    "Ich esse vegan": "Vegiatrian / Vegan",
    "I avoid certain foods for ethical/cultural/religious reasons": "Cultural / Ethnical",
    "Ich vermeide bestimmte Lebensmittel aus ethischen, kulturellen oder religiösen Gründen": "Cultural / Ethnical",
    "I follow a high carbohydrate diet": "High Carb",
    "Ich esse kohlenhydratreich": "High Carb",
    "I follow a diet low in carbohydrates": "Low Carb",
    "Ich esse kohlenhydrat-arm": "Low Carb",
    "I follow a low fat or cholosterol diet": "Low Fat",
    "Ich esse fettarm oder cholesterin-arm": "Low Fat",
    "I follow a diet with reduced salt consumption": "Low Salt",
    "Ich esse salz-reduziert": "Low Salt",
    "I follow a diet low in protein": "Low Protein",
    "Ich esse protein-arm": "Low Protein",
    "I follow a diet rich in protein": "High Protein",
    "Ich esse protein-reich": "High Protein",
    "I follow an environmentally friendly / sustainable diet": "Sustainable",
    "Ich ernähre mich umweltreundlich und nachhaltig": "Sustainable",
  }

  survey_df["diet"] = survey_df["diet"].apply(lambda x: safe_dict(x, diets, False))

  educations = {
    "Manditory School": "0:) primary education",
    "Middle school": "0:) primary education",
    "High school": "1.) secondary education",
    "Vocational school": "1.) secondary education",
    "master's diploma": "2.) tertiary education",
    "College / University": "2.) tertiary education",
    "Obligatorische Schule": "0:) primary education",
    "Weiterführende Schule": "0:) primary education",
    "Matura": "1.) secondary education",
    "Berufsschule": "1.) secondary education",
    "Meister- / eidg. Diplom": "2.) tertiary education",
    "Studium": "2.) tertiary education",
  }

  survey_df["education"] = survey_df["education"].apply(lambda x: safe_dict(x, educations, False))

  snack_frequencies = {
    "sehr selten bis nie": "0.) never",
    "never":"0.) never",
    "once or twice per year":"0.) never",
    "ca. monatlich":"1.) monthly",
    "monthly":"1.) monthly",
    "ca. wöchentlich":"2.) weekly",
    "weekly":"2.) weekly",
    "ca. 2-3 mal pro Woche":"2.) weekly",
    "ca. 4-5 mal pro Woche":"3.) almost daily",
    "daily":"3.) almost daily",
    "ca. täglich":"3.) almost daily",
  }

  snack_frequencies_int = {
    "sehr selten bis nie": 0,
    "never":0,
    "once or twice per year":0,
    "ca. monatlich":1,
    "monthly":1,
    "ca. wöchentlich":4,
    "weekly":4,
    "ca. 2-3 mal pro Woche":10,
    "ca. 4-5 mal pro Woche":20,
    "daily":31,
    "ca. täglich":31,
  }

  survey_df["snack_frequency_int"] = survey_df["snack_frequency"].apply(lambda x: safe_dict(x, snack_frequencies_int, False))
  survey_df["snack_frequency"] = survey_df["snack_frequency"].apply(lambda x: safe_dict(x, snack_frequencies, False))

  ar_frequencies = {
    "Never used":"0.) Never",
    "Noch nie benutz":"0.) Never",
    "Tried once or twice":"1.) Few Times",
    "Schon ein oder zwei Mal benutzt":"1.) Few Times",
    "I use it sometimes":"2.) Sometimes",
    "Ich benutze es hin und wieder privat":"2.) Sometimes",
    "I worked with it on a project":"3.) Regularly",
    "Ich habe an einem Projekt damit gearbeitet":"3.) Regularly",
    "I use it regularly for private purpose":"3.) Regularly",
    "Ich benutze es regelmäßig privat":"3.) Regularly",
    "It is part of my job on a regular basis":"3.) Regularly",
    "Ich komme auf der Arbeit regelmäßig damit in Kontakt":"3.) Regularly",
    "I am an expert / developer in the field":"4.) Expert",
    "Ich bin ein Experte / Entwickler auf dem Feld":"4.) Expert",
  }

  ar_frequencies_int = {
    "Never used":0,
    "Noch nie benutz":0,
    "Tried once or twice":1,
    "Schon ein oder zwei Mal benutzt":1,
    "I use it sometimes":2,
    "Ich benutze es hin und wieder privat":2,
    "I worked with it on a project":3,
    "Ich habe an einem Projekt damit gearbeitet":3,
    "I use it regularly for private purpose":3,
    "Ich benutze es regelmäßig privat":3,
    "It is part of my job on a regular basis":3,
    "Ich komme auf der Arbeit regelmäßig damit in Kontakt":3,
    "I am an expert / developer in the field":4,
    "Ich bin ein Experte / Entwickler auf dem Feld":4,
  }

  survey_df["ar_frequency_int"] = survey_df["ar_frequency"].apply(lambda x: safe_dict(x, ar_frequencies_int, False))
  survey_df["ar_frequency"] = survey_df["ar_frequency"].apply(lambda x: safe_dict(x, ar_frequencies, False))

  survey_df["BI_avg"] = survey_df[["BI1", "BI2","BI3"]].mean(axis=1, numeric_only=True)
  survey_df["EE_avg"] = survey_df[["EE1", "EE2","EE3"]].mean(axis=1, numeric_only=True)
  survey_df["FL_avg"] = survey_df[["FL2","FL3"]].mean(axis=1, numeric_only=True)
  survey_df["HM_avg"] = survey_df[["HM1", "HM2"]].mean(axis=1, numeric_only=True)
  survey_df["IE_avg"] = survey_df[["IE1", "IE2"]].mean(axis=1, numeric_only=True)
  survey_df["PE_avg"] = survey_df[["PE1", "PE2","PE3"]].mean(axis=1, numeric_only=True)
  survey_df["PI_avg"] = survey_df[["PI1", "PI2","PI3"]].mean(axis=1, numeric_only=True)
  survey_df["SI_avg"] = survey_df[["SI1", "SI2","SI3"]].mean(axis=1, numeric_only=True)
  
  survey_df.fillna(value=pd.np.nan, inplace=True)

  return survey_df


def render_box_per_col(col, survey_df):
  is_test = survey_df["group"] == "Test"
  is_control = survey_df["group"] == "Control"
  data = []
  data.append(go.Box(
    x = survey_df[col][is_test],
    name="test",
    marker = dict(
        color = 'rgb(7,40,89)'),
    line = dict(
        color = 'rgb(7,40,89)')
  ))
  data.append(go.Box(
    x = survey_df[col][is_control],
    name="control",
    marker = dict(
        color = 'rgb(107,174,214)'),
    line = dict(
        color = 'rgb(107,174,214)')
  ))

  graph = dcc.Graph(
    figure = go.Figure( 
      data = data,
      layout = go.Layout(
        showlegend=True,
        legend=go.layout.Legend(
            x=0,
            y=1.0
        ),
        margin=go.layout.Margin(l=40, r=0, t=40, b=30)
      )
    ),
    style={'height': 150},
    id='box_{}'.format(col)
  )

  graph_div = html.Div([graph], 
      style={'padding-top': '20',
            'padding-bottom': '20'})

  return graph_div

def data_per_col(col, survey_df):
  is_test = survey_df["group"] == "Test"
  is_control = survey_df["group"] == "Control"

  data = [
    go.Histogram(
      x = survey_df[col][is_test].sort_values(),
      name="test",
      opacity=0.75,
      marker = dict(
          color = 'rgb(7,40,89)'),
    ),
    go.Histogram(
      x = survey_df[col][is_control].sort_values(),
      name="control",
      opacity=0.75,
      marker = dict(
          color = 'rgb(107,174,214)'),
    )
  ]
  return data

def render_hist_per_col(col, survey_df):
  data = data_per_col(col, survey_df)

  graph = dcc.Graph(
    figure = go.Figure( 
      data = data,
      layout = go.Layout(
        showlegend=True,
        legend=go.layout.Legend(
            x=0,
            y=1.0
        ),
        margin=go.layout.Margin(l=40, r=0, t=40, b=30)
      )
    ),
    style={'height': 300}
  )

  graph_div = html.Div([graph], 
      style={'padding-top': '20',
            'padding-bottom': '20'})

  return graph_div

def render_table(survey_df):
  table =  dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in survey_df.columns],
    data=survey_df.to_dict("rows"),
  )
  return table  

#def load_user_tracking(user_id, task_id):
#  filename = tracking_files[user_id][task_id]

def calc_p_whitney(col, s, ns):
  Rg = col.rank()
  
  nt = col[s].count()
  nc = col[ns].count()

  if (Rg == Rg.iloc[0]).all():
    return Rg[s].sum() - nt * (nt + 1) / 2, 0.5, nt, nc

  u, p = stats.mannwhitneyu(Rg[s], Rg[ns])
  return p

# def calc_p_whitney(colname, survey_df):
#   col = survey_df[colname]
#   istest = survey_df["group"]=="Test"
#   iscontrol = survey_df["group"]=="Control"
#   Rg = col.rank()
#
#   nt = col[istest].count()
#   nc = col[iscontrol].count()
#
#   if (Rg == Rg.iloc[0]).all():
#     return Rg[istest].sum() - nt * (nt + 1) / 2, 0.5, nt, nc
#
#   u, p = mannwhitneyu(Rg[istest], Rg[iscontrol])
#   return u, p, nt, nc

def calc_p_t(colname, survey_df):
  col = survey_df[colname]
  istest = survey_df["group"]=="Test"
  iscontrol = survey_df["group"]=="Control"

  t, p = ttest_ind(col[istest].values, col[iscontrol].values, axis=0, nan_policy='omit')
  return t, p

def table_group(task_nr, survey_df, header):
  istest = survey_df["group"] == "Test"
  iscontrol = survey_df["group"] == "Control"

  isoverweight = survey_df["bmi"] > 25
  isnormal = survey_df["bmi"] <= 25
  
  iseducated = survey_df["bmi"] > 25

  isliterate = survey_df["FL_avg"] > 4.5
  isilliterate = survey_df["FL_avg"] <= 4.5

  cols = ["nutri_score",
          "energy",
          "sat_fat",
          "sugar",
          "natrium",
          "protein",
          "fiber",
          "health_percentage",
          "time"]

  data = pd.DataFrame()
  for col in cols:
    col_name = "{}_{}".format(col, task_nr)
    data.loc[col, "N Total"] = "[{}]".format(int(data.loc[col, "N Test"] + data.loc[col, "N Control"]))
    data.loc[col, "mean Total"] = "{:.2f}".format(survey_df[col_name].mean())
    data.loc[col, "SD Total"] = "({:.2f})".format(survey_df[col_name].std())
    
    p = calc_p_whitney(survey_df["group"], istest, iscontrol)
    data.loc[col, "p group"] = "{:.4f}".format(p)
    data.loc[col, "N Test"] = "[{}]".format(int(len(survey_df[istest])))
    data.loc[col, "mean Test"] = "{:.2f}".format(survey_df[col_name][istest].mean())
    data.loc[col, "SD Test"] = "({:.2f})".format(survey_df[col_name][istest].std())
    data.loc[col, "N Control"] = "[{}]".format(int(len(survey_df[iscontrol])))
    data.loc[col, "mean Control"] = "{:.2f}".format(survey_df[col_name][iscontrol].mean())
    data.loc[col, "SD Control"] = "({:.2f})".format(survey_df[col_name][iscontrol].std())
    
    p = calc_p_whitney(survey_df["FL_avg"], isliterate, isilliterate)
    data.loc[col, "p FL"] = "{:.4f}".format(p)
    data.loc[col, "N FL>4.5"] = "[{}]".format(int(len(survey_df[isliterate])))
    data.loc[col, "mean FL>4.5"] = "{:.2f}".format(survey_df[col_name][isliterate].mean())
    data.loc[col, "SD FL>4.5"] = "({:.2f})".format(survey_df[col_name][isliterate].std())
    data.loc[col, "N FL<=4.5"] = "[{}]".format(int(len(survey_df[isilliterate])))
    data.loc[col, "mean FL<=4.5"] = "{:.2f}".format(survey_df[col_name][isilliterate].mean())
    data.loc[col, "SD FL<=4.5"] = "({:.2f})".format(survey_df[col_name][isilliterate].std())

    p = calc_p_whitney(survey_df["FL_avg"], isliterate, isilliterate)
    data.loc[col, "p FL"] = "{:.4f}".format(p)
    data.loc[col, "N FL>4.5"] = "[{}]".format(int(len(survey_df[isliterate])))
    data.loc[col, "mean FL>4.5"] = "{:.2f}".format(survey_df[col_name][isliterate].mean())
    data.loc[col, "SD FL>4.5"] = "({:.2f})".format(survey_df[col_name][isliterate].std())
    data.loc[col, "N FL<=4.5"] = "[{}]".format(int(len(survey_df[isilliterate])))
    data.loc[col, "mean FL<=4.5"] = "{:.2f}".format(survey_df[col_name][isilliterate].mean())
    data.loc[col, "SD FL<=4.5"] = "({:.2f})".format(survey_df[col_name][isilliterate].std())


  data["index"] = data.index
  data_dict = data.to_dict("rows")

  table =  dash_table.DataTable(
    id='table',
    columns=[ {"name": "", "id": "index"},
              {"name": "u", "id": "u"},
              {"name": "p", "id": "p"},
              {"name": "Total mean", "id": "mean Total"},
              {"name": "(SD)", "id": "SD Total"},
              {"name": "[N]", "id": "Total N"},
              {"name": "Test mean", "id": "mean Test"},
              {"name": "(SD)", "id": "SD Test"},
              {"name": "[N]", "id": "Test N"},
              {"name": "Control mean", "id": "mean Control"},
              {"name": "(SD)", "id": "SD Control"},
              {"name": "[N]", "id": "Control N"}],
    data=data_dict,
    style_as_list_view=True,
    style_cell={'padding': '5px'},
    style_header={
        'backgroundColor': 'white',
        'fontWeight': 'bold'
    },
    style_cell_conditional=[
        {
            'if': {'column_id': c},
            'textAlign': 'left'
        } for c in ['index','SD Total', 'SD Test', 'SD Control', 'Total N', 'Test N', 'Control N']
    ],
  )

  ret_div = html.Div([
    html.H1("Task {}".format(task_nr)),
    html.H2(header),
    html.Div( [table],
              style={ 'padding-top': '10',
                      'padding-bottom': '30',
                      'padding-left': '30',
                      'padding-right': '5'}),
    render_box_per_col("nutri_score_{}".format(task_nr), survey_df),
    render_hist_per_col("nutri_label_{}".format(task_nr), survey_df.sort_values(by="nutri_label_{}".format(task_nr)))
  ])
  
  return ret_div

def creat_mean_desc(col, survey_df, header = None):
  data = pd.DataFrame()
  istest = survey_df["group"] == "Test"
  iscontrol = survey_df["group"] == "Control"
  if isinstance(header, str):
    title = html.H3(header)
  else:
    title = html.H3(col)

  ret_div = html.Div([title,
                      html.P("Total mean (SD) \t\t {:.2f} ({:.2f})".format(survey_df[col].mean(), survey_df[col].std())),
                      html.P("Test mean (SD) \t\t {:.2f} ({:.2f})".format(survey_df[col][istest].mean(), survey_df[col][istest].std())),
                      html.P("Control mean (SD) \t\t {:.2f} ({:.2f})".format(survey_df[col][iscontrol].mean(), survey_df[col][iscontrol].std())),
                      render_box_per_col(col, survey_df)])

  return ret_div

def create_count_desc(col, survey_df, header=None):
  data = pd.DataFrame()
  istest = survey_df["group"] == "Test"
  iscontrol = survey_df["group"] == "Control"
  survey_df.loc[survey_df[col].isna(),col] = "Missing"
  data["count Total"] = survey_df[col].value_counts()
  data["% Total"] = (data["count Total"] / data["count Total"].sum() * 100).apply(lambda x : "({:.1f}%)".format(x))
  data.loc["Total", "count Total"] = data["count Total"].sum()
  data["count Test"] = survey_df[col][istest].value_counts()
  data["% Test"] = (data["count Test"] / data["count Test"].sum() * 100).apply(lambda x : "({:.1f}%)".format(x))
  data.loc["Total", "count Test"] = data["count Test"].sum()
  data["count Control"] = survey_df[col][iscontrol].value_counts()
  data["% Control"] = (data["count Control"] / data["count Control"].sum() * 100).apply(lambda x : "({:.1f}%)".format(x))
  data.loc["Total", "count Control"] = data["count Control"].sum()
  data.loc["Total", ["% Total","% Test","% Control"]] = ""
  data["index"] = data.index

  data = data.sort_index()

  data_dict = data.to_dict("rows")

  table =  dash_table.DataTable(
    id='table',
    columns=[ {"name": "", "id": "index"},
              {"name": "Total N", "id": "count Total"},
              {"name": "(%)", "id": "% Total"},
              {"name": "Test N", "id": "count Test"},
              {"name": "(%)", "id": "% Test"},
              {"name": "Control N", "id": "count Control"},
              {"name": "(%)", "id": "% Control"},],
    data=data_dict,
    style_as_list_view=True,
    style_cell={'padding': '5px'},
    style_header={
        'backgroundColor': 'white',
        'fontWeight': 'bold'
    },
    style_cell_conditional=[
        {
            'if': {'column_id': c},
            'textAlign': 'left'
        } for c in ['index', '% Total', '% Test', '% Control']
    ],
  )

  if isinstance(header, str):
    title = html.H3(header)
  else:
    title = html.H3(col)

  ret_div = html.Div([title,
                      html.Div( [table],
                                style={ 'padding-top': '10',
                                        'padding-bottom': '30',
                                        'padding-left': '30',
                                        'padding-right': '5'}),
                      render_hist_per_col(col, survey_df),                  
                    ])

  return ret_div

def get_question_text_save(col, questions_df, question_ids):
  try:
    question_text = questions_df[" question.text,"][question_ids[col]]
  except:
    question_text = "Error: Question wasn't found"
  return question_text

def create_survey(cols, survey_df, header):
  questionsfile = os.path.join(BASEPATH, "questionlayout-evaluation.csv")
  questions_df = pd.read_csv(questionsfile, sep=";", index_col="question.id")
  questions_df["time_1"] = "task 1"
  questions_df["time_2"] = "task 2"
  questions_df["time_3"] = "task 3"
  questions_df["time_4"] = "task 4"

  question_ids = {
    "IE1":"jcruLQD1jtsb",
    "IE2":"eaTgLd8mTqIl",
    "PE1":"q0mA3PRRFjx7",
    "PE2":"sBItcnzLbeab",
    "PE3":"HNBvOMYBB0aG",
    "EE1":"MEMNKBeL1Yx1",
    "EE2":"erPaRi4mPyPG",
    "EE3":"QVMeswBQSWAi",
    "SI1":"xdCMMXgxnem1",
    "SI2":"wfA9uqPz8cRt",
    "SI3":"xUlfUW6JGEav",
    "HM1":"JYEh0RF8Fm8b",
    "HM2":"DuGG9VdyhxCd",
    "PI1":"Y4v77TAeZzKs",
    "PI2":"QVzNIkgWgGxB",
    "PI3":"BQXqCdJgdxle",
    "BI1":"b4YNQSqEHFaE",
    "BI2":"GfV0SwI2TmuK",
    "BI3":"PEWOeMEEayNA",
    "FL1":"Wiq2wP97n7RO",
    "FL2":"zDVqi1Ti9Nwq",
    "FL3":"WeELc4DWjE6P",
    "time_1":"time_1",
    "time_2":"time_2",
    "time_3":"time_3",
    "time_4":"time_4",
  }
  
  question_texts = {col: get_question_text_save(col, questions_df, question_ids) for col in cols}
  question_texts["Average"] = "--- Average ---"

  survey_df_tmp = survey_df.loc[:,cols]
  survey_df_tmp.loc[:,"Average"] = survey_df_tmp.mean(axis=1,numeric_only=True)
  survey_df_tmp.loc[:,"group"] = survey_df.loc[:,"group"]
  cols.append("Average")

  data = pd.DataFrame()
  istest = survey_df["group"] == "Test"
  iscontrol = survey_df["group"] == "Control"
  data["mean Total"] = survey_df_tmp[cols].mean().apply(lambda x : "{:.2f}".format(x))
  data["SD Total"] = survey_df_tmp[cols].std().apply(lambda x : "({:.2f})".format(x))
  data["mean Test"] = survey_df_tmp[cols][istest].mean().apply(lambda x : "{:.2f}".format(x))
  data["SD Test"] = survey_df_tmp[cols][istest].std().apply(lambda x : "({:.2f})".format(x))
  data["mean Control"] = survey_df_tmp[cols][iscontrol].mean().apply(lambda x : "{:.2f}".format(x))
  data["SD Control"] = survey_df_tmp[cols][iscontrol].std().apply(lambda x : "({:.2f})".format(x))
  data["question"] = pd.Series(question_texts)
  
  for col in cols:
    _, data.loc[col, "p (rank)"], _, _ = calc_p_whitney(col, survey_df_tmp)
    _, data.loc[col, "p (t)"] = calc_p_t(col, survey_df_tmp)

  data["p (rank)"] = data["p (rank)"].apply(lambda x : "{:.4f}".format(x))
  data["p (t)"] = data["p (t)"].apply(lambda x : "{:.4f}".format(x))

  data_dict = data.to_dict("rows")

  table =  dash_table.DataTable(
    id='table',
    columns=[ {"name": "", "id": "question"},
              {"name": "Total mean", "id": "mean Total"},
              {"name": "(SD)", "id": "SD Total"},
              {"name": "Test mean", "id": "mean Test"},
              {"name": "(SD)", "id": "SD Test"},
              {"name": "Control mean", "id": "mean Control"},
              {"name": "(SD)", "id": "SD Control"},
              {"name": "p (rank)", "id": "p (rank)"},
              {"name": "p (t)", "id": "p (t)"}],
    data=data_dict,
    style_as_list_view=True,
    style_cell={'padding': '5px'},
    style_header={
        'backgroundColor': 'white',
        'fontWeight': 'bold'
    },
    style_cell_conditional=[
        {
            'if': {'column_id': c},
            'textAlign': 'left'
        } for c in ['question', 'SD Total', 'SD Test', 'SD Control', "u"]
    ],
  )

  ret_div = html.Div([html.H3(header),
                      html.Div( [table],
                                style={ 'padding-top': '10',
                                        'padding-bottom': '30',
                                        'padding-left': '30',
                                        'padding-right': '5'})])

  return ret_div


def bmi_class(bmi):
  if bmi < 18.5:
    return "0:) Underweight (BMI < 18.5)"
  elif bmi < 25:
    return "1.) Normal (18.5 ≤ BMI < 25)"
  elif bmi < 30:
    return "2.) Overweight (25 ≤ BMI < 30)"
  else:
    return "3.) Obese (30 ≤ BMI"

def safe_dict(_key, _dict, _int=True):
  try:
    if _int:
      val = _dict[int(_key)]
    else:
      val = _dict[_key]
  except:
    val = None
  return val
  

app.layout = html.Div([
    html.Button("Refresh", id="refresh"),
    html.Div([], 
      id="graphs", 
      style={'width':'70%',
            'padding-top': '40',
            'padding-bottom': '10',
            'padding-left': '50',
            'padding-right': '50'}),
])



@app.callback(Output("graphs", "children"),
              [Input("refresh", "n_clicks")])
def update_survey(_):
  survey_df = combine_all_data()

  print("printing new data")
  return [creat_mean_desc("age", survey_df, "Age"),
          create_count_desc("age_class", survey_df, "Age"),
          creat_mean_desc("bmi", survey_df, "Body Mass Index"),
          create_count_desc("bmi_class", survey_df, "Weight"),
          create_count_desc("gender", survey_df, "Gender"),
          create_count_desc("education", survey_df, "Education"),
          create_count_desc("snack_frequency", survey_df, "Machine Usage Frequency"),
          creat_mean_desc("snack_frequency_int", survey_df, "Machine Usage Frequency"),
          create_count_desc("ar_frequency", survey_df, "AR Usage Frequency"),
          create_survey(["ar_frequency_int"],
                        survey_df,
                        "AR Frequency"),
          html.Hr(),
          table_group(1, survey_df, "Choose a snack of your choice"),
          html.Hr(),
          table_group(2, survey_df,"Choose a drink of your choice"),
          html.Hr(),
          table_group(3, survey_df,"Choose the healthiest snack"),
          html.Hr(),
          table_group(4, survey_df,"Choose the healthiest drink"),
          html.Hr(),
          create_survey(["time_1", "time_2","time_3","time_4"],
                        survey_df,
                        "Time Taken per Task"),
          html.Hr(),              
          create_survey(["IE1", "IE2"],
                        survey_df,
                        "Intervention Effect"),
          create_survey(["PE1", "PE2", "PE3"],
                        survey_df,
                        "Performance Expectancy"),
          create_survey(["EE1", "EE2", "EE3"],
                        survey_df,
                        "Effort Expectancy"),
          create_survey(["SI2", "SI3"],
                        survey_df,
                        "Social Influence"),
          create_survey(["HM1", "HM2"],
                        survey_df,
                        "Hedonic Motivations"),
          create_survey(["PI1", "PI2", "PI3"],
                        survey_df,
                        "Personal Innovativeness"),
          create_survey(["BI1", "BI2", "BI3"],
                        survey_df,
                        "Behavioural Intention"),
          create_survey(["FL2", "FL3"],
                        survey_df,
                        "Food Literacy (ohne FL1)"),
          create_survey(["FL1", "FL2", "FL3"],
                        survey_df,
                        "Food Literacy"),
          create_survey(["SI1"],
                        survey_df,
                        "Observation Bias"),
          #render_table(survey_df)
        ]


if __name__ == '__main__':
  app.run_server(debug=True, host="0.0.0.0", port=80)