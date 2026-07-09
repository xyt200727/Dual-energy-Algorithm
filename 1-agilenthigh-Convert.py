import os
import re
import ast
import xml.etree.ElementTree as ET
from molmass import Formula
import json
import pandas as pd
import numpy as np

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

    columns = ['high m', 'high rt', 'high a', 'high y', 'high Molecule Name', 'high Formula', 'high CAS ID', 'high MSPeaks', 'high suremass']
    df = pd.DataFrame(data, columns=columns)
    return df

def process_cef_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    cef_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.cef')]

    for cef_file in cef_files:
        input_path = os.path.join(input_folder, cef_file)
        output_filename = os.path.splitext(cef_file)[0] + '.xlsx'
        output_path = os.path.join(output_folder, output_filename)

        df = parse_cef_file(input_path)
        df.to_excel(output_path, index=False)

if __name__ == "__main__":
    input_dir = r".\CEF file path"
    output_dir = r".\CEF to excel file output path"
    process_cef_folder(input_dir, output_dir)
