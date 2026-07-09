import re
import ast
import xml.etree.ElementTree as ET
from molmass import Formula
import json  # 用于将MSPeaks转为JSON字符串
import pandas as pd  # 用于数据处理
import numpy as np  # 用于数值计算


def parse_cef_file(file_path1, remove_null_molecule_name=False):


    tree = ET.parse(file_path1)
    root = tree.getroot()
    data = []

    for compound in root.findall('.//Compound'):
        location = compound.find('.//Location')
        results = compound.find('.//Results')
        molecule = results.find('.//Molecule') if results is not None else None
        database = molecule.find('.//Database') if molecule is not None else None
        accession = database.find('.//Accession') if database is not None else None
        spectrum = compound.find('.//Spectrum')
        ms_peaks = spectrum.findall('.//p') if spectrum is not None else []


        peaks_data = []
        for peak in ms_peaks:
            x = peak.get('x')
            y = peak.get('y')
            x = float(x) if x != 'null' else np.nan
            y = float(y) if y != 'null' else np.nan

            if not np.isnan(y) and y > 8:
                peaks_data.append((x, y))


        m_loc = location.get('m') if location is not None else 'null'
        rt_loc = float(location.get('rt')) if location is not None and location.get('rt') != 'null' else np.nan
        a_loc = location.get('a') if location is not None else 'null'
        y_loc = location.get('y') if location is not None else 'null'
        name = molecule.get('name') if molecule is not None else 'null'
        formula = molecule.get('formula') if molecule is not None else 'null'
        cas_id = accession.get('id') if accession is not None else 'null'

        exact_mass = 'null'
        if formula != 'null':
            try:
                formula_obj = Formula(formula)
                exact_mass = f"{formula_obj.isotope.mass:.6f}"
            except Exception as e:
                print(f"Error processing formula {formula}: {e}")
                exact_mass = 'error'


        rt_decimal_places = len(str(rt_loc).split('.')[-1]) if not np.isnan(rt_loc) else 0

        if not remove_null_molecule_name or name != 'null':
            data.append([
                m_loc,
                rt_loc,
                a_loc,
                y_loc,
                name,
                formula,
                cas_id,
                peaks_data,
                exact_mass
            ])

    columns = ['m', 'rt', 'a', 'y', 'Molecule Name', 'Formula', 'CAS ID', 'MSPeaks', 'suremass']
    df = pd.DataFrame(data, columns=columns)


    df.drop_duplicates(subset='MSPeaks', inplace=True)

    return df


def match_and_export_to_excel(excel_path, cef_path, output_path):

    excel_data = pd.read_excel(excel_path)


    cef_data = parse_cef_file(cef_path)


    matched_data = []
    for _, row in excel_data.iterrows():
        excel_rt = row['high rt']



        potential_matches = cef_data[abs(cef_data['rt'] - excel_rt) <= 0.06]
        if potential_matches.empty:
            matched_entry = {
                "high Molecule name": row["high Molecule Name"],
                "high m": row["high m"],
                "high rt": row["high rt"],
                "high a": row["high a"],
                "high y": row["high y"],
                "high formula": row["high Formula"],
                "high CAS ID": row["high CAS ID"],
                "high 匹配分数": row["匹配因子"],
                "high 基峰信噪比": row["基峰信噪比"],
                "high 基峰解卷积的面积": row["基峰解卷积的面积"],
                "high 组分 RI": row["组分 RI"],
                "high 谱库 RI": row["谱库 RI"],
                "high MSPeaks": row["high MSPeaks"],
                "high suremass": row["high suremass"],
                "low Molecule name": None,
                "low m": None,
                "low rt": None,
                "low a": None,
                "low y": None,
                "low formula": None,
                "low CAS ID": None,
                "low MSPeaks": None,
                "low suremass": None
            }
            matched_data.append(matched_entry)

        else:

            potential_matches = potential_matches[pd.to_numeric(potential_matches['a'], errors='coerce').notna()]
            potential_matches['a'] = potential_matches['a'].astype(float)


            for _, compound in potential_matches.iterrows():
                matched_entry = {
                    "high Molecule name": row["high Molecule Name"],
                    "high m": row["high m"],
                    "high rt": row["high rt"],
                    "high a": row["high a"],
                    "high y": row["high y"],
                    "high formula": row["high Formula"],
                    "high CAS ID": row["high CAS ID"],
                    "high 基峰信噪比": row["基峰信噪比"],
                    "high 基峰解卷积的面积": row["基峰解卷积的面积"],
                    "high 匹配分数": row["匹配因子"],
                    "high 组分 RI": row["组分 RI"],
                    "high 谱库 RI": row["谱库 RI"],
                    "high MSPeaks": (row["high MSPeaks"]),
                    "high suremass": row["high suremass"],
                    "low Molecule name": compound["Molecule Name"],
                    "low m": compound["m"],
                    "low rt": compound["rt"],
                    "low a": compound["a"],
                    "low y": compound["y"],
                    "low formula": compound["Formula"],
                    "low CAS ID": compound["CAS ID"],
                    "low MSPeaks": compound["MSPeaks"],
                    "low suremass": compound["suremass"]
                }
                matched_data.append(matched_entry)


    matched_df = pd.DataFrame(matched_data)
    matched_df.to_excel(output_path, index=False)
    print(f"saved {output_path}")


# 调用函数
if __name__ == "__main__":

    excel_path = r".\The Excel file path output in Step 2"
    cef_path = r".\Path of the CEF file exported by the unknown substance analysis software"
    output_path = r"\The path of the exported Excel file"
    match_and_export_to_excel(excel_path, cef_path, output_path)
