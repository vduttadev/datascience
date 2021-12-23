import os
import pandas as pd
from .trad_plan_analysis.adjudicate import run_traditional_plan

dir_path = os.path.dirname(os.path.realpath(__file__))

path = os.path.join(dir_path, 'data/dummy_plan_v3.csv')
plan_df = pd.read_csv(path)
type_summary = run_traditional_plan(plan_df)

type_summary = type_summary.sort_index()
out_path = os.path.join(dir_path, 'data/trad_output_sample.csv')
type_summary.to_csv(out_path)
